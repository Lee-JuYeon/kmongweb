class SettingsViewModel {
    constructor() {
        this.settings = {
            refreshInterval: {
                parseUnReadMessagesinDB: 30,
                sendUnReadMessagesViaTelebot: 30,
                replyViaTeleBot: 10
            },
            telegram: {
                botToken: '',
                chatId: ''
            },
            chatrooms: {
                checked: []
            }
        };
        this.observers = [];
        this.isChecking = false; // ID 확인 모드 상태
    }

    /**
     * Add an observer to be notified of data changes
     * @param {Function} observer - Callback function to be called on data change
     */
    addObserver(observer) {
        this.observers.push(observer);
    }

    /**
     * Remove an observer
     * @param {Function} observer - Observer to remove
     */
    removeObserver(observer) {
        this.observers = this.observers.filter(obs => obs !== observer);
    }

    /**
     * Notify all observers with current settings data
     */
    notifyObservers() {
        this.observers.forEach(observer => observer(this.settings));
    }

    /**
     * Load settings from server
     * @returns {Promise} - Promise that resolves when settings are loaded
     */
    loadSettings() {
        return fetch('/api/settings/loadSettings')
            .then(response => response.json())
            .then(data => {
                this.settings = data;
                this.notifyObservers();
                return data;
            })
            .catch(error => {
                console.error('설정 불러오기 실패:', error);
                throw error;
            });
    }

    updateRefreshInterval(interval) {
        // 입력값 검증
        if (!interval || isNaN(interval) || interval < 5) {
            return Promise.reject('5초 이상의 값을 입력해주세요.');
        }
    
        console.log(`settings_viewmodel.js, updateRefreshInterval // 갱신주기 설정 요청: ${interval}초`);
    
        return fetch('/api/settings/updateRefreshInterval', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ interval: interval }),
        })
        .then(response => {
            console.log(`settings_viewmodel.js, updateRefreshInterval // 서버 응답 상태: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log(`settings_viewmodel.js, updateRefreshInterval // 서버 응답 데이터:`, data);
            if (data.success) {
                this.settings.refreshInterval.parseUnReadMessagesinDB = interval;
                this.settings.refreshInterval.sendUnReadMessagesViaTelebot = interval;
                this.settings.refreshInterval.replyViaTeleBot = Math.max(5, Math.floor(interval / 3));
                this.notifyObservers();
                return data;
            } else {
                throw new Error(data.message || '갱신주기 업데이트 실패');
            }
        });
    }

    /**
     * Update Telegram bot settings
     * @param {string} token - Telegram bot token
     * @param {string} chatId - Telegram chat ID
     * @returns {Promise} - Promise that resolves when Telegram settings are updated
     */
    updateTelegramSettings(token, chatId) {
        if (!token || !chatId) {
            return Promise.reject('텔레그램 봇 토큰과 채팅 ID를 입력해주세요.');
        }

        return fetch('/api/settings/updateTelegramSettings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token, chatId }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.settings.telegram.botToken = token;
                this.settings.telegram.chatId = chatId;
                this.notifyObservers();
                return data;
            } else {
                throw new Error(data.message || '텔레그램 설정 업데이트 실패');
            }
        });
    }

    /**
     * Update the check status of a chatroom
     * @param {number} chatroomId - The chatroom ID
     * @param {boolean} isChecked - Whether the chatroom is checked
     * @returns {Promise} - Promise that resolves when the chatroom check status is updated
     */
    updateChatroomCheck(chatroomId, isChecked) {
        if (chatroomId === undefined || chatroomId === null) {
            return Promise.reject('채팅방 ID가 필요합니다.');
        }

        return fetch('/api/settings/updateChatroomCheck', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ chatroomId, isChecked }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 체크된 채팅방 목록 업데이트
                if (!this.settings.chatrooms) {
                    this.settings.chatrooms = { checked: [] };
                }
                
                const checkedList = this.settings.chatrooms.checked || [];
                
                if (isChecked && !checkedList.includes(chatroomId)) {
                    checkedList.push(chatroomId);
                } else if (!isChecked && checkedList.includes(chatroomId)) {
                    const index = checkedList.indexOf(chatroomId);
                    if (index !== -1) {
                        checkedList.splice(index, 1);
                    }
                }
                
                this.settings.chatrooms.checked = checkedList;
                this.notifyObservers();
                return data;
            } else {
                throw new Error(data.message || '채팅방 체크 상태 업데이트 실패');
            }
        });
    }

    /**
     * Get all checked chatroom IDs
     * @returns {Array} - Array of checked chatroom IDs
     */
    getCheckedChatrooms() {
        if (!this.settings.chatrooms || !this.settings.chatrooms.checked) {
            return [];
        }
        return this.settings.chatrooms.checked;
    }

    /**
     * Check if a chatroom is checked
     * @param {number} chatroomId - The chatroom ID
     * @returns {boolean} - Whether the chatroom is checked
     */
    isChatroomChecked(chatroomId) {
        const checkedList = this.getCheckedChatrooms();
        return checkedList.includes(chatroomId);
    }

    /**
     * Start Telegram ID check mode
     * @param {string} token - Telegram bot token
     * @returns {Promise} - Promise that resolves when ID check mode is started
     */
    startTelegramIdCheck(token) {
        if (!token) {
            return Promise.reject('텔레그램 봇 토큰을 입력해주세요.');
        }

        this.isChecking = true;

        return fetch('/api/settings/startTelegramIdCheck', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return data;
            } else {
                this.isChecking = false;
                throw new Error(data.message || '텔레그램 ID 확인 모드 시작 실패');
            }
        })
        .catch(error => {
            this.isChecking = false;
            throw error;
        });
    }

    /**
     * Stop Telegram ID check mode
     * @returns {Promise} - Promise that resolves when ID check mode is stopped
     */
    stopTelegramIdCheck() {
        return fetch('/api/settings/stopTelegramIdCheck', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            this.isChecking = false;
            if (data.success) {
                return data;
            } else {
                throw new Error(data.message || '텔레그램 ID 확인 모드 중지 실패');
            }
        })
        .catch(error => {
            this.isChecking = false;
            throw error;
        });
    }

    /**
     * Send test message via Telegram
     * @param {string} message - Message to send (optional)
     * @returns {Promise} - Promise that resolves when test message is sent
     */
    sendTestMessage(message = '🔔 이것은 테스트 메시지입니다.') {
        return fetch('/api/settings/testTelegramMessage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return data;
            } else {
                throw new Error(data.message || '테스트 메시지 전송 실패');
            }
        });
    }

    /**
     * Get current settings data
     * @returns {Object} - Settings object
     */
    getSettings() {
        return this.settings;
    }

    /**
     * Get refresh interval
     * @returns {number} - Current refresh interval in seconds
     */
    getRefreshInterval() {
        return this.settings.refreshInterval.parseUnReadMessagesinDB;
    }

    /**
     * Get Telegram bot token
     * @returns {string} - Current Telegram bot token
     */
    getTelegramBotToken() {
        return this.settings.telegram.botToken;
    }

    /**
     * Get Telegram chat ID
     * @returns {string} - Current Telegram chat ID
     */
    getTelegramChatId() {
        return this.settings.telegram.chatId;
    }

    /**
     * Check if Telegram ID check mode is active
     * @returns {boolean} - True if ID check mode is active
     */
    isIdCheckActive() {
        return this.isChecking;
    }
}

export default SettingsViewModel;