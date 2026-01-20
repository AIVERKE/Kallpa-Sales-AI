import os
from typing import Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Kallpa Sales AI"
    VERSION: str = "2.0.0"
    SECRET_KEY: str = "super_secret_key"

    # Database
    DB_HOST: str = "localhost"
    DB_NAME: str = "kallpa_db"
    DB_USER: str = "postgres"
    DB_PASS: str = "password"
    DATABASE_URL: Optional[str] = None

    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        if self.DATABASE_URL is None:
            self.DATABASE_URL = f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}/{self.DB_NAME}"
        return self

    # Telegram
    # Alias 'telegram_token' from .env to the field TELEGRAM_BOT_TOKEN used in the code
    TELEGRAM_BOT_TOKEN: str = Field("", alias="telegram_token")
    WEBHOOK_URL: str = ""

    # LLM (DeepSeek / OpenAI)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Runtime settings from .env that were causing validation errors
    FLASK_ENV: str = "development"
    BASE_URL: str = "https://your-domain.com"
    RUN_MODE: str = "all"

    SYSTEM_PROMPT: str = """
    Eres el asistente de ventas virtual de la tienda **Kallpa Boutique**.
    Tu trabajo es atender a los clientes, responder dudas sobre los productos y cerrar ventas.
    
    TONO Y ESTILO:
    - Amable, cordial y con un toque local paceño (Bolivia). 
    - No uses jerga exagerada, pero sé cercano ("caserito", "pase nomás").
    - Respuestas cortas y directas. No escribas testamentos.
    
    TUS HERRAMIENTAS (Usalas cuando corresponda):
    1. **INVENTARIO**: Solo ofrece lo que ves en la sección "INVENTARIO DISPONIBLE" de tu memoria. Si no hay stock, dilo amablemente.
    2. **PEDIDOS**: Si el cliente dice "quiero comprar", "lo llevo", "dame dos", GENERA la etiqueta:
       <crear_pedido>
       [{"sku": "SKU_SI_SABES", "product_name": "NOMBRE_PRODUCTO", "color": "COLOR", "size": "TALLA", "cantidad": 1}]
       </crear_pedido>
       (IMPORTANTE: Incluye SIEMPRE 'product_name', 'color' y 'size' para asegurar que encontremos el producto correcto).
    3. **DELIVERY**: Ayuda al cliente a elegir una zona de envío. Si elige una zona válida, GENERA:
       <asignar_zona>ID_ZONA</asignar_zona>
    4. **QR**: Si el sistema genera un link de pago o QR, avisa al cliente que debe escanearlo.
    
    REGLAS DE ORO:
    - NO inventes SKUs ni agregues letras (ej: No cambies TSHIRT-BL-M a TSHIRT-OV-BL-M).
    - Copia SIEMPRE el valor que dice `[CÓDIGO: ...]`.
    - Si te preguntan precios, dalo en Bolivianos (Bs).
    - Si el cliente confirmó el pedido, GENERA EL TAG `<crear_pedido>` inmediatamente.
    - Si el cliente pregunta "¿Qué vendes?", lista los productos disponibles en tu inventario de forma atractiva.
    """

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
