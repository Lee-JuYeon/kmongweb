import utils.kmong_checker.db_message as db_message
from model.message_dto import MessageDTO
from datetime import date

class MessageService:
    def __init__(self):
        # Ensure all chatroom tables have the required columns
        db_message.add_missing_columns_to_all_chatrooms()
    
    def get_all_chatroom_tables(self):
        """Get a list of all chatroom tables"""
        return db_message.read_all_chatroom_tables()
    
    def get_chatroom_by_id(self, chatroom_id):
        """Get chatroom information by ID"""
        return db_message.read_chatroom_by_id(chatroom_id)
    
    def get_messages_by_chatroom_id(self, chatroom_id):
        """Get all messages for a specific chatroom"""
        return db_message.read_all_messages(chatroom_id)
    
    def create_chatroom(self, chatroom_id):
        """Create a new chatroom with the given ID"""
        if db_message.check_chatroom_table_exists(chatroom_id):
            return False, f"채팅방 ID {chatroom_id}가 이미 존재합니다."
        
        db_message.create_chatroom_table(chatroom_id)
        return True, f"채팅방 ID {chatroom_id}가 생성되었습니다."
    
    def delete_chatroom(self, chatroom_id):
        """Delete a chatroom by ID"""
        db_message.delete_chatroom_table(chatroom_id)
        return True, f"채팅방 ID {chatroom_id}가 삭제되었습니다."
    
    def create_message(self, chatroom_id, admin_id, text, client_id, sender_id, 
                      replied_kmong=1, replied_telegram=0, seen=0, kmong_message_id=0):
        """Create a new message in the specified chatroom"""
        # Ensure chatroom exists
        if not db_message.check_chatroom_table_exists(chatroom_id):
            db_message.create_chatroom_table(chatroom_id)
        
        # Create MessageDTO object
        message_dto = MessageDTO(
            admin_id=admin_id,
            text=text,
            client_id=client_id,
            sender_id=sender_id,
            replied_kmong=replied_kmong,
            replied_telegram=replied_telegram,
            seen=seen,
            kmong_message_id=kmong_message_id,
            date=date.today()
        )
        
        # Add message to DB
        db_message.create_message(chatroom_id, message_dto)
        return True, "메시지가 추가되었습니다."
    
    def update_unread_messages(self, chatroom_id):
        """읽지 않은 메시지를 모두 읽음 상태로 업데이트"""
        try:
            # 읽지 않은 메시지(seen == 0)를 읽음 상태(seen == 1)로 업데이트
            db_message.update_unread_message(chatroom_id)
            return True
        except Exception as e:
            return False
    
    def sync_chat_history(self, chatroom_id, messages):
        """Sync chat history for a specific chatroom by replacing all messages"""
        # Delete existing chatroom
        self.delete_chatroom(chatroom_id)
        
        # Create new chatroom
        self.create_chatroom(chatroom_id)
        
        # Add each message to the chatroom
        for message in messages:
            db_message.create_message(chatroom_id, message)
        
        return True, "채팅 내역이 동기화되었습니다."
    
# from datetime import date
# from model.message_dto import MessageDTO
# import kmong_checker.db_message as db_message
# import kmong_checker.db_account as db_account


# from selenium_custom.selenium_manager import SeleniumManager
# from dummy.dummySingleton import DummySingleton

# class MessageService:
#     def __init__(self):
#         self.db_message = db_message
#         self.db_account = db_account

#        # 클래스를 인스턴스화
#         self.selenium_manager = SeleniumManager()
#         self.dummy_manager = DummySingleton()

#     def create_message(self, table_id: int, admin_id: int, text: str, client_id: int, sender_id: int, 
#                       replied_kmong: int = 0, replied_telegram: int = 0, seen: int = 0, kmong_message_id: int = 0):
#         """메시지 생성"""
#         message_dto = MessageDTO(
#             admin_id=admin_id,
#             text=text,
#             client_id=client_id,
#             sender_id=sender_id,
#             replied_kmong=replied_kmong,
#             replied_telegram=replied_telegram,
#             seen=seen,
#             kmong_message_id=kmong_message_id,
#             date=date.today()
#         )
#         self.db_message.create_message(table_id, message_dto)
#         return message_dto

#     def read_message_by_id(self, table_id: int, message_id: int):
#         """메시지 ID로 조회"""
#         return self.db_message.read_message_by_id(table_id, message_id)

