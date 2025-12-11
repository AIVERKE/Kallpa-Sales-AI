import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web.app import app
from src.web.extensions import db

def reset_database():
    print("⚠️  Advertencia: Esto eliminará la tabla 'users' y sus relaciones.")
    print("Conectando a la base de datos...")
    
    with app.app_context():
        try:
            print("Forzando eliminación de tabla 'users' (CASCADE)...")
            # Force drop with cascade for PostgreSQL dependencies
            db.session.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            db.session.commit()
            
            print("Creando nuevas tablas...")
            db.create_all()
            print("✅ Base de datos reseteada correctamente.")
            print("Ahora puedes registrar usuarios nuevos.")
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == "__main__":
    reset_database()
