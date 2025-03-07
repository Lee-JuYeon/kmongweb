import contextlib
import sqlite3
from datetime import datetime

def dict_factory(cursor, row):
    contents = {}
    for idx, col in enumerate(cursor.description):
        contents[col[0]] = row[idx]
    return contents

def get_connect_db():
    conn = sqlite3.connect("db_kmong_checker2.db")
    return conn

def create_db():
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = """CREATE TABLE IF NOT EXISTS tb_kmong_message (
            idx INTEGER PRIMARY KEY,
            userid TEXT UNIQUE,
            passwd TEXT,
            message_id INTEGER,
            last_noti_message_id INTEGER,
            message_count INTEGER,
            message_content TEXT,
            login_cookie TEXT,
            check_date DATETIME,
            tele_chat_room_id INTEGER DEFAULT 0,
            tele_chat_is_send INTEGER DEFAULT 0,
            tele_chat_reply INTEGER DEFAULT 0
        )"""
    cursor.execute(sql)

     # ✅ 기존 테이블에서 컬럼 정보 가져오기
    cursor.execute("PRAGMA table_info(tb_kmong_message)")
    columns = [column[1] for column in cursor.fetchall()]

    # ✅ 필요한 컬럼이 없으면 추가
    new_columns = {
        "tele_chat_room_id": "INTEGER DEFAULT 0",
        "tele_chat_is_send": "INTEGER DEFAULT 0",
        "tele_chat_reply": "INTEGER DEFAULT 0"
    }

    for column, column_type in new_columns.items():
        if column not in columns:
            alter_query = f"ALTER TABLE tb_kmong_message ADD COLUMN {column} {column_type}"
            cursor.execute(alter_query)
            print(f"추가된 칼럼 : {column}")
            
    conn.commit()
    conn.close()

def select_message_tot_count():
    conn = get_connect_db()
    conn.row_factory = dict_factory
    cur = conn.cursor()

    sql = "SELECT SUM(message_count) AS sum_message_count FROM tb_kmong_message"
    cur.execute(sql)

    row = cur.fetchone()

    cur.close()
    conn.close()

    count = row.get("sum_message_count", 0)

    if count == None:
        count = 0

    return count

def select_message(userid):
    conn = get_connect_db()
    conn.row_factory = dict_factory
    cur = conn.cursor()

    data = {"userid": userid}
    sql = "SELECT * FROM tb_kmong_message WHERE userid = :userid"
    cur.execute(sql, data)

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row

def delete_message(userid):
    conn = get_connect_db()
    cur = conn.cursor()

    data = {"userid": userid}
    sql = "DELETE FROM tb_kmong_message WHERE userid = :userid"
    cur.execute(sql, data)
    conn.commit()

    cur.close()
    conn.close()

