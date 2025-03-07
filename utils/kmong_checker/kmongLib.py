import time
import os
import sys
import traceback
import json
import hashlib
import logging
import requests

import random

from datetime import datetime

from utils.kmong_checker import config
from utils.kmong_checker import commonLib
from utils.kmong_checker import networkLib
from utils.kmong_checker import dbLib
from utils.kmong_checker.config import LOGLEVEL
from utils.kmong_checker import db_account
from utils.kmong_checker import db_message

from model.account_dto import AccountDTO
from model.message_dto import MessageDTO

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KmongMessage:
    def __init__(self):
        pass 

    def get_header(self):
        # ✅ 랜덤한 User-Agent 목록
        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.5195.136 Mobile Safari/537.36"
        ]

        header = {
            "User-Agent": random.choice(USER_AGENTS),  # 랜덤 User-Agent 적용
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://kmong.com/",
            "Origin": "https://kmong.com",
            "Connection": "keep-alive"
        }
        return header
    

    def migrationDB(self):
        # 전에 쓰던 DB에서 데이터 모두 가져옴
        legacyDB = dbLib.select_message_list()

        if db_account.check_account_table_exists():
            logging.info(f"kmongLib, migrationDB // ✅ account_table이 존재합니다.")
        else:
            logging.info(f"kmongLib, migrationDB // ⚠️ account_table이 존재하지 않아 테이블을 추가합니다.")
            # 계정 테이블 생성
            db_account.create_account_table()

            # 계정 테이블에 for문으로 데이터추가하기
            for account in legacyDB:

                email = account['userid']
                password = account['passwd']
                login_cookie = account['login_cookie']

                # 전에 쓰던 db에서 새로 생성된 계정 테이블에 모델파싱하여 추가
                db_account.create_account(account_dto=AccountDTO(
                    user_id=0,
                    email=email,
                    password=password,
                    login_cookie=login_cookie
                ))



    def login(self, userid, passwd):
        header = self.get_header()

        url = f"https://kmong.com/modalLogin"
        logging.info(f"kmongLib, login // 🗝️ 로그인 시도: URL = {url}, 사용자 = {userid}")

        data = {"email": userid, "password": passwd, "remember": True, "next_page": "/", "is_dormant": 0}

        try:
            res = networkLib.retry_req_json(url, header, [], data)
            logging.info(f"kmongLib, login // 💭 res.text = {res.text}")

            json_data = json.loads(res.text)
        except Exception as e:
            logging.error(f"kmongLib, login // ⛔ 로그인 실패 - 요청 중 오류 발생: {str(e)}")
            return False, ''

        meta = json_data.get('meta', {})
        status = meta.get('status', -1)
        msg = meta.get('msg', '')
        cookie_str = ''

        if status == 1 and msg == "succeed to login":
            cookies = res.cookies
            cookie_dict = {cookie.name: cookie.value for cookie in cookies}
            cookie_str = json.dumps(cookie_dict)
            check_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 현재 날짜와 시간
            # dbLib.update_message(userid, passwd, cookie_str, 0, 0, "")  # check_date 추가
            db_account.update_account(email= userid, password=passwd, login_cookie=cookie_str)
            logging.info(f"kmongLib, login // ✅ 로그인 성공: 사용자 {userid} 로그인됨")
        else:
            # dbLib.update_message(userid, passwd, "", 0, 0, "[Error] 로그인 실패")  # 빈 check_date 전달
            db_account.update_account(email= userid, password=passwd, login_cookie="")
            logging.error(f"kmongLib, login // ⛔ 로그인 실패: {msg}")
            return False, ''

        return True, cookie_str
    
    def getMessagesFromDB(self):
        messageList = dbLib.select_message_list()
        return messageList
    
    def readAccountList(self):
        accountList = db_account.read_all_accounts()
        return accountList

    def check_unread_message(self, userid, passwd, cookie_str):
        header = self.get_header()

        if cookie_str is None or cookie_str == '':
            logging.warning(f"kmongLib, check_unread_message // 🍪 쿠키 없음: {userid} 사용자 쿠키가 없거나 비어있음")
            return False

        try: 
            cookies = json.loads(cookie_str)
        except Exception as e:
            logging.error(f"kmongLib, check_unread_message // ⛔ 쿠키 파싱 오류: {str(e)}")
            return False

        url = f"https://kmong.com/api/v5/user/messages?page=1"  
                  
        try:
            res = networkLib.retry_req_get(url, header, cookies)
            json_data = json.loads(res.text)
        except Exception as e:
            logging.error(f"kmongLib, check_unread_message // ⛔ 메시지 요청 오류: {str(e)}")
            return False

        # 서버로부터 받은 메시지 개수
        message_count = json_data.get('total', -1)
        if message_count == -1:
            logging.warning(f"kmongLib, check_unread_message // ⛔ 메시지 개수 확인 실패: {userid} 사용자")
            return False

        # 메시지 내용 및 ID 추출
        message_id = 0
        message_content = ''
        if message_count > 0:
            dates = json_data.get('dates', [])
            if dates:
                messages = dates[0].get('messages', [])
                if messages:
                    # 가장 최근 메시지
                    latest_message = messages[0]

                    print(f"📦 json 최신 메세지 : {latest_message}")

                    # 메세지 id
                    kmong_message_id = latest_message.get('MID', 0)
                    message_id = kmong_message_id

                    # 메세지 내용
                    message_content = latest_message.get('message', '')

                    # 해시 처리
                    message_content_hs = message_content + userid
                    test_hash = hashlib.new('shake_256')
                    test_hash.update(message_content_hs.encode('utf-8'))
                    kmong_message_id = int(test_hash.hexdigest(3), 16)

                    # 채팅룸 id
                    chatroom_id = latest_message.get('inbox_group_id', 0)

                    # 내 id
                    admin_id = latest_message.get('MSGTO', 0)

                    # 의뢰자 id
                    client_id = latest_message.get('MSGFROM', 0)

                    # client_id = latest_message.get('user', 0).get('USERID', 0)
                    logging.info(f"kmongLib, check_unread_message // ⏫ 업데이트 : email={userid}, password={passwd}, admin_id={admin_id}, client_id={client_id}, message={message_content}")
                    db_account.update_account(email= userid, password=passwd, login_cookie=cookie_str, user_id=admin_id)

                    # chatroom_id로 된 테이블이 존재하는지?
                    if db_message.check_chatroom_table_exists(table_id=chatroom_id):
                        logging.info(f"kmongLib, migrationDB // ✅ account_table이 존재합니다.")
                    else:
                        logging.info(f"kmongLib, migrationDB // ⚠️ account_table이 존재하지 않아 테이블을 추가합니다.")

                        # chatroom_id로 된 테이블이 없어 생성함.
                        db_message.create_chatroom_table(table_id=chatroom_id)

                    # chatroom 테이블에 메세지 모두 가져오기
                    existing_messages = db_message.read_all_messages(table_id=chatroom_id)
                    # 기존 메세지에서 kmong_message_id데이터들만 따로 뽑아 json리스트로 만들기.
                    existing_ids = {msg['kmong_message_id'] for msg in existing_messages}

                    # for문으로 돌려서 새로운 메세지의 kmong_message_id가 중복되지 않는 새로운 값인 경우
                    if message_id not in existing_ids:
                        # 새로운 메세지를 chatroom 테이블에 추가
                        logging.info(f"kmongLib, check_unread_message // 🆕 새로운 메시지를 추가합니다: {message_id}")
                        db_message.create_message(table_id=chatroom_id, message_dto=MessageDTO(
                            admin_id=admin_id,
                            text=message_content,
                            client_id=client_id,
                            sender_id=client_id,
                            replied_kmong=0,
                            replied_telegram=0,
                            kmong_message_id=kmong_message_id,
                            seen=0,
                            date=datetime.today()
                        ))
                    else:
                        # kmong_message_id값이 중복된경우
                        logging.info(f"kmongLib, check_unread_message // 🔁 이미 존재하는 메시지: {message_id}")                 
                   
                    # 데이터베이스 업데이트
                    dbLib.update_message(userid, passwd, cookie_str, message_count, kmong_message_id, message_content)
                    
                    # updateChatroomList 호출하여 UI를 갱신
                    try:
                        # UI 갱신을 위해 서버에 요청
                        urls = ["http://127.0.0.1:7100/updateChatroomList", "http://172.30.1.22:7100/updateChatroomList"]
                        for url in urls:
                            try:
                                response = requests.get(url, timeout=5)
                                if response.status_code == 200:
                                    logging.info(f"kmongLib, check_unread_message // ✅ updateChatroomList 호출 성공")
                                    return response.json()  # 또는 response.text (필요에 따라 변경)
                            except requests.exceptions.RequestException as e:
                                logging.error(f"kmongLib, check_unread_message // ⛔ updateChatroomList 호출 실패: {response.status_code}")
                        return None  # 모든 요청이 실패한 경우
                    except Exception as e:
                        logging.error(f"kmongLib, check_unread_message // ⛔ updateChatroomList 호출 중 오류 발생: {str(e)}")
        return True
    
