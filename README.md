# Kallpa Sales AI

Asistente de ventas con IA para Telegram, diseñado para el mercado boliviano.

## Requisitos

- Python 3.9+
- PostgreSQL
- Cuenta de Telegram Bot (BotFather)
- API Keys: OpenAI / DeepSeek

## Instalación

1.  **Clonar el repositorio:**

    ```bash
    git clone <repo-url>
    cd Kallpa-Sales-AI
    ```

2.  **Crear entorno virtual:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    venv\Scripts\activate     # Windows
    ```

3.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar variables de entorno:**
    Copiar el archivo de ejemplo y editarlo:

    ```bash
    cp .env.example .env
    ```

5.  **Base de Datos:**
    Ejecutar el script SQL inicial (asegúrate de tener la DB creada):

    ```bash
    psql -h localhost -U postgres -d kallpa_db -f scripts/db/001-kallpa.sql
    ```

## Ejecución

El proyecto tiene dos modos principales: **Bot** (Polling) y **Web** (Webhook/API).

### Modo Bot (Local Polling)

Para desarrollo local rápido:

```bash
python scripts/run_app.py bot
```

### Modo Web (Flask)

Para producción o webhooks:

```bash
python scripts/run_app.py web
```

## Estructura del Proyecto

- `src/`: Código fuente principal.
  - `bot/`: Lógica del bot de Telegram.
  - `web/`: Aplicación Flask.
  - `services/`: Lógica de negocio e integraciones (IA, etc).
  - `config/`: Configuraciones y prompts.
- `scripts/`: Scripts de utilidad y entry point.
- `tests/`: (Pendiente)

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md).
