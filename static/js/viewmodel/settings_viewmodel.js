/**
 * Settings ViewModel - Handles business logic for application settings
 * Implements observable pattern to notify subscribers of data changes
 */
class SettingsViewModel {
    constructor() {
        this.settings = {
            refreshInterval: 30, // Default value
            telegramBotToken: '',
            telegramChatId: ''
        };
        this.observers = [];
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
        return fetch('/loadSettings')
            .then(response => response.json())
            .then(data => {
                this.settings = data;
                this.notifyObservers();
                return data;
            })
            .catch(error => {
                console.error('Error fetching settings:', error);
                throw error;
            });
    }

    /**
     * Update refresh interval
     * @param {number} interval - Refresh interval in seconds
     * @returns {Promise} - Promise that resolves when refresh interval is updated
     */
    updateRefreshInterval(interval) {
        // Validate input
        if (!interval || isNaN(interval) || interval < 5) {
            return Promise.reject('5초 이상의 값을 입력해주세요.');
        }

        return fetch('/updateRefreshInterval', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ interval: interval }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.settings.refreshInterval = interval;
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

        return fetch('/updateTelegramSettings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ token, chatId }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.settings.telegramBotToken = token;
                this.settings.telegramChatId = chatId;
                this.notifyObservers();
                return data;
            } else {
                throw new Error(data.message || '텔레그램 설정 업데이트 실패');
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
        return this.settings.refreshInterval;
    }

    /**
     * Get Telegram bot token
     * @returns {string} - Current Telegram bot token
     */
    getTelegramBotToken() {
        return this.settings.telegramBotToken;
    }

    /**
     * Get Telegram chat ID
     * @returns {string} - Current Telegram chat ID
     */
    getTelegramChatId() {
        return this.settings.telegramChatId;
    }
}

export default SettingsViewModel;