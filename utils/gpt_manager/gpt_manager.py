from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
from utils.kmong_checker.db_message import read_all_chatroom_tables, read_all_messages
from collections import defaultdict
import os

# 환경 변수 로드
load_dotenv()
openai_api_key = os.getenv('openai_api_key')

class GPTManager:
    def __init__(self):
        load_dotenv()  # 환경 변수 로드
        openai_api_key = os.getenv('openai_api_key')

        if not openai_api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")

        self.client = OpenAI(api_key=openai_api_key)
    
    def fetch_predefined_qna(self, table_id: int):
        """이전 대화를 학습하고, 현재 대화 내용을 바탕으로 AI가 추천 답변을 생성"""
        predefined_qna = defaultdict(list)
        chatroom_tables = read_all_chatroom_tables()

        for table_name in chatroom_tables:
            table_id = int(table_name.replace("chatroom_", ""))
            messages = read_all_messages(table_id)
            
            conversation_history = []
            prev_sender = None
            
            for message in messages:
                client_id = message["client_id"]
                sender_id = message["sender_id"]
                text = message["text"]
                
                is_client = client_id == sender_id
                role = "client" if is_client else "me"
                
                if prev_sender == sender_id:
                    conversation_history[-1].append(text)
                else:
                    conversation_history.append([text])
                
                predefined_qna[role].append(text)
                prev_sender = sender_id
        
        # 현재 채팅방 데이터 가져오기
        current_messages = read_all_messages(table_id)
        current_conversation = []
        
        for message in current_messages:
            client_id = message["client_id"]
            sender_id = message["sender_id"]
            text = message["text"]
            
            is_client = client_id == sender_id
            current_conversation.append({
                "role": "client" if is_client else "me",  # 기존 sender -> role 변경
                "content": text  # 기존 text -> content 변경
            })
        
        return {
            "training_data": predefined_qna,
            "current_conversation": current_conversation
        }
    
    def get_answer_from_gpt(self, prompt: str) -> str:
        """GPT를 사용하여 답변 생성"""
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return "답변을 생성하는 데 오류가 발생했습니다."
    
    def format_conversation(self, conversation: list) -> str:
        """대화 내용을 포맷하여 하나의 문자열로 변환"""
        if not conversation:
            return "대화 기록이 없습니다."
        
        return "\n".join([f"{msg.get('role', 'unknown')}: {msg.get('content', '내용 없음')}" for msg in conversation])
    
    def generate_response(self, conversation: list, response_type: str) -> str:
        """대화 유형에 따라 적절한 응답을 생성"""
        prompt_templates = {
            "positive_basic": "기본적인 긍정 답변: '예, 가능합니다.'",
            "positive_detailed": "상세한 긍정 답변: '예, 가능합니다. 이렇게 진행하면 해결됩니다.'",
            "negative_basic": "기본적인 거절 답변: '죄송하지만 처리할 수 없습니다.'",
            "negative_with_margin": "여지를 남기는 거절 답변: '현재 어렵지만, 추후 검토 가능합니다.'",
            "alternative_solution": "대체 가능한 방법 제시: '현재는 어렵지만, 이런 방법이 있습니다.'"
        }
        
        if response_type not in prompt_templates:
            raise ValueError(f"잘못된 response_type: {response_type}")

        full_prompt = f"""
        대화 내용: {self.format_conversation(conversation)}
        대답 시 고려할 사항:
        {prompt_templates[response_type]}
        """
        return self.get_answer_from_gpt(full_prompt)

    def return_answers(self, message_id: int, conversation: list):
        """대화를 기반으로 5개의 답변을 생성"""
        responses = {
            key: self.generate_response(conversation, key)
            for key in ["positive_basic", "positive_detailed", "negative_basic", "negative_with_margin", "alternative_solution"]
        }
        
        print(f"\n📩 Message ID: {message_id}에 대한 AI 답변 리스트 📩\n")
        for key, value in responses.items():
            print(f"🔹 {key.replace('_', ' ').title()}:\n{value}\n{'-'*50}")
        
        return responses

