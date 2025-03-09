import AccountViewModel from './viewmodel/account_viewmodel.js';
import MessageViewModel from './viewmodel/message_viewmodel.js';
import AiReplyViewModel from './viewmodel/ai_reply_viewmodel.js';
import SettingsViewModel from './viewmodel/settings_viewmodel.js';
import AccountUI from './account_ui.js';
import MessageUI from './message_ui.js';
import AiReplyModal from './ai_reply_modal.js'
import SettingsUI from './settings_ui.js';  // 갱신주기 핸들러 import


document.addEventListener('DOMContentLoaded', function() {
    // Initialize ViewModels
    const accountViewModel = new AccountViewModel();
    const messageViewModel = new MessageViewModel();
    const aiReplyViewModel = new AiReplyViewModel();
    const settingsViewModel = new SettingsViewModel();

    // Initialize UI handlers
    const accountUI = new AccountUI(accountViewModel);
    // SettingsViewModel을 MessageUI 생성자에 전달 (체크박스 상태 관리용)
    const messageUI = new MessageUI(messageViewModel, settingsViewModel);
    const aiReplyModal = new AiReplyModal(aiReplyViewModel, messageViewModel);
    const settingsUI = new SettingsUI(settingsViewModel);  // SettingsViewModel 전달
 

    // Initialize UIs
    accountUI.initialize();
    messageUI.initialize();
    // aiReplyModal.initialize()
    setttingsUI.initialize();  // 갱신주기 핸들러 초기화

    
    // Start auto-refresh for chatrooms
    messageUI.startAutoRefresh(30000);
});
