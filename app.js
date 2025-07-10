 // DOM Elements
        const initialScreen = document.getElementById('initial-screen');
        const profileScreen = document.getElementById('profile-screen');
        const chatScreen = document.getElementById('chat-screen');
        const profileForm = document.getElementById('profile-form');
        const messagesContainer = document.getElementById('messages');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const historyList = document.getElementById('history-list');
        const chatTitle = document.getElementById('chat-title');
        const statusIndicator = document.getElementById('status-indicator');
        const newChatButton = document.getElementById('new-chat-button');
        const deleteHistoryButton = document.getElementById('delete-history-button');
        const backToOptionsButton = document.getElementById('back-to-options');
        const backFromChatButton = document.getElementById('back-from-chat');
        
        // App State
        let currentChatType = '';
        let currentChatId = '';
        let currentChat = null;
        let profile = null;
        let isOnline = navigator.onLine;
        
        // Initialize the app
        function init() {
            // Check online status
            updateOnlineStatus();
            window.addEventListener('online', updateOnlineStatus);
            window.addEventListener('offline', updateOnlineStatus);
            
            // Load profile if exists
            loadProfile();
            
            // Set up event listeners
            document.querySelectorAll('.option-card').forEach(card => {
                card.addEventListener('click', handleOptionSelect);
            });
            
            profileForm.addEventListener('submit', handleProfileSubmit);
            sendButton.addEventListener('click', sendMessage);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
            
            newChatButton.addEventListener('click', showInitialScreen);
            deleteHistoryButton.addEventListener('click', deleteAllHistory);
            backToOptionsButton.addEventListener('click', showInitialScreen);
            backFromChatButton.addEventListener('click', handleBackFromChat);
            
            // If profile exists, show history screen
            if (profile) {
                renderHistoryList();
            } else {
                showInitialScreen();
            }
        }
        
        // Handle back button from chat
        function handleBackFromChat() {
            if (currentChat?.messages?.length > 1) {
                showInitialScreen();
            } else {
                // Remove empty chat from history
                const chatHistory = getChatHistory();
                const updatedHistory = chatHistory.filter(chat => chat.id !== currentChatId);
                saveChatHistory(updatedHistory);
                showInitialScreen();
            }
        }
        
        // Update online status
        function updateOnlineStatus() {
            isOnline = navigator.onLine;
            statusIndicator.textContent = isOnline ? 'Online' : 'Offline (responses may be limited)';
            statusIndicator.style.color = isOnline ? '#4CAF50' : '#FF9800';
        }
        
        // Handle option selection
        function handleOptionSelect(e) {
            const option = e.currentTarget.getAttribute('data-option');
            currentChatType = option;
            
            switch (option) {
                case 'medical':
                    chatTitle.textContent = 'Medical Advice';
                    break;
                case 'checkup':
                    chatTitle.textContent = 'Health Checkup';
                    break;
                case 'learning':
                    chatTitle.textContent = 'Learning';
                    break;
            }
            
            // For medical advice and health checkup, require profile
            if ((option === 'medical' || option === 'checkup') && !profile) {
                showProfileScreen();
            } else {
                startNewChat();
            }
        }
        
        // Show profile screen
        function showProfileScreen() {
            initialScreen.style.display = 'none';
            profileScreen.style.display = 'block';
            chatScreen.style.display = 'none';
        }
        
        // Show initial screen
        function showInitialScreen() {
            initialScreen.style.display = 'block';
            profileScreen.style.display = 'none';
            chatScreen.style.display = 'none';
            currentChatType = '';
            currentChatId = '';
            renderHistoryList();
        }
        
        // Handle profile submission
        function handleProfileSubmit(e) {
            e.preventDefault();
            
            profile = {
                name: document.getElementById('name').value,
                age: document.getElementById('age').value,
                sex: document.getElementById('sex').value,
                description: document.getElementById('initial-description').value || '',
                updatedAt: new Date().toISOString()
            };
            
            // Save profile to localStorage
            localStorage.setItem('healthAssistantProfile', JSON.stringify(profile));
            
            startNewChat();
        }
        
        // Load profile from localStorage
        function loadProfile() {
            const savedProfile = localStorage.getItem('healthAssistantProfile');
            if (savedProfile) {
                profile = JSON.parse(savedProfile);
            }
        }
        
        // Start a new chat
        function startNewChat() {
            currentChatId = Date.now().toString();
            
            // Create initial messages based on chat type
            let initialBotMessage = '';
            switch (currentChatType) {
                case 'medical':
                    initialBotMessage = `Hello ${profile?.name || 'there'}, I'm here to provide general medical advice. Please describe your symptoms or concerns.`;
                    break;
                case 'checkup':
                    initialBotMessage = `Hello ${profile?.name || 'there'}, let's do a health checkup. I'll ask you some questions about your health.`;
                    break;
                case 'learning':
                    initialBotMessage = "Hello! What would you like to learn about today?";
                    break;
            }
            
            // Initialize in-memory chat (not saved to history yet)
            currentChat = {
                id: currentChatId,
                type: currentChatType,
                title: chatTitle.textContent,
                createdAt: new Date().toISOString(),
                messages: [
                    { sender: 'bot', content: initialBotMessage, timestamp: new Date().toISOString() }
                ]
            };
            
            // Show chat screen with initial message
            showChatScreen();
            renderMessages(currentChat.messages);
        }
        
        // Show chat screen
        function showChatScreen() {
            initialScreen.style.display = 'none';
            profileScreen.style.display = 'none';
            chatScreen.style.display = 'flex';
        }
        
        // Send message
        function sendMessage() {
            const messageText = messageInput.value.trim();
            if (!messageText) return;
            
            // Add user message to UI
            const userMessage = {
                sender: 'user',
                content: messageText,
                timestamp: new Date().toISOString()
            };
            addMessageToUI(userMessage);
            
            // Add to current chat
            currentChat.messages.push(userMessage);
            
            // Save to history if first user message
            const chatHistory = getChatHistory();
            if (!chatHistory.some(chat => chat.id === currentChatId)) {
                chatHistory.push(currentChat);
                saveChatHistory(chatHistory);
                renderHistoryList();
            } else {
                // Update existing chat
                const existingChat = chatHistory.find(chat => chat.id === currentChatId);
                if (existingChat) {
                    existingChat.messages = currentChat.messages;
                    saveChatHistory(chatHistory);
                }
            }
            
            // Clear input
            messageInput.value = '';
            
            // Generate bot response
            generateBotResponse(messageText);
        }
        
        // Generate bot response
        function generateBotResponse(userMessage) {
            let botResponse = '';
            let updateProfileDescription = false;
            
            switch (currentChatType) {
                case 'medical':
                    botResponse = "I understand your concern. While I can't diagnose, I recommend monitoring your symptoms. If they persist or worsen, please consult a healthcare professional.";
                    updateProfileDescription = true;
                    break;
                case 'checkup':
                    botResponse = "Thanks for that information. Based on what you've shared, I suggest keeping track of these symptoms and discussing them with your doctor during your next visit.";
                    updateProfileDescription = true;
                    break;
                case 'learning':
                    botResponse = "That's an interesting topic! Here's some general information about it: [Sample educational content would go here].";
                    break;
                default:
                    botResponse = "I'm here to help. Can you tell me more about what you need?";
            }
            
            // Simulate typing delay
            setTimeout(() => {
                const botMessage = {
                    sender: 'bot',
                    content: botResponse,
                    timestamp: new Date().toISOString()
                };
                
                // Add bot message to UI
                addMessageToUI(botMessage);
                
                // Add to current chat
                currentChat.messages.push(botMessage);
                
                // Update history
                const chatHistory = getChatHistory();
                const existingChat = chatHistory.find(chat => chat.id === currentChatId);
                if (existingChat) {
                    existingChat.messages = currentChat.messages;
                    saveChatHistory(chatHistory);
                }
                
                // Update profile description if needed
                if (updateProfileDescription && profile) {
                    updateProfileWithChatInfo(userMessage);
                }
            }, 1000);
        }
        
        // Update profile with chat information
        function updateProfileWithChatInfo(userMessage) {
            if (!profile) return;
            
            const separator = profile.description ? "\n\n---\n\n" : "";
            profile.description += `${separator}${new Date().toLocaleString()}: ${userMessage}`;
            profile.updatedAt = new Date().toISOString();
            
            localStorage.setItem('healthAssistantProfile', JSON.stringify(profile));
        }
        
        // Add message to UI
        function addMessageToUI(message) {
            const messageElement = document.createElement('div');
            messageElement.classList.add('message');
            messageElement.classList.add(message.sender === 'user' ? 'user-message' : 'bot-message');
            
            const timestamp = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            messageElement.innerHTML = `
                <div>${message.content}</div>
                <div style="font-size: 0.8rem; color: #aaa; text-align: right;">${timestamp}</div>
            `;
            
            messagesContainer.appendChild(messageElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Render messages
        function renderMessages(messages) {
            messagesContainer.innerHTML = '';
            messages.forEach(message => {
                addMessageToUI(message);
            });
        }
        
        // Render history list
        function renderHistoryList() {
            const chatHistory = getChatHistory();
            historyList.innerHTML = '';
            
            if (chatHistory.length === 0) {
                historyList.innerHTML = '<p style="padding: 1rem; color: #aaa;">No conversations yet</p>';
                return;
            }
            
            chatHistory.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).forEach(chat => {
                const historyItem = document.createElement('div');
                historyItem.classList.add('history-item');
                historyItem.setAttribute('data-chat-id', chat.id);
                
                const lastMessage = chat.messages[chat.messages.length - 1]?.content || '';
                const preview = lastMessage.length > 50 ? lastMessage.substring(0, 50) + '...' : lastMessage;
                const date = new Date(chat.createdAt).toLocaleString();
                
                historyItem.innerHTML = `
                    <div class="history-title">${chat.title}</div>
                    <div class="history-preview">${preview}</div>
                    <div class="history-date">${date}</div>
                `;
                
                historyItem.addEventListener('click', () => {
                    loadChat(chat.id);
                });
                
                historyList.appendChild(historyItem);
            });
        }
        
        // Load chat from history
        function loadChat(chatId) {
            const chatHistory = getChatHistory();
            const chat = chatHistory.find(chat => chat.id === chatId);
            
            if (chat) {
                currentChatId = chatId;
                currentChatType = chat.type;
                currentChat = chat;
                chatTitle.textContent = chat.title;
                
                showChatScreen();
                renderMessages(chat.messages);
            }
        }
        
        // Get chat history from localStorage
        function getChatHistory() {
            const savedHistory = localStorage.getItem('healthAssistantChatHistory');
            return savedHistory ? JSON.parse(savedHistory) : [];
        }
        
        // Save chat history to localStorage
        function saveChatHistory(history) {
            localStorage.setItem('healthAssistantChatHistory', JSON.stringify(history));
        }
        
        // Delete all chat history
        function deleteAllHistory() {
            if (confirm("Are you sure you want to delete all chat history? This cannot be undone.")) {
                localStorage.removeItem('healthAssistantChatHistory');
                renderHistoryList();
            }
        }
        
        // Initialize the app when DOM is loaded
        document.addEventListener('DOMContentLoaded', init);
