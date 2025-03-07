class AccountDTO:
    def __init__(self, email: str, password: str, login_cookie: str, user_id: int):
        self.email = email
        self.password = password
        self.login_cookie = login_cookie
        self.user_id = user_id

    def __repr__(self):
        return f"""AccountDTO(
            user_id={self.user_id},
            email={self.email},
            password={self.password},
            login_cookie={self.login_cookie}
        )"""