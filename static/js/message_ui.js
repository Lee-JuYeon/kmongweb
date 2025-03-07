/**
 * Message UI Handler - Manages UI interactions for message and chatroom management
 */
class MessageUI {
    constructor(messageViewModel) {
        this.viewModel = messageViewModel;
        
        // DOM elements
        this.chatRoomListContainer = document.getElementById('chat-room-list');
        this.chatListContainer = document.getElementById('chat-list');
        this.replyEditText = document.getElementById('reply-edittext');
        this.sendButton = document.getElementById('send-button');
        this.syncButton = document.getElementById('chat-sync-text');
        
        // Initialize event listeners
        this._initEventListeners();
        
        // Subscribe to view model changes
        this.viewModel.addChatroomObserver(this._renderChatrooms.bind(this));
        this.viewModel.addMessageObserver(this._renderMessages.bind(this));
    }

    /**
     * Initialize all UI event listeners
     * @private
     */
    _initEventListeners() {
        // Send button
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this._handleSendMessage());
        }
        
        // Sync button
        if (this.syncButton) {
            this.syncButton.addEventListener('click', () => this._handleSyncChatHistory());
        }
    }

    /**
     * Handle send message button click
     * @private
     */
    _handleSendMessage() {
        const messageText = this.replyEditText?.value;
        if (!messageText || !messageText.trim()) {
            alert('메시지 내용을 입력해주세요.');
            return;
        }
        
        this.viewModel.sendMessage(messageText)
            .then(() => {
                // Clear input field
                if (this.replyEditText) this.replyEditText.value = '';
            })
            .catch(error => {
                alert('메시지 전송 실패: ' + error);
                console.error('Error sending message:', error);
            });
    }

    /**
     * Handle sync chat history button click
     * @private
     */
    _handleSyncChatHistory() {
        this.viewModel.syncChatHistory()
            .then(() => {
                console.log('채팅 내역 동기화 완료');
            })
            .catch(error => {
                alert('채팅 내역 동기화 실패: ' + error);
                console.error('Error syncing chat history:', error);
            });
    }

    /**
     * Render chatrooms in the UI (observer callback)
     * @param {Array} chatrooms - Array of chatroom objects
     * @private
     */
    _renderChatrooms(chatrooms) {
        if (!this.chatRoomListContainer) return;
        
        this.chatRoomListContainer.innerHTML = '';  // Clear existing list
        
        chatrooms.forEach(chatroomData => {
            const chatRoomItem = document.createElement('div');
            chatRoomItem.classList.add('chat-room-item');
            
            // Store chatroom data
            chatRoomItem.setAttribute('data-chatroom-id', chatroomData.chatroom_id);
            
            // Email display
            const emailElement = document.createElement('div');
            emailElement.classList.add('chat-room-email');
            
            // Count unread messages
            let unreadMessages = 0;
            for (let i = 0; i < chatroomData.messages.length; i++) {
                if (chatroomData.messages[i].seen == 0 && 
                    chatroomData.messages[i].client_id == chatroomData.messages[i].sender_id) {
                    unreadMessages++;
                }
            }
            
            // Show unread message count
            if (unreadMessages > 0) {
                emailElement.innerText = `🔔 ${chatroomData.email} (${unreadMessages})`;
            } else {
                emailElement.innerText = chatroomData.email;
            }
            
            // Last message display
            let lastMessageText = `새 메시지가 없습니다.(${chatroomData.chatroom_id})`;
            if (chatroomData.messages.length > 0) {
                const lastMessage = chatroomData.messages[chatroomData.messages.length - 1];
                lastMessageText = lastMessage.text;
                
                // Store client and admin IDs
                chatRoomItem.setAttribute('data-client-id', lastMessage.client_id);
                chatRoomItem.setAttribute('data-admin-id', lastMessage.admin_id);
            }
            
            const messageElement = document.createElement('div');
            messageElement.innerText = lastMessageText;
            messageElement.classList.add('chat-room-message');
            
            // Add elements to chatroom item
            chatRoomItem.appendChild(emailElement);
            chatRoomItem.appendChild(messageElement);
            
            // Add click event
            chatRoomItem.addEventListener('click', () => this._handleChatroomSelection(chatRoomItem));
            
            // Add to list
            this.chatRoomListContainer.appendChild(chatRoomItem);
        });
    }

    /**
     * Handle chatroom selection
     * @param {HTMLElement} chatRoomItem - Selected chatroom element
     * @private
     */
    _handleChatroomSelection(chatRoomItem) {
        const chatroomId = chatRoomItem.getAttribute('data-chatroom-id');
        const clientId = chatRoomItem.getAttribute('data-client-id');
        const adminId = chatRoomItem.getAttribute('data-admin-id');
        
        // Update view model
        this.viewModel.setCurrentChatroom(chatroomId, clientId, adminId);
        
        // Load messages
        this.viewModel.loadMessages(chatroomId);
        
        // Highlight selected chatroom
        document.querySelectorAll('.chat-room-item').forEach(item => {
            item.classList.remove('selected');
        });
        chatRoomItem.classList.add('selected');
    }

    /**
     * Render messages in the UI (observer callback)
     * @param {Array} messages - Array of message objects
     * @private
     */
    _renderMessages(messages) {
        if (!this.chatListContainer) return;
        
        this.chatListContainer.innerHTML = '';  // Clear existing list
        
        if (messages.length === 0) {
            this.chatListContainer.innerHTML = '<p>메시지가 없습니다.</p>';
            return;
        }
        
        const currentChatroom = this.viewModel.getCurrentChatroomInfo();
        
        messages.forEach(message => {
            const messageContainer = document.createElement('div');
            messageContainer.classList.add('message-container');
            
            // Store message data
            messageContainer.dataset.chatroomId = currentChatroom.chatroomId;
            messageContainer.dataset.clientId = message.client_id;
            messageContainer.dataset.adminId = message.admin_id;
            
            const messageElement = document.createElement('div');
            messageElement.classList.add('message-item');
            
            // Format date
            const formattedDate = new Date(message.date).toLocaleString("ko-KR", {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            });
            
            // Determine message style based on sender
            const isSender = message.client_id === message.sender_id;
            const backgroundClass = isSender ? 'gray-background' : 'yellow-background';
            
            // Message content
            messageElement.innerHTML = `
                <div class="message-text ${backgroundClass}">
                    ${message.text}
                </div>
                <div class="message-date">${formattedDate}</div>
            `;
            
            // Set alignment based on sender
            messageContainer.classList.add(isSender ? 'left' : 'right');
            messageContainer.appendChild(messageElement);
            
            // Add to chat list
            this.chatListContainer.appendChild(messageContainer);
        });
        
        // Scroll to bottom
        this.chatListContainer.scrollTop = this.chatListContainer.scrollHeight;
    }

    /**
     * Initialize UI by loading chatrooms
     */
    initialize() {
        this.viewModel.loadChatrooms()
            .catch(error => console.error('Error initializing message UI:', error));
    }

    /**
     * Start auto-refresh for chatrooms
     * @param {number} interval - Refresh interval in milliseconds
     */
    startAutoRefresh(interval = 30000) {
        setInterval(() => {
            this.viewModel.loadChatrooms()
                .catch(error => console.error('Error auto-refreshing chatrooms:', error));
        }, interval);
    }
}

export default MessageUI;