function getToken() { return localStorage.getItem('token'); }
function ensureLoggedIn() {
    const token = getToken();
    if (!token) { window.location.href = '/login'; return false; }
    return true;
}
async function sendMessageToBot(message) {
    const token = getToken();
    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ text: message })
    });
    if (response.status === 401) {
        alert('Session expired. Please log in again.');
        localStorage.removeItem('token'); localStorage.removeItem('username');
        window.location.href = '/login';
        return { reply: 'Unauthorized. Please log in again.' };
    }
    try { return await response.json(); } catch { return { reply: 'Server returned invalid response.' }; }
}
function addMessage(text, className) {
    const div = document.createElement('div');
    div.classList.add('message', className);
    div.textContent = text;
    const container = document.getElementById('chat-container');
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}
window.addEventListener('DOMContentLoaded', () => {
    if (!ensureLoggedIn()) return;
    const welcome = document.getElementById('welcome');
    const username = localStorage.getItem('username');
    if (welcome && username) welcome.textContent = `BodhiPilot — ${username}`;
    const form = document.getElementById('input-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('user-input');
        const userText = input.value.trim();
        if (!userText) return;
        input.value = '';
        addMessage(userText, 'user-message');
        const data = await sendMessageToBot(userText);
        addMessage(data.reply, 'bot-message');
    });
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = '/login';
    });
});