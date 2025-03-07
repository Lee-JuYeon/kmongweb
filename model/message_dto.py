from datetime import date

class MessageDTO:
    def __init__(self, 
                admin_id: int = 0, 
                text: str = "", 
                client_id: int = 0, 
                sender_id: int = 0, 
                replied_kmong: int = 0,  # 0: False, 1: True
                replied_telegram: int = 0, 
                seen: int = 0,  # 0: Unseen, 1: Seen
                kmong_message_id: int = 0, 
                date: date = date.today()):
        self.admin_id = admin_id
        self.text = text
        self.client_id = client_id
        self.sender_id = sender_id
        self.replied_kmong = replied_kmong
        self.replied_telegram = replied_telegram
        self.seen = seen
        self.kmong_message_id = kmong_message_id
        self.date = date

    def __repr__(self):
        return f"""MessageDTO(
            admin_id={self.admin_id},
            text={self.text},
            client_id={self.client_id},
            sender_id={self.sender_id},
            replied_kmong={self.replied_kmong},
            replied_telegram={self.replied_telegram},
            seen={self.seen},
            kmong_message_id={self.kmong_message_id},
            date={self.date}
        )"""