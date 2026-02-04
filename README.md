# Kallpa Sales AI

Asistente de ventas con IA para Telegram, diseñado para el mercado boliviano. Este bot ayuda a gestionar el inventario, realizar ventas y coordinar envíos de manera automatizada.

## Requisitos Previos

Asegúrate de tener instalado lo siguiente antes de comenzar:

- **Python 3.9** o superior
- **PostgreSQL**: Base de datos local o remota.
- **Git**: Para clonar el repositorio.
- **Cuenta de Telegram**: Para crear el bot con BotFather.

## Instalación

Sigue estos pasos para configurar el proyecto en tu máquina local:

1.  **Clonar el repositorio:**

    ```bash
    git clone https://github.com/AIVERKE/Kallpa-Sales-AI.git
    cd Kallpa-Sales-AI
    ```

2.  **Crear y activar entorno virtual:**

    Es recomendable usar un entorno virtual para aislar las dependencias.

    _Windows:_

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

    _Linux/Mac:_

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instalar dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno:**

    Crea un archivo `.env` en la raíz del proyecto copiando el ejemplo:

    ```bash
    cp .env.example .env  # En Windows: copy .env.example .env
    ```

    Edita el archivo `.env` con tus credenciales:
    - `DATABASE_URL`: `postgresql+asyncpg://usuario:password@localhost:5432/kallpa_db`
    - `TELEGRAM_BOT_TOKEN`: Token obtenido de @BotFather.
    - `DEEPSEEK_API_KEY`: Tu API Key de DeepSeek (o OpenAI si se configura).
    - `SECRET_KEY`: Una cadena segura para seguridad (puedes generar una aleatoria).

5.  **Configurar Base de Datos:**

    Asegúrate de que la base de datos `kallpa_db` (o el nombre que hayas puesto en `.env`) exista en tu PostgreSQL.

    Luego, ejecuta los scripts iniciales para crear las tablas y datos semilla:

    ```bash
    # Inicializar tablas (esto suele manejarse automáticamente al iniciar la app o via scripts de migración si existen)
    # Por ahora, asegurate de correr los scripts SQL si tienes o usar el init del ORM.

    # Si tienes un archivo SQL inicial:
    # psql -h localhost -U postgres -d kallpa_db -f scripts/db/001-kallpa.sql

    # Opción Recomendada (Scripts de Python):

    # 1. Inicializar tablas vacías:
    python scripts/init_db.py

    # 2. Inicializar Y cargar datos de prueba (Reset completo):
    python scripts/seed_data.py
    ```

## Ejecución

El proyecto puede correr en dos modos: **Bot (Polling)** para desarrollo local y **Web (Webhook)** para producción.

### 1. Modo Desarrollo Local (Recomendado)

En este modo, el bot corre en tu máquina y consulta activamente a Telegram por nuevos mensajes. No necesitas IP pública ni HTTPS.

```bash
python src/main.py bot
```

_Verás un mensaje indicando que el bot ha iniciado._

### 2. Modo Servidor Web (Producción / Webhooks)

Este modo levanta un servidor FastAPI que espera recibir actualizaciones de Telegram via Webhook.

```bash
python src/main.py web
```

_Esto iniciará el servidor en `http://0.0.0.0:8000`. Para que funcione con Telegram, necesitas configurar el Webhook apuntando a tu URL pública (ej. usando ngrok o un deploy real)._

## Estructura del Proyecto

- `src/`: Código fuente.
  - `core/`: Configuración global y constantes.
  - `domain/`: Modelos de datos (SQLModel).
  - `infrastructure/`: Conexiones a DB, Telegram y Web.
  - `services/`: Lógica de negocio (IA, Gestión de Pedidos, Chat).
- `scripts/`: Scripts de utilidad (run_bot, seeds, verificaciones).
- `requirements.txt`: Dependencias del proyecto.

## Contribuir

1. Crea una rama para tu feature (`git checkout -b feature/nueva-feature`).
2. Haz tus cambios y commit.
3. Sube tu rama y abre un Pull Request.
