import sqlite3
from datetime import datetime
from model.message_dto import MessageDTO

def dict_factory(cursor, row):
    contents = {}
    for idx, col in enumerate(cursor.description):
        contents[col[0]] = row[idx]
    return contents

def get_connect_db():
    conn = sqlite3.connect("db_kmong_checker2.db")
    return conn

def check_chatroom_table_exists(table_id: int): 
    table_name = f"chatroom_{table_id}"
    conn = get_connect_db()
    cursor = conn.cursor()
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    cursor.execute(sql, (table_name,))
    table_exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return table_exists

def create_chatroom_table(table_id: int):
    table_name = f"chatroom_{table_id}"
    conn = get_connect_db()
    cursor = conn.cursor()
    sql = f"""CREATE TABLE IF NOT EXISTS {table_name} (
                idx INTEGER PRIMARY KEY AUTOINCREMENT, 
                admin_id INTEGER DEFAULT 0, 
                text TEXT DEFAULT '', 
                client_id INTEGER DEFAULT 0, 
                sender_id INTEGER DEFAULT 0, 
                replied_kmong INTEGER DEFAULT 0, 
                replied_telegram INTEGER DEFAULT 0, 
                seen INTEGER DEFAULT 0,
                kmong_message_id INTEGER DEFAULT 0,
                date DATE DEFAULT CURRENT_DATE
            )"""
    cursor.execute(sql)
    conn.commit()
    conn.close()

