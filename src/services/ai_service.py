from openai import OpenAI
import json
from src.config.settings import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from src.config.prompts import SYSTEM_PROMPT
from src.database.repositories import get_memory, save_memory

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=f"{DEEPSEEK_BASE_URL}/v1"
)


def ai_response(user_id, prompt, memory_context=""):
    # 1. Obtener memoria previa
    if not memory_context:
        memory = get_memory(user_id)
        memory_context = (
            f"Memoria del cliente:\n{memory}\n"
            if memory else
            "Memoria del cliente: Sin memoria previa.\n"
        )

    # 2. Construir mensajes
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": memory_context},
        {"role": "user", "content": prompt},
    ]

    # 3. Llamada al modelo
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=messages
    )

    output = response.choices[0].message.content

    # 4. Procesar <memoria> si existe
    if "<memoria>" in output:
        try:
            json_text = output.split("<memoria>")[1].split("</memoria>")[0]
            data = json.loads(json_text)

            FIELD_MAP = {
                "dolor": "dolor_principal"
            }

            BOOLEAN_FIELDS = ["interes"]

            for field, value in data.items():
                mapped_field = FIELD_MAP.get(field, field)

                # Normalizar booleanos
                if mapped_field in BOOLEAN_FIELDS:
                    if isinstance(value, bool):
                        pass
                    else:
                        val = str(value).lower().strip()
                        if val in ["true", "si", "sí", "1"]:
                            value = True
                        elif val in ["false", "no", "0"]:
                            value = False
                        else:
                            print(f"Valor inválido para booleano ({mapped_field}):", value)
                            continue

                save_memory(user_id, mapped_field, value)

            # Limpiar memoria del mensaje visible
            output = output.replace(f"<memoria>{json_text}</memoria>", "").strip()

        except Exception as e:
            print("Error procesando memoria:", e)

    # Limpiar restos
    output = output.replace("<memoria>", "").replace("</memoria>", "").strip()

    return output
