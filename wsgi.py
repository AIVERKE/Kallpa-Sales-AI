import sys
import os

# Add project root to sys.path to ensure src module is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.web.app import app

if __name__ == "__main__":
    app.run()
