from flask import Flask, render_template, request, jsonify, redirect
import time
import sys
import schedule
import random
import logging

import utils.kmong_checker.dbLib as dbLib
import utils.kmong_checker.kmongLib as kmongLib
import utils.kmong_manager.kmong_manger as kmongManager
import utils.kmong_manager.db_account as db_account
import utils.kmong_manager.db_message as db_message
from static.js.service.settings_service import SettingsService


import threading
from routes.account_routes import account_bp
from routes.message_routes import message_bp
from routes.settings_routes import settings_bp

from utils.telegram_manager.legacy_telegram_manager import LegacyTelegramManager

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

kmongManager = kmongManager.KmongManager()
kmong_message = kmongLib.KmongMessage()
settings_service = SettingsService()

# 텔레그램 매니저 인스턴스 (전역 변수)
telegram = None

# 텔레그램 관리자 초기화
def init_telegram():
    
    global telegram
    
    # 기존 인스턴스가 있으면 먼저 종료 시도
    if telegram:
        try:
            telegram.stop_bot()
            time.sleep(2)  # 종료 시간 확보
            logger.info("app.py, init_telegram // 기존 텔레그램 봇 인스턴스 정리")
        except:
            pass
    
    # 싱글톤 인스턴스 가져오기
    telegram = LegacyTelegramManager.get_instance()
    
    # 텔레그램 봇 시작 전 잠시 대기
    time.sleep(2)
    
    # 연결 상태 확인
    if not telegram.check_connection():
        logger.error("app.py, init_telegram // ⛔ 텔레그램 봇 연결에 실패했습니다. 설정을 확인하세요.")
        return None
    
    # 모니터링 준비
    if not telegram.prepareObserving():
        logger.error("app.py, init_telegram // ⛔ 텔레그램 모니터링 설정에 실패했습니다.")
    
    return telegram


# 크몽에서 새로운 메세지 받아오기
def getMessageListFromKmongWeb():
    try:
        row_list = dbLib.select_message_list()

        for row in row_list:
            userid = row.get("userid", "")
            passwd = row.get("passwd", "")
            login_cookie = row.get("login_cookie", "")

            ret = kmong_message.check_unread_message(userid, passwd, login_cookie).get("message_content", "") != ""
            if not ret:
                logger.info("app.py, getMessageListFromKmongWeb // ⛔ 쿠키로 로그인 실패, 새로 로그인 시도")
                ret, login_cookie = kmong_message.login(userid, passwd)
                if ret:
                    dto = kmong_message.check_unread_message(userid, passwd, login_cookie)
                    kmongManager.parsingUnreadMessage(email=userid, pw=passwd, cookie=login_cookie, data=dto)
                else:
                    logger.error("app.py, refreshgetMessageListFromKmongWeb_scheduler // ⛔ 크몽 로그인 실패")
        return ret
    except Exception as e:
        logger.error(f"app.py, getMessageListFromKmongWeb // ⛔ 크몽 메시지 확인 중 오류: {str(e)}")
        return False

# 현재 설정에 따라 스케줄러 재설정
def refresh_scheduler():
    global telegram
    
    logger.info("app.py, refresh_scheduler // ▶️ 스케줄러 갱신 시작")
    
    # 텔레그램 인스턴스 확인 및 필요시 초기화
    if telegram is None:
        logger.warning("app.py, refresh_scheduler // ⚠️ 텔레그램 봇이 초기화되지 않았습니다. 초기화를 시도합니다.")
        telegram = init_telegram()
        if telegram is None:
            logger.error("app.py, refresh_scheduler // ⛔ 텔레그램 봇 초기화 실패, 스케줄링은 텔레그램을 제외하고 진행합니다.")
    
    # 기존 스케줄 제거
    logger.info("app.py, refresh_scheduler // 기존 스케줄 제거")
    schedule.clear()

    # 현재 설정 가져오기
    settings = settings_service.get_settings()
    refresh_interval = settings.get('refreshInterval', {})
    
    # 각 작업에 대한 간격 설정
    kmong_interval = refresh_interval.get('parseUnReadMessagesinDB', 120)  # 기본값만 제공

    # 텔레그램 봇이 있는 경우에만 텔레그램 관련 스케줄 설정
    if telegram:
        send_interval = refresh_interval.get('sendUnReadMessagesViaTelebot', 30)  # 기본값만 제공
        reply_interval = refresh_interval.get('replyViaTeleBot', 10)  # 기본값만 제공
        
        # 텔레그램 관련 스케줄 설정
        schedule.every(send_interval).seconds.do(telegram.sendNewMessageByTelegram)
        schedule.every(reply_interval).seconds.do(telegram.replyByTelegram)
        logger.info(f"app.py, refresh_scheduler // 텔레그램 스케줄 설정: send={send_interval}s, reply={reply_interval}s")
    
    # 크몽웹에서 계정과 메세지 받아오기 (텔레그램과 무관하게 실행)
    schedule.every(kmong_interval).seconds.do(getMessageListFromKmongWeb)
    logger.info(f"app.py, refresh_scheduler // 크몽 메시지 체크 간격: {kmong_interval}s")
    
    logger.info("app.py, refresh_scheduler // ✅ 스케줄러 갱신 완료")
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
        kmongManager.migrationDB()
        
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