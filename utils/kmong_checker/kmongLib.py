import time
import os
import sys
import os.path
import traceback
import json
import datetime
import copy
import pyautogui
import json
from bs4 import BeautifulSoup
import hashlib


from kmong_checker import config
from kmong_checker import commonLib
from kmong_checker import networkLib
from kmong_checker import dbLib
from kmong_checker.config import LOGLEVEL


class KmongMessage:
    def __init__(self):
        pass

    def get_header(self):
        header = {}

        return header

    def login(self, userid, passwd):
        header = self.get_header()

        url = f"https://kmong.com/modalLogin"
        commonLib.print_log(LOGLEVEL.D, f"login: url = {url}")

        data = {"email": userid, "password": passwd, "remember": True, "next_page": "/", "is_dormant": 0}

        res = networkLib.retry_req_json(url, header, [], data)
        json_data = json.loads(res.text)

        meta = json_data.get('meta', {})
        status = meta.get('status', -1)
        msg = meta.get('msg', '')
        cookie_str = ''

        if status == 1 and msg == "succeed to login":
            cookies = res.cookies

            cookie_dict = {}

            for cookie in cookies:
                name = cookie.name
                value = cookie.value
                cookie_dict[name] = value

            cookie_str = json.dumps(cookie_dict)

            dbLib.update_message(userid, passwd, cookie_str, 0, 0, "")
        else:
            dbLib.update_message(userid, passwd, "", 0, 0, "[Error] 로그인 실패")

            return False, ''

        return True, cookie_str

    def check_unread_message(self, userid, passwd, cookie_str):
        header = self.get_header()

        if cookie_str is None or cookie_str == '':
            return False

        try:
            cookies = json.loads(cookie_str)
        except:
            return False

        url = f"https://kmong.com/api/v5/user/messages?page=1"
        #commonLib.print_log(LOGLEVEL.D, f"get_unread_message: url = {url}")

        res = networkLib.retry_req_get(url, header, cookies)
        json_data = json.loads(res.text)

        message_count = json_data.get('total', -1)

        if message_count == -1:
            return False

        message_id = 0
        message_content = ''

        if message_count > 0:
            #print("read:", json_data )
            dates = json_data.get('dates', [])
            messages = dates[0].get('messages')

            if messages is not None:
                msg = messages[0]
                message_id = msg.get('MID', 0)
                message_content = msg.get('message', '')
 
                message_content_hs = message_content + userid
                test_hash = hashlib.new('shake_256')
                test_hash.update(message_content_hs.encode('utf-8'))
                message_id = int(test_hash.hexdigest(3),16)

        dbLib.update_message(userid, passwd, cookie_str, message_count, message_id, message_content)

        return msg
