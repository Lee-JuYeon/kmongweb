import sqlite3
from datetime import datetime
from model.account_dto import AccountDTO

def dict_factory(cursor, row):
    contents = {}
    for idx, col in enumerate(cursor.description):
        contents[col[0]] = row[idx]
    return contents

def get_connect_db():
    conn = sqlite3.connect("db_kmong_checker2.db")
    return conn

def check_account_table_exists():
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = """SELECT name FROM sqlite_master WHERE type='table' AND name='account_table'"""
    cursor.execute(sql)
    table_exists = cursor.fetchone() is not None

    cursor.close()
    conn.close()

    return table_exists

def create_account_table():
    conn = get_connect_db()
    cursor = conn.cursor()
    # 'index'를 'idx'로 변경
    sql = """CREATE TABLE IF NOT EXISTS account_table (
                idx INTEGER PRIMARY KEY AUTOINCREMENT,  -- 'index'를 'idx'로 변경
                email TEXT UNIQUE NOT NULL, 
                password TEXT NOT NULL,
                login_cookie TEXT,
                user_id INTEGER DEFAULT 0
            )"""
    cursor.execute(sql)
    conn.commit()
    conn.close()

def create_account(account_dto: AccountDTO):
    conn = get_connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM account_table WHERE email = ?", (account_dto.email,))
    count = cursor.fetchone()[0]

    if count == 0:  # 중복이 없을 때만 INSERT
        sql = """INSERT INTO account_table (email, password, login_cookie, user_id)
                 VALUES (?, ?, ?, ?)"""
        cursor.execute(sql, (account_dto.email, account_dto.password, account_dto.login_cookie, account_dto.user_id))
        conn.commit()
        print(f"✅ 계정 저장 완료: {account_dto.email}")
    else:
        print(f"⚠️ 중복된 이메일 존재: {account_dto.email}")

    cursor.close()
    conn.close()



def read_account_by_email(email):
    conn = get_connect_db()
    cursor = conn.cursor()

    sql = "SELECT * FROM account_table WHERE email = ?"
    cursor.execute(sql, (email,))
    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None

def read_all_accounts():
    conn = get_connect_db()
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    sql = "SELECT * FROM account_table"
    cursor.execute(sql)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows  # ✅ dict 형태로 반환됨

# 데이터 업데이트
def update_account(email, password=None, login_cookie=None, user_id=None):
    conn = get_connect_db()
    cursor = conn.cursor()

    update_fields = []
    data = {'email': email}

    if password:
        update_fields.append("password = :password")
        data['password'] = password
    if login_cookie:
        update_fields.append("login_cookie = :login_cookie")
        data['login_cookie'] = login_cookie
    if user_id:
        update_fields.append("user_id = :user_id")
        data['user_id'] = user_id

    # 필드가 존재하면 업데이트
    if update_fields:
        update_query = ", ".join(update_fields)
        sql = f"UPDATE account_table SET {update_query} WHERE email = :email"
        cursor.execute(sql, data)
        conn.commit()

    cursor.close()
    conn.close()

def delete_account(email):
    conn = get_connect_db()
    cursor = conn.cursor()

    data = {'email': email}
    sql = "DELETE FROM account_table WHERE email = :email"
    cursor.execute(sql, data)
    conn.commit()

    cursor.close()
    conn.close()