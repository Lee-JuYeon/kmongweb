from flask import Flask, render_template, request, jsonify, redirect
import time
import sys
import schedule
import random
import logging

import utils.kmong_checker.dbLib as dbLib
import utils.kmong_checker.kmongLib as kmongLib
import utils.kmong_checker.db_account as db_account
import utils.kmong_checker.db_message as db_message
from static.js.service.settings_service import SettingsService


import threading
from routes.account_routes import account_bp
from routes.message_routes import message_bp
from routes.settings_routes import settings_bp

from utils.telegram_manager.legacy_telegram_manager import LegacyTelegramManager
from dummy.dummySingleton import DummySingleton

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Blueprint 등록
app.register_blueprint(account_bp)
app.register_blueprint(message_bp)
app.register_blueprint(settings_bp)

kmongLibInstance = kmongLib.KmongMessage()
settings_service = SettingsService()

# 텔레그램 매니저 인스턴스 (전역 변수)
telegram = None

def init_telegram():
    """텔레그램 관리자 초기화"""
    from utils.telegram_manager.legacy_telegram_manager import LegacyTelegramManager
    
    # 싱글톤 인스턴스 가져오기
    global telegram
    telegram = LegacyTelegramManager.get_instance()
    
    # 텔레그램 봇 시작 전 잠시 대기 (이전 인스턴스가 종료될 시간 확보)
    import time
    time.sleep(1)
    
    # 연결 상태 확인
    if not telegram.check_connection():
        logger.error("텔레그램 봇 연결에 실패했습니다. 설정을 확인하세요.")
        return None
    
    # 모니터링 준비
    if not telegram.prepareObserving():
        logger.error("텔레그램 모니터링 설정에 실패했습니다.")
    
    # 테스트 메시지 전송 (봇 작동 확인)
    if telegram.sendDummyMessage():
        logger.info("텔레그램 봇이 성공적으로 초기화되었습니다.")
    else:
        logger.error("텔레그램 테스트 메시지 전송에 실패했습니다.")
    
    return telegram


# 크몽에서 새로운 메세지 받아오기
dummy = DummySingleton()
def getMessageListFromKmongWeb():
    """크몽 웹에서 새 메시지 가져오기"""
    try:
        userid = dummy.get_admin_info()['email']
        passwd = dummy.get_admin_info()['password']
        login_cookie = dummy.get_admin_info()['login_cookie']

        ret = kmongLibInstance.check_unread_message(userid, passwd, login_cookie)
        if not ret:
            logger.info("쿠키로 로그인 실패, 새로 로그인 시도")
            ret, login_cookie = kmongLibInstance.login(userid, passwd)
            if ret:
                kmongLibInstance.check_unread_message(userid, passwd, login_cookie)
            else:
                logger.error("크몽 로그인 실패")
        
        return ret
    except Exception as e:
        logger.error(f"크몽 메시지 확인 중 오류: {str(e)}")
        return False


def refresh_scheduler():
    """현재 설정에 따라 스케줄러 재설정"""
    global telegram
    
    # 텔레그램 인스턴스 확인
    if telegram is None:
        logger.error("텔레그램 봇이 초기화되지 않았습니다.")
        return False
    
    # 기존 스케줄 제거
    schedule.clear()

    # 현재 설정 가져오기
    settings = settings_service.get_settings()
    refresh_interval = settings.get('refreshInterval', {})
    
    # 각 작업에 대한 간격 설정 (값 범위를 제한하여 오버플로우 방지)
    parse_interval = min(max(refresh_interval.get('parseUnReadMessagesinDB', 30), 10), 3600)
    send_interval = min(max(refresh_interval.get('sendUnReadMessagesViaTelebot', 10), 5), 3600)
    reply_interval = min(max(refresh_interval.get('replyViaTeleBot', 10), 5), 3600)

    logger.info(f"스케줄러 간격 설정 - 파싱: {parse_interval}초, 전송: {send_interval}초, 답장: {reply_interval}초")
    
    # 텔레그램으로 안읽은 새 매세지 보내주기
    schedule.every(send_interval).seconds.do(telegram.sendNewMessageByTelegram)
    
    # 텔레그램 답장 확인하기
    schedule.every(reply_interval).seconds.do(telegram.replyByTelegram)
        
    # 크몽웹에서 계정과 메세지 받아오기
    schedule.every(parse_interval).seconds.do(getMessageListFromKmongWeb)
    
    logger.info("스케줄러가 갱신되었습니다.")
    return True  

