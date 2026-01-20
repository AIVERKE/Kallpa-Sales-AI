import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Reload=True for dev environment convenience
    uvicorn.run("src.infrastructure.web.main:app", host="0.0.0.0", port=port, reload=True)
