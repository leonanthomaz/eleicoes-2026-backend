# main.py
from pathlib import Path

import uvicorn
from fastapi.staticfiles import StaticFiles

from app import create_app

app = create_app()

# Fotos locais (opcional) ficam em app/fotos/ e são servidas em /fotos
FOTOS_DIR = Path(__file__).parent / "app" / "fotos"
FOTOS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/fotos", StaticFiles(directory=str(FOTOS_DIR)), name="fotos")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)