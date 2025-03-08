/**
 * Message ViewModel - Handles business logic for message and chatroom management
 * Implements observable pattern to notify subscribers of data changes
 */
class MessageViewModel {
    constructor() {
        this.chatrooms = [];
        this.messages = [];
        this.currentChatroomId = null;
        this.currentClientId = null;
        this.currentAdminId = null;
        
        // Observer lists for different data types
        this.chatroomObservers = [];
        this.messageObservers = [];
        this.currentChatroomObservers = [];
    }

    /**
     * Add an observer for chatrooms
     * @param {Function} observer - Callback function to be called on data change
     */
    addChatroomObserver(observer) {
        this.chatroomObservers.push(observer);
    }

    /**
     * Add an observer for messages
     * @param {Function} observer - Callback function to be called on data change
     */
    addMessageObserver(observer) {
        this.messageObservers.push(observer);
    }

    /**
     * Add an observer for current chatroom changes
     * @param {Function} observer - Callback function to be called on data change
     */
    addCurrentChatroomObserver(observer) {
        this.currentChatroomObservers.push(observer);
    }

    /**
     * Remove a chatroom observer
     * @param {Function} observer - Observer to remove
     */
    removeChatroomObserver(observer) {
        this.chatroomObservers = this.chatroomObservers.filter(obs => obs !== observer);
    }

    /**
     * Remove a message observer
     * @param {Function} observer - Observer to remove
     */
    removeMessageObserver(observer) {
        this.messageObservers = this.messageObservers.filter(obs => obs !== observer);
    }

    /**
     * Remove a current chatroom observer
     * @param {Function} observer - Observer to remove
     */
    removeCurrentChatroomObserver(observer) {
        this.currentChatroomObservers = this.currentChatroomObservers.filter(obs => obs !== observer);
    }

    /**
     * Notify chatroom observers
     */
    notifyChatroomObservers() {
        this.chatroomObservers.forEach(observer => observer(this.chatrooms));
    }

    /**
     * Notify message observers
     */
    notifyMessageObservers() {
        this.messageObservers.forEach(observer => observer(this.messages));
    }

    /**
     * Notify current chatroom observers
     */
    notifyCurrentChatroomObservers() {
        const currentChatroomData = {
            chatroomId: this.currentChatroomId,
            clientId: this.currentClientId,
            adminId: this.currentAdminId
        };
        this.currentChatroomObservers.forEach(observer => observer(currentChatroomData));
    }

    /**
     * Set current chatroom
     * @param {string} chatroomId - Chatroom ID
     * @param {string} clientId - Client ID
     * @param {string} adminId - Admin ID
     */
    setCurrentChatroom(chatroomId, clientId, adminId) {
        this.currentChatroomId = chatroomId;
        this.currentClientId = clientId;
        this.currentAdminId = adminId;
        this.notifyCurrentChatroomObservers();
    }

    /**
     * Load chatrooms from server
     * @returns {Promise} - Promise that resolves when chatrooms are loaded
     */
    loadChatrooms() {
        return fetch('/api/message/updateChatroomList')
            .then(response => response.json())
            .then(data => {
                this.chatrooms = data;
                this.notifyChatroomObservers();
                return data;
            })
            .catch(error => {
                console.error('Error fetching chatroom list:', error);
                throw error;
            });
    }

    /**
     * Load messages for a specific chatroom
     * @param {string} chatroomId - Chatroom ID
     * @returns {Promise} - Promise that resolves when messages are loaded
     */
    loadMessages(chatroomId) {
        return fetch(`/api/message/loadChatHistory/${chatroomId}`)
            .then(response => {
                if (!response.ok) throw new Error("메시지를 불러오는 데 실패했습니다.");
                return response.json();
            })
            .then(data => {
                this.messages = data;
                this.notifyMessageObservers();
                // 여기서 this._markMessagesAsRead(chatroomId)를 호출했지만, 해당 메소드가 없음
                // 대신 markMessagesAsRead를 사용
                return data;
            })
            .catch(error => {
                console.error('메시지 로딩 중 오류:', error);
                throw error;
            });
    }

    /**
    * 메시지를 읽음 처리하는 메소드
     * @param {string} chatroomId - Chatroom ID
     * @returns {Promise} - Promise that resolves when messages are marked as read
     */
    markMessagesAsRead(chatroomId) {
        const requestData = { chatroom_id: chatroomId };
        return fetch('/api/message/updateClientUnreadMessage', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) throw new Error("메시지 읽음 처리에 실패했습니다.");
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 읽음 처리 후 채팅방 목록 업데이트 (읽지 않은 메시지 카운트 갱신을 위해)
                return this.loadChatrooms().then(() => data);
            } else {
                throw new Error(data.message || "메시지 읽음 처리 실패");
            }
        })
        .catch(error => {
            console.error("메시지 읽음 처리 중 오류:", error);
            throw error;
        });
    }
    
    /**
     * Send a message
     * @param {string} text - Message text
     * @returns {Promise} - Promise that resolves when message is sent
     */
    sendMessage(text) {
        if (!text || !text.trim()) {
            return Promise.reject("메시지 내용이 없습니다.");
        }

        if (!this.currentChatroomId || !this.currentClientId || !this.currentAdminId) {
            return Promise.reject("채팅방 정보가 없습니다.");
        }

        const requestData = {
            chatroom_id: this.currentChatroomId,
            client_id: this.currentClientId,
            admin_id: this.currentAdminId,
            text: text.trim()
        };

        return fetch('/api/message/sendMessageInWeb', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) throw new Error("메시지 전송에 실패했습니다.");
            return response.json();
        })
        .then(data => {
            if (data.success) {
                return Promise.all([
                    this.loadMessages(this.currentChatroomId),
                    this.loadChatrooms()
                ]).then(() => data);
            } else {
                throw new Error(data.message || "메시지 전송 실패");
            }
        });
    }

    /**
     * Sync chat history with server
     * @returns {Promise} - Promise that resolves when chat history is synced
     */
    syncChatHistory() {
        if (!this.currentChatroomId || !this.currentClientId || !this.currentAdminId) {
            return Promise.reject("채팅방 정보가 없습니다.");
        }

        const requestData = {
            chatroom_id: this.currentChatroomId,
            client_id: this.currentClientId,
            admin_id: this.currentAdminId
        };

        return fetch('/api/message/syncChatHistory', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) throw new Error("채팅 내역 동기화에 실패했습니다.");
            return response.json();
        })
        .then(data => {
            if (data.success) {
                return Promise.all([
                    this.loadMessages(this.currentChatroomId),
                    this.loadChatrooms()
                ]).then(() => data);
            } else {
                throw new Error(data.message || "채팅 내역 동기화 실패");
            }
        });
    }

    /**
     * Get current chatrooms
     * @returns {Array} - Array of chatroom objects
     */
    getChatrooms() {
        return this.chatrooms;
    }

    /**
     * Get current messages
     * @returns {Array} - Array of message objects
     */
    getMessages() {
        return this.messages;
    }

    /**
     * Get current chatroom info
     * @returns {Object} - Current chatroom info object
     */
    getCurrentChatroomInfo() {
        return {
            chatroomId: this.currentChatroomId,
            clientId: this.currentClientId,
            adminId: this.currentAdminId
        };
    }
}

export default MessageViewModel;