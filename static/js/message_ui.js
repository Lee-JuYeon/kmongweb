/**
 * Message UI Handler - Manages UI interactions for message and chatroom management
 */
class MessageUI {
    constructor(messageViewModel, settingsViewModel) {
        this.viewModel = messageViewModel;
        this.settingsViewModel = settingsViewModel;
        
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
        
        // 설정 변경 관찰
        if (this.settingsViewModel) {
            this.settingsViewModel.addObserver(this._handleSettingsChanged.bind(this));
        }
    }

    /**
     * 설정 변경 핸들러 - 설정 변경 시 채팅방 목록 다시 렌더링
     * @param {Object} settings - 변경된 설정 정보
     * @private
     */
    _handleSettingsChanged(settings) {
        // 체크박스 상태가 변경되었을 가능성이 있으므로 채팅방 목록 다시 렌더링
        this._renderChatrooms(this.viewModel.getChatrooms());
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
     * 채팅방 체크박스 클릭 처리
     * @param {Event} event - 클릭 이벤트
     * @param {number} chatroomId - 채팅방 ID
     * @private
     */
    _handleChatroomCheckboxClick(event, chatroomId) {
        // 이벤트 전파 중지 (채팅방 선택 이벤트 방지)
        event.stopPropagation();
        
        // 체크박스 상태 가져오기
        const isChecked = event.target.checked;
        
        // 설정 업데이트
        if (this.settingsViewModel) {
            this.settingsViewModel.updateChatroomCheck(chatroomId, isChecked)
                .then(() => {
                    console.log(`채팅방 ${chatroomId} 체크 상태 업데이트 완료: ${isChecked}`);
                })
                .catch(error => {
                    console.error(`채팅방 체크 상태 업데이트 실패:`, error);
                    // 실패 시 체크박스 상태 원복
                    event.target.checked = !isChecked;
                });
        }
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
            
            // Create checkbox container
            const checkboxContainer = document.createElement('div');
            checkboxContainer.classList.add('chatroom-checkbox-container');
            
            // Create checkbox
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.classList.add('chatroom-checkbox');
            checkbox.id = `chatroom-check-${chatroomData.chatroom_id}`;
            
            // Set checkbox state from settings
            if (this.settingsViewModel) {
                checkbox.checked = this.settingsViewModel.isChatroomChecked(chatroomData.chatroom_id);
            }
            
            // Add checkbox event listener
            checkbox.addEventListener('click', (event) => 
                this._handleChatroomCheckboxClick(event, chatroomData.chatroom_id)
            );
            
            checkboxContainer.appendChild(checkbox);
            
            // Email display
            const emailContainer = document.createElement('div');
            emailContainer.classList.add('chatroom-content-container');
            
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
            emailContainer.appendChild(emailElement);
            emailContainer.appendChild(messageElement);
            
            chatRoomItem.appendChild(checkboxContainer);
            chatRoomItem.appendChild(emailContainer);
            
            // Add click event (전체 아이템 클릭 이벤트는 체크박스 클릭 시 예외 처리)
            chatRoomItem.addEventListener('click', (event) => {
                // 체크박스 클릭 이벤트가 아닌 경우에만 채팅방 선택 처리
                if (!event.target.classList.contains('chatroom-checkbox')) {
                    this._handleChatroomSelection(chatRoomItem);
                }
            });
            
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
        
        // 변경: 메시지 로드 전에 먼저 읽음 처리 요청
        this.viewModel.markMessagesAsRead(chatroomId)
            .then(() => {
                // 읽음 처리 후 메시지 로드
                return this.viewModel.loadMessages(chatroomId);
            })
            .catch(error => {
                console.error('메시지 읽음 처리 중 오류:', error);
                // 오류가 발생해도 메시지는 로드
                this.viewModel.loadMessages(chatroomId);
            });

        // 채팅방 선택 표시 (UI)
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
        // 먼저 설정 로드 (체크박스 상태 가져오기 위해)
        if (this.settingsViewModel) {
            this.settingsViewModel.loadSettings()
                .then(() => {
                    // 설정 로드 후 채팅방 목록 로드
                    return this.viewModel.loadChatrooms();
                })
                .catch(error => console.error('Error initializing message UI:', error));
        } else {
            // 설정 ViewModel이 없는 경우 기본 초기화
            this.viewModel.loadChatrooms()
                .catch(error => console.error('Error initializing message UI:', error));
        }
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