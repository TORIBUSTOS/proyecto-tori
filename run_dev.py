"""
Script de inicio del servidor TORO Web - MODO DESARROLLO
Incluye hot-reload para cambios en código
"""
import uvicorn
from pathlib import Path
import sys

# Agregar backend al path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

if __name__ == "__main__":
    print("[INFO] Iniciando TORO Investment Manager Web - MODO DESARROLLO")
    print("[INFO] Hot-reload ACTIVADO - Los cambios en código se recargan automáticamente")
    print("[WEB] http://localhost:8000")
    print("[DOCS] http://localhost:8000/docs")
    print()

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
