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

# 텔레그램 관리자 초기화
def init_telegram():
    from utils.telegram_manager.legacy_telegram_manager import LegacyTelegramManager
    
    # 싱글톤 인스턴스 가져오기
    global telegram
    telegram = LegacyTelegramManager.get_instance()
    
    # 텔레그램 봇 시작 전 잠시 대기 (이전 인스턴스가 종료될 시간 확보)
    import time
    time.sleep(1)
    
    # 연결 상태 확인
    if not telegram.check_connection():
        logger.error("app.py, init_telegram // ⛔ 텔레그램 봇 연결에 실패했습니다. 설정을 확인하세요.")
        return None
    
    # 모니터링 준비
    if not telegram.prepareObserving():
        logger.error("app.py, init_telegram // ⛔ 텔레그램 모니터링 설정에 실패했습니다.")
    
    # 테스트 메시지 전송 (봇 작동 확인)
    if telegram.sendDummyMessage():
        logger.info("app.py, init_telegram // ✅ 텔레그램 봇이 성공적으로 초기화되었습니다.")
    else:
        logger.error("app.py, init_telegram // ⛔ 텔레그램 테스트 메시지 전송에 실패했습니다.")
    
    return telegram


# 크몽에서 새로운 메세지 받아오기
dummy = DummySingleton()
def getMessageListFromKmongWeb():
    try:
        userid = dummy.get_admin_info()['email']
        passwd = dummy.get_admin_info()['password']
        login_cookie = dummy.get_admin_info()['login_cookie']

        ret = kmongLibInstance.check_unread_message(userid, passwd, login_cookie)
        if not ret:
            logger.info("app.py, getMessageListFromKmongWeb // ⛔ 쿠키로 로그인 실패, 새로 로그인 시도")
            ret, login_cookie = kmongLibInstance.login(userid, passwd)
            if ret:
                kmongLibInstance.check_unread_message(userid, passwd, login_cookie)
            else:
                logger.error("app.py, refreshgetMessageListFromKmongWeb_scheduler // ⛔ 크몽 로그인 실패")
        
        return ret
    except Exception as e:
        logger.error(f"app.py, getMessageListFromKmongWeb // ⛔ 크몽 메시지 확인 중 오류: {str(e)}")
        return False

# 현재 설정에 따라 스케줄러 재설정
def refresh_scheduler():
    global telegram
    
    # 텔레그램 인스턴스 확인
    if telegram is None:
        logger.error("app.py, refresh_scheduler // ⛔ 텔레그램 봇이 초기화되지 않았습니다.")
        return False
    
    # 기존 스케줄 제거
    schedule.clear()

    # 현재 설정 가져오기
    settings = settings_service.get_settings()
    refresh_interval = settings.get('refreshInterval', {})
    
    # 각 작업에 대한 간격 설정 (값 범위를 제한하여 오버플로우 방지) // 기본 120초, 최소 60초, 최대 1시간
    kmong_interval = min(max(refresh_interval.get('parseUnReadMessagesinDB', 120), 110), 3600)
    send_interval = min(max(refresh_interval.get('sendUnReadMessagesViaTelebot', 10), 5), 3600)
    reply_interval = min(max(refresh_interval.get('replyViaTeleBot', 10), 5), 3600)

    
    # 텔레그램으로 안읽은 새 매세지 보내주기
    schedule.every(send_interval).seconds.do(telegram.sendNewMessageByTelegram)
    
    # 텔레그램 답장 확인하기
    schedule.every(reply_interval).seconds.do(telegram.replyByTelegram)
        
    # 크몽웹에서 계정과 메세지 받아오기
    schedule.every(kmong_interval).seconds.do(getMessageListFromKmongWeb)
    
    return True  

# 백그라운드 작업 스레드
def background_task():    
    def run_scheduler():
        """스케줄러 실행 루프"""
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                logger.error(f"app.py, background_task, run_scheduler // ⛔ 스케줄러 실행 중 오류 발생: {str(e)}")
            
            # 짧은 간격으로 sleep
            time.sleep(1.0)
    
    # 초기 스케줄 설정
    refresh_scheduler()
    
    # 스케줄러 실행
    run_scheduler()

@app.route('/')
def index():
    return render_template('index.html')

# 애플리케이션 초기화
def init():
    try:
        # 데이터베이스 초기화
        dbLib.create_db()
        db_message.add_missing_columns_to_all_chatrooms()
        
        # 텔레그램 초기화
        init_telegram()
        
        # 기존DB 마이그레이션
        kmongLibInstance.migrationDB()
        
        return True
    except Exception as e:
        logger.error(f"app.py, init // ⛔ 초기화 중 오류 발생: {str(e)}")
        return False
    
if __name__ == '__main__':
    # 애플리케이션 초기화
    if not init():
        logger.error("app.py, __main__ // ⛔ 초기화에 실패했습니다. 애플리케이션을 종료합니다.")
        sys.exit(1)
    
    # 메시지 체크 스레드를 별도의 백그라운드 스레드로 실행
    threading.Thread(target=background_task, daemon=True).start()
    
    # 스레드 시작 후 잠시 대기 (초기화 시간 확보)
    time.sleep(2)
        
    # Flask 애플리케이션 실행
    app.run(host='0.0.0.0', port=7100, debug=True)