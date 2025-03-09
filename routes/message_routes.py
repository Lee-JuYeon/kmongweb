from flask import Blueprint, request, jsonify
from datetime import date

from static.js.service.message_service import MessageService
from static.js.service.account_service import AccountService

from utils.telegram_manager.legacy_telegram_manager import LegacyTelegramManager
from utils.selenium_manager.selenium_manager import SeleniumManager
from utils.gpt_manager.gpt_manager import GPTManager

from model.message_dto import MessageDTO


# Blueprint 생성
message_bp = Blueprint('message', __name__, url_prefix='/api/message')

# 인스턴스 생성
message_service = MessageService()
account_service = AccountService()
chatGPT = GPTManager()
selenium = SeleniumManager()
telegram = LegacyTelegramManager()

# [채팅방 목록] 특정 채팅방의 메세지 목록 불러오기
@message_bp.route('/loadChatHistory/<int:chatroom_id>')
def loadChatHistoryByChatRoomIdFromDB(chatroom_id):
    """특정 채팅방의 메시지 목록 불러오기"""
    try:
        # Use message service to get messages
        messages = message_service.get_messages_by_chatroom_id(chatroom_id)
        return jsonify(messages)
    except Exception as e:
        print(f"채팅 내역 불러오기 오류: {e}")
        return jsonify({"error": "채팅 내역을 불러오는 중 오류가 발생했습니다"}), 500

# [채팅방 목록] 채팅방 리스트 업데이트
@message_bp.route('/updateChatroomList')
def updateChatroomList():
    # Get all accounts from service
    accounts = account_service.get_all_accounts()

    # Get all chatroom tables from service
    chatroom_table_list = message_service.get_all_chatroom_tables()

    chatroomList = []

    for chatroom_table in chatroom_table_list:
        # Extract table ID from chatroom_table string
        if isinstance(chatroom_table, str):
            table_id = int(chatroom_table.split('_')[1])  # chatroom_123 → 123
            chatroom_data = message_service.get_chatroom_by_id(table_id)
        else:
            chatroom_data = chatroom_table  # Already a dictionary, use as is

        # Skip if no chatroom data
        if not chatroom_data:
            continue

        for account in accounts:
            # Match user_id with admin_id
            if ('user_id' in account and account['user_id'] > 0 and 
                'admin_id' in chatroom_data and chatroom_data['admin_id'] == account['user_id']):
                
                # Get messages for this chatroom
                messageList = message_service.get_messages_by_chatroom_id(table_id)

                # Add to chatroom list if messages exist
                if messageList:
                    # Check if there are any unread messages in this chatroom
                    has_unread_messages = any(msg.get('seen', 1) == 0 for msg in messageList)
                    
                    chatroom_data = {
                        'email': account['email'],
                        'user_id': account['user_id'],
                        'messages': messageList, 
                        'chatroom_id': table_id,
                        'has_unread_messages': has_unread_messages  # Add flag for unread messages
                    }
                    chatroomList.append(chatroom_data)

    # Process each chatroom to find the most recent message date
    for chatroom in chatroomList:
        messages = chatroom['messages']
        if messages:
            # Try to find the most recent message date
            # Assuming each message has a 'date' field in a format that can be sorted
            try:
                # Sort messages by date (assuming newer dates are "greater")
                # Convert string dates to comparable format if needed
                latest_message = max(messages, key=lambda msg: msg.get('date', ''))
                chatroom['latest_date'] = latest_message.get('date', '')
            except (TypeError, ValueError):
                # Fallback if date comparison fails
                chatroom['latest_date'] = ''
        else:
            chatroom['latest_date'] = ''

    # Sort the chatroomList:
    # 1. Chatrooms with unread messages (bell emoji) appear first
    # 2. Within each group (unread/read), sort by most recent date
    chatroomList.sort(key=lambda x: (
        not x['has_unread_messages'],  # Unread messages first
        '' if not x['latest_date'] else str(x['latest_date']),  # Then by date (descending)
    ), reverse=True)  # Reverse for descending date order (newest first)

    return jsonify(chatroomList)


# [대화] 상대방이 안읽은 메세지 -> 읽은 메세지로 업데이트
@message_bp.route('/updateClientUnreadMessage', methods=['POST'])
def updateClientUnreadMessageToReadMessage():
    try:
        data = request.json
        chatroom_id = data.get('chatroom_id')
        
        if not chatroom_id:
            return jsonify({"success": False, "message": "채팅방 ID가 필요합니다."}), 400
                   
        # 채팅방의 모든 메시지를 읽음 처리
        success = message_service.update_unread_messages(chatroom_id)
        
        if success:
            return jsonify({"success": True, "message": "메시지가 읽음 처리되었습니다."})
        else:
            return jsonify({"success": False, "message": "메시지 읽음 처리에 실패했습니다."})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"서버 내부 오류: {str(e)}"}), 500


