from flask import Blueprint, request, jsonify
from datetime import date

from static.js.service.message_service import MessageService
from static.js.service.account_service import AccountService
from static.js.service.settings_service import SettingsService

from utils.telegram_manager.legacy_telegram_manager import LegacyTelegramManager
from utils.selenium_manager.selenium_manager import SeleniumManager
from utils.gpt_manager.gpt_manager import GPTManager
from dummy.dummySingleton import DummySingleton


# Blueprint 생성
settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')

# 인스턴스 생성
message_service = MessageService()
account_service = AccountService()
settings_service = SettingsService()

chatGPT = GPTManager()
selenium = SeleniumManager()
dummy = DummySingleton()
telegram = LegacyTelegramManager()

# 엔드포인트: 설정 관련
@settings_bp.route('/loadSettings')
def load_settings_endpoint():
    """현재 설정 반환"""
    settings = settings_service.get_settings()
    return jsonify(settings)

@settings_bp.route('/updateRefreshInterval', methods=['POST'])
def update_refresh_interval():
    """메시지 갱신주기 업데이트 엔드포인트"""
    try:
        data = request.json
        interval = data.get('interval')
        
        # 입력값 검증
        if not interval or not isinstance(interval, int) or interval < 5:
            return jsonify({
                'success': False, 
                'message': '유효하지 않은 간격 값입니다. 5초 이상의 값을 입력하세요.'
            }), 400

        # 설정 업데이트
        success, message = settings_service.update_refresh_interval(interval)
        
        if success:
            # 스케줄러 재설정 - app.py에서 정의된 함수 호출
            from app import refresh_scheduler
            refresh_scheduler()
            
        return jsonify({
            'success': success, 
            'message': message, 
            'interval': interval
        })
    
    except Exception as e:
        print(f"갱신주기 업데이트 중 오류: {e}")
        return jsonify({'success': False, 'message': f'갱신주기 업데이트에 실패했습니다: {str(e)}'}), 500

@settings_bp.route('/updateTelegramSettings', methods=['POST'])
def update_telegram_settings():
    """텔레그램 봇 설정 업데이트 엔드포인트"""
    try:
        data = request.json
        token = data.get('token')
        chat_id = data.get('chatId')
        
        # 입력값 검증
        if not token or not chat_id:
            return jsonify({
                'success': False, 
                'message': '텔레그램 봇 토큰과 채팅 ID가 필요합니다.'
            }), 400
            
        # 설정 업데이트
        success, message = settings_service.update_telegram_settings(token, chat_id)
        
        if success:
            # TelegramManager 인스턴스 업데이트 및 초기화
            from app import init_telegram
            
            # 텔레그램 봇 초기화
            update_result = init_telegram()
            
            if update_result:
                try:
                    # 테스트 메시지 전송
                    telegram.send_message(
                        email="시스템", 
                        messageCount=0, 
                        message="✅ 텔레그램 봇 설정이 성공적으로 업데이트되었습니다."
                    )
                    
                    # 스케줄러 재설정
                    from app import refresh_scheduler
                    refresh_scheduler()
                    
                except Exception as e:
                    print(f"텔레그램 봇 설정 적용 중 오류: {e}")
                    return jsonify({
                        'success': False, 
                        'message': f'텔레그램 봇 설정이 저장되었지만, 적용 중 오류가 발생했습니다: {str(e)}'
                    })
            else:
                return jsonify({
                    'success': False, 
                    'message': '텔레그램 봇 설정이 저장되었지만, 봇 초기화에 실패했습니다.'
                })
                
        return jsonify({
            'success': success, 
            'message': message
        })
        
    except Exception as e:
        print(f"텔레그램 설정 업데이트 중 오류: {e}")
        return jsonify({'success': False, 'message': f'텔레그램 설정 업데이트에 실패했습니다: {str(e)}'}), 500

@settings_bp.route('/testTelegramMessage', methods=['POST'])
def test_telegram_message():
    """텔레그램 봇 테스트 메시지 전송"""
    try:
        # 요청에서 테스트 메시지 가져오기 (기본값 설정)
        data = request.json
        test_message = data.get('message', '🔔 이것은 테스트 메시지입니다.')
        
        # 메시지 전송
        result = telegram.send_message(
            email="테스트",
            messageCount=0,
            message=test_message
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': '테스트 메시지가 성공적으로 전송되었습니다.'
            })
        else:
            return jsonify({
                'success': False,
                'message': '메시지 전송에 실패했습니다. 텔레그램 봇 설정을 확인하세요.'
            })
    
    except Exception as e:
        print(f"텔레그램 테스트 메시지 전송 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'텔레그램 테스트 메시지 전송 중 오류가 발생했습니다: {str(e)}'
        }), 500

@settings_bp.route('/startReplyPolling', methods=['POST'])
def start_reply_polling():
    """텔레그램 답장 폴링 시작"""
    try:
        # 폴링 간격 (기본 5초)
        data = request.json
        interval = data.get('interval', 5)
        
        # 답장 폴링 시작
        from app import replyByTelegram
        
        def on_reply_callback(reply_info):
            """답장 수신 시 호출될 콜백 함수"""
            try:
                replyByTelegram()
            except Exception as e:
                print(f"답장 처리 콜백 오류: {str(e)}")
        
        telegram.start_reply_polling(interval=interval, callback=on_reply_callback)
        
        return jsonify({
            'success': True,
            'message': f'텔레그램 답장 폴링이 시작되었습니다. (간격: {interval}초)'
        })
        
    except Exception as e:
        print(f"텔레그램 답장 폴링 시작 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'텔레그램 답장 폴링 시작 중 오류가 발생했습니다: {str(e)}'
        }), 500

@settings_bp.route('/stopReplyPolling', methods=['POST'])
def stop_reply_polling():
    """텔레그램 답장 폴링 중지"""
    try:
        telegram.stop_reply_polling()
        
        return jsonify({
            'success': True,
            'message': '텔레그램 답장 폴링이 중지되었습니다.'
        })
        
    except Exception as e:
        print(f"텔레그램 답장 폴링 중지 중 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'텔레그램 답장 폴링 중지 중 오류가 발생했습니다: {str(e)}'
        }), 500