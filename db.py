# ---------- db.py ----------
import psycopg2
from psycopg2 import sql

def connect_to_db(db_params):
    try:
        return psycopg2.connect(**db_params)
    except psycopg2.Error as e:
        messagebox.showerror("Ошибка БД", f"Ошибка подключения к базе данных:\n{str(e)}")
        return None

def execute_query(conn, query, params=None):
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            conn.commit()
            return True
    except psycopg2.Error as e:
        conn.rollback()
        messagebox.showerror("Ошибка БД", f"Ошибка выполнения запроса:\n{str(e)}")
        return None