def select_message_list():
    conn = get_connect_db()
    conn.row_factory = dict_factory
    cur = conn.cursor()

    sql = "SELECT * FROM tb_kmong_message ORDER BY userid ASC"
    cur.execute(sql)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    # check_date 값이 문자열로 되어 있으면 날짜 객체로 변환
    for row in rows:
        if row.get("check_date"):
            row["check_date"] = datetime.strptime(row["check_date"], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        else:
            row["check_date"] = ""

    return rows



def insert_message(userid, passwd, login_cookie):
    conn = get_connect_db()
    cur = conn.cursor()

    data = {}
    data['userid'] = userid
    data['passwd'] = passwd
    data['login_cookie'] = login_cookie
    data['check_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    sql = "INSERT INTO tb_kmong_message (userid, passwd, login_cookie, message_id, message_count, message_content" \
          ", last_noti_message_id, check_date)" \
          "VALUES (:userid, :passwd, :login_cookie, 0, 0, '', 0, :check_date)"

    cur.execute(sql, data)
    conn.commit()

    cur.close()
    conn.close()

def update_message(userid, passwd, login_cookie, message_count, message_id, message_content):
    conn = get_connect_db()
    cur = conn.cursor()

    data = {}
    data['userid'] = userid
    data['passwd'] = passwd
    data['login_cookie'] = login_cookie
    data['message_id'] = message_id
    data['message_count'] = message_count
    data['message_content'] = message_content

    sql = "UPDATE tb_kmong_message SET passwd = :passwd, message_id = :message_id, login_cookie = :login_cookie" \
          ", message_count = :message_count, message_content = :message_content" \
          " WHERE userid = :userid"

    cur.execute(sql, data)
    conn.commit()

    cur.close()
    conn.close()


def update_last_noti_message(userid, message_id):
    conn = get_connect_db()
    cur = conn.cursor()

    data = {'userid': userid, 'message_id': message_id}

    sql = "UPDATE tb_kmong_message SET last_noti_message_id = :message_id WHERE userid = :userid"

    cur.execute(sql, data)
    conn.commit()

    cur.close()
    conn.close()

def update_tele_chat_room_id(userid, tele_chat_room_id, tele_chat_is_send):
    
    conn = get_connect_db()
    cur = conn.cursor()
    
    sql = """
    UPDATE tb_kmong_message 
    SET tele_chat_room_id = ?, tele_chat_is_send = ? 
    WHERE userid = ?
    """
    cur.execute(sql, (tele_chat_room_id, tele_chat_is_send, userid))
    conn.commit()
    
    cur.close()
    conn.close()

################ 메세지 테이블
# 테이블 생성 함수
def create_message_table():
    conn = get_connect_db()
    cursor = conn.cursor()
    # replied -> replied_telegram = 현재 텔레그램에서 답장기능을 통해 답장을 했는지?를 묻는상태.
    # replied_kmong = 실제 크몽서버로도 답장을 보냈는지? (텔레그램과 커스텀웹에서만 통신해봤자 실제 크몽서버와는 무관하여 통신이 연결되지 않음.)
    # from_user_id = 누구로부터 온 메세지인지 알아아야함. (현재 텔레그램 챗방은 단 하나임. 그래서 누구로부터 온 메세지인지 id값을 통해 카톡 메세지처럼 따로 구현할수있음)
    sql = """CREATE TABLE IF NOT EXISTS tb_messages (
                message_id INTEGER PRIMARY KEY, 
                chat_id INTEGER NOT NULL,        
                user_id INTEGER NOT NULL,        
                first_name TEXT,                 
                last_name TEXT,                  
                username TEXT,                   
                text TEXT NOT NULL,              
                date INTEGER NOT NULL,           
                replied BOOLEAN DEFAULT FALSE   
            )"""
    cursor.execute(sql)
    conn.commit()
    conn.close()


# 메시지 삽입 (CREATE)
def insert_message(message_id, chat_id, user_id, first_name, last_name, username, text, date, replied):
    conn = get_connect_db()
    cur = conn.cursor()

    # ✅ 중복 확인
    cur.execute("SELECT COUNT(*) FROM tb_messages WHERE message_id = ?", (message_id,))
    count = cur.fetchone()[0]

    if count == 0:  # ✅ 중복이 없을 때만 INSERT
        sql = """
        INSERT INTO tb_messages (message_id, chat_id, user_id, first_name, last_name, username, text, date, replied)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cur.execute(sql, (message_id, chat_id, user_id, first_name, last_name, username, text, date, replied))
        conn.commit()
        print(f"✅ 메시지 저장 완료: {message_id}")
    else:
        print(f"⚠️ 중복된 메시지 존재: {message_id}")

    cur.close()
    conn.close()


# 특정 메시지 조회 (READ)
def get_message_by_id(message_id):
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = "SELECT * FROM tb_messages WHERE message_id = ?"
    cursor.execute(sql, (message_id,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None

# 전체 메시지 목록 조회 (READ)
def get_all_messages():
    conn = get_connect_db()
    conn.row_factory = dict_factory  # ✅ dict 형태로 변환
    cur = conn.cursor()

    sql = "SELECT * FROM tb_messages"
    cur.execute(sql)
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows  # ✅ dict 형태로 반환됨


# 메시지 답변 상태 업데이트 (UPDATE)
def update_message_replied(message_id, replied=True):
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = "UPDATE tb_messages SET replied = ? WHERE message_id = ?"
    cursor.execute(sql, (replied, message_id))
    conn.commit()
    conn.close()

# 특정 메시지 삭제 (DELETE)
def delete_message(message_id):
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = "DELETE FROM tb_messages WHERE message_id = ?"
    cursor.execute(sql, (message_id,))
    conn.commit()
    conn.close()

# 전체 메시지 삭제 (DELETE)
def delete_all_chat_messages():
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = "DELETE FROM tb_messages"
    cursor.execute(sql)
    conn.commit()
    conn.close()