def create_message(table_id: int, message_dto: MessageDTO):
    table_name = f"chatroom_{table_id}"
    conn = get_connect_db()
    cursor = conn.cursor()
    sql = f"""INSERT INTO {table_name} 
              (admin_id, text, client_id, sender_id, replied_kmong, replied_telegram, seen, kmong_message_id, date)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    cursor.execute(sql, (message_dto.admin_id, message_dto.text, message_dto.client_id,
                         message_dto.sender_id, message_dto.replied_kmong, message_dto.replied_telegram, 
                         message_dto.seen, message_dto.kmong_message_id, message_dto.date))
    conn.commit()
    cursor.close()
    conn.close()

def read_chatroom_by_id(table_id: int):
    """ 특정 채팅방 정보 조회 """
    table_name = f"chatroom_{table_id}"
    conn = get_connect_db()
    conn.row_factory = dict_factory  # ✅ 딕셔너리로 반환하도록 설정
    cursor = conn.cursor()

    sql = f"SELECT * FROM {table_name} LIMIT 1"
    cursor.execute(sql)
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return row  # ✅ dict 형태로 반환됨


def read_all_chatroom_tables():
    """ chatroom_으로 시작하는 모든 테이블 조회 """
    conn = get_connect_db()
    cursor = conn.cursor()

    # 'chatroom_'으로 시작하는 테이블 이름 조회
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chatroom_%';"
    cursor.execute(sql)

    # 결과 가져오기
    chatroom_tables = cursor.fetchall()

    cursor.close()
    conn.close()

    # 테이블 이름만 리스트로 반환
    return [table[0] for table in chatroom_tables]

# 특정 메시지 조회 (READ)
def read_message_by_id(table_id: int, message_id: int):
    """ 메시지 ID로 조회 """
    table_name = f"chatroom_{table_id}"
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = f"SELECT * FROM {table_name} WHERE idx = ?"
    cursor.execute(sql, (message_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


# 전체 메시지 목록 조회 (READ)
def read_all_messages(table_id: int):
    """ 모든 메시지 조회 - 테이블이 없는 경우 자동 생성 """
    table_name = f"chatroom_{table_id}"
    conn = None
    cursor = None
    
    try:
        # 먼저 테이블이 존재하는지 확인
        if not check_chatroom_table_exists(table_id):
            print(f"테이블 {table_name}이 존재하지 않습니다. 자동으로 생성합니다.")
            create_chatroom_table(table_id)
        
        # 메시지 조회 시작
        conn = get_connect_db()
        conn.row_factory = dict_factory  # 결과를 딕셔너리 형태로 변환
        cursor = conn.cursor()

        sql = f"SELECT * FROM {table_name} ORDER BY date DESC"
        cursor.execute(sql)
        rows = cursor.fetchall()

        return rows  # 모든 메시지를 dict 형태로 반환
    
    except sqlite3.Error as e:
        print(f"메시지 조회 중 오류 발생 (테이블 ID: {table_id}): {str(e)}")
        return []  # 오류 발생 시 빈 리스트 반환
    
    finally:
        # 연결 자원 해제
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_message(table_id: int, message_id: int, text=None, replied_kmong=None, replied_telegram=None, seen=None, kmong_message_id=None):
    """ 메시지 업데이트 """
    table_name = f"chatroom_{table_id}"
    conn = get_connect_db()
    cursor = conn.cursor()

    update_fields = []
    data = {'message_id': message_id}

    if text is not None:
        update_fields.append("text = :text")
        data['text'] = text
    if replied_kmong is not None:
        update_fields.append("replied_kmong = :replied_kmong")
        data['replied_kmong'] = replied_kmong
    if replied_telegram is not None:
        update_fields.append("replied_telegram = :replied_telegram")
        data['replied_telegram'] = replied_telegram
    if seen is not None:
        update_fields.append("seen = :seen")
        data['seen'] = seen
    if kmong_message_id is not None:
        update_fields.append("kmong_message_id = :kmong_message_id")
        data['kmong_message_id'] = kmong_message_id

    if update_fields:
        update_query = ", ".join(update_fields)
        sql = f"UPDATE {table_name} SET {update_query} WHERE idx = :message_id"
        cursor.execute(sql, data)
        conn.commit()

    cursor.close()
    conn.close()

# db_message.py
def update_unread_message(table_id: int):
    """읽지 않은 메시지(seen == 0) 업데이트"""
    table_name = f"chatroom_{table_id}"
    conn = get_connect_db()
    cursor = conn.cursor()

    # 읽지 않은 메시지 조건 (seen == 0, client_id == sender_id)
    sql = f"""
        UPDATE {table_name} 
        SET seen = 1 
        WHERE seen = 0 AND client_id = sender_id
    """
    cursor.execute(sql)
    conn.commit()

    cursor.close()
    conn.close()

def delete_all_messages(table_id: int):
    """ 모든 메시지 삭제 """
    table_name = f"chatroom_{table_id}"
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = f"DELETE FROM {table_name}"
    cursor.execute(sql)
    conn.commit()

    cursor.close()
    conn.close()

def delete_chatroom_table(table_id: int):
    """ 채팅방 테이블 삭제 """
    table_name = f"chatroom_{table_id}"
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = f"DROP TABLE IF EXISTS {table_name}"
    cursor.execute(sql)
    conn.commit()

    cursor.close()
    conn.close()

def add_missing_columns_to_all_chatrooms():
    """ 모든 chatroom_ 테이블에 'seen'과 'kmong_message_id' 컬럼 추가 """
    conn = get_connect_db()
    cursor = conn.cursor()

    # 'chatroom_'으로 시작하는 모든 테이블 찾기
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'chatroom_%';")
    chatroom_tables = cursor.fetchall()

    for table in chatroom_tables:
        table_name = table[0]

        # 해당 테이블의 컬럼 목록 가져오기
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]

        # seen 컬럼 추가
        if "seen" not in columns:
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN seen INTEGER DEFAULT 0;"
            cursor.execute(alter_sql)
            print(f"✅ {table_name} 테이블에 'seen' 컬럼 추가 완료!")

        # kmong_message_id 컬럼 추가
        if "kmong_message_id" not in columns:
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN kmong_message_id INTEGER DEFAULT 0;"
            cursor.execute(alter_sql)
            print(f"✅ {table_name} 테이블에 'kmong_message_id' 컬럼 추가 완료!")

    conn.commit()
    cursor.close()
    conn.close()

