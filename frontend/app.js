/**
 * AI Agent RAG Frontend Application
 * Handles chat interface, API communication, and session management
 */

// ===================================
// Configuration
// ===================================
const CONFIG = {
    API_BASE_URL: '/api/v1',
    HEALTH_CHECK_INTERVAL: 30000, // 30 seconds
    TOAST_DURATION: 4000,
};

// ===================================
// State Management
// ===================================
const state = {
    sessionId: null,
    isLoading: false,
    isConnected: false,
    messages: [],
};

// ===================================
// DOM Elements
// ===================================
const elements = {
    chatContainer: document.getElementById('chatContainer'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    messagesContainer: document.getElementById('messagesContainer'),
    queryInput: document.getElementById('queryInput'),
    sendBtn: document.getElementById('sendBtn'),
    charCount: document.getElementById('charCount'),
    sessionId: document.getElementById('sessionId'),
    connectionStatus: document.getElementById('connectionStatus'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    toastContainer: document.getElementById('toastContainer'),
    newChatBtn: document.getElementById('newChatBtn'),
};

// ===================================
// API Functions
// ===================================

/**
 * Check API health status
 */
async function checkHealth() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            updateConnectionStatus(true);
            return data;
        }
        throw new Error('Health check failed');
    } catch (error) {
        updateConnectionStatus(false);
        console.error('Health check error:', error);
        return null;
    }
}

/**
 * Send a query to the AI Agent
 */
