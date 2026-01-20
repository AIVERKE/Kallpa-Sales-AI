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
    session: ChatSession
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
    """

    messages = [
        {"role": "system", "content": settings.SYSTEM_PROMPT},
        {"role": "assistant", "content": f"Memoria del sistema:\n{memory_context}"},
        {"role": "user", "content": message},
    ]

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

    # Remove <qr> tag
    output = output.replace("<qr>", "").replace("</qr>", "")

    return output.strip()