#     def read_all_messages(self, table_id: int):
#         """모든 메시지 조회"""
#         return self.db_message.read_all_messages(table_id)

#     def update_message(self, table_id: int, message_id: int, text=None, replied_kmong=None, 
#                       replied_telegram=None, seen=None, kmong_message_id=None):
#         """메시지 업데이트"""
#         self.db_message.update_message(table_id, message_id, text, replied_kmong, 
#                                       replied_telegram, seen, kmong_message_id)

#     def update_unread_message(self, table_id: int):
#         """읽지 않은 메시지 업데이트"""
#         self.db_message.update_unread_message(table_id)

#     def delete_all_messages(self, table_id: int):
#         """모든 메시지 삭제"""
#         self.db_message.delete_all_messages(table_id)

#     def delete_chatroom_table(self, table_id: int):
#         """채팅방 테이블 삭제"""
#         self.db_message.delete_chatroom_table(table_id)
    
#     def check_chatroom_table_exists(self, table_id: int):
#         """채팅방 테이블이 존재하는지 확인"""
#         return self.db_message.check_chatroom_table_exists(table_id)
    
#     def create_chatroom_table(self, table_id: int):
#         """채팅방 테이블 생성"""
#         self.db_message.create_chatroom_table(table_id)

#     def get_all_chatroom_tables(self):
#         """모든 채팅방 테이블 가져오기"""
#         return self.db_message.read_all_chatroom_tables()
    
#     def get_chatroom_by_id(self, table_id: int):
#         """채팅방 정보 가져오기"""
#         return self.db_message.read_chatroom_by_id(table_id)

#     def get_all_chatrooms(self):
#         """모든 채팅방 목록 가져오기"""
#         # DB에서 모든 계정 정보 조회
#         accounts = self.db_account.read_all_accounts()

#         # DB에서 모든 chatroom_ 테이블 조회
#         chatroom_table_list = self.db_message.read_all_chatroom_tables()

#         chatroomList = []

#         for chatroom_table in chatroom_table_list:
#             # chatroom_table이 문자열이면 테이블 ID 추출
#             if isinstance(chatroom_table, str):
#                 table_id = int(chatroom_table.split('_')[1])  # chatroom_123 → 123
#                 chatroom_data = self.db_message.read_chatroom_by_id(table_id)
#             else:
#                 chatroom_data = chatroom_table  # 이미 딕셔너리라면 그대로 사용

#             # chatroom_data가 None인 경우 처리 (테이블에 대한 정보가 없을 경우)
#             if not chatroom_data:
#                 continue

#             for account in accounts:
#                 # 'user_id'가 존재하고, 'admin_id'가 일치하는 경우에만 처리
#                 if ('user_id' in account and account.get('user_id') > 0 and 
#                     'admin_id' in chatroom_data and chatroom_data.get('admin_id') == account.get('user_id')):
#                     # 메시지 목록 가져오기
#                     messageList = self.db_message.read_all_messages(table_id=table_id)

#                     # 메시지가 있을 경우
#                     if messageList:
#                         # chatroom_data에 필요한 정보 추가
#                         chatroom_data = {
#                             'email': account.get('email'),
#                             'user_id': account.get('user_id'),
#                             'messages': messageList, 
#                             'chatroom_id': table_id
#                         }
#                         chatroomList.append(chatroom_data)

#         return chatroomList

#     def send_message_in_web(self, chatroom_id: int, admin_id: int, client_id: int, text: str):
#         """웹에서 메시지 전송"""
#         try:
#             accountList = self.db_account.read_all_accounts()
#             for account in accountList:
#                 try:
#                     admin_id_int = int(admin_id)
#                 except ValueError:
#                     print(f"message_service.py, send_message_in_web // ❌ admin_id 변환 실패: {admin_id}")
#                     continue

#                 try:
#                     account_user_id = int(account.get('user_id'))
#                 except ValueError:
#                     print(f"message_service.py, send_message_in_web // ❌ account['user_id'] 변환 실패: {account.get('user_id')}")
#                     continue

#                 if admin_id_int == account_user_id:
#                     # 1️⃣ 크몽 로그인
#                     self.selenium_manager.login(
#                         self.dummy_manager.get_admin_info()['email'], 
#                         self.dummy_manager.get_admin_info()['password']
#                     )

