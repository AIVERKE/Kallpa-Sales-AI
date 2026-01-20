import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.db.session import init_db
from src.domain.models import * # Import all models to register them with metadata

if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_db())
    print("Database initialized.")
