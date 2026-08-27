/**
 * Roze AI Chat Widget - Premium Edition
 * Features: Glassmorphism, Streaming Text, Voice UI, Product Cards, Quick Replies
 */

(function () {
    'use strict';

    // Configuration
    let config = {
        apiEndpoint: 'http://localhost:8003',
        position: 'bottom-right',
        primaryColor: '#000000', // Premium Black
        secondaryColor: '#C5A059', // Gold accent
        textColor: '#ffffff',
        welcomeMessage: 'Hello! I am your personal Roze BioHealth assistant. How can I help you today?',
        autoOpenDelay: 0,
        botAvatar: 'https://cdn-icons-png.flaticon.com/512/4712/4712035.png' // Professional Icon Placeholder
    };

    // State
    let isOpen = false;
    let isRecording = false;
    let recognition = null;
    let isTyping = false;
    let sessionId = localStorage.getItem('roze_session_id') || ('sess_' + Math.random().toString(36).substr(2, 9));
    localStorage.setItem('roze_session_id', sessionId);

    // --- UTILS ---

    const escapeHtml = (unsafe) => {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    const parseMarkdown = (text) => {
        // Simple Markdown Parser
        let html = escapeHtml(text || "");
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Bold
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>'); // Italic
        html = html.replace(/\n/g, '<br>'); // Newlines
        html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>'); // Links
        return html;
    }

    // --- INITIALIZATION ---

    async function loadConfig() {
        try {
            const response = await fetch(`${config.apiEndpoint}/admin/settings`);
            const settings = await response.json();

            // Merge settings
            if (settings) {
                config.position = settings.widget_position || config.position;
                config.primaryColor = settings.primary_color || config.primaryColor;
                config.secondaryColor = settings.secondary_color || config.secondaryColor;
                config.textColor = settings.text_color || config.textColor;
                config.welcomeMessage = settings.welcome_message || config.welcomeMessage;
                config.autoOpenDelay = settings.auto_open_delay || 0;
            }
        } catch (e) {
            console.warn("Using default config due to fetch error", e);
        }
        applyStyles();
    }

    function applyStyles() {
        const styleId = 'roze-chat-styles';
        let styleElement = document.getElementById(styleId);
        if (styleElement) styleElement.remove();

        const styles = `
            :root {
                --primary: ${config.primaryColor};
                --secondary: ${config.secondaryColor};
                --text-on-primary: ${config.textColor};
                --glass-bg: rgba(255, 255, 255, 0.85);
                --glass-border: rgba(255, 255, 255, 0.4);
                --shadow-lg: 0 20px 60px rgba(0,0,0,0.15);
                --shadow-sm: 0 4px 12px rgba(0,0,0,0.08);
                --font-stack: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }

            .roze-widget-container {
                position: fixed;
                z-index: 999999;
                font-family: var(--font-stack);
                ${getPositionStyles()}
            }

            /* --- LAUNCH BUTTON --- */
            .roze-launch-btn {
                width: 64px;
                height: 64px;
                border-radius: 50%;
                background: linear-gradient(135deg, var(--primary), #333);
                color: var(--text-on-primary);
                border: 1px solid rgba(255,255,255,0.2);
                cursor: pointer;
                box-shadow: var(--shadow-lg);
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                backdrop-filter: blur(10px);
            }
            
            .roze-launch-btn:hover {
                transform: scale(1.08) translateY(-2px);
            }

            .roze-icon img {
                width: 32px;
                height: 32px;
                filter: invert(1);
            }

            /* --- MAIN WINDOW --- */
            .roze-chat-window {
                width: 400px;
                height: 650px;
                max-height: 80vh;
                background: var(--glass-bg);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--glass-border);
                border-radius: 24px;
                box-shadow: var(--shadow-lg);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                margin-bottom: 20px;
                opacity: 0;
                transform: translateY(20px) scale(0.95);
                transform-origin: bottom right;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                pointer-events: none;
            }

            .roze-chat-window.open {
                opacity: 1;
                transform: translateY(0) scale(1);
                pointer-events: all;
            }

            /* --- HEADER --- */
            .roze-header {
                padding: 20px 24px;
                background: transparent;
                border-bottom: 1px solid rgba(0,0,0,0.05);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .roze-header-info h3 {
                margin: 0;
                font-size: 18px;
                font-weight: 700;
                color: #1a1a1a;
                letter-spacing: -0.5px;
            }

            .roze-status {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                color: #10B981;
                font-weight: 500;
            }
            .roze-status-dot {
                width: 8px;
                height: 8px;
                background: #10B981;
                border-radius: 50%;
                box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
            }

            .roze-close-btn {
                background: transparent;
                border: none;
                font-size: 20px;
                color: #666;
                cursor: pointer;
                padding: 5px;
                border-radius: 50%;
                transition: background 0.2s;
            }
            .roze-close-btn:hover { background: rgba(0,0,0,0.05); }

            /* --- MESSAGES AREA --- */
            .roze-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 16px;
                scroll-behavior: smooth;
            }

            .roze-msg {
                max-width: 85%;
                font-size: 14px;
                line-height: 1.5;
                animation: fadeIn 0.3s ease-out;
            }

            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

            .roze-msg-bot {
                align-self: flex-start;
                background: white;
                color: #1a1a1a;
                border-radius: 18px 18px 18px 4px;
                padding: 14px 18px;
                box-shadow: var(--shadow-sm);
                border: 1px solid rgba(0,0,0,0.03);
            }

            .roze-msg-user {
                align-self: flex-end;
                background: var(--primary);
                color: var(--text-on-primary);
                border-radius: 18px 18px 4px 18px;
                padding: 14px 18px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }

            /* --- RICH ELEMENTS: CAROUSEL --- */
            .roze-carousel {
                display: flex;
                gap: 12px;
                overflow-x: auto;
                padding: 4px;
                margin-top: 8px;
                scrollbar-width: none;
            }
            .roze-carousel::-webkit-scrollbar { display: none; }

            .roze-card {
                min-width: 160px;
                max-width: 160px;
                background: white;
                border-radius: 12px;
                padding: 10px;
                border: 1px solid rgba(0,0,0,0.05);
                display: flex;
                flex-direction: column;
                gap: 6px;
                transition: transform 0.2s;
            }
            .roze-card:hover { transform: translateY(-4px); }

            .roze-card-img {
                width: 100%;
                height: 100px;
                background: #f5f5f5;
                border-radius: 8px;
                object-fit: cover;
            }
            .roze-card-title { font-size: 12px; font-weight: 600; color: #333; height: 32px; overflow: hidden; }
            .roze-card-price { font-size: 12px; color: var(--secondary); font-weight: 700; }
            .roze-card-btn {
                background: #f0f0f0;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
                cursor: pointer;
                transition: background 0.2s;
            }
            .roze-card-btn:hover { background: #e0e0e0; }

            /* --- CHIPS --- */
            .roze-chips {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 8px;
            }
            .roze-chip {
                background: rgba(0,0,0,0.05);
                border: 1px solid rgba(0,0,0,0.05);
                padding: 8px 14px;
                border-radius: 20px;
                font-size: 12px;
                color: #555;
                cursor: pointer;
                transition: all 0.2s;
            }
            .roze-chip:hover {
                background: var(--secondary);
                color: white;
                border-color: var(--secondary);
            }

            /* --- INPUT AREA --- */
            .roze-footer {
                padding: 16px;
                background: rgba(255,255,255,0.6);
                border-top: 1px solid rgba(0,0,0,0.05);
                display: flex;
                gap: 10px;
                align-items: center;
            }

            .roze-input {
                flex: 1;
                border: none;
                background: white;
                padding: 14px 16px;
                border-radius: 24px;
                font-size: 14px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                outline: none;
                transition: box-shadow 0.2s;
            }
            .roze-input:focus { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }

            .roze-mic-btn, .roze-send-btn {
                width: 42px;
                height: 42px;
                border-radius: 50%;
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.2s;
            }
            
            .roze-mic-btn {
                background: transparent;
                color: #666;
            }
            .roze-mic-btn.active { color: #e74c3c; animation: pulse 1s infinite; }
            
            .roze-send-btn {
                background: var(--primary);
                color: white;
            }
            .roze-send-btn:hover { transform: scale(1.1); }

            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

            /* TYPING INDICATOR */
            .roze-typing { display: flex; gap: 4px; padding: 10px 18px; }
            .dot { width: 6px; height: 6px; background: #bbb; border-radius: 50%; animation: bounce 1.4s infinite; }
            .dot:nth-child(2) { animation-delay: 0.2s; }
            .dot:nth-child(3) { animation-delay: 0.4s; }
            @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }

            /* MOBILE OPTIMIZATION */
            @media (max-width: 480px) {
                .roze-chat-window {
                    width: 100%;
                    height: 100%;
                    max-height: 100%;
                    border-radius: 0;
                    margin: 0;
                    bottom: 0; right: 0; left: 0;
                }
                .roze-widget-container { bottom: 20px; right: 20px; }
            }
        `;

        styleElement = document.createElement('style');
        styleElement.id = styleId;
        styleElement.textContent = styles;
        document.head.appendChild(styleElement);
    }

    function getPositionStyles() {
        if (config.position === 'bottom-left') return 'bottom: 24px; left: 24px;';
        if (config.position === 'top-right') return 'top: 24px; right: 24px;';
        return 'bottom: 24px; right: 24px;';
    }

    // --- DOM BUILDER ---

    function createWidget() {
        const container = document.createElement('div');
        container.className = 'roze-widget-container';

        container.innerHTML = `
            <div id="roze-chat-window" class="roze-chat-window">
                <!-- Header -->
                <div class="roze-header">
                    <div class="roze-header-info">
                        <h3>Roze BioHealth AI</h3>
                        <div class="roze-status">
                            <div class="roze-status-dot"></div>
                            Online
                        </div>
                    </div>
                    <button class="roze-close-btn" onclick="window.RozeChat.toggle()">✕</button>
                </div>

                <!-- Messages -->
                <div id="roze-messages" class="roze-messages">
                    <div class="roze-msg roze-msg-bot">
                        ${config.welcomeMessage}
                    </div>
                </div>

                <!-- Typing -->
                <div id="roze-typing" class="roze-msg roze-msg-bot roze-typing" style="display:none">
                    <div class="dot"></div><div class="dot"></div><div class="dot"></div>
                </div>

                <!-- Inputs -->
                <div class="roze-footer">
                    <input type="text" id="roze-input" class="roze-input" placeholder="Type a message...">
                    <button id="roze-mic" class="roze-mic-btn" title="Speak">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                           <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                           <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                        </svg>
                    </button>
                    <button id="roze-send" class="roze-send-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                           <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Launcher -->
            <button class="roze-launch-btn" onclick="window.RozeChat.toggle()">
                <div class="roze-icon">
                    <img src="${config.botAvatar}" alt="Chat">
                </div>
            </button>
        `;

        document.body.appendChild(container);

        // Bind Events
        document.getElementById('roze-send').onclick = sendMessage;
        document.getElementById('roze-input').onkeypress = (e) => {
            if (e.key === 'Enter') sendMessage();
        };

        // Voice Logic
        const micBtn = document.getElementById('roze-mic');
        if ('webkitSpeechRecognition' in window) {
            recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = () => {
                isRecording = true;
                micBtn.classList.add('active');
            };

            recognition.onend = () => {
                isRecording = false;
                micBtn.classList.remove('active');
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('roze-input').value = transcript;
                sendMessage();
            };

            micBtn.onclick = () => {
                if (isRecording) recognition.stop();
                else recognition.start();
            };
        } else {
            micBtn.style.display = 'none'; // Unsupported
        }
    }

    // --- MESSAGING LOGIC ---

    function toggle() {
        const win = document.getElementById('roze-chat-window');
        isOpen = !isOpen;
        if (isOpen) win.classList.add('open');
        else win.classList.remove('open');
    }

    async function sendMessage() {
        const input = document.getElementById('roze-input');
        const text = input.value.trim();
        if (!text) return;

        // User Message
        appendMessage(text, 'user');
        input.value = '';

        // Bot Thinking
        showTyping(true);

        try {
            const res = await fetch(`${config.apiEndpoint}/api/test-chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, session_id: sessionId })
            });
            const data = await res.json();

            showTyping(false);

            // Handle Response (Check if Structured or Plain)
            // The backend returns { response: BotResponse } or similar structure
            // Based on previous edit: `return response_data` (which is BotResponse object)

            let botText = "";
            let products = [];
            let chips = [];
            let order = null;

            // Handle if data is the object directly
            if (data.text) {
                botText = data.text;
                products = data.products || [];
                chips = data.quick_replies || [];
                order = data.order_details || null;
            } else if (data.response) {
                // Fallback if backend wrapper exists
                botText = data.response;
            }

            // 1. Text (Instant Snap - No Streaming)
            appendMessage(botText, 'bot');

            // 2. Products Carousel
            if (products.length > 0) {
                renderCarousel(products);
            }

            // 3. Order Details
            if (order) {
                renderOrderCard(order);
            }

            // 4. Cart Update (New)
            if (data.cart_state) {
                renderCartToast(data.cart_state);
            }

            // 5. Quick Replies
            if (chips.length > 0) {
                renderChips(chips);
            }

        } catch (e) {
            console.error(e);
            showTyping(false);
            appendMessage("I'm having trouble connecting. Please try again.", 'bot');
        }
    }

    function appendMessage(html, sender) {
        const container = document.getElementById('roze-messages');
        const div = document.createElement('div');
        div.className = `roze-msg roze-msg-${sender}`;
        // Parse markdown immediately
        div.innerHTML = parseMarkdown(html);
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        return div;
    }

    function renderCartToast(cart) {
        // Check if exists, update or create
        let toast = document.getElementById('roze-cart-toast');
        if (!toast) {
            const container = document.getElementById('roze-chat-window');
            toast = document.createElement('div');
            toast.id = 'roze-cart-toast';
            toast.style.cssText = `
                position: absolute; top: 70px; right: 20px;
                background: var(--primary); color: white;
                padding: 8px 12px; border-radius: 20px;
                font-size: 12px; font-weight: 600;
                box-shadow: var(--shadow-sm); z-index: 10;
                display: flex; gap: 6px; align-items: center;
                animation: slideIn 0.3s ease-out;
            `;
            // Add slideIn animation definition to style if needed, or just standard CSS
            container.appendChild(toast);
        }

        if (cart.count > 0) {
            toast.innerHTML = `<span>🛍️</span> ${cart.count} items | ${cart.currency} ${cart.total}`;
            toast.style.display = 'flex';
        } else {
            toast.style.display = 'none';
        }
    }

    function showTyping(show) {
        const el = document.getElementById('roze-typing');
        el.style.display = show ? 'flex' : 'none';
        const container = document.getElementById('roze-messages');
        container.scrollTop = container.scrollHeight;
    }

    // Streaming function removed

    function renderCarousel(products) {
        const container = document.getElementById('roze-messages');
        const carousel = document.createElement('div');
        carousel.className = 'roze-carousel';

        products.forEach(p => {
            const card = document.createElement('div');
            card.className = 'roze-card';

            // Use pre-processed image URL from backend
            const imgUrl = p.image_url || 'https://placehold.co/100?text=No+Image';

            // Clean escape for JS string
            const safeName = p.name ? p.name.replace(/'/g, "\\'") : "Product";

            card.innerHTML = `
                <img src="${imgUrl}" class="roze-card-img" onerror="this.src='https://placehold.co/100?text=Error'" />
                <div class="roze-card-title">${p.name}</div>
                <div class="roze-card-price">${p.currency || 'AED'} ${p.price || '--'}</div>
                <button class="roze-card-btn" onclick="window.RozeChat.sendText('Add ${safeName} to my cart')">Add to Cart</button>
            `;
            carousel.appendChild(card);
        });

        container.appendChild(carousel);
        container.scrollTop = container.scrollHeight;
    }

    function renderOrderCard(order) {
        const container = document.getElementById('roze-messages');
        const div = document.createElement('div');
        div.className = 'roze-msg roze-msg-bot';
        div.style.background = '#f8f9fa';
        div.innerHTML = `
            <strong>📦 Order #${order.id}</strong><br>
            Status: <span style="color:var(--secondary)">${order.status.toUpperCase()}</span><br>
            Total: ${order.currency} ${order.total}<br>
            <div style="margin-top:8px; height:4px; width:100%; background:#ddd; border-radius:2px;">
                <div style="height:100%; width:${order.status === 'completed' ? '100%' : '50%'}; background:#10B981; border-radius:2px;"></div>
            </div>
        `;
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function renderChips(chips) {
        const container = document.getElementById('roze-messages');
        const chipContainer = document.createElement('div');
        chipContainer.className = 'roze-chips';

        chips.forEach(text => {
            const chip = document.createElement('div');
            chip.className = 'roze-chip';
            chip.textContent = text;
            chip.onclick = () => {
                window.RozeChat.sendText(text);
                chipContainer.remove(); // Remove chips after selection
            };
            chipContainer.appendChild(chip);
        });

        container.appendChild(chipContainer);
        container.scrollTop = container.scrollHeight;
    }

    // Public API
    window.RozeChat = {
        init: async () => {
            await loadConfig();
            createWidget();
            // Proactive Trigger
            setTimeout(() => {
                if (!isOpen) {
                    toggle();
                }
            }, 10000); // 10s delay as requested
        },
        toggle,
        sendText: (text) => {
            document.getElementById('roze-input').value = text;
            sendMessage();
        }
    };

    // Auto Init
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.RozeChat.init);
    } else {
        window.RozeChat.init();
    }

})();
