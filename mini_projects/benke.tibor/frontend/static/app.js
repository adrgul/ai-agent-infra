const chatMessages = document.getElementById('chatMessages');
const queryForm = document.getElementById('queryForm');
const queryInput = document.getElementById('queryInput');
const userIdInput = document.getElementById('userIdInput');
const sessionIdInput = document.getElementById('sessionIdInput');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');
const debugSession = document.getElementById('debugSession');
const debugDomain = document.getElementById('debugDomain');
const debugCitations = document.getElementById('debugCitations');
const debugWorkflow = document.getElementById('debugWorkflow');
const debugNextStep = document.getElementById('debugNextStep');
let typingEl = null;

function clearEmptyState() {
    const emptyState = chatMessages.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
}

function showTyping() {
    clearEmptyState();
    if (typingEl) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'message bot';
    wrapper.id = 'typing-indicator';
    wrapper.innerHTML = `
        <div class="message-content">
            <div class="typing">
                <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(wrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    typingEl = wrapper;
}

function hideTyping() {
    if (typingEl && typingEl.parentNode) {
        typingEl.parentNode.removeChild(typingEl);
    }
    typingEl = null;
}

function addMessage(content, type = 'info', citations = null, debug = null) {
    clearEmptyState();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    let html = `<div class="message-content">${escapeHtml(content)}`;

    if (citations && citations.length > 0) {
        html += `<div class="citations">📎 Források: ${citations.join(', ')}</div>`;
    }

    if (debug) {
        html += `<div class="debug-panel">`;
        if (debug.domain) html += `<span class="debug-label">Domain:</span> ${debug.domain}<br>`;
        if (debug.session) html += `<span class="debug-label">Session:</span> ${debug.session.substring(0, 8)}...<br>`;
        html += `</div>`;
    }

    html += `</div>`;
    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function askQuestion(question) {
    clearEmptyState();
    queryInput.value = question;
    queryInput.focus();
    // Trigger submit
    queryForm.dispatchEvent(new Event('submit'));
}

queryForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const query = queryInput.value.trim();
    const userId = userIdInput.value.trim() || 'demo_user';
    const sessionId = sessionIdInput.value.trim() || 'demo_session';

    if (!query) return;

    addMessage(query, 'user');
    queryInput.value = '';
    sendBtn.disabled = true;
    showTyping();

    try {
        const response = await fetch('http://localhost:8001/api/query/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                session_id: sessionId,
                query: query,
                organisation: 'Demo Org'
            })
        });

        if (!response.ok) {
            const error = await response.json();
            addMessage(`❌ Hiba: ${error.error || 'Ismeretlen hiba'}`, 'error');
            return;
        }

        const raw = await response.json();
        const payload = raw.data ?? raw; // backend wraps in { success, data }

        const citations = payload.citations ? payload.citations.map(c => c.source || 'Unknown') : [];

        // Update debug panel
        debugSession.textContent = sessionId;
        debugDomain.textContent = payload.domain || 'general';
        
        // Show citation count with average score
        if (payload.citations && payload.citations.length > 0) {
            const avgScore = (payload.citations.reduce((sum, c) => sum + (c.score || 0), 0) / payload.citations.length).toFixed(3);
            debugCitations.textContent = `${payload.citations.length} (avg: ${avgScore})`;
        } else {
            debugCitations.textContent = '0';
        }
        
        if (payload.workflow) {
            const action = payload.workflow.action || 'none';
            const status = payload.workflow.status || '';
            debugWorkflow.textContent = status ? `${action} (${status})` : action;
            debugNextStep.textContent = payload.workflow.next_step || payload.workflow.type || '-';
        } else {
            debugWorkflow.textContent = 'none';
            debugNextStep.textContent = '-';
        }

        hideTyping();
        addMessage(
            payload.answer || 'Sajnos nem tudtam válaszolni.',
            'bot',
            citations,
            {
                domain: payload.domain || 'general',
                session: sessionId
            }
        );

    } catch (error) {
        console.error('Fetch error:', error);
        hideTyping();
        addMessage(`❌ Hálózati hiba: ${error.message}`, 'error');
    } finally {
        sendBtn.disabled = false;
        queryInput.focus();
        hideTyping();
    }
});

// Reset chat to empty state
if (resetBtn) {
    resetBtn.addEventListener('click', () => {
        chatMessages.innerHTML = `
            <div class="empty-state">
                <h2>🤖 Üdvözöljük a KnowledgeRouter-ben!</h2>
                <p>Kérdezz meg bármit az alábbi doménekről. Az AI agent intelligensen felismeri és irányítja a kérdéseket.</p>
                
                <div class="example-questions">
                    <button class="example-btn" onclick="askQuestion('Szeretnék szabadságot igényelni október 3-4-re.')">HR: Szabadság igénylés</button>
                    <button class="example-btn" onclick="askQuestion('Nem működik a VPN-em, hogyan lehet megoldani?')">IT: VPN probléma</button>
                    <button class="example-btn" onclick="askQuestion('Mi a cégünk brand guideline-ja?')">Marketing: Brand guide</button>
                    <button class="example-btn" onclick="askQuestion('Mennyi pénz maradt a költségvetésből?')">Finance: Költségvetés</button>
                    <button class="example-btn" onclick="askQuestion('Mit kell tudni az alkalmazotti szerződésről?')">Legal: Szerződés</button>
                    <button class="example-btn" onclick="askQuestion('Milyen általános információk érdekelnek?')">General: Egyéb kérdés</button>
                </div>
            </div>
        `;
        queryInput.value = '';
        if (debugSession) debugSession.textContent = sessionIdInput.value;
        if (debugDomain) debugDomain.textContent = '-';
        if (debugCitations) debugCitations.textContent = '0';
        if (debugWorkflow) debugWorkflow.textContent = 'none';
        if (debugNextStep) debugNextStep.textContent = '-';
    });
}

// Initialize debug panel
if (debugSession && sessionIdInput) {
    debugSession.textContent = sessionIdInput.value;
}
if (queryInput) {
    queryInput.focus();
}
if (debugWorkflow) debugWorkflow.textContent = 'none';
if (debugNextStep) debugNextStep.textContent = '-';
