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

def get_memory(telegram_user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, negocio, canal_venta, zona, mensajes_diarios,
               dolor_principal, interes, ultima_objecion, estado_embudo, last_message
        FROM memory
        WHERE telegram_user_id = %s
    """, (telegram_user_id,))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def save_memory(telegram_user_id, field, value):
    conn = get_connection()
    cur = conn.cursor()

    # Si el registro no existe, lo creamos
    cur.execute("""
        INSERT INTO memory (telegram_user_id, {0})
        VALUES (%s, %s)
        ON CONFLICT (telegram_user_id)
        DO UPDATE SET {0} = EXCLUDED.{0}, updated_at = CURRENT_TIMESTAMP;
    """.format(field), (telegram_user_id, value))

    conn.commit()
    cur.close()
    conn.close()
