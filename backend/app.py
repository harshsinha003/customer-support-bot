from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from config import get_settings
from database import get_db, init_db, close_db
from models import ChatSession, Message, Escalation, SessionStatus, MessageRole, EscalationTrigger
from llm_service import LLMService

settings = get_settings()
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
import os
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Initialize LLM Service
llm_service = LLMService()

# Pydantic Models
class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None

class CreateSessionResponse(BaseModel):
    session_id: str
    status: str
    created_at: datetime

class SendMessageRequest(BaseModel):
    session_id: str
    message: str

class MessageResponse(BaseModel):
    role: str
    content: str
    confidence_score: Optional[float]
    timestamp: datetime

class SendMessageResponse(BaseModel):
    session_id: str
    response: str
    confidence_score: float
    should_escalate: bool
    timestamp: datetime

class ConversationHistoryResponse(BaseModel):
    session_id: str
    status: str
    messages: List[MessageResponse]

class EscalateRequest(BaseModel):
    session_id: str
    reason: Optional[str] = "User requested escalation"

class EscalateResponse(BaseModel):
    session_id: str
    escalated: bool
    summary: str
    escalated_at: datetime

# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()
    print("[OK] Database initialized successfully")
    print(f"[OK] {settings.APP_NAME} is running!")
    
    # Check which AI provider is configured
    ai_provider = getattr(settings, 'AI_PROVIDER', 'mock').lower()
    if ai_provider == "gemini":
        gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
        if gemini_key and gemini_key != "paste-your-actual-gemini-key-here":
            print("[OK] Gemini API key configured - using Google Gemini for responses")
        else:
            print("[INFO] No Gemini API key configured - using mock responses for demo")
            print("   To enable AI responses, add your Gemini API key to the .env file")
    elif ai_provider == "openai":
        openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        if openai_key and openai_key != "sk-your-openai-key-here":
            print("[OK] OpenAI API key configured - using GPT-4 for responses")
        else:
            print("[INFO] No OpenAI API key configured - using mock responses for demo")
            print("   To enable AI responses, add your OpenAI API key to the .env file")
    else:
        print("[INFO] Using mock responses for demo mode")
        print("   To enable AI responses, configure AI_PROVIDER and add API key to the .env file")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await close_db()
    print("Database connections closed")

# API Endpoints
@app.get("/")
async def root():
    """Serve the frontend HTML"""
    frontend_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_file):
        return FileResponse(frontend_file)
    return {"status": "ok", "message": "AI Customer Support Bot API", "version": "1.0"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "AI Customer Support Bot API", "version": "1.0"}

@app.post("/api/chat/create", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    
    new_session = ChatSession(
        session_id=session_id,
        user_id=request.user_id,
        status=SessionStatus.ACTIVE
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return CreateSessionResponse(
        session_id=new_session.session_id,
        status=new_session.status.value,
        created_at=new_session.created_at
    )

@app.post("/api/chat/message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get AI response"""
    
    # Fetch session
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == request.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Get conversation history
    messages_result = await db.execute(
        select(Message)
        .where(Message.session_id == request.session_id)
        .order_by(Message.timestamp)
    )
    messages = messages_result.scalars().all()
    
    conversation_history = [
        {"role": msg.role.value, "content": msg.content}
        for msg in messages
    ]
    
    # Save user message
    user_message = Message(
        session_id=request.session_id,
        role=MessageRole.USER,
        content=request.message
    )
    db.add(user_message)
    
    # Generate AI response
    response_text, confidence_score, should_escalate = await llm_service.generate_response(
        request.message,
        conversation_history
    )
    
    # Save assistant message
    assistant_message = Message(
        session_id=request.session_id,
        role=MessageRole.ASSISTANT,
        content=response_text,
        confidence_score=confidence_score
    )
    db.add(assistant_message)
    
    # Update session timestamp
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return SendMessageResponse(
        session_id=request.session_id,
        response=response_text,
        confidence_score=confidence_score,
        should_escalate=should_escalate,
        timestamp=assistant_message.timestamp
    )

@app.get("/api/chat/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history for a session"""
    
    # Fetch session
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.timestamp)
    )
    messages = messages_result.scalars().all()
    
    message_list = [
        MessageResponse(
            role=msg.role.value,
            content=msg.content,
            confidence_score=msg.confidence_score,
            timestamp=msg.timestamp
        )
        for msg in messages
    ]
    
    return ConversationHistoryResponse(
        session_id=session.session_id,
        status=session.status.value,
        messages=message_list
    )

@app.post("/api/chat/escalate", response_model=EscalateResponse)
async def escalate_to_human(
    request: EscalateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Escalate conversation to human agent"""
    
    # Fetch session
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == request.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get conversation history for summary
    messages_result = await db.execute(
        select(Message)
        .where(Message.session_id == request.session_id)
        .order_by(Message.timestamp)
    )
    messages = messages_result.scalars().all()
    
    conversation_history = [
        {"role": msg.role.value, "content": msg.content}
        for msg in messages
    ]
    
    # Generate conversation summary
    summary = await llm_service.summarize_conversation(conversation_history)
    
    # Create escalation record
    escalation = Escalation(
        session_id=request.session_id,
        trigger_type=EscalationTrigger.CUSTOMER_DRIVEN,
        reason=request.reason
    )
    db.add(escalation)
    
    # Update session status
    session.status = SessionStatus.ESCALATED
    session.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(escalation)
    
    return EscalateResponse(
        session_id=request.session_id,
        escalated=True,
        summary=summary,
        escalated_at=escalation.escalated_at
    )

@app.delete("/api/chat/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session and all related data"""
    
    result = await db.execute(
        select(ChatSession).where(ChatSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()
    
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
