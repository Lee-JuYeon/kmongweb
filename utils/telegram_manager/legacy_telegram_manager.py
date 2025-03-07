import requests
import telebot
import os
import logging
import threading
import time
import traceback
from dotenv import load_dotenv
from datetime import datetime
from utils.kmong_checker import dbLib
from utils.kmong_checker import kmongLib
from utils.kmong_checker import db_message


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 환경 변수 로드
load_dotenv()
telebot_token = os.getenv('telebot_token')
telebot_chat_id = os.getenv('telebot_chat_id')

# 전역 봇 인스턴스
bot = None

# 봇 인스턴스 초기화 함수 (제어를 위해 별도 함수로 분리)
def initialize_bot():
    global bot
    if bot is None:
        try:
            bot = telebot.TeleBot(telebot_token)
            logger.info("텔레그램 봇 초기화 성공")
        except Exception as e:
            logger.error(f"텔레그램 봇 초기화 실패: {str(e)}")
            return None
    return bot

# 초기화
bot = initialize_bot()


kmongLibInstance = kmongLib.KmongMessage()


class LegacyTelegramManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{telebot_token}"
        self.last_update_id = 0  # 마지막으로 처리한 update_id
        self.polling_thread = None
        self.stop_polling = False
        self.polling_lock = threading.Lock()
        
        # 폴링 상태 표시용
        self.is_polling = False
        
        # 연결 상태 체크
        self.check_connection()
    
    def check_connection(self):
        """텔레그램 API 연결 상태 확인"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('ok'):
                bot_info = data.get('result', {})
                logger.info(f"텔레그램 봇 연결 성공: {bot_info.get('username', '알 수 없음')}")
                return True
            else:
                logger.error(f"텔레그램 봇 연결 실패: {data}")
                return False
        except Exception as e:
            logger.error(f"텔레그램 API 연결 체크 실패: {str(e)}")
            return False

    # 메세지 보내기
    def send_message(self, email, messageCount, message, parse_mode=None):
        """텔레그램으로 메시지 전송"""
        if not bot:
            logger.error("텔레그램 봇이 초기화되지 않았습니다.")
            return False
            
        message_text = (
            f"🔔 Kmong 새 메세지 알림 🔔\n\n"
            f"✉️ {email}\n"
            f"💬 ({messageCount}): {message}"
        )
        try:
            # 메시지 전송
            sent_message = bot.send_message(
                chat_id=telebot_chat_id,
                text=message_text,
                parse_mode=parse_mode
            )
            
            logger.info(f"메시지 전송 성공 (ID: {sent_message.message_id}): {message[:30]}...")
            return True
        except Exception as e:
            logger.error(f"메시지 전송 실패: {str(e)}")
            traceback.print_exc()
            return False

    # 텔레그램으로 새 매세지 알려주기   
    def sendNewMessageByTelegram(self):  
        """새 메시지 모두 텔레그램으로 전송"""
        try:
            logger.info("새 메시지 텔레그램 전송 시작")
            # 전송된 메시지 수 추적
            getMessageCount = 0

            # 1. 모든 테이브의 데이터를 가져오기 위해 user_id부터 접근                                                                                                                                                                                                                                                                                                                                                                                                                
            accountList = kmongLibInstance.readAccountList()
            sent_count = 0
            
            for account in accountList:
                try:
                    user_id = account.get("user_id", "")
                    getEmail = account.get("email", "")

                    # user_id가 없는 계정은 건너뜀
                    if not user_id:
                        continue  

                    # 2. user_id로 모든 테이블에 접근하여 seen이 0인 모델을 가져온다.
                    messages = db_message.read_all_messages(table_id=user_id)

                    getMessageCount = 0
                    for message in messages:
                        if(message.get("seen", 0) == 0):
                            getMessageCount += 1
                            getMessage = message.get("text", "")
                            # 3. 메세지 보내기
                            result = self.send_message(email=getEmail, messageCount=getMessageCount, message=getMessage)
                            if result:
                                sent_count += 1
                                # 메시지 전송 성공 시 seen 상태 업데이트
                                db_message.update_message(
                                    table_id=user_id,
                                    message_id=message.get("idx"),
                                    seen=1  # 읽음으로 표시
                                )
                except Exception as e:
                    logger.error(f"계정 {account.get('email', '알 수 없음')} 처리 중 오류: {str(e)}")
                    continue
            
            logger.info(f"총 {sent_count}개의 메시지 전송 완료")
            return True
        except Exception as e:
            logger.error(f"메시지 전송 중 오류 발생: {str(e)}")
            traceback.print_exc()
            return False

    # 텔래그램으로 답장하기
    def replyByTelegram(self):
        """텔레그램 답장 처리 및 DB 업데이트"""
        try:
            # 텔레그램에서 답장 확인
            with self.polling_lock:
                reply_info = self.listen_for_replies()
            
            if not reply_info:
                # 새 답장이 없으면 종료
                return False
            
            # 로그 출력
            logger.info("=" * 50)
            logger.info("텔레그램 답장이 감지되었습니다!")
            logger.info(f"메시지 ID: {reply_info['message_id']}")
            logger.info(f"보낸 사람: {reply_info['first_name']} {reply_info['last_name']} (@{reply_info['username']})")
            logger.info(f"내용: {reply_info['text']}")
            logger.info(f"원본 메시지 ID: {reply_info['reply_to_message_id']}")
            logger.info("=" * 50)
            
            # 원본 메시지 ID
            original_message_id = reply_info['reply_to_message_id']
            
            # 모든 채팅방 테이블 조회
            chatroom_tables = db_message.read_all_chatroom_tables()
            
            found = False
            
            # 각 채팅방에서 원본 메시지 찾기
            for table_name in chatroom_tables:
                # 테이블 ID 추출 (chatroom_123 => 123)
                if not table_name.startswith('chatroom_'):
                    continue
                    
                table_id = int(table_name.split('_')[1])
                
                # 테이블이 존재하는지 확인
                if not db_message.check_chatroom_table_exists(table_id):
                    continue
                
                # 해당 테이블의 모든 메시지 조회
                try:
                    messages = db_message.read_all_messages(table_id)
                    
                    # kmong_message_id가 원본 메시지 ID와 일치하는 메시지 찾기
                    for message in messages:
                        # 메시지 ID 매칭 (여러 가능한 필드 확인)
                        if (message.get('kmong_message_id') == original_message_id or 
                            message.get('idx') == original_message_id):
                            
                            # 메시지 찾음 - DB 업데이트
                            db_message.update_message(
                                table_id=table_id,
                                message_id=message.get('idx'),
                                seen=1,                   # 읽음 표시
                                replied_telegram=1        # 텔레그램 답장 표시
                            )
                            
                            logger.info(f"메시지 상태 업데이트 완료: 테이블 ID {table_id}, 메시지 ID {message.get('idx')}")
                            found = True
                            break
                    
                    if found:
                        break
                        
                except Exception as e:
                    logger.error(f"테이블 {table_name} 처리 중 오류: {str(e)}")
                    continue
            
            if found:
                logger.info(f"텔레그램 답장 처리 완료: {reply_info['text']}")
                return True
            else:
                logger.warning(f"원본 메시지를 찾을 수 없습니다. 메시지 ID: {original_message_id}")
                return False
                
        except Exception as e:
            logger.error(f"텔레그램 답장 처리 중 오류 발생: {str(e)}")
            traceback.print_exc()
            return False
        
    def prepareObserving(self):
        """텔레그램 답장 모니터링 시작"""
        try:
            # 답장 처리 폴링 시작
            def on_reply_received(reply_info):
                try:
                    self.replyByTelegram()
                except Exception as e:
                    logger.error(f"답장 처리 콜백 오류: {str(e)}")
                    traceback.print_exc()
            
            # 답장 폴링 시작 (10초 간격으로 변경 - 더 넓은 간격으로 설정해 충돌 가능성 감소)
            self.start_reply_polling(interval=10, callback=on_reply_received)
            logger.info("텔레그램 답장 모니터링 시작")
            return True
        except Exception as e:
            logger.error(f"텔레그램 모니터링 설정 중 오류: {str(e)}")
            traceback.print_exc()
            return False

    def get_updates(self):
        """
        텔레그램 봇 API를 사용하여 업데이트를 가져옵니다.
        
        Returns:
            list: 업데이트 목록
        """
        try:
            # getUpdates API 호출 (timeout 추가)
            url = f"{self.base_url}/getUpdates?offset={self.last_update_id + 1}&timeout=5"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if not data.get('ok'):
                error_code = data.get('error_code')
                description = data.get('description', '')
                
                if error_code == 409:
                    logger.warning(f"Conflict 에러 발생: {description} - 30초 후 재시도합니다.")
                    # 충돌 감지 시 30초 대기 후 재시도
                    time.sleep(30)
                    return []
                
                logger.error(f"API 호출 실패: {data}")
                return []
            
            return data.get('result', [])
        except requests.exceptions.Timeout:
            logger.warning("API 요청 타임아웃, 잠시 후 재시도합니다.")
            return []
        except requests.exceptions.ConnectionError:
            logger.error("네트워크 연결 오류, 30초 후 재시도합니다.")
            time.sleep(30)
            return []
        except Exception as e:
            logger.error(f"업데이트 가져오기 실패: {str(e)}")
            traceback.print_exc()
            return []
    
    def listen_for_replies(self):
        """
        텔레그램 봇에 대한 답장을 확인합니다.
        
        Returns:
            dict or None: 답장 메시지 정보 (없으면 None)
        """
        if self.is_polling:
            logger.debug("이미 폴링 중입니다. 건너뜁니다.")
            return None
           
        try:
            self.is_polling = True
            
            # 업데이트 가져오기
            updates = self.get_updates()
            
            if not updates:
                self.is_polling = False
                return None
            
            # 마지막 업데이트 처리
            latest_update = updates[-1]
            self.last_update_id = latest_update.get('update_id', self.last_update_id)
            
            # 메시지가 없으면 처리 중단
            if 'message' not in latest_update:
                self.is_polling = False
                return None
            
            message = latest_update['message']
            
            # 답장이 아니면 None 반환
            if 'reply_to_message' not in message:
                self.is_polling = False
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
            
            self.is_polling = False
            return reply_info
        except Exception as e:
            logger.error(f"답장 확인 중 오류 발생: {str(e)}")
            traceback.print_exc()
            self.is_polling = False
            return None

    def start_reply_polling(self, interval=10, callback=None):
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
                    with self.polling_lock:
                        reply_info = self.listen_for_replies()
                    
                    if reply_info and callback:
                        # 콜백 함수 호출
                        callback(reply_info)
                    
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"폴링 중 오류 발생: {str(e)}")
                    traceback.print_exc()
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
        if not bot:
            logger.error("봇이 초기화되지 않았습니다.")
            return False

        try:
            logger.info("텔레그램 봇 폴링 시작...")
            bot.polling(none_stop=True)
            return True
        except Exception as e:
            logger.error(f"봇 폴링 오류: {str(e)}")
            traceback.print_exc()
            return False
    
    def start_bot_polling_async(self):
        """
        텔레그램 봇의 기본 폴링을 비동기적으로 시작합니다.
        """
        if not bot:
            logger.error("봇이 초기화되지 않았습니다.")
            return False
        
        def polling_worker():
            try:
                logger.info("텔레그램 봇 폴링 시작 (비동기)...")
                bot.polling(none_stop=True)
            except Exception as e:
                logger.error(f"봇 폴링 오류: {str(e)}")
                traceback.print_exc()
        
        thread = threading.Thread(target=polling_worker)
        thread.daemon = True
        thread.start()
        return True



#############################################   
    # 추출한 대화방 아이디, tele_chat_is_send를 데이터베이스에 업데이트합니다.
    def update_chat_id_in_db(self, user_id, tele_chat_room_id, tele_chat_is_send):
        """
        추출한 대화방 아이디, tele_chat_is_send를 데이터베이스에 업데이트합니다.
        """
        try:
            # 데이터베이스에 chat_id 저장 또는 업데이트
            dbLib.update_tele_chat_room_id(user_id, tele_chat_room_id, tele_chat_is_send)
            logger.info(f"대화방 아이디 업데이트 완료: {tele_chat_room_id}")
            return True
        except Exception as e:
            logger.error(f"대화방 아이디 업데이트 실패: {str(e)}")
            traceback.print_exc()
            return False


    # 텔레봇으로 메세지 내역 받아와 최근 대화방 아이디값과 tele_chat_is_send(텔레그램에 매세지 보냈는지?) 갱신하기
    def sendUnReadMessagesViaTelebot(self):
        """
        텔레그램 봇api를 사용하여 메시지 내역을 가져온다
        가져온 메세지 내역에서 최근 대화방 아이디를 추출한다.
        추출한 대화방 아이디를 데이터베이스에 저장한다
        """
        try:
            if not bot:
                logger.error("텔레그램 봇이 초기화되지 않았습니다.")
                return False
                
            unReadMessageListFromDB = self.getUnreadMessageListFromDB()        

            sent_count = 0
            # 📌 새로운 메시지가 있으면 텔레그램으로 전송
            if unReadMessageListFromDB:
                for unReadMessage in unReadMessageListFromDB:
                    message_text = (
                        "🔔 Kmong 새 메시지 알림 🔔\n"
                        f"✉️ {unReadMessage['userid']}\n"
                        f"💬 ({unReadMessage['message_count']}): {unReadMessage['message_content']}\n"
                    )

                    try:
                        # 텔레그램 메시지 전송
                        result = bot.send_message(telebot_chat_id, message_text)
                        
                        if result:
                            sent_count += 1
                            # 메시지 전송 후 DB 업데이트 (chatroom_id, tele_chat_is_send) 1 == 보냄, 0 == 안보냄
                            self.update_chat_id_in_db(unReadMessage['userid'], telebot_chat_id, 1)
                    except Exception as e:
                        logger.error(f"메시지 전송 실패: {str(e)}")
                
                logger.info(f"{sent_count}개의 메시지가 텔레그램으로 전송되었습니다.")
                return True
            else:
                logger.info("전송할 새 메시지가 없습니다.")
                return False
        except Exception as e:
            logger.error(f"메시지 전송 중 오류 발생: {str(e)}")
            traceback.print_exc()
            return False
           
    def sendDummyMessage(self):
        """
        테스트용 더미 메시지 전송
        """
        if not bot:
            logger.error("텔레그램 봇이 초기화되지 않았습니다.")
            return False
            
        try:
            message_text = (
                "🔔 Kmong 새 메시지 알림 🔔\n"
                f"✉️ test@test.com\n"
                f"💬 (99): 테스트용 메세지입니다. 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} \n"
            )

            # 텔레그램 메시지 전송 및 결과 확인
            sent_message = bot.send_message(telebot_chat_id, message_text)
            logger.info(f"테스트 메시지 전송 성공: {sent_message.message_id}")
            return True
        except Exception as e:
            logger.error(f"테스트 메시지 전송 실패: {str(e)}")
            traceback.print_exc()
            return False
 

    def replyViaTeleBot(self):
        """
        텔레그램 답장 기능 호출 (기존 메소드와 호환성 유지)
        """
        try:
            data = self.get_recent_message_info()

            logger.info(f"텔레봇 최근메세지: {data}")
            
            # 가장최근 답변가져오기
            if data:
                # 해당 텔레그램 안전하게 값 가져오기
                message_id = data["message_id"]
                chat_id = data["chat_id"]
                user_id = data["user_id"]
                first_name = data["first_name"]
                last_name = data["last_name"]
                username = data["username"]
                date = data["date"]
                text = data["text"]
                replied = data["replied"]
                reply_to_message_id = data["reply_to_message_id"]

                # 해당 텔레그램 메세지 DB에 저장
                allMessages = dbLib.get_all_messages()

                # reply_t0_message_id가 존재해야 db에 저장됨. 즉, 텔레그램에서 답장기능을 이용하여 답장을 한 것만 db에 저장된다는 의미.
                # 문제점 1) 그러면 상대방이 보낸메세지는 reply_to_message_id가 존재하지 않는데 어떻게 할꺼임?
                #   -> 그러면 if reply_to_messsage_id or user_id != myUserId 로하여, 보낸사람이 내가 아닐경우에도 true로 작동하게 하면됨.
                if reply_to_message_id or str(user_id) != str(telebot_chat_id):
                    # message_id가 기존 데이터에 없으면 삽입
                    if not any(str(dict(message).get("message_id", "")) == str(message_id) for message in allMessages):
                        dbLib.insert_message(message_id, chat_id, user_id, first_name, last_name, username, text, date, replied)
                        logger.info(f"새 텔레그램 메시지가 DB에 저장되었습니다. ID: {message_id}")
                        return True
                    else:
                        logger.info(f"[알림] message_id {message_id}는 이미 존재합니다.")
                        return False
                else:
                    logger.info("메시지가 답장이 아니거나 자신이 보낸 메시지입니다.")
                    return False
            else:
                logger.debug("-------- [알림] 새로운 메시지가 없음.--------")
                return False
        except Exception as e:
            logger.error(f"텔레그램 답장 처리 중 오류: {str(e)}")
            traceback.print_exc()
            return False


    def replyViaWeb(self, replyText):
        """
        웹 인터페이스에서 답장 전송
        """
        if not bot:
            logger.error("텔레그램 봇이 초기화되지 않았습니다.")
            return False
            
        try:
            # 텔레그램으로 메시지 전송
            sent_message = bot.send_message(telebot_chat_id, replyText)
            
            # DB에 메시지 저장
            message_id = sent_message.message_id
            chat_id = telebot_chat_id
            user_id = telebot_chat_id
            first_name = "Web"
            last_name = "User"
            username = "web_user"
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            text = replyText
            replied = 1
            
            # 모든 메시지 가져오기
            allMessages = dbLib.get_all_messages()
            
            # 중복 방지 확인
            if not any(str(dict(message).get("message_id", "")) == str(message_id) for message in allMessages):
                dbLib.insert_message(message_id, chat_id, user_id, first_name, last_name, username, text, date, replied)
                logger.info(f"웹 답장이 DB에 저장되었습니다. ID: {message_id}")
                return True
            else:
                logger.info(f"[알림] message_id {message_id}는 이미 존재합니다.")
                return False
        except Exception as e:
            logger.error(f"웹 답장 전송 실패: {str(e)}")
            traceback.print_exc()
            return False

    def get_recent_message_info(self):
        """
        텔레그램 봇 API를 사용하여 최근 메시지 내역을 가져오고,
        대화방 아이디, 메시지 내용, 보낸 사람 정보, 메시지 시간 등을 추출합니다.
        """
        try:
            # getUpdates API 호출 (offset을 사용하여 중복 메시지 방지)
            url = f"{self.base_url}/getUpdates?offset={self.last_update_id + 1}"

            response = requests.get(url, timeout=10)
            data = response.json()

            # 응답 확인
            if not data.get("ok"):
                print(f"TelegramBot, get_recdent_message_info // Exceptino : API 호출 실패: {data}")
                return None


            # 응답 내용 출력 (디버깅용)
            print(f"TelegramBot, get_recdent_message_info // API 응답 데이터 : {data}")


            # 최신 메시지에서 chat.id 추출
            updates = data.get("result", [])
            if not updates:
                return None


            latest_message = updates[-1]  # 가장 최신 메시지
            message = latest_message.get("message", {})


           
            chatroom_id = message.get("chat", {}).get("id")
            if not chatroom_id:
                print("chat_id를 찾을 수 없습니다.")
                return None


            from_user = message.get("from", {})
            user_id = from_user.get("id")
            first_name = from_user.get("first_name")
            last_name = from_user.get("last_name", "")
            username = from_user.get("username", "")
            text = message.get("text")
            date = message.get("date")
            reply_to_message_id = message.get("reply_to_message", {}).get("message_id", None)


            # replied 여부는 reply_to_message_id로 확인 가능
            replied = True if reply_to_message_id else False


            self.last_update_id = latest_message.get("update_id")  # 마지막 update_id 갱신


            return {
                "message_id": message.get("message_id"),
                "chat_id": chatroom_id,
                "user_id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "text": text,
                "date": date,
                "replied": replied,
                "reply_to_message_id" : reply_to_message_id
            }


        except Exception as e:
            print(f"메시지 내역 가져오기 실패: {str(e)}")
            return None