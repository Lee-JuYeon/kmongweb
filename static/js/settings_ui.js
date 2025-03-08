import SettingsViewModel from './viewmodel/settings_viewmodel.js';

class SettingsUI {
    constructor() {
        // Initialize ViewModel
        this.viewModel = new SettingsViewModel();
        
        // DOM elements - Settings dropdown
        this.settingsButton = document.getElementById('settings-button');
        this.settingsDropdown = document.getElementById('settings-dropdown');
        this.accountManagementMenu = document.getElementById('account-management-menu'); 
        this.refreshRateMenu = document.getElementById('refresh-rate-menu');
        this.telegramBotMenu = document.getElementById('telegram-bot-menu');

        // DOM elements - Refresh rate modal
        this.refreshModal = document.getElementById('refresh-rate-modal');
        this.refreshCloseBtn = this.refreshModal?.querySelector('.close-modal');
        this.refreshSaveBtn = document.getElementById('set-refresh-rate');
        this.refreshIntervalInput = document.getElementById('refresh-interval');
        
        // DOM elements - Telegram bot modal
        this.telegramModal = document.getElementById('telegram-bot-modal');
        this.telegramCloseBtn = this.telegramModal?.querySelector('.close-modal');
        this.telegramSaveBtn = document.getElementById('set-telegram-bot');
        this.telegramBotTokenInput = document.getElementById('telegram-bot-token');
        this.telegramChatIdInput = document.getElementById('telegram-chat-id');
        
        // 새로운 텔레그램 ID 확인 버튼
        this.telegramCheckIdBtn = document.getElementById('check-telegram-id');
        this.telegramTestBtn = document.getElementById('test-telegram-bot');
        this.telegramStatusMessage = document.getElementById('telegram-status-message');
        
        // Subscribe to ViewModel updates
        this.viewModel.addObserver(this._handleSettingsUpdate.bind(this));
        
        // Initialize event listeners
        this._initEventListeners();
        
        // 드롭다운 요소 직접 참조 업데이트 (안전장치)
        this.settingsDropdown = document.getElementById('settings-dropdown');
    }