async function sendQuery(query) {
    const payload = {
        query: query,
        session_id: state.sessionId,
    };

    const response = await fetch(`${CONFIG.API_BASE_URL}/ask`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

// ===================================
// UI Functions
// ===================================

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    state.isConnected = connected;
    const statusElement = elements.connectionStatus;
    const statusText = statusElement.querySelector('.status-text');
    
    statusElement.classList.remove('connected', 'error');
    
    if (connected) {
        statusElement.classList.add('connected');
        statusText.textContent = 'Connected';
    } else {
        statusElement.classList.add('error');
        statusText.textContent = 'Disconnected';
    }
}

/**
 * Show/hide loading overlay
 */
function setLoading(loading) {
    state.isLoading = loading;
    elements.loadingOverlay.classList.toggle('visible', loading);
    elements.sendBtn.disabled = loading || !elements.queryInput.value.trim();
    elements.queryInput.disabled = loading;
}

/**
 * Update character count
 */
function updateCharCount() {
    const count = elements.queryInput.value.length;
    elements.charCount.textContent = count;
    elements.sendBtn.disabled = count === 0 || state.isLoading;
}

/**
 * Auto-resize textarea
 */
function autoResizeTextarea() {
    const textarea = elements.queryInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'toastSlideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, CONFIG.TOAST_DURATION);
}

/**
 * Format timestamp
 */
function formatTime(date) {
    return new Date(date).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

/**
 * Create message element
 */
function createMessageElement(role, content, metadata = {}) {
    const message = document.createElement('div');
    message.className = `message ${role}`;
    
    const avatar = role === 'user' ? '👤' : '🤖';
    const roleName = role === 'user' ? 'You' : 'AI Agent';
    
    let metaHTML = '';
    if (metadata.queryType) {
        metaHTML = `
            <span class="query-type-badge ${metadata.queryType}">${metadata.queryType}</span>
            <span>${formatTime(metadata.timestamp || new Date())}</span>
        `;
    } else {
        metaHTML = `<span>${formatTime(new Date())}</span>`;
    }
    
    let sourcesHTML = '';
    if (metadata.sources && metadata.sources.length > 0) {
        const sourceTags = metadata.sources
            .map(source => `<span class="source-tag">${source}</span>`)
            .join('');
        sourcesHTML = `
            <div class="message-sources">
                <div class="sources-label">Sources</div>
                <div class="source-tags">${sourceTags}</div>
            </div>
        `;
    }
    
    // Process content for display (handle markdown-like formatting)
    const formattedContent = formatContent(content);
    
    message.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-role">${roleName}</span>
                <span class="message-meta">${metaHTML}</span>
            </div>
            <div class="message-text">${formattedContent}</div>
            ${sourcesHTML}
        </div>
    `;
    
    return message;
}

/**
 * Format content with basic markdown support
 */
function formatContent(content) {
    // Escape HTML
    content = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Convert line breaks to paragraphs
    const paragraphs = content.split(/\n\n+/);
    return paragraphs
        .map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`)
        .join('');
}

/**
 * Add typing indicator
 */
function addTypingIndicator() {
    const typing = document.createElement('div');
    typing.className = 'message assistant';
    typing.id = 'typingIndicator';
    typing.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    elements.messagesContainer.appendChild(typing);
    scrollToBottom();
}

/**
 * Remove typing indicator
 */
function removeTypingIndicator() {
    const typing = document.getElementById('typingIndicator');
    if (typing) typing.remove();
}

/**
 * Add message to chat
 */
function addMessage(role, content, metadata = {}) {
    // Hide welcome screen on first message
    if (state.messages.length === 0) {
        elements.welcomeScreen.classList.add('hidden');
    }
    
    const messageElement = createMessageElement(role, content, metadata);
    elements.messagesContainer.appendChild(messageElement);
    
    state.messages.push({ role, content, metadata });
    
    scrollToBottom();
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
}

/**
 * Update session ID display
 */
function updateSessionDisplay(sessionId) {
    state.sessionId = sessionId;
    elements.sessionId.textContent = sessionId ? sessionId.slice(0, 8) + '...' : 'Not started';
}

/**
 * Clear chat and start new session
 */
function clearChat() {
    state.messages = [];
    state.sessionId = null;
    elements.messagesContainer.innerHTML = '';
    elements.welcomeScreen.classList.remove('hidden');
    updateSessionDisplay(null);
    showToast('New chat started', 'success');
}

// ===================================
// Event Handlers
// ===================================

/**
 * Handle send message
 */
async function handleSend() {
    const query = elements.queryInput.value.trim();
    if (!query || state.isLoading) return;
    
    // Check connection first
    if (!state.isConnected) {
        showToast('Not connected to server. Please check if the backend is running.', 'error');
        return;
    }
    
    // Clear input
    elements.queryInput.value = '';
    updateCharCount();
    autoResizeTextarea();
    
    // Add user message
    addMessage('user', query);
    
    // Show loading state
    setLoading(true);
    addTypingIndicator();
    
    try {
        const response = await sendQuery(query);
        
        removeTypingIndicator();
        
        // Update session if new
        if (response.session_id) {
            updateSessionDisplay(response.session_id);
        }
        
        // Add assistant message
        addMessage('assistant', response.answer, {
            queryType: response.query_type,
            sources: response.sources,
            timestamp: response.timestamp,
        });
        
    } catch (error) {
        removeTypingIndicator();
        console.error('Query error:', error);
        showToast(`Error: ${error.message}`, 'error');
        addMessage('assistant', `I'm sorry, I encountered an error processing your request. Please try again.\n\nError: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

/**
 * Handle suggestion card click
 */
function handleSuggestionClick(event) {
    const card = event.target.closest('.suggestion-card');
    if (!card) return;
    
    const query = card.dataset.query;
    if (query) {
        elements.queryInput.value = query;
        updateCharCount();
        autoResizeTextarea();
        handleSend();
    }
}

/**
 * Handle keyboard shortcuts
 */
function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSend();
    }
}

// ===================================
// Initialization
// ===================================

/**
 * Initialize application
 */
async function init() {
    // Set up event listeners
    elements.queryInput.addEventListener('input', () => {
        updateCharCount();
        autoResizeTextarea();
    });
    
    elements.queryInput.addEventListener('keydown', handleKeydown);
    elements.sendBtn.addEventListener('click', handleSend);
    elements.newChatBtn.addEventListener('click', clearChat);
    
    // Suggestion cards
    document.querySelectorAll('.suggestion-card').forEach(card => {
        card.addEventListener('click', handleSuggestionClick);
    });
    
    // Initial health check
    await checkHealth();
    
    // Periodic health checks
    setInterval(checkHealth, CONFIG.HEALTH_CHECK_INTERVAL);
    
    // Focus input
    elements.queryInput.focus();
    
    console.log('AI Agent RAG Frontend initialized');
}

// Start application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
