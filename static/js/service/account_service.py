import utils.kmong_manager.db_account as db_account
from model.account_dto import AccountDTO

class AccountService:
    def __init__(self):
        self._ensure_account_table_exists()
    
    def _ensure_account_table_exists(self):
        """Ensure the account table exists in the database"""
        if not db_account.check_account_table_exists():
            db_account.create_account_table()
    
    def get_all_accounts(self):
        """Retrieve all accounts from the database"""
        return db_account.read_all_accounts()
    
    def get_account_by_email(self, email):
        """Retrieve a specific account by email"""
        return db_account.read_account_by_email(email)
    
    def create_account(self, email, password):
        """Create a new account with the given email and password"""
        if not email or not password:
            return False, "이메일과 비밀번호를 입력해주세요."
        
        # Create AccountDTO object
        account_dto = AccountDTO(email=email, password=password, login_cookie='', user_id=0)
        
        # Add account to DB
        db_account.create_account(account_dto)
        return True, "계정이 추가되었습니다."
    
    def update_account(self, email, password=None, login_cookie=None, user_id=None):
        """Update an existing account"""
        if not email:
            return False, "이메일을 입력해주세요."
        
        db_account.update_account(email, password, login_cookie, user_id)
        return True, "계정이 수정되었습니다."
    
    def delete_account(self, email):
        """Delete an account by email"""
        if not email:
            return False, "이메일을 입력해주세요."
        
        db_account.delete_account(email)
        return True, "계정이 삭제되었습니다."