#                     # 2️⃣ 지정된 채팅방으로 이동
#                     self.selenium_manager.getClientChatRoom(chatroom_id=chatroom_id, client_id=client_id)

#                     # 3️⃣ 메시지 전송
#                     dto = MessageDTO(
#                         admin_id=admin_id,
#                         text=text,
#                         client_id=client_id,
#                         sender_id=admin_id,
#                         replied_kmong=1,
#                         replied_telegram=0,
#                         seen=0,
#                         kmong_message_id=0,
#                         date=date.today()
#                     )  
                    
#                     print(f"🧍‍♀️ message_service.py, send_message_in_web, dto // MessageDTO : {dto}")

#                     self.selenium_manager.send_message(
#                         message=text, 
#                         dto=dto,
#                         chatroomID=chatroom_id
#                     )
                
#                     return True, "메시지가 전송되었습니다."
            
#             return False, "해당 admin_id의 계정을 찾을 수 없음"
#         except Exception as e:
#             print(f"메시지 전송 중 오류: {e}")
#             return False, f"메시지 전송에 실패했습니다. 오류: {e}"

#     def sync_chat_history(self, chatroom_id: int, admin_id: int, client_id: int):
#         """채팅 내역 동기화"""
#         try:
#             accountList = self.db_account.read_all_accounts()
#             for account in accountList:
#                 try:
#                     admin_id_int = int(admin_id)
#                 except ValueError:
#                     print(f"message_service.py, sync_chat_history // ❌ admin_id 변환 실패: {admin_id}")
#                     continue

#                 try:
#                     account_user_id = int(account.get('user_id'))
#                 except ValueError:
#                     print(f"message_service.py, sync_chat_history // ❌ account['user_id'] 변환 실패: {account.get('user_id')}")
#                     continue

#                 if admin_id_int == account_user_id:
#                     # 크몽 로그인
#                     self.selenium_manager.login(
#                         self.dummy_manager.get_admin_info()['email'], 
#                         self.dummy_manager.get_admin_info()['password']
#                     )

#                     # 지정된 채팅방으로 이동
#                     self.selenium_manager.getClientChatRoom(chatroom_id=chatroom_id, client_id=client_id)

#                     # 채팅 내역 가져오기
#                     chat_history = self.selenium_manager.getChatHistory(admin_id=admin_id_int)
#                     print(f"💬 채팅 내역 : {chat_history}")

#                     # DB 업데이트 1. chatroom 테이블 없애기
#                     self.db_message.delete_chatroom_table(table_id=chatroom_id)
#                     print(f"❌ 삭제된 테이블 ID : {chatroom_id} // 남아있는 테이블 {self.db_message.read_all_chatroom_tables()}")

#                     # DB 업데이트 2. chatroom 테이블 새로 생성
#                     if self.db_message.check_chatroom_table_exists(table_id=chatroom_id):
#                         self.db_message.delete_chatroom_table(table_id=chatroom_id)
#                         print(f"❌ 테이블이 여전히 남아있어 다시 삭제함")
                    
#                     # 테이블 생성
#                     self.db_message.create_chatroom_table(table_id=chatroom_id)
#                     print(f"➕ 테이블 새로 생성함.")

#                     # DB 업데이트 3. chat_history를 DTO list로 만들기
#                     for chat_item in chat_history:
#                         print(f"🔔 테이블에 추가할 메시지 dto를 사용하여 추가할예정")
#                         dto = MessageDTO(
#                             admin_id=chat_item.admin_id,
#                             text=chat_item.text,
#                             client_id=chat_item.client_id,
#                             sender_id=chat_item.sender_id,
#                             replied_kmong=1,
#                             replied_telegram=1,
#                             seen=1,
#                             kmong_message_id=0,
#                             date=chat_item.date
#                         )
#                         # DB 업데이트 4. chatroom 테이블에 DTO list를 순차적으로 넣기
#                         self.db_message.create_message(table_id=chatroom_id, message_dto=dto)        
#                         print(f"🧩 messageModel이 'chatroom_{chatroom_id}'에 추가되는 중")
                    
#                     self.selenium_manager.close_driver()
#                     return True, "채팅 내역이 성공적으로 동기화되었습니다."
            
#             return False, "해당 admin_id의 계정을 찾을 수 없음"
#         except Exception as e:
#             print(f"채팅 내역 동기화 중 오류: {e}")
#             return False, f"채팅 내역 동기화에 실패했습니다. 오류: {e}"