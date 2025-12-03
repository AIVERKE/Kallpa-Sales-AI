# 📄 **README.md — Kallpa Sales AI (Backend + Chatbot)**

# 🤖 Kallpa Sales AI – Backend + Telegram Chatbot

Asistente de ventas inteligente para el ecosistema Kallpa.

Este proyecto integra:

- Flask ⚙️ (API backend)
- PostgreSQL 🗄️ (base de datos CRM + IA)
- Bot de Telegram 💬
- DeepSeek AI 🔥 (motor LLM)
- Estructura de CRM (clientes, oportunidades, cotizaciones)
- Registro inteligente de conversaciones

---

## 📦 1. Requisitos Previos

Antes de empezar asegúrate de tener instalado:

- Python 3.10+
- PostgreSQL 14+
- Git
- pip o pipenv
- Una API Key de **DeepSeek**
- Una API key de **@BotFather**

---

## 📁 2. Clonar el repositorio

```bash
git clone <https://github.com/AIVERKE/Kallpa-Sales-AI.git>
cd Kallpa-Sales-AI
```

---

## 🏗️ 3. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
```

---

## 📦 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## ⚙️ 5. Crear archivo `.env`

Se tiene el archivo .env.example con el código base para crear el archivo .env
En la raíz del proyecto crear el archivo .env:

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

DB_HOST=localhost
DB_NAME=kallpa
DB_USER=postgres
DB_PASS=1234

TELEGRAM_TOKEN=XXXXXXXX:YYYYYYYYYYYYYYYYYYYY

FLASK_ENV=development
```

---

## 🗄️ 6. Configurar Base de Datos

Este proyecto incluye un esquema completo CRM + IA.

1️⃣ Ingresa a PostgreSQL:

```bash
psql -U postgres
```

2️⃣ Crea la base:

```sql
CREATE DATABASE kallpa_sales_ai;
```

3️⃣ Carga el archivo SQL:

```bash
psql -U postgres -d kallpa -f 001-kallpa.sql
```

(El archivo `001-kallpa.sql` es el dump compartido en este repositorio.)

---

## 🧪 7. Probar la conexión a PostgreSQL

```bash
python
```

```python
from db.connection import get_connection
c = get_connection()
print(c)
```

Si no explota → ¡está bien configurado!

---

## 🤖 8. Ejecutar el bot de Telegram (modo desarrollo - polling)

El bot funciona sin dominio ni webhook, ideal para desarrollo local.

```bash
python run_bot.py
```

Deberías ver:

```
🤖 Bot de Kallpa Sales AI corriendo en modo POLLING...
```

Ahora envía un mensaje a tu bot en Telegram.

---

## 🧠 9. ¿Cómo funciona el bot?

1. Recibe mensajes desde Telegram
2. Usa DeepSeek para generar la respuesta
3. Guarda historial en la tabla `ai_interactions`
4. Responde al usuario

Toda la integración está en:

```
telegram_bot/bot.py
openai_client/ai.py
db/queries.py
```

---

## 🌐 10. Ejecutar Flask (solo si usas endpoints)

```bash
python app.py
```

Abrir en navegador:

```
http://localhost:5000
```

---

## 📚 11. Estructura del proyecto

```
Kallpa-Sales-AI/
│
├── app.py                 # API Flask
├── run_bot.py             # Bot Telegram (polling)
├── config.py              # Configuración con .env
├── requirements.txt
│
├── openai_client/
│   └── ai.py              # Llamadas a DeepSeek
│
├── db/
│   ├── connection.py      # Conexión PostgreSQL
│   └── queries.py         # Consultas y persistencia
│
└── telegram_bot/
    └── bot.py             # Lógica del bot
```

---

## 🔥 12. ¿Cómo editar la personalidad del Asistente?

En `openai_client/ai.py`, el `system prompt` define el comportamiento del bot:

```python
{"role": "system", "content": "Eres Kallpa Sales AI, un asistente de ventas inteligente."}
```

Puedes hacerlo más largo, más humano, más consultivo o más orientado a ventas.

---

## 🧑‍🤝‍🧑 13. Equipo y Contribución

1. Cada contribución debe hacerse en una rama nueva:

   ```
   git checkout -b feature/nombre
   ```

2. Hacer commit:

   ```
   git commit -m "feat: añadida funcionalidad X"
   ```

3. Subir cambios:

   ```
   git push origin feature/nombre
   ```

4. Abrir Pull Request.

---

## ✔️ 15. Todo listo

Ya puedes:

- Ejecutar el bot
- Conectar DeepSeek
- Guardar conversaciones
- Usar la base CRM
- Extender el sistema

Cualquier miembro del equipo debería poder levantar el proyecto en 5–10 minutos.

---
