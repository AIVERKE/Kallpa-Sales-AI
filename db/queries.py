from db.connection import get_connection

def save_ai_interaction(user_id, customer_id, prompt, response):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO ai_interactions (telegram_user_id, customer_id, type, prompt, response)
    VALUES (%s, %s, %s, %s, %s)
    """, (user_id, customer_id, "chat", prompt, response))
    conn.commit()
    cur.close()
    conn.close()