# [대화] 웹으로 메세지 보내기
@message_bp.route('/sendMessageInWeb', methods=['POST'])
def sendMessageInWeb():
    try:
        data = request.json
        chatroom_id = data.get('chatroom_id')
        admin_id = data.get('admin_id')
        client_id = data.get('client_id')
        text = data.get('text')

         # 필수 파라미터 검증
        if not all([chatroom_id, admin_id, client_id, text]):
            return jsonify({
                'success': False, 
                'message': '모든 필드(chatroom_id, admin_id, client_id, text)가 필요합니다.'
            }), 400

        # Get accounts from service
        accountList = account_service.get_all_accounts()
        
        for account in accountList:
            try:
                admin_id = int(admin_id)
                account_user_id = int(account['user_id'])
            except ValueError as e:
                print(f"ID 변환 오류: {e}")
                continue  # Skip this account on conversion error

            if admin_id == account_user_id:
                # 1) Login to Kmong
                selenium.login(account['email'], 
                                     account['password'])

                # 2) Navigate to chatroom
                selenium.getClientChatRoom(chatroom_id=chatroom_id, client_id=client_id)

                # 3) Create message DTO and send message
                dto = MessageDTO(
                    admin_id=admin_id,
                    text=text,
                    client_id=client_id,
                    sender_id=admin_id,
                    replied_kmong=1,
                    replied_telegram=0,
                    seen=0,
                    kmong_message_id=0,
                    date=date.today()
                )
                
                selenium.send_message(
                    message=text, 
                    dto=dto,
                    chatroomID=chatroom_id
                )
            
                return jsonify({'success': True, 'message': '메시지가 전송되었습니다.'})
                
        return jsonify({'success': False, 'message': '해당 admin_id의 계정을 찾을 수 없음'})
    
    except Exception as e:
        print(f"메시지 전송 중 오류: {e}")
        return jsonify({'success': False, 'message': f'메시지 전송에 실패했습니다: {str(e)}'})


# [대화] 이전 대화기록 불러오기
@message_bp.route('/syncChatHistory', methods=['POST'])
def syncChatHistory():
    try:
        data = request.json
        chatroom_id = data.get('chatroom_id')
        admin_id = data.get('admin_id')
        client_id = data.get('client_id')

        # Validate required fields
        if not all([chatroom_id, admin_id, client_id]):
            return jsonify({'success': False, 'message': '필수 필드가 누락되었습니다.'})

        # Get accounts from service
        accountList = account_service.get_all_accounts()

        for account in accountList:
            try:
                admin_id = int(admin_id)
                account_user_id = int(account['user_id'])
            except ValueError as e:
                print(f"ID 변환 오류: {e}")
                continue  # Skip this account on conversion error

            if admin_id == account_user_id:
                # Login to Kmong
                selenium.login(account['email'],account['password'])

                # Navigate to chatroom
                selenium.getClientChatRoom(chatroom_id=chatroom_id, client_id=client_id)

                # Get chat history
                chat_history = selenium.getChatHistory(admin_id=admin_id)
                
                # Use message service to sync chat history
                success, message = message_service.sync_chat_history(chatroom_id, chat_history)
                
                selenium.close_driver()
                return jsonify({'success': success, 'message': message})
                
        return jsonify({'success': False, 'message': '해당 admin_id의 계정을 찾을 수 없음'})
    
    except Exception as e:
        print(f"채팅 내역 동기화 중 오류: {e}")
        return jsonify({'success': False, 'message': f'채팅 내역 동기화에 실패했습니다: {str(e)}'})


# ChatGPT 답변 추천 
@message_bp.route('/get_gpt_suggestions', methods=['POST'])
def get_gpt_suggestions():
 
    data = request.get_json()  # JSON 데이터 받기
    response_type = data.get("type")
    chatroom_id = data.get("chatroom_id")

    if not chatroom_id:
        return jsonify({"error": "chatroom_id is required"}), 400

    # ✅ GPT 학습용 데이터 가져오기
    qna_data = chatGPT.fetch_predefined_qna(chatroom_id)

    # ✅ 현재 대화 내역을 conversation에 저장
    conversation = qna_data["current_conversation"]

    # ✅ GPT로 답변 생성
    answer = chatGPT.generate_response(conversation, response_type)

    return jsonify({"answer": answer})
