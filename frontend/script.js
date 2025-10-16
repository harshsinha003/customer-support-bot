const API_BASE_URL = 'http://localhost:8002/api';

let currentSessionId = null;
let isWaitingForResponse = false;

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const sessionIdDisplay = document.getElementById('sessionId');
const statusDisplay = document.getElementById('status');
const escalationBanner = document.getElementById('escalationBanner');
const escalateBtn = document.getElementById('escalateBtn');
const newSessionBtn = document.getElementById('newSessionBtn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await createNewSession();
    setupEventListeners();
});

function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    escalateBtn.addEventListener('click', escalateToHuman);
    newSessionBtn.addEventListener('click', createNewSession);
}

async function createNewSession() {
    try {
        statusDisplay.textContent = 'Connecting...';
        statusDisplay.className = 'status';
        
        const response = await fetch(`${API_BASE_URL}/chat/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) throw new Error('Failed to create session');
        
        const data = await response.json();
        currentSessionId = data.session_id;
        sessionIdDisplay.textContent = currentSessionId.substring(0, 8) + '...';
        statusDisplay.textContent = 'Connected';
        statusDisplay.className = 'status connected';
        
        // Clear chat messages except welcome message
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    <strong>Support Bot:</strong>
                    <p>Hello! I'm here to help you. How can I assist you today?</p>
                </div>
                <span class="timestamp">${formatTime(new Date())}</span>
            </div>
        `;
        
        escalationBanner.style.display = 'none';
        userInput.disabled = false;
        sendBtn.disabled = false;
        
    } catch (error) {
        console.error('Error creating session:', error);
        statusDisplay.textContent = 'Connection failed';
        statusDisplay.className = 'status disconnected';
        alert('Failed to connect to server. Please make sure the backend is running on http://localhost:8002');
    }
}

async function sendMessage() {
    if (isWaitingForResponse) return;
    
    const message = userInput.value.trim();
    if (!message || !currentSessionId) return;
    
    // Add user message to UI
    addMessage('user', message);
    userInput.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    isWaitingForResponse = true;
    sendBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });
        
        if (!response.ok) throw new Error('Failed to send message');
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator();
        
        // Add bot response to UI
        addMessage('bot', data.response, data.confidence_score);
        
        // Show escalation banner if needed
        if (data.should_escalate) {
            escalationBanner.style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator();
        addMessage('bot', 'Sorry, I encountered an error. Please try again or contact support.', 0);
    } finally {
        isWaitingForResponse = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

function addMessage(role, content, confidenceScore = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const timestamp = formatTime(new Date());
    const displayName = role === 'user' ? 'You' : 'Support Bot';
    
    let confidenceBadge = '';
    if (confidenceScore !== null) {
        const confidenceLevel = confidenceScore >= 0.8 ? 'high' : 
                               confidenceScore >= 0.6 ? 'medium' : 'low';
        confidenceBadge = `<span class="confidence-score ${confidenceLevel}">
            ${(confidenceScore * 100).toFixed(0)}% confident
        </span>`;
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <strong>${displayName}:</strong>${confidenceBadge}
            <p>${escapeHtml(content)}</p>
        </div>
        <span class="timestamp">${timestamp}</span>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function escalateToHuman() {
    if (!currentSessionId) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/escalate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                reason: 'User requested human agent'
            })
        });
        
        if (!response.ok) throw new Error('Failed to escalate');
        
        const data = await response.json();
        
        addMessage('bot', 
            `I've escalated your case to a human agent. Here's a summary of our conversation:\n\n${data.summary}\n\nA support agent will be with you shortly.`
        );
        
        escalationBanner.style.display = 'none';
        statusDisplay.textContent = 'Escalated to Human Agent';
        statusDisplay.className = 'status';
        
        // Disable input
        userInput.disabled = true;
        sendBtn.disabled = true;
        
    } catch (error) {
        console.error('Error escalating:', error);
        alert('Failed to escalate. Please try again.');
    }
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
    });
}

function escapeHtml(text) {
    // First escape HTML to prevent XSS
    const div = document.createElement('div');
    div.textContent = text;
    let escapedText = div.innerHTML;
    
    // Apply basic Markdown formatting
    // Bold text: **text** -> <strong>text</strong>
    escapedText = escapedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert newlines to <br>
    escapedText = escapedText.replace(/\n/g, '<br>');
    
    return escapedText;
}
