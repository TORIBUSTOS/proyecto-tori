"""
Script de inicio del servidor TORO Web (LEGACY)

RECOMENDACIÓN: Usar los archivos .bat para iniciar el sistema:
- INICIAR_TORO_DEV.bat   → Para desarrollo
- INICIAR_TORO_PROD.bat  → Para uso normal

Este archivo se mantiene para compatibilidad.
"""
import uvicorn
from pathlib import Path
import sys

# Agregar backend al path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

if __name__ == "__main__":
    print("=" * 80)
    print("[AVISO] Usando script legacy run.py")
    print("[RECOMENDACIÓN] Usar INICIAR_TORO_DEV.bat o INICIAR_TORO_PROD.bat")
    print("=" * 80)
    print()
    print("[INFO] Iniciando TORO Investment Manager Web - MODO DESARROLLO")
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
