# 🚀 AI Customer Support Bot - Setup Guide

## Prerequisites

- Python 3.8 or higher
- Google Gemini API Key (get one from https://ai.google.dev/)
- Git (for version control)

## Step-by-Step Setup Instructions

### 1️⃣ **Install Python Dependencies**

Open PowerShell/Terminal and navigate to the project directory:

```powershell
cd "c:\c programes\Projects\customer support bot"
```

Install required Python packages:

```powershell
pip install -r backend/requirements.txt
```

### 2️⃣ **Set Up Environment Variables**

Create a `.env` file in the `backend` directory:

```powershell
cd backend
New-Item -Path ".env" -ItemType File
```

Open the `.env` file and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
DEBUG=True
```

**To get your Gemini API Key:**
1. Go to https://ai.google.dev/
2. Click "Get API key in Google AI Studio"
3. Create a new API key
4. Copy and paste it into your `.env` file

### 3️⃣ **Run the Backend Server**

From the `backend` directory:

```powershell
# Make sure you're in the backend folder
cd "c:\c programes\Projects\customer support bot\backend"

# Run the FastAPI server
uvicorn app:app --reload --port 8001
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Application startup complete.
```

### 4️⃣ **Open the Frontend**

While the backend is running, open your web browser and go to:

```
http://localhost:8001
```

Or:

```
http://127.0.0.1:8001
```

The chat interface should load automatically!

## 🎯 Quick Start (One Command)

After setting up the `.env` file, you can run everything with one command:

```powershell
cd "c:\c programes\Projects\customer support bot\backend"; uvicorn app:app --reload --port 8001
```

Then open `http://localhost:8001` in your browser.

## 📝 Testing the Bot

Once the application is running:

1. The chat interface will load with a welcome message
2. Type a question like:
   - "What's your refund policy?"
   - "I can't log into my account"
   - "How do I track my order?"
3. The AI will respond with helpful answers
4. Try different questions to test the FAQ matching and AI responses

## 🔧 Troubleshooting

### Issue: "Port already in use"
**Solution:** Another process is using port 8001. Either:
- Kill the process: `netstat -ano | findstr :8001` then `taskkill /PID <process_id> /F`
- Use a different port: `uvicorn app:app --reload --port 8002`

### Issue: "Module not found"
**Solution:** Install dependencies again:
```powershell
pip install -r backend/requirements.txt
```

### Issue: "API key not found"
**Solution:** Make sure your `.env` file is in the `backend` folder with the correct API key.

### Issue: "Cannot connect to server"
**Solution:** 
- Check if the backend is running
- Make sure you're accessing `http://localhost:8001` (not 8000)
- Check the terminal for error messages

## 📁 Project Structure

```
customer support bot/
├── backend/
│   ├── app.py              # Main FastAPI application
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database models and setup
│   ├── llm_service.py      # AI service integration
│   ├── models.py           # Pydantic models
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables (you create this)
├── frontend/
│   ├── index.html         # Chat interface
│   ├── script.js          # Frontend logic
│   └── style.css          # Styling
├── data/
│   └── faqs.json          # FAQ knowledge base
└── README.md              # Project documentation
```

## 🎨 Features to Test

1. **FAQ Matching** - Ask about refunds, returns, shipping
2. **AI Responses** - Ask complex questions that aren't in FAQs
3. **Conversation History** - Chat maintains context across messages
4. **Session Management** - Click "New Conversation" to start fresh
5. **Confidence Scores** - See how confident the AI is in its responses
6. **Escalation** - Low confidence responses may suggest human support

## 🚀 Production Deployment

For production deployment, you would:

1. Set `DEBUG=False` in `.env`
2. Use a production ASGI server
3. Set up a proper database (PostgreSQL instead of SQLite)
4. Configure CORS for your domain
5. Add authentication and rate limiting
6. Deploy to a cloud platform (AWS, Azure, Google Cloud)

## 📞 Support

If you encounter any issues:
1. Check the terminal for error messages
2. Verify your `.env` file is correctly configured
3. Make sure all dependencies are installed
4. Check that port 8001 is available

---

**Happy Testing! 🎉**
