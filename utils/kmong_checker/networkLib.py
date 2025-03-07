import os
import random
import string
import time
import platform
import traceback
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# ✅ 랜덤한 User-Agent 목록
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.5195.136 Mobile Safari/537.36"
]

def get_fake_headers():
    """ 실제 브라우저에서 가져온 User-Agent와 일반적인 웹 요청 헤더 생성 """
    return {
        "User-Agent": random.choice(USER_AGENTS),  # 랜덤 User-Agent 적용
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://kmong.com/",
        "Origin": "https://kmong.com",
        "Connection": "keep-alive"
    }



def retry_req_get(url, header, cookie, proxy_server=None):
    res = False

    with requests.Session() as s:
        try:
            retries = 3
            backoff_factor = 0.3
            status_forcelist = (500, 502, 504)

            retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
                          status_forcelist=status_forcelist)

            adapter = HTTPAdapter(max_retries=retry)
            s.mount('http://', adapter)
            s.mount('https://', adapter)


            # 헤더 설정
            if header is None:
                header = get_fake_headers()

            # 랜덤 지연시간 적용 (사람처럼 보이도록)
            time.sleep(random.uniform(1.5, 4.0))

            res = s.get(url, headers=header, cookies=cookie, proxies=proxy_server)
        except:
            traceback.print_exc()

    return res

def retry_req_post(url, header, cookie, data, proxy_server=None):
    res = False

    with requests.Session() as s:
        try:
            retries = 5
            backoff_factor = 0.3
            status_forcelist = (500, 502, 504)

            retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
                          status_forcelist=status_forcelist)

            adapter = HTTPAdapter(max_retries=retry)
            s.mount('http://', adapter)
            s.mount('https://', adapter)

            # 헤더 설정
            if header is None:
                header = get_fake_headers()

            # 랜덤 지연시간 적용
            time.sleep(random.uniform(1.5, 4.0))

            res = s.post(url, data, headers=header, cookies=cookie, proxies=proxy_server)
        except:
            traceback.print_exc()

    return res

def retry_req_json(url, header, cookie, data, proxy_server=None):
    res = False

    header['content-type'] = 'application/json'

    with requests.Session() as s:
        try:
            retries = 5
            backoff_factor = 0.3
            status_forcelist = (500, 502, 504)

            retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor,
                          status_forcelist=status_forcelist)

            adapter = HTTPAdapter(max_retries=retry)
            s.mount('http://', adapter)
            s.mount('https://', adapter)


            # 헤더 설정
            if header is None:
                header = get_fake_headers()
            header['Content-Type'] = 'application/json'

            # 랜덤 지연시간 적용
            time.sleep(random.uniform(1.5, 4.0))


            res = s.post(url, data=json.dumps(data), headers=header, cookies=cookie, proxies=proxy_server)
        except:
            traceback.print_exc()

    return res