    /**
     * Initialize event listeners for UI controls
     * @private
     */
    _initEventListeners() {
        // Settings dropdown toggle
        if (this.settingsButton) {
            console.log("Settings button found:", this.settingsButton);
            this.settingsButton.addEventListener('click', (event) => {
                console.log("Settings button clicked");
                event.stopPropagation(); // 이벤트 버블링 방지
                
                // 현재 상태 확인
                const isVisible = this.settingsDropdown.style.display === 'block';
                
                // 상태 토글
                if (isVisible) {
                    this.settingsDropdown.style.display = 'none';
                } else {
                    this.settingsDropdown.style.display = 'block';
                    
                    // 중요: 비동기 작업 후에도 표시 상태 유지
                    setTimeout(() => {
                        if (this.settingsDropdown) {
                            this.settingsDropdown.style.display = 'block';
                        }
                    }, 0);
                }
                
                console.log("Dropdown display:", this.settingsDropdown.style.display);
            });
        }
        
        // 다른 영역 클릭 시 드롭다운 닫기
        document.addEventListener('click', (event) => {
            // 클릭된 요소가 버튼이나 드롭다운 내부가 아닌 경우에만 닫기
            if (this.settingsDropdown && 
                event.target !== this.settingsButton && 
                !this.settingsButton.contains(event.target) &&
                !this.settingsDropdown.contains(event.target)) {
                
                this.settingsDropdown.style.display = 'none';
            }
        });
        
        // Menu item clicks
        if (this.refreshRateMenu) {
            this.refreshRateMenu.addEventListener('click', (e) => {
                e.preventDefault();
                this.settingsDropdown.style.display = 'none'; // 클래스 제거 대신 직접 스타일 설정
                this.refreshModal.style.display = 'block';
                // Pre-fill with current value
                this.refreshIntervalInput.value = this.viewModel.getRefreshInterval();
            });
        }
        
        // 계정 관리 메뉴 클릭 이벤트 리스너 추가
        if (this.accountManagementMenu) {
            this.accountManagementMenu.addEventListener('click', (e) => {
                e.preventDefault();
                this.settingsDropdown.style.display = 'none'; // 드롭다운 닫기
                
                // 계정 관리 모달 열기
                const accountModal = document.getElementById('account_modal');
                if (accountModal) {
                    accountModal.style.display = 'flex';
                }
            });
        }

        if (this.telegramBotMenu) {
            this.telegramBotMenu.addEventListener('click', (e) => {
                e.preventDefault();
                this.settingsDropdown.style.display = 'none';
                this.telegramModal.style.display = 'block';
                // Pre-fill with current values
                this.telegramBotTokenInput.value = this.viewModel.getTelegramBotToken();
                this.telegramChatIdInput.value = this.viewModel.getTelegramChatId();
                
                // 상태 메시지 초기화
                if (this.telegramStatusMessage) {
                    this.telegramStatusMessage.textContent = '';
                    this.telegramStatusMessage.className = '';
                }
            });
        }
        
        // Refresh modal events
        if (this.refreshCloseBtn) {
            this.refreshCloseBtn.addEventListener('click', () => {
                this.refreshModal.style.display = 'none';
            });
        }
        
        if (this.refreshSaveBtn) {
            this.refreshSaveBtn.addEventListener('click', () => this._handleRefreshSave());
        }
        
        if (this.refreshIntervalInput) {
            this.refreshIntervalInput.addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    this._handleRefreshSave();
                }
            });
        }
        
        // Telegram modal events
        if (this.telegramCloseBtn) {
            this.telegramCloseBtn.addEventListener('click', () => {
                // 모달 닫기 시 ID 확인 모드 중지
                if (this.viewModel.isIdCheckActive()) {
                    this.viewModel.stopTelegramIdCheck()
                        .catch(error => console.error('ID 확인 모드 중지 실패:', error));
                }
                this.telegramModal.style.display = 'none';
            });
        }
        
        if (this.telegramSaveBtn) {
            this.telegramSaveBtn.addEventListener('click', () => this._handleTelegramSave());
        }
        
        // 텔레그램 ID 확인 버튼 이벤트
        if (this.telegramCheckIdBtn) {
            this.telegramCheckIdBtn.addEventListener('click', () => this._handleTelegramIdCheck());
        }
        
        // 텔레그램 테스트 버튼 이벤트
        if (this.telegramTestBtn) {
            this.telegramTestBtn.addEventListener('click', () => this._handleTelegramTest());
        }
        
        // Close modals when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target === this.refreshModal) {
                this.refreshModal.style.display = 'none';
            }
            if (event.target === this.telegramModal) {
                // 모달 닫기 시 ID 확인 모드 중지
                if (this.viewModel.isIdCheckActive()) {
                    this.viewModel.stopTelegramIdCheck()
                        .catch(error => console.error('ID 확인 모드 중지 실패:', error));
                }
                this.telegramModal.style.display = 'none';
            }
        });
    }

    /**
     * Handle refresh interval save button click
     * @private
     */
    _handleRefreshSave() {
        const intervalValue = this.refreshIntervalInput?.value;
        
        this.viewModel.updateRefreshInterval(parseInt(intervalValue))
            .then(response => {
                alert('갱신주기가 업데이트되었습니다.');
                this.refreshModal.style.display = 'none';
            })
            .catch(error => {
                alert('갱신주기 업데이트 실패: ' + error);
                console.error('Error updating refresh interval:', error);
            });
    }

    /**
     * Handle Telegram settings save button click
     * @private
     */
    _handleTelegramSave() {
        const token = this.telegramBotTokenInput?.value;
        const chatId = this.telegramChatIdInput?.value;
        
        // 저장 전 ID 확인 모드 중지
        if (this.viewModel.isIdCheckActive()) {
            this.viewModel.stopTelegramIdCheck()
                .catch(error => console.error('ID 확인 모드 중지 실패:', error));
        }
        
        this.viewModel.updateTelegramSettings(token, chatId)
            .then(response => {
                alert('텔레그램 설정이 업데이트되었습니다.');
                this.telegramModal.style.display = 'none';
            })
            .catch(error => {
                alert('텔레그램 설정 업데이트 실패: ' + error);
                console.error('Error updating Telegram settings:', error);
            });
    }
    
    /**
     * Handle Telegram ID check button click
     * @private
     */
    _handleTelegramIdCheck() {
        const token = this.telegramBotTokenInput?.value;
        
        if (!token) {
            alert('텔레그램 봇 토큰을 입력해주세요.');
            return;
        }
        
        // 이미 ID 확인 모드가 활성화된 경우 중지
        if (this.viewModel.isIdCheckActive()) {
            this._updateTelegramStatus('ID 확인 모드를 중지합니다...', 'info');
            
            this.viewModel.stopTelegramIdCheck()
                .then(() => {
                    this._updateTelegramStatus('ID 확인 모드가 중지되었습니다.', 'success');
                    this.telegramCheckIdBtn.textContent = 'Chat ID 자동 확인';
                })
                .catch(error => {
                    this._updateTelegramStatus('ID 확인 모드 중지 실패: ' + error, 'error');
                    console.error('ID 확인 모드 중지 실패:', error);
                });
        } else {
            // ID 확인 모드 시작
            this._updateTelegramStatus('ID 확인 모드를 시작합니다...', 'info');
            
            this.viewModel.startTelegramIdCheck(token)
                .then(() => {
                    this._updateTelegramStatus(
                        '텔레그램 앱에서 봇을 찾아 메시지를 보내고 "/id" 명령어를 실행하세요. 받은 ID를 위 Chat ID 필드에 입력하세요.', 
                        'success'
                    );
                    this.telegramCheckIdBtn.textContent = 'ID 확인 모드 중지';
                })
                .catch(error => {
                    this._updateTelegramStatus('ID 확인 모드 시작 실패: ' + error, 'error');
                    console.error('ID 확인 모드 시작 실패:', error);
                });
        }
    }
    
    /**
     * Handle Telegram test button click
     * @private
     */
    _handleTelegramTest() {
        const token = this.telegramBotTokenInput?.value;
        const chatId = this.telegramChatIdInput?.value;
        
        if (!token || !chatId) {
            alert('텔레그램 봇 토큰과 채팅 ID를 모두 입력해주세요.');
            return;
        }
        
        // 저장하지 않고 바로 테스트 메시지 전송
        this._updateTelegramStatus('테스트 메시지를 전송합니다...', 'info');
        
        // 임시로 설정 업데이트 후 테스트 메시지 전송
        this.viewModel.updateTelegramSettings(token, chatId)
            .then(() => this.viewModel.sendTestMessage())
            .then(() => {
                this._updateTelegramStatus('테스트 메시지가 성공적으로 전송되었습니다.', 'success');
            })
            .catch(error => {
                this._updateTelegramStatus('테스트 메시지 전송 실패: ' + error, 'error');
                console.error('테스트 메시지 전송 실패:', error);
            });
    }
    
    /**
     * Update Telegram status message
     * @param {string} message - Status message
     * @param {string} type - Message type (info, success, error)
     * @private
     */
    _updateTelegramStatus(message, type) {
        if (!this.telegramStatusMessage) return;
        
        this.telegramStatusMessage.textContent = message;
        this.telegramStatusMessage.className = `telegram-status-${type}`;
    }

    /**
     * Handle settings update from ViewModel
     * @param {Object} settings - Updated settings data
     * @private
     */
    _handleSettingsUpdate(settings) {
        // Update UI with new settings if needed
        console.log('Settings updated:', settings);
    }

    /**
     * Initialize the settings UI handler
     */
    initialize() {
        // Load initial settings
        this.viewModel.loadSettings()
            .then(() => {
                console.log('Settings loaded successfully');
            })
            .catch(error => {
                console.error('Error loading settings:', error);
            });
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    const settingsUI = new SettingsUI();
    settingsUI.initialize();
});

export default SettingsUI;