# 메시지 체크 스레드
def background_task():
    """백그라운드 작업 스레드"""
    logger.info("백그라운드 태스크 시작")
    
    def run_scheduler():
        """스케줄러 실행 루프"""
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                logger.error(f"스케줄러 실행 중 오류 발생: {str(e)}")
            
            # 짧은 간격으로 sleep
            time.sleep(1.0)
    
    # 초기 스케줄 설정
    refresh_scheduler()
    
    # 스케줄러 실행
    run_scheduler()

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

def init():
    """애플리케이션 초기화"""
    try:
        # 데이터베이스 초기화
        dbLib.create_db()
        db_message.add_missing_columns_to_all_chatrooms()
        
        # 텔레그램 초기화
        init_telegram()
        
        # 기존DB 마이그레이션
        kmongLibInstance.migrationDB()
        
        logger.info("애플리케이션 초기화 완료")
        return True
    except Exception as e:
        logger.error(f"초기화 중 오류 발생: {str(e)}")
        return False
    
if __name__ == '__main__':
    # 애플리케이션 초기화
    if not init():
        logger.error("초기화에 실패했습니다. 애플리케이션을 종료합니다.")
        sys.exit(1)
    
    # 메시지 체크 스레드를 별도의 백그라운드 스레드로 실행
    threading.Thread(target=background_task, daemon=True).start()
    
    # 스레드 시작 후 잠시 대기 (초기화 시간 확보)
    time.sleep(2)
    
    logger.info("Flask 애플리케이션 시작")
    
    # Flask 애플리케이션 실행
    app.run(host='0.0.0.0', port=7100, debug=True)
    
# from flask import Flask, render_template, request, jsonify, redirect
# import time
# import sys
# import schedule
# import random

# import utils.kmong_checker.dbLib as dbLib
# import utils.kmong_checker.kmongLib as kmongLib
# import utils.kmong_checker.db_account as db_account
# import utils.kmong_checker.db_message as db_message
# from static.js.service.settings_service import SettingsService


# import threading
# from routes.account_routes import account_bp
# from routes.message_routes import message_bp
# from routes.settings_routes import settings_bp

# from utils.telegram_manager.legacy_telegram_manager import LegacyTelegramManager
# from dummy.dummySingleton import DummySingleton

# app = Flask(__name__, static_folder='static')

# # Blueprint 등록
# app.register_blueprint(account_bp)
# app.register_blueprint(message_bp)
# app.register_blueprint(settings_bp)

# kmongLibInstance = kmongLib.KmongMessage()
# settings_service = SettingsService()

# # def init_telegram():
# #     global telegram
# #     telegram = LegacyTelegramManager()
# #     telegram.prepareObserving()
# #     telegram.sendDummyMessage()
# def init_telegram():
#     """텔레그램 관리자 초기화"""
#     from utils.telegram_manager.legacy_telegram_manager import LegacyTelegramManager
    
#     # 싱글톤 인스턴스 가져오기
#     global telegram
#     telegram = LegacyTelegramManager.get_instance()
    
#     # 텔레그램 봇 시작 전 잠시 대기 (이전 인스턴스가 종료될 시간 확보)
#     import time
#     time.sleep(1)
    
#     # 연결 상태 확인
#     if not telegram.check_connection():
#         print("텔레그램 봇 연결에 실패했습니다. 설정을 확인하세요.")
#         return None
    
#     # 모니터링 준비
#     if not telegram.prepareObserving():
#         print("텔레그램 모니터링 설정에 실패했습니다.")
    
#     # 테스트 메시지 전송 (봇 작동 확인)
#     if telegram.sendDummyMessage():
#         print("텔레그램 봇이 성공적으로 초기화되었습니다.")
#     else:
#         print("텔레그램 테스트 메시지 전송에 실패했습니다.")
    
#     return telegram


# # 크몽에서 새로운 메세지 받아오기
# dummy = DummySingleton()
# def getMessageListFromKmongWeb():

#     # messageList = kmongLibInstance.getMessagesFromDB()

#     # for messageItem in messageList:
#     #     userid = messageItem.get("userid", "")
#     #     passwd = messageItem.get("passwd", "")
#     #     login_cookie = messageItem.get("login_cookie", "")
        
#     #     ret = kmongLibInstance.legacy_check_unread_message(userid, passwd, login_cookie)
            
#     #     if not ret:
#     #         ret, login_cookie = kmongLibInstance.legacy_login(userid, passwd)
#     #         kmongLibInstance.legacy_check_unread_message(userid, passwd, login_cookie)
#     userid = dummy.get_admin_info()['email']
#     passwd = dummy.get_admin_info()['password']
#     login_cookie = dummy.get_admin_info()['login_cookie']

#     ret = kmongLibInstance.check_unread_message(userid, passwd, login_cookie)
#     if not ret:
#         ret, login_cookie = kmongLibInstance.login(userid,passwd)
#         kmongLibInstance.check_unread_message(userid, passwd,login_cookie)


