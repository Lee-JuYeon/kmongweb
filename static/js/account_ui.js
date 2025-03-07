/**
 * Account UI Handler - Manages UI interactions for account management
 */
class AccountUI {
    constructor(accountViewModel) {
        this.viewModel = accountViewModel;
        
        // DOM elements
        this.accountListContainer = document.getElementById('account-list');
        this.emailInput = document.getElementById('email');
        this.passwordInput = document.getElementById('password');
        this.addAccountButton = document.querySelector('.add-account-button');
        this.accountModal = document.getElementById('account_modal');
        this.closeModalBtn = document.querySelector('.close-account_modal');
        this.openModalBtn = document.getElementById('account_button');
        
        // Initialize event listeners
        this._initEventListeners();
        
        // Subscribe to view model changes
        this.viewModel.addObserver(this._renderAccounts.bind(this));
    }

    /**
     * Initialize all UI event listeners
     * @private
     */
    _initEventListeners() {
        // Add account button
        if (this.addAccountButton) {
            this.addAccountButton.addEventListener('click', () => this._handleCreateAccount());
        }
        
        // Modal open button
        if (this.openModalBtn) {
            this.openModalBtn.addEventListener('click', () => this.openModal());
        }
        
        // Modal close button
        if (this.closeModalBtn) {
            this.closeModalBtn.addEventListener('click', () => this.closeModal());
        }
        
        // Modal outside click
        if (this.accountModal) {
            this.accountModal.addEventListener('click', (event) => this._handleOutsideClick(event));
        }
    }

    /**
     * Open account modal
     */
    openModal() {
        if (this.accountModal) {
            this.accountModal.style.display = 'flex';
        }
    }

    /**
     * Close account modal
     */
    closeModal() {
        if (this.accountModal) {
            this.accountModal.style.display = 'none';
        }
    }

    /**
     * Handle click outside modal
     * @param {Event} event - Click event
     * @private
     */
    _handleOutsideClick(event) {
        if (event.target === this.accountModal) {
            this.closeModal();
        }
    }

    /**
     * Handle create account button click
     * @private
     */
    _handleCreateAccount() {
        const email = this.emailInput?.value;
        const password = this.passwordInput?.value;
        
        if (!email || !password) {
            alert('이메일과 비밀번호를 입력해주세요.');
            return;
        }
        
        this.viewModel.createAccount(email, password)
            .then(data => {
                alert('계정이 추가되었습니다.');
                
                // Clear input fields
                if (this.emailInput) this.emailInput.value = '';
                if (this.passwordInput) this.passwordInput.value = '';
            })
            .catch(error => {
                alert('계정 추가 실패: ' + error);
                console.error('Error adding account:', error);
            });
    }

    /**
     * Render accounts in the UI (observer callback)
     * @param {Array} accounts - Array of account objects
     * @private
     */
    _renderAccounts(accounts) {
        if (!this.accountListContainer) return;
        
        this.accountListContainer.innerHTML = '';  // Clear existing list
        
        accounts.forEach(account => {
            const accountItemContainer = document.createElement('div');
            accountItemContainer.classList.add('account-item');
            
            // Email display
            const emailView = document.createElement('div');
            emailView.classList.add('account-item-email');
            emailView.innerText = account.email;
            
            // Password display
            const passwordView = document.createElement('div');
            passwordView.classList.add('account-item-password');
            passwordView.innerText = account.password;
            
            // Container for buttons
            const buttonsContainer = document.createElement('div');
            buttonsContainer.classList.add('account-item-buttons');
            
            // Edit button
            const editView = document.createElement('div');
            editView.classList.add('account-item-editbutton');
            editView.innerText = '수정';
            editView.addEventListener('click', () => this._handleUpdateAccount(account.email));
            
            // Delete button
            const deleteView = document.createElement('div');
            deleteView.classList.add('account-item-deletebutton');
            deleteView.innerText = '삭제';
            deleteView.addEventListener('click', () => this._handleDeleteAccount(account.email));
            
            // Add buttons to container
            buttonsContainer.appendChild(editView);
            buttonsContainer.appendChild(deleteView);
            
            // Add all elements to account item
            accountItemContainer.appendChild(emailView);
            accountItemContainer.appendChild(passwordView);
            accountItemContainer.appendChild(buttonsContainer);
            
            // Add account item to the list
            this.accountListContainer.appendChild(accountItemContainer);
        });
    }

    /**
     * Handle update account button click
     * @param {string} email - Email of account to update
     * @private
     */
    _handleUpdateAccount(email) {
        const newPassword = prompt('새 비밀번호를 입력해주세요.');
        if (!newPassword) return;
        
        this.viewModel.updateAccount(email, newPassword)
            .then(data => {
                alert('계정이 수정되었습니다.');
            })
            .catch(error => {
                alert('계정 수정 실패: ' + error);
                console.error('Error updating account:', error);
            });
    }

    /**
     * Handle delete account button click
     * @param {string} email - Email of account to delete
     * @private
     */
    _handleDeleteAccount(email) {
        if (!confirm('정말로 이 계정을 삭제하시겠습니까?')) return;
        
        this.viewModel.deleteAccount(email)
            .then(data => {
                alert('계정이 삭제되었습니다.');
            })
            .catch(error => {
                alert('계정 삭제 실패: ' + error);
                console.error('Error deleting account:', error);
            });
    }

    /**
     * Initialize the UI by loading accounts
     */
    initialize() {
        this.viewModel.loadAccounts()
            .catch(error => console.error('Error initializing account UI:', error));
    }
}

export default AccountUI;