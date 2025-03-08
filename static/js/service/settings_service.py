import os
import json
import logging

class SettingsService:
    
    def __init__(self):
        """Initialize SettingsService with default settings"""
        self.settings_file = 'settings.json'
        self.default_settings = {
            'refreshInterval': {
                'parseUnReadMessagesinDB': 30,  # 기본값 25-35초
                'sendUnReadMessagesViaTelebot': 30,  # 기본값 25-35초
                'replyViaTeleBot': 10  # 기본값 8-12초
            },
            'telegram': {
                'botToken': '',
                'chatId': ''
            }
        }
        # 로깅 설정
        self.logger = logging.getLogger(__name__)
        self.settings = self._load_settings()
        
    def _load_settings(self):
        """Load settings from file or create with defaults if not exists"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # 설정이 모든 필수 키를 가지고 있는지 확인하고 없으면 기본값으로 보완
                    self._validate_and_complete_settings(loaded_settings)
                    return loaded_settings
            else:
                # 파일이 없으면 기본 설정 저장 후 반환
                self._save_settings(self.default_settings)
                return self.default_settings
        except Exception as e:
            self.logger.error(f"설정 로드 중 오류: {e}")
            return self.default_settings

    def _validate_and_complete_settings(self, settings):
        """설정에 필요한 키가 모두 있는지 확인하고 없으면 기본값으로 채움"""
        # refreshInterval 체크
        if 'refreshInterval' not in settings:
            settings['refreshInterval'] = self.default_settings['refreshInterval']
        else:
            for key in self.default_settings['refreshInterval']:
                if key not in settings['refreshInterval']:
                    settings['refreshInterval'][key] = self.default_settings['refreshInterval'][key]
        
        # telegram 설정 체크
        if 'telegram' not in settings:
            settings['telegram'] = self.default_settings['telegram']
        else:
            for key in self.default_settings['telegram']:
                if key not in settings['telegram']:
                    settings['telegram'][key] = self.default_settings['telegram'][key]    

        return settings
  
    def _save_settings(self, settings):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"설정 저장 중 오류: {e}")
            return False
    
    def get_settings(self):
        """Get current settings"""
        return self.settings
    
    def update_refresh_interval(self, interval):
        """Update refresh interval settings"""
        if not interval or not isinstance(interval, int) or interval < 5:
            return False, '유효하지 않은 간격 값입니다. 5초 이상의 값을 입력하세요.'
        
        try:
            logging.info(f"settings_service.py, update_refresh_interval // 갱신주기 업데이트: {interval}초")
            
            # 각 간격 업데이트
            self.settings['refreshInterval']['parseUnReadMessagesinDB'] = interval
            self.settings['refreshInterval']['sendUnReadMessagesViaTelebot'] = interval
            self.settings['refreshInterval']['replyViaTeleBot'] = max(5, interval // 3)  # 빠른 작업과 느린 작업 간의 비율 유지
            
            logging.info(f"settings_service.py, update_refresh_interval // 업데이트된 설정: {self.settings['refreshInterval']}")
            
            # 설정 저장
            if self._save_settings(self.settings):
                logging.info("settings_service.py, update_refresh_interval // ✅ 갱신주기 저장 성공")
                return True, '갱신주기가 업데이트되었습니다.'
            else:
                logging.error("settings_service.py, update_refresh_interval // ⛔ 갱신주기 저장 실패")
                return False, '갱신주기 저장 중 오류가 발생했습니다.'
        except Exception as e:
            logging.error(f"settings_service.py, update_refresh_interval // ⛔ 갱신주기 업데이트 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False, f'갱신주기 업데이트에 실패했습니다: {str(e)}'
    
    def update_telegram_settings(self, token, chat_id):
        """Update Telegram bot settings"""
        if not token or not chat_id:
            return False, '텔레그램 봇 토큰과 채팅 ID가 필요합니다.'
        
        try:
            # 텔레그램 설정 업데이트
            self.settings['telegram']['botToken'] = token
            self.settings['telegram']['chatId'] = chat_id
            
            # 설정 저장
            if self._save_settings(self.settings):
                return True, '텔레그램 설정이 업데이트되었습니다.'
            else:
                return False, '텔레그램 설정 저장 중 오류가 발생했습니다.'
        except Exception as e:
            print(f"텔레그램 설정 업데이트 중 오류: {e}")
            return False, f'텔레그램 설정 업데이트에 실패했습니다: {str(e)}'
        

    def get_telegram_settings(self):
        """텔레그램 설정 가져오기"""
        return {
            'botToken': self.settings['telegram'].get('botToken', ''),
            'chatId': self.settings['telegram'].get('chatId', '')
        }
        
    def check_telegram_settings_valid(self):
        """현재 텔레그램 설정이 유효한지 확인"""
        token = self.settings['telegram'].get('botToken', '')
        chat_id = self.settings['telegram'].get('chatId', '')
            
        return bool(token and chat_id)