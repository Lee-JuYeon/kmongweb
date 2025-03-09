from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By                             
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs

from model.account_dto import AccountDTO
from model.message_dto import MessageDTO
from datetime import date
import time
import json
import re
import weakref
import utils.kmong_manager.db_message as db_message



class SeleniumManager:
    def __init__(self):
        self.driver = None

    def _init_driver(self):
        """WebDriver 초기화 메소드"""
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")  # GPU 비활성화
        options.add_argument("--no-sandbox")   # 샌드박스 모드 비활성화
        options.add_argument("--start-maximized")  # 창 최대화
        options.add_argument("--disable-blink-features=AutomationControlled")  # 자동화 탐지 방지

        # User-Agent 설정 (브라우저처럼 보이게)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # 기본 헤더 추가
        options.add_argument("Accept-Language: en-US,en;q=0.9,ko;q=0.8")
        options.add_argument("Accept-Encoding: gzip, deflate, br")
        options.add_argument("Connection: keep-alive")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("✅ WebDriver 초기화 완료.")

    def switch_to_main_tab(self):
        """메인 탭을 자동으로 찾고, 불필요한 탭을 닫는다."""
        if len(self.driver.window_handles) > 1:
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if "kmong.com" in self.driver.current_url:  # 크몽 도메인이 있는 탭 찾기
                    print(f"✅ 메인 탭 찾음: {self.driver.current_url}")
                    return
            print("⚠️ 크몽 메인 탭을 찾지 못함. 첫 번째 탭을 유지합니다.")
            self.driver.switch_to.window(self.driver.window_handles[0])  # 첫 번째 탭 사용
        else:
            print("✅ 단일 탭 사용 중.")


    def getChatroomIdByURL(self):
        # 현재 브라우저의 URL 가져오기
        current_url = self.driver.current_url

        # URL 파싱
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)

        # inbox_group_id 값 가져오기 (int 변환)
        chatroom_id = int(query_params.get("inbox_group_id", [0])[0])  # 기본값 0 설정
        return chatroom_id
    
    def getClientIdByURL(self):
        parsed_url = urlparse(self.driver.current_url)
        query_params = parse_qs(parsed_url.query)
        client_id = int(query_params.get("partner_id", [0])[0])  # 기본값 0 설정
        return client_id 
 
    def getAdminId(self):
        try:
            # 모든 <script> 태그의 내용을 가져옴
            scripts = self.driver.find_elements(By.TAG_NAME, "script")

            # USERID 값을 찾기 위한 정규 표현식
            userid_pattern = re.compile(r'"USERID":(\d+)')

            # 각 <script> 태그의 내용을 확인하며 USERID 값을 찾음
            for script in scripts:
                script_content = script.get_attribute("innerHTML")
                match = userid_pattern.search(script_content)
                if match:
                    userid = match.group(1)
                    return userid  # USERID 값을 반환

            # USERID를 찾지 못한 경우 None 반환
            return None
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            return None

    def login(self, username, password):
        """크몽 로그인 메소드"""
        try:
            self._init_driver()

            self.driver.get("https://kmong.com/")

            # 로그인 화면 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[text()='로그인']"))
            )
            login_button = self.driver.find_element(By.XPATH, "//*[text()='로그인']")
            login_button.click()

            # 이메일 입력 필드 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            
            # 이메일 입력
            email_input = self.driver.find_element(By.NAME, "email")
            email_input.send_keys(username)
            
            # 비밀번호 입력
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)
            password_input.send_keys(Keys.RETURN)  # 로그인 버튼 대신 엔터 입력

            print(f"🔑 {username} 로그인 완료.")

            # ✅ 로그인 후 메인 탭 찾기
            time.sleep(2)  # 크몽에서 자동으로 탭을 띄우는 시간 확보
            self.switch_to_main_tab()
        except Exception as e:
            print(f"❌ 로그인 중 오류 발생: {e}")
            raise

    def closeModalIfExists(self):
        """모달이 존재하면 닫기"""
        try:
            # 모달이 나타날 때까지 기다림
            modal = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="modal-container"]'))
            )
            
            # 모달이 있으면 닫기
            close_button = modal.find_element(By.CSS_SELECTOR, 'button')
            close_button.click()
            
            # 모달이 닫힐 때까지 기다림
            WebDriverWait(self.driver, 10).until(
                EC.invisibility_of_element(modal)
            )
            print("🔄 모달 닫음.")
        except Exception:
            print("✅ 모달 없음.")

    def getClientChatRoom(self, chatroom_id, client_id):
        """클라이언트 채팅방으로 이동"""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//img[@alt="avatar"]'))  
            )
            
            url = f"https://kmong.com/inboxes?inbox_group_id={chatroom_id}&partner_id={client_id}"
            self.driver.get(url)
            print(f"📨 채팅 페이지 이동 완료. (URL: {url})")

            # 채팅 목록이 로드될 때까지 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.w-full.rounded-lg.border.border-solid'))
            )

            self.closeModalIfExists()  # 모달이 뜨면 닫기

            print("✅ 채팅 페이지 로드 완료.")

        except Exception as e:
            print(f"❌ 채팅 페이지 이동 중 오류 발생: {e}")
            raise

    def getChatHistory(self, admin_id):
            """채팅 메시지 추출 메소드"""
            try:
                # ✅ 실행 전 메인 탭 유지
                self.switch_to_main_tab()
    
                # ul과 그 내부의 div가 로드될 때까지 대기
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.flex.flex-col.overflow-y-auto'))
                )
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.my-5.flex.flex-col.items-center.gap-y-2.text-center'))
                )
                print("✅ ul과 주변 div 요소 로드 완료.")

                # ul 내부의 li 요소들 찾기
                chat_items = self.driver.find_elements(By.CSS_SELECTOR, 'ul.flex.flex-col.overflow-y-auto > li')

                # li가 1개 이상인지 확인
                if len(chat_items) > 0:
                    print(f"✅ {len(chat_items)}개의 채팅 메시지 발견.")
                    chat_history = []

                   
                    for item in chat_items:
                        try:
                            # 발신자 확인 (내 메시지인지 상대방 메시지인지)
                            sender_class = item.get_attribute("class")
                            sender_id = admin_id if "items-end" in sender_class else self.getClientIdByURL()


                            # 메시지 텍스트 추출
                            text_element = item.find_element(By.CSS_SELECTOR, 'div[role="presentation"]')
                            text = text_element.text.strip() if text_element else "내용 없음"

                            # # 타임스탬프 추출
                            # timestamp_element = item.find_element(By.CSS_SELECTOR, 'p.text-[10px].font-normal.text-gray-500')
                            # timestamp = timestamp_element.text.strip() if timestamp_element else "시간 없음"

                            # print(f" 💥 테스트용 어드민계정 : {self.getAdminId()}")

                            chat_history.append(MessageDTO(
                                admin_id=admin_id,
                                text=text, 
                                client_id=self.getClientIdByURL(), 
                                sender_id=sender_id, 
                                replied_kmong=1, 
                                replied_telegram=1, 
                                seen=1,
                                kmong_message_id=0,
                                date=date.today()
                            ))
                        except Exception as e:
                            print(f"⚠️ 메시지 추출 오류 발생: {e}")
                    return chat_history
                else:
                    print("⚠️ 채팅 메시지가 없습니다.")
                    return []

            except Exception as e:
                print(f"❌ 채팅 메시지 추출 중 오류 발생: {e}")
                raise

    def send_message(self, message = str, dto = MessageDTO, chatroomID = int):
        # 메시지를 전송하는 메소드
        try:
            # ✅ 실행 전 메인 탭 유지
            self.switch_to_main_tab()

            # ul과 그 내부의 div가 로드될 때까지 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.flex.flex-col.overflow-y-auto'))
            )
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.my-5.flex.flex-col.items-center.gap-y-2.text-center'))
            )
            print("✅ ul과 주변 div 요소 로드 완료.")

            # ul 내부의 li 요소들 찾기
            chat_items = self.driver.find_elements(By.CSS_SELECTOR, 'ul.flex.flex-col.overflow-y-auto > li')

            # li가 1개 이상인지 확인
            if len(chat_items) > 0:
                print(f"✅ {len(chat_items)}개의 채팅 메시지 발견.")
                    
                # textarea 요소 찾기 (메시지 입력)
                textarea = self.driver.find_element(By.CSS_SELECTOR, 'textarea[placeholder="메시지를 입력하세요. (Enter: 줄바꿈 / Ctrl+Enter: 전송)"]')

                # 메시지 입력
                textarea.clear()  # 기존 내용 지우기
                textarea.send_keys(message)  # 메시지 입력

               
                # disabled 속성을 제거할 버튼 찾기
                send_button = self.driver.find_element(By.CSS_SELECTOR, 'button[role="button"][color="yellow"]')

                # disabled 속성 제거
                self.driver.execute_script("arguments[0].removeAttribute('disabled')", send_button)

                # 버튼 클릭
                send_button.click()

                print("✅ 메시지가 성공적으로 전송되었습니다.")

                # ✅ 약한 참조를 사용하여 외부 콜백 실행

                db_message.create_message(
                    table_id=chatroomID,
                    message_dto=dto
                )
            else:    
                print("⚠️ 채팅 메시지가 없어 메세지를 보낼 수 없음")
        except Exception as e:
            print(f"메시지 전송 중 오류 발생: {e}")
            raise
        finally :
            self.close_driver()


    def close_driver(self):
        # WebDriver 종료 메소드
        if self.driver:
            self.driver.quit()  # WebDriver 종료
            print("WebDriver 종료 완료.")
