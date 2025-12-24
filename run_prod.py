"""
Script de inicio del servidor TORO Web - MODO PRODUCCIÓN
Sin hot-reload para uso estable y continuo
"""
import uvicorn
from pathlib import Path
import sys

# Agregar backend al path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

if __name__ == "__main__":
    print("[INFO] Iniciando TORO Investment Manager Web - MODO PRODUCCIÓN")
    print("[INFO] Sistema estable - Sin hot-reload")
    print("[WEB] http://localhost:8000")
    print("[DOCS] http://localhost:8000/docs")
    print()

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
