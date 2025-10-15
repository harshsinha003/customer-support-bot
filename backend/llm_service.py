import json
import re
import random
from typing import List, Dict, Tuple
from config import get_settings

settings = get_settings()

class LLMService:
    def __init__(self):
        self.ai_provider = settings.AI_PROVIDER.lower()
        self.use_ai = False
        
        if self.ai_provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
                self.use_ai = True
                self.ai_type = "gemini"
                print("[OK] Using Google Gemini for responses")
            except ImportError:
                print("[WARNING] Gemini dependencies not available, using mock responses")
                self.use_ai = False
        elif self.ai_provider == "openai" and settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
                self.llm = ChatOpenAI(
                    model=settings.OPENAI_MODEL,
                    temperature=0.7,
                    openai_api_key=settings.OPENAI_API_KEY
                )
                self.use_ai = True
                self.ai_type = "openai"
                print("[OK] Using OpenAI GPT-4 for responses")
            except ImportError:
                print("[WARNING] OpenAI dependencies not available, using mock responses")
                self.use_ai = False
        else:
            print(f"[INFO] No {self.ai_provider.upper()} API key provided, using mock responses for demo")

        self.faq_data = self._load_faqs()
        self.escalation_keywords = [
            "speak to human", "talk to agent", "human support",
            "real person", "escalate", "supervisor", "manager"
        ]
        
    def _load_faqs(self) -> List[Dict]:
        """Load FAQ data from JSON file"""
        try:
            with open("../data/faqs.json", "r") as f:
                data = json.load(f)
                return data.get("faqs", [])
        except FileNotFoundError:
            print("Warning: faqs.json not found")
            return []
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in faqs.json")
            return []
    
    def _search_faq(self, query: str) -> str:
        """Search FAQ database for relevant answers"""
        query_lower = query.lower()
        for faq in self.faq_data:
            keywords = faq.get("keywords", [])
            if any(keyword.lower() in query_lower for keyword in keywords):
                return faq["answer"]
        return None
    
    def _check_escalation_keywords(self, message: str) -> bool:
        """Check if message contains escalation keywords"""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in self.escalation_keywords)
    
    def _detect_conversation_loop(self, conversation_history: List[Dict]) -> bool:
        """Detect if conversation is in a loop"""
        if len(conversation_history) < 6:
            return False
        
        recent_assistant_messages = [
            msg["content"] for msg in conversation_history[-6:]
            if msg["role"] == "assistant"
        ]
        
        if len(recent_assistant_messages) >= 3:
            # Check if same response appears 3+ times
            for msg in recent_assistant_messages:
                if recent_assistant_messages.count(msg) >= settings.MAX_LOOP_DETECTION:
                    return True
        return False
    
    async def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict]
    ) -> Tuple[str, float, bool]:
        """
        Generate response using LLM with conversation context or mock responses
        Returns: (response, confidence_score, should_escalate)
        """
        
        # Check for explicit escalation request
        if self._check_escalation_keywords(user_message):
            return (
                "I understand you'd like to speak with a human agent. Let me connect you to our support team.",
                1.0,
                True
            )
        
        # Check for conversation loop
        if self._detect_conversation_loop(conversation_history):
            return (
                "I notice we're having difficulty resolving your issue. Let me connect you with a human agent who can better assist you.",
                0.5,
                True
            )
        
        # Search FAQ first
        faq_answer = self._search_faq(user_message)
        
        if self.use_ai:
            if self.ai_type == "gemini":
                return await self._generate_gemini_response(user_message, conversation_history, faq_answer)
            elif self.ai_type == "openai":
                return await self._generate_openai_response(user_message, conversation_history, faq_answer)
        
        return self._generate_mock_response(user_message, faq_answer)
    
    def _calculate_confidence(self, response: str, faq_match: str) -> float:
        """Calculate confidence score for the response"""
        confidence = 0.8  # Base confidence
        
        # Higher confidence if FAQ match
        if faq_match:
            confidence = 0.95
        
        # Lower confidence for uncertainty phrases
        uncertainty_phrases = [
            "i'm not sure", "i don't know", "uncertain",
            "might be", "possibly", "perhaps", "maybe"
        ]
        if any(phrase in response.lower() for phrase in uncertainty_phrases):
            confidence -= 0.3
        
        # Lower confidence for very short responses
        if len(response.split()) < 10:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    async def _generate_gemini_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        faq_answer: str
    ) -> Tuple[str, float, bool]:
        """Generate response using Google Gemini"""
        
        # Create system prompt
        system_prompt = """You are a helpful AI Customer Support Assistant for a technology company. Your role is to:
1. Answer customer questions accurately and professionally about products and services
2. Help with account issues, technical problems, billing inquiries, and general support
3. Use the FAQ information provided when relevant to give accurate responses
4. Maintain a friendly yet professional tone
5. Guide customers through troubleshooting steps when needed
6. If you're uncertain about specific policies or technical details, acknowledge it and suggest contacting human support

Company Context: We are a technology company providing software solutions and services to customers worldwide.

FAQ Context: {faq_context}

If you cannot answer confidently about company policies or technical issues, suggest contacting our support team at support@company.com or using live chat."""
        
        faq_context = faq_answer if faq_answer else "No specific FAQ match found."
        
        # Build conversation context
        conversation_text = ""
        for msg in conversation_history[-settings.MAX_CONVERSATION_HISTORY:]:
            role = "Customer" if msg["role"] == "user" else "Support"
            conversation_text += f"{role}: {msg['content']}\n"
        
        # Create full prompt
        full_prompt = f"""{system_prompt.format(faq_context=faq_context)}

Previous conversation:
{conversation_text}

Customer: {user_message}
Support:"""
        
        try:
            # Generate response with Gemini
            response = await self._call_gemini_async(full_prompt)
            response_text = response.strip()
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(response_text, faq_answer)
            
            # Determine if escalation is needed
            should_escalate = confidence_score < settings.CONFIDENCE_THRESHOLD
            
            if should_escalate:
                response_text += "\n\nWould you like me to connect you with a human agent for more detailed assistance?"
            
            return response_text, confidence_score, should_escalate
            
        except Exception as e:
            print(f"Error generating Gemini response: {e}")
            return (
                "I'm experiencing technical difficulties. Let me connect you with a human agent.",
                0.0,
                True
            )
    
    async def _call_gemini_async(self, prompt: str) -> str:
        """Async wrapper for Gemini API call"""
        import asyncio
        
        def _sync_call():
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                raise e
        
        # Run in executor to make it async
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_call)
    
    async def _generate_openai_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        faq_answer: str
    ) -> Tuple[str, float, bool]:
        """Generate response using OpenAI"""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        # Create system prompt
        system_prompt = """You are a helpful customer support assistant. Your role is to:
1. Answer customer questions accurately and professionally
2. Use the FAQ information provided when relevant
3. Maintain context from previous conversation
4. Be concise but friendly
5. If you're uncertain or the question is outside your scope, acknowledge it

FAQ Context: {faq_context}

If you cannot answer confidently, say so and suggest human assistance."""
        
        faq_context = faq_answer if faq_answer else "No specific FAQ match found."
        
        # Build conversation context
        messages = [
            SystemMessage(content=system_prompt.format(faq_context=faq_context))
        ]
        
        # Add conversation history (last N messages)
        for msg in conversation_history[-settings.MAX_CONVERSATION_HISTORY:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current user message
        messages.append(HumanMessage(content=user_message))
        
        # Generate response
        try:
            response = await self.llm.ainvoke(messages)
            response_text = response.content
            
            # Calculate confidence score based on response characteristics
            confidence_score = self._calculate_confidence(response_text, faq_answer)
            
            # Determine if escalation is needed
            should_escalate = confidence_score < settings.CONFIDENCE_THRESHOLD
            
            if should_escalate:
                response_text += "\n\nWould you like me to connect you with a human agent for more detailed assistance?"
            
            return response_text, confidence_score, should_escalate
            
        except Exception as e:
            print(f"Error generating OpenAI response: {e}")
            return (
                "I'm experiencing technical difficulties. Let me connect you with a human agent.",
                0.0,
                True
            )
    
    def _generate_mock_response(self, user_message: str, faq_answer: str) -> Tuple[str, float, bool]:
        """Generate mock response for demo purposes"""
        user_lower = user_message.lower()
        
        # If we have a FAQ match, use it
        if faq_answer:
            return faq_answer, 0.9, False
        
        # Mock responses based on keywords
        mock_responses = {
            "hello": ["Hello! How can I help you today?", "Hi there! What can I assist you with?", "Greetings! How may I help you?"],
            "help": ["I'm here to help! What specific assistance do you need?", "I'd be happy to help. What can I do for you?"],
            "problem": ["I'm sorry to hear you're having an issue. Can you tell me more about what's happening?", "Let me help you resolve this problem. What's going on?"],
            "error": ["I understand you're encountering an error. Could you provide more details about the error message?", "Errors can be frustrating. Let me help you troubleshoot this."],
            "thank": ["You're welcome! Is there anything else I can help you with?", "Happy to help! Let me know if you need anything else."],
            "bye": ["Thank you for contacting us. Have a great day!", "Goodbye! Feel free to reach out anytime."],
        }
        
        # Check for keywords in user message
        for keyword, responses in mock_responses.items():
            if keyword in user_lower:
                response = random.choice(responses)
                confidence = 0.8 if len(user_message.split()) > 3 else 0.6
                should_escalate = confidence < settings.CONFIDENCE_THRESHOLD
                return response, confidence, should_escalate
        
        # Default response
        default_responses = [
            "I understand you're looking for assistance. Could you please provide more details about what you need help with?",
            "I'd like to help you better. Can you tell me more about your question or issue?",
            "Thank you for your message. To provide the best assistance, could you give me more information?",
        ]
        
        response = random.choice(default_responses)
        confidence = 0.5  # Lower confidence for generic responses
        should_escalate = confidence < settings.CONFIDENCE_THRESHOLD
        
        if should_escalate:
            response += "\n\nWould you like me to connect you with a human agent for more detailed assistance?"
        
        return response, confidence, should_escalate
    
    async def summarize_conversation(self, conversation_history: List[Dict]) -> str:
        """Summarize conversation for escalation"""
        if self.use_ai:
            if self.ai_type == "gemini":
                return await self._summarize_with_gemini(conversation_history)
            elif self.ai_type == "openai":
                return await self._summarize_with_openai(conversation_history)
        
        return self._summarize_with_mock(conversation_history)
    
    async def _summarize_with_gemini(self, conversation_history: List[Dict]) -> str:
        """Summarize using Google Gemini"""
        messages_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history
        ])
        
        prompt = f"""Summarize the following customer support conversation in 2-3 sentences, 
highlighting the main issue and any unresolved concerns:

{messages_text}

Summary:"""
        
        try:
            response = await self._call_gemini_async(prompt)
            return response.strip()
        except Exception as e:
            return "Conversation summary unavailable."
    
    async def _summarize_with_openai(self, conversation_history: List[Dict]) -> str:
        """Summarize using OpenAI"""
        from langchain_core.messages import HumanMessage
        
        messages_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history
        ])
        
        prompt = f"""Summarize the following customer support conversation in 2-3 sentences, 
highlighting the main issue and any unresolved concerns:

{messages_text}

Summary:"""
        
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            return "Conversation summary unavailable."
    
    def _summarize_with_mock(self, conversation_history: List[Dict]) -> str:
        """Mock conversation summary"""
        if not conversation_history:
            return "No conversation history available."
        
        user_messages = [msg for msg in conversation_history if msg['role'] == 'user']
        if user_messages:
            last_user_msg = user_messages[-1]['content'][:100]  # First 100 chars
            return f"Customer inquiry: {last_user_msg}..."
        
        return "Customer support conversation summary."
