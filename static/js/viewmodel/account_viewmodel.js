/**
 * Account ViewModel - Handles business logic for account management
 * Implements observable pattern to notify subscribers of data changes
 */
class AccountViewModel {
    constructor() {
        this.accounts = [];
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
     * Notify all observers with current accounts data
     */
    notifyObservers() {
        this.observers.forEach(observer => observer(this.accounts));
    }

    /**
     * Load accounts from server
     * @returns {Promise} - Promise that resolves when accounts are loaded
     */
    loadAccounts() {
        return fetch('/api/account/loadAccountList')
            .then(response => response.json())
            .then(data => {
                this.accounts = data;
                this.notifyObservers();
                return data;
            })
            .catch(error => {
                console.error('Error fetching account list:', error);
                throw error;
            });
    }

    /**
     * Create a new account
     * @param {string} email - Account email
     * @param {string} password - Account password
     * @returns {Promise} - Promise that resolves when account is created
     */
    createAccount(email, password) {
        if (!email || !password) {
            return Promise.reject('이메일과 비밀번호를 입력해주세요.');
        }

        return fetch('/api/account/createAccount', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return this.loadAccounts().then(() => data);
            } else {
                throw new Error(data.message || '계정 추가 실패');
            }
        });
    }

    /**
     * Update an existing account
     * @param {string} email - Email of account to update
     * @param {string} password - New password
     * @returns {Promise} - Promise that resolves when account is updated
     */
    updateAccount(email, password) {
        if (!email || !password) {
            return Promise.reject('이메일과 비밀번호를 입력해주세요.');
        }

        return fetch('/api/account/updateAccount', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return this.loadAccounts().then(() => data);
            } else {
                throw new Error(data.message || '계정 수정 실패');
            }
        });
    }

    /**
     * Delete an account
     * @param {string} email - Email of account to delete
     * @returns {Promise} - Promise that resolves when account is deleted
     */
    deleteAccount(email) {
        if (!email) {
            return Promise.reject('이메일을 입력해주세요.');
        }

        return fetch('/api/account/deleteAccount', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return this.loadAccounts().then(() => data);
            } else {
                throw new Error(data.message || '계정 삭제 실패');
            }
        });
    }

    /**
     * Get current accounts data
     * @returns {Array} - Array of account objects
     */
    getAccounts() {
        return this.accounts;
    }
}

export default AccountViewModel;
