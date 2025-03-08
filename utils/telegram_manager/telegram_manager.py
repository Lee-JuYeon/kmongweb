import os
import telebot
import logging
import threading
import time
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):

         # 설정 파일에서 토큰과 채팅 ID 로드
        self.settings_file = 'settings.json'
        self.settings = self._load_settings()

         # 봇 토큰과 채팅 ID 설정
        self.token = self.settings.get('telegram', {}).get('botToken', '')
        self.chat_id = self.settings.get('telegram', {}).get('chatId', '')

            # 봇 인스턴스와 기타 변수 초기화
        self.bot = None
        self.base_url = None
        self.last_update_id = 0
        self.polling_thread = None
        self.stop_polling = False
        
        # 토큰이 설정되어 있으면 봇 초기화
        if self.token:
            self.initialize()
        
    # 설정 파일에서 설정 로드  
    def _load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {'telegram': {'botToken': '', 'chatId': ''}}
        except Exception as e:
            logger.error(f"설정 로드 중 오류: {str(e)}")
            return {'telegram': {'botToken': '', 'chatId': ''}}
    
    # 봇 명령어 핸들러를 등록합니다.
    def register_handlers(self):
        @self.bot.message_handler(commands=['start', 'help'])
        def handle_start_help(message):
            self.bot.reply_to(message, 
                "안녕하세요! 이 봇은 메시지를 주고받기 위한 봇입니다.\n"
                "/help - 도움말 보기\n"
                "/id - 현재 채팅 ID 확인하기")
        
        @self.bot.message_handler(commands=['id'])
        def handle_id_command(message):
            self.bot.reply_to(message, f"현재 채팅 ID: {message.chat.id}")
            logger.info(f"ID 요청: 채팅 ID {message.chat.id}")
        
        @self.bot.message_handler(func=lambda message: True)
        def echo_all(message):
            # 모든 메시지 로깅
            logger.info(f"메시지 수신 - 채팅 ID: {message.chat.id}, 내용: {message.text[:30]}...")
    
    # 메세지 보내기
    def send_message(self, email, messageCount, message, parse_mode=None):
        """
        텔레그램 봇을 통해 메시지를 보냅니다.
        
        Args:
            text (str): 보낼 메시지 내용
            parse_mode (str, optional): 텍스트 파싱 모드 ('HTML', 'Markdown' 등)
        
        Returns:
            bool: 메시지 전송 성공 여부
        """
        # 봇이나 채팅 ID가 없으면 초기화 시도
        if not self.bot:
            logger.warning("봇이 초기화되지 않았습니다. 초기화를 시도합니다.")
            if not self.initialize():
                logger.error("봇 초기화 실패로 메시지를 보낼 수 없습니다.")
                return False
        
        if not self.chat_id:
            logger.error("채팅 ID가 설정되지 않아 메시지를 보낼 수 없습니다.")
            return False
        
        message_text = (
            f"🔔 Kmong 새 메세지 알림 🔔\n\n"
            f"✉️ {email}\n"
            f"💬 ({messageCount}): {message}"
        )
        try:
            # 메시지 전송
            sent_message = self.bot.send_message(
                chat_id=self.chat_id,
                text=message_text,
                parse_mode=parse_mode
            )
            
            logger.info(f"메시지 전송 성공 (ID: {sent_message.message_id}): {message[:30]}...")
            return True
        except Exception as e:
            logger.error(f"메시지 전송 실패: {str(e)}")
            return False

  
    def get_updates(self):
        """
        텔레그램 봇 API를 사용하여 업데이트를 가져옵니다.
        
        Returns:
            list: 업데이트 목록
        """
        try:
            # getUpdates API 호출
            url = f"{self.base_url}/getUpdates?offset={self.last_update_id + 1}"
            response = requests.get(url)
            data = response.json()
            
            if not data.get('ok'):
                logger.error(f"API 호출 실패: {data}")
                return []
            
            return data.get('result', [])
        except Exception as e:
            logger.error(f"업데이트 가져오기 실패: {str(e)}")
            return []
    
    def listen_for_replies(self):
        """
        텔레그램 봇에 대한 답장을 확인합니다.
        
        Returns:
            dict or None: 답장 메시지 정보 (없으면 None)
        """
        # 봇이 초기화되지 않았으면 초기화
        if not self.bot:
            logger.warning("봇이 초기화되지 않았습니다. 초기화를 시도합니다.")
            if not self.initialize():
                logger.error("봇 초기화 실패로 답장을 확인할 수 없습니다.")
                return None
        
        try:
            # 업데이트 가져오기
            updates = self.get_updates()
            
            if not updates:
                return None
            
            # 마지막 업데이트 처리
            latest_update = updates[-1]
            self.last_update_id = latest_update.get('update_id', self.last_update_id)
            
            # 메시지가 없으면 처리 중단
            if 'message' not in latest_update:
                return None
            
            message = latest_update['message']
            
            # 답장이 아니면 None 반환
            if 'reply_to_message' not in message:
                return None
            
            # 사용자 정보 추출
            from_user = message.get('from', {})
            
            # 답장 정보 추출
            reply_info = {
                'message_id': message.get('message_id'),
                'chat_id': message.get('chat', {}).get('id'),
                'user_id': from_user.get('id'),
                'username': from_user.get('username', ""),
                'first_name': from_user.get('first_name', ""),
                'last_name': from_user.get('last_name', ""),
                'text': message.get('text', ""),
                'date': message.get('date'),
                'reply_to_message_id': message.get('reply_to_message', {}).get('message_id')
            }
            
            # 로그 출력
            logger.info(f"답장 수신: {reply_info['text'][:30]}... (ID: {reply_info['message_id']})")
            logger.debug(f"답장 정보: {reply_info}")
            
            return reply_info
        except Exception as e:
            logger.error(f"답장 확인 중 오류 발생: {str(e)}")
            return None

    def start_reply_polling(self, interval=5, callback=None):
        """
        주기적으로 답장을 확인하는 폴링을 시작합니다.
        
        Args:
            interval (int): 폴링 간격 (초)
            callback (callable, optional): 답장 수신 시 호출할 콜백 함수
        """
        # 이미 폴링 중이면 중단
        if self.polling_thread and self.polling_thread.is_alive():
            logger.warning("이미 폴링이 실행 중입니다.")
            return
        
        # 폴링 상태 초기화
        self.stop_polling = False
        
        def polling_worker():
            logger.info(f"답장 폴링 시작 (간격: {interval}초)")
            
            while not self.stop_polling:
                try:
                    reply_info = self.listen_for_replies()
                    
                    if reply_info and callback:
                        # 콜백 함수 호출
                        callback(reply_info)
                    
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"폴링 중 오류 발생: {str(e)}")
                    time.sleep(interval)  # 오류 발생 시에도 대기
        
        # 새 스레드로 폴링 시작
        self.polling_thread = threading.Thread(target=polling_worker)
        self.polling_thread.daemon = True
        self.polling_thread.start()
    
    def stop_reply_polling(self):
        """답장 폴링을 중지합니다."""
        if self.polling_thread and self.polling_thread.is_alive():
            self.stop_polling = True
            self.polling_thread.join(timeout=1.0)
            logger.info("답장 폴링이 중지되었습니다.")
        else:
            logger.warning("실행 중인 폴링이 없습니다.")
    
    def start_bot_polling(self):
        """
        텔레그램 봇의 기본 폴링을 시작합니다.
        주의: 이 메소드는 메인 스레드를 차단합니다.
        """
        if not self.bot:
            logger.error("봇이 초기화되지 않았습니다.")
            return False
        
        try:
            logger.info("텔레그램 봇 폴링 시작...")
            self.bot.polling(none_stop=True)
            return True
        except Exception as e:
            logger.error(f"봇 폴링 오류: {str(e)}")
            return False
    
    def start_bot_polling_async(self):
        """
        텔레그램 봇의 기본 폴링을 비동기적으로 시작합니다.
        """
        if not self.bot:
            logger.error("봇이 초기화되지 않았습니다.")
            return False
        
        def polling_worker():
            try:
                logger.info("텔레그램 봇 폴링 시작 (비동기)...")
                self.bot.polling(none_stop=True)
            except Exception as e:
                logger.error(f"봇 폴링 오류: {str(e)}")
        
        thread = threading.Thread(target=polling_worker)
        thread.daemon = True
        thread.start()
        return True


# 사용 예시
def handle_reply(reply_info):
    """답장 수신 시 처리할 콜백 함수"""
    print(f"새 답장 받음: {reply_info['text']}")
    print(f"보낸 사람: {reply_info['first_name']} {reply_info['last_name']} (@{reply_info['username']})")
    print(f"답장 ID: {reply_info['message_id']}, 원본 ID: {reply_info['reply_to_message_id']}")
    print("-" * 50)


if __name__ == "__main__":
    # 텔레그램 봇 인스턴스 생성
    telegram_bot = TelegramManager.get_instance()
    

    # 답장 폴링 시작 (콜백 함수 등록)
    telegram_bot.start_reply_polling(interval=3, callback=handle_reply)
    
    try:
        # 프로그램이 종료되지 않도록 유지
        print("텔레그램 봇이 실행 중입니다. Ctrl+C를 눌러 종료하세요.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 종료 시 폴링 중지
        telegram_bot.stop_reply_polling()
        print("프로그램이 종료되었습니다.")