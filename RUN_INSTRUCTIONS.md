# 🚀 How to Run AI Customer Support Bot

## 📋 Prerequisites

1. **Python 3.8+** installed on your system
2. **Git** (already have since you cloned the repo)
3. **A terminal/command prompt**

## ⚡ Quick Start Commands

### **Method 1: Windows PowerShell (Recommended)**

```powershell
# 1. Navigate to project directory
cd "c:\c programes\Projects\customer support bot"

# 2. Install Python dependencies
pip install -r backend/requirements.txt

# 3. Navigate to backend folder
cd backend

# 4. Run the server
python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# 5. Open browser to: http://localhost:8001
```

### **Method 2: One-Line Command**

```powershell
cd "c:\c programes\Projects\customer support bot\backend"; python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

## 🌐 Access Your Bot

After running the server, open your web browser and go to:

**🔗 http://localhost:8001**

## 🛠️ Troubleshooting

### If you get "module not found" errors:
```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install requirements again
pip install -r backend/requirements.txt
```

### If port 8001 is busy:
```powershell
# Use a different port
python -m uvicorn app:app --host 0.0.0.0 --port 8002 --reload
# Then access: http://localhost:8002
```

### If Python is not recognized:
```powershell
# Try these alternatives
py -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
# OR
python3 -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

## 📱 Features Available

✅ **AI-Powered Responses** - Using Google Gemini AI
✅ **Professional Dark Theme** - Sleek UI design  
✅ **Session Management** - Conversation history
✅ **Confidence Scoring** - AI response quality indicators
✅ **FAQ Integration** - Pre-built knowledge base
✅ **Escalation Support** - Human agent handoff
✅ **Real-time Chat** - Instant responses

## 🔧 Configuration

Your bot is pre-configured with:
- **AI Provider**: Google Gemini (Free)
- **Database**: SQLite (No setup needed)
- **Theme**: Professional Dark Mode
- **Port**: 8001

## 🎯 Development Mode

For development with auto-reload:
```powershell
python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload --log-level debug
```

## 🚫 Stop the Server

Press `Ctrl + C` in the terminal to stop the server.

---

## 📞 Need Help?

If you encounter issues:
1. Check that all dependencies are installed
2. Verify your API key in `.env` file  
3. Ensure no other service is using port 8001
4. Try running with administrator privileges

**Happy Chatting! 🤖💬**