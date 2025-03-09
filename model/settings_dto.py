from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class SettingsDTO:
    """Data Transfer Object for application settings"""
    
    # Refresh intervals in seconds
    parse_messages_interval: int = 30
    send_messages_interval: int = 30
    reply_messages_interval: int = 10
    
    # Telegram settings
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # Chatroom checkbox settings
    checked_chatrooms: List[int] = None
    
    def __post_init__(self):
        # Initialize empty list if None
        if self.checked_chatrooms is None:
            self.checked_chatrooms = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary format"""
        return {
            'refreshInterval': {
                'parseUnReadMessagesinDB': self.parse_messages_interval,
                'sendUnReadMessagesViaTelebot': self.send_messages_interval,
                'replyViaTeleBot': self.reply_messages_interval
            },
            'telegram': {
                'botToken': self.telegram_bot_token,
                'chatId': self.telegram_chat_id
            },
            'chatrooms': {
                'checked': self.checked_chatrooms
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SettingsDTO':
        """Create DTO from dictionary format"""
        refresh_interval = data.get('refreshInterval', {})
        telegram = data.get('telegram', {})
        chatrooms = data.get('chatrooms', {})
        
        return cls(
            parse_messages_interval=refresh_interval.get('parseUnReadMessagesinDB', 30),
            send_messages_interval=refresh_interval.get('sendUnReadMessagesViaTelebot', 30),
            reply_messages_interval=refresh_interval.get('replyViaTeleBot', 10),
            telegram_bot_token=telegram.get('botToken', ''),
            telegram_chat_id=telegram.get('chatId', ''),
            checked_chatrooms=chatrooms.get('checked', [])
        )