# Guía de Despliegue en Producción

Tu aplicación **Kallpa Sales AI** ahora está lista para producción. He generado los siguientes archivos clave:

## Archivos Generados

- **`wsgi.py`**: Punto de entrada para servidores de producción.
- **`Procfile`**: Archivo para despliegues en **Heroku**, **Render**, o **Railway**.
- **`Dockerfile`**: Para despliegue en cualquier contenedor (Docker, AWS, DigitalOcean).
- **`requirements.txt`**: Actualizado con `gunicorn` (servidor web de producción).

## Opciones de Despliegue

### Opción 1: Railway / Render / Heroku (Recomendado)

Estas plataformas detectarán automáticamente el archivo `Procfile` o `Dockerfile`.

1. **Subir a GitHub**: Asegúrate de que tu código esté en un repositorio.
2. **Conectar**: Conecta tu repositorio a Railway/Render.
3. **Variables de Entorno**: Configura las siguientes variables en el panel de control de tu proveedor:
   - `TELEGRAM_TOKEN`: Tu token del bot.
   - `OPENAI_API_KEY`: Tu key de OpenAI.
   - `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`: Credenciales de tu base de datos PostgreSQL en producción.
   - `SECRET_KEY`: Una cadena aleatoria larga y segrura.

### Opción 2: Docker

Si tienes un servidor con Docker instalado:

1. **Construir Imagen**:
   ```bash
   docker build -t kallpa-sales-ai .
   ```
2. **Correr Contenedor**:
   ```bash
   docker run -p 5000:5000 --env-file .env kallpa-sales-ai
   ```

### Opción 3: Servidor Linux (VPS)

Si despliegas manualmente en un Ubuntu/Debian:

1. Instalar dependencias: `pip install -r requirements.txt`
2. Ejecutar con Gunicorn:
   ```bash
   gunicorn --workers 3 --bind 0.0.0.0:8000 wsgi:app
   ```
3. Configurar Nginx como proxy inverso hacia el puerto 8000.

## Nota Importante sobre Windows

El archivo `requirements.txt` ahora incluye `gunicorn`, que **no funciona en Windows**.

- Si desarrollas en Windows, sigue usando `py scripts/run_app.py`.
- Si intentas instalar `pip install -r requirements.txt` en Windows, _podría_ fallar en gunicorn. Si eso pasa, puedes ignorarlo o eliminar la línea de gunicorn localmente (pero asegúrate de que esté para el servidor de producción).