# def refresh_scheduler():
#     """현재 설정에 따라 스케줄러 재설정"""
#     global schedule_with_random_interval

#     # 기존 스케줄 제거
#     schedule.clear()

#     # 현재 설정 가져오기
#     settings = settings_service.get_settings()
#     refresh_interval = settings.get('refreshInterval', {})
    
#     # 각 작업에 대한 간격 설정 (값 범위를 제한하여 오버플로우 방지)
#     parse_interval = min(max(refresh_interval.get('parseUnReadMessagesinDB', 30), 10), 3600)
#     send_interval = min(max(refresh_interval.get('sendUnReadMessagesViaTelebot', 10), 5), 3600)
#     reply_interval = min(max(refresh_interval.get('replyViaTeleBot', 10), 5), 3600)

    
#     # 텔레그램으로 안읽은 새 매세지 보내주기
#     schedule.every(send_interval).seconds.do(telegram.sendNewMessageByTelegram)
    
#     # 텔레그램 답장 확인하기
#     schedule.every(reply_interval).seconds.do(telegram.replyByTelegram)
        
#     # 크몽웹에서 계정과 메세지 받아오기
#     schedule.every(parse_interval).seconds.do(getMessageListFromKmongWeb)
    
#     print("스케줄러가 갱신되었습니다.")  

# # 메시지 체크 스레드
# def background_task():
#     def run_scheduler():
#         while True:
#             try:
#                 schedule.run_pending()
#             except Exception as e:
#                 print(f"스케줄러 실행 중 오류 발생: {str(e)}")
            
#             # 짧은 간격으로 sleep
#             time.sleep(1.0)
    
#     # 초기 스케줄 설정
#     refresh_scheduler()
    
#     # 스케줄러 실행
#     run_scheduler()

# @app.route('/')
# def index():
#     # 메시지 데이터를 index.html에 전달
#     return render_template('index.html')

# def init():
#     """애플리케이션 초기화"""
#     dbLib.create_db()
#     db_message.add_missing_columns_to_all_chatrooms()
#     init_telegram()

#     # 기존DB 버리고 새로운DB 사용
#     kmongLibInstance.migrationDB()
    
# if __name__ == '__main__':
#     init()
    
#     # 메시지 체크 스레드를 별도의 백그라운드 스레드로 실행
#     threading.Thread(target=background_task, daemon=True).start()

#     # Flask 애플리케이션 실행
#     app.run(host='0.0.0.0', port=7100, debug=True)




#     while True:
#         try:
#             # 데이터베이스에서 모든 계정 정보를 가져옴
#             accounts = dbLib.select_message_list()
#             kmong_message.user_data = []  # 🔹 기존 데이터 초기화 (중복 방지)


#             # 각 계정에 대해 메시지 확인 및 데이터베이스 업데이트
#             for account in accounts:
#                 userid = account.get("userid", "")
#                 passwd = account.get("passwd", "")
#                 login_cookie = account.get("login_cookie", "")

#                 # 🔹 메시지 확인 및 DB 업데이트
#                 message_count, message_content, message_id = kmong_message.check_unread_message(userid, passwd, login_cookie)
#                 check_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#                 # ✅ message_id 값을 DB에 저장하도록 수정
#                 dbLib.update_message(userid, passwd, login_cookie, message_count, message_id, message_content, check_date)

#             if not tabulate_called:  # tabulateDBdata가 아직 호출되지 않았을 때만 실행
#                 kmong_message.tabulateDBdata()
#                 tabulate_called = True  # tabulateDBdata가 호출되었음을 표시
                    
#             

#             time.sleep(30)  # 30초마다 실행

            
#         except Exception as e:
#             # 예외 발생 시 에러 메시지를 출력하고 60초 대기 후 재시도합니다.
#             print(f"에러 :  in message checking: {e}")
#             time.sleep(60)  # 에러 발생 시 60초 대기 후 재시도

# # 별도의 스레드(daemon 스레드)로 메시지 확인 함수 실행
# threading.Thread(target=check_messages_periodically, daemon=True).start()



# # 메시지 확인 API 엔드포인트 (GET 방식)
# @app.route('/check_messages', methods=['GET'])
# def check_messages():
#     try:
#         # 메시지 서비스의 check_messages 함수를 호출합니다.
#         # message_service.check_messages(bot, chat_id)
#         return jsonify({"결과": "메세지들이 확인되었습니다."}), 200
#     except Exception as e:
#         # 예외 발생 시 에러 메시지와 함께 500 에러 반환
#         return jsonify({"에러": str(e)}), 500


