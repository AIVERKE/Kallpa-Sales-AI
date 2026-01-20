import json
from openai import OpenAI
from src.core.config import settings
from src.domain.models import Customer, ChatSession

client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url=f"{settings.DEEPSEEK_BASE_URL}/v1"
)

async def get_ai_response(
    message: str,
    customer: Customer,
    session: ChatSession,
    product_context: str = "",
    delivery_context: str = "",
    history: list = []
) -> str:
    """
    Generates a response using the LLM, injecting customer memory and context.
    """

    # 1. Build Memory Context
    memory_context = f"""
    Cliente: {customer.full_name or 'Desconocido'}
    ID Cliente: {customer.id}
    Estado: {customer.status}
    Contexto Sesión: {json.dumps(session.context_data, ensure_ascii=False)}
    
    INVENTARIO DISPONIBLE:
    {product_context}
    
    ZONAS DE DELIVERY (Para calcular envío):
    {delivery_context}
    
    INSTRUCCIONES: 
    1. Para VENDER: Usa solo productos del INVENTARIO.
    2. Para CREAR PEDIDO: Si el usuario confirma, usa <crear_pedido>[JSON]</crear_pedido>.
    3. Para ENVÍO: 
       - Pregunta la zona/barrio (ej: Sopocachi, Satélite).
       - Busca la zona en la lista 'ZONAS DE DELIVERY'.
       - Si encuentras coincidencia, GENERA: <asignar_zona>ID_ZONA</asignar_zona>.
       - Si el usuario dice "voy a recoger", usa ID: -1 (<asignar_zona>-1</asignar_zona>).
    """

    messages = [
        {"role": "system", "content": settings.SYSTEM_PROMPT},
        {"role": "assistant", "content": f"Memoria del sistema:\n{memory_context}"},
    ]
    
    # Inject History
    messages.extend(history)
    
    # Current User Message
    messages.append({"role": "user", "content": message})

    try:
        # 2. Call LLM
        # Note: 'client.chat.completions.create' is synchronous.
        # In a real async app, use 'AsyncOpenAI' or run in threadpool.
        # For simplicity in this migration, we use the sync client but wrapped if needed.
        # Ideally: client = AsyncOpenAI(...)

        response = client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=messages
        )

        output = response.choices[0].message.content
        return output

    except Exception as e:
        print(f"Error LLM: {e}")
        return "Lo siento, tengo problemas de conexión con mi cerebro digital."

def parse_memory_tags(response_text: str) -> dict:
    """
    Extracts <memoria>...</memoria> content from the response.
    """
    data = {}
    if "<memoria>" in response_text:
        try:
            json_text = response_text.split("<memoria>")[1].split("</memoria>")[0]
            data = json.loads(json_text)
        except Exception:
            pass
    return data

def clean_response(response_text: str) -> str:
    """
    Removes system tags from the response to show to the user.
    """
    output = response_text
    # Remove <memoria> block
    if "<memoria>" in output:
        parts = output.split("<memoria>")
        output = parts[0] + (parts[1].split("</memoria>")[1] if "</memoria>" in parts[1] else "")

    # Remove <crear_pedido> block
    if "<crear_pedido>" in output:
        parts = output.split("<crear_pedido>")
        # Keep text before and after
        output = parts[0] + (parts[1].split("</crear_pedido>")[1] if "</crear_pedido>" in parts[1] else "")

    # Remove <asignar_zona> block
    if "<asignar_zona>" in output:
        parts = output.split("<asignar_zona>")
        output = parts[0] + (parts[1].split("</asignar_zona>")[1] if "</asignar_zona>" in parts[1] else "")

    # Remove <qr> tag
    output = output.replace("<qr>", "").replace("</qr>", "")

    return output.strip()
