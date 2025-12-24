"""
TORO Investment Manager - Web Application
FastAPI Backend Principal
"""

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Rutas API
from .routes import router
from .admin_catalogo import router as admin_catalogo_router
from .admin_batch import router as admin_batch_router

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# =========================
# APP
# =========================
app = FastAPI(
    title="TORO Investment Manager",
    description="Sistema de gestion financiera y analisis de inversiones",
    version="2.1.0",
)

# =========================
# MIDDLEWARE
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# STATIC FILES
# =========================
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# =========================
# FAVICON
# =========================
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = BASE_DIR / "frontend" / "static" / "img" / "favicon" / "favicon.ico"
    return FileResponse(favicon_path)

# =========================
# API ROUTES
# =========================
app.include_router(router)
app.include_router(admin_catalogo_router)
app.include_router(admin_batch_router)

# =========================
# HTML ROUTES
# =========================
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "TORO Investment Manager",
            "user": "Tori / Rosario",
        },
    )


@app.get("/reportes", response_class=HTMLResponse)
async def reportes(request: Request):
    return templates.TemplateResponse(
        "reportes.html",
        {
            "request": request,
            "title": "Reportes Ejecutivos",
        },
    )


@app.get("/batches", response_class=HTMLResponse)
async def batches(request: Request):
    return templates.TemplateResponse(
        "batches.html",
        {
            "request": request,
            "title": "Gestión de Batches",
        },
    )


@app.get("/configuracion", response_class=HTMLResponse)
async def configuracion(request: Request):
    return templates.TemplateResponse(
        "configuracion.html",
        {
            "request": request,
            "title": "Configuración del Sistema",
        },
    )


@app.get("/metadata", response_class=HTMLResponse)
async def metadata(request: Request):
    return templates.TemplateResponse(
        "metadata.html",
        {
            "request": request,
            "title": "Metadata de Movimientos",
        },
    )


@app.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request):
    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "title": "Analytics y Visualizaciones",
        },
    )


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "TORO Web",
        "version": "2.1.0",
    }

# =========================
# EVENTS
# =========================
@app.on_event("startup")
async def startup_event():
    print("=" * 60)
    print("TORO Investment Manager Web - INICIADO")
    print("=" * 60)
    print("Web UI:       http://localhost:8000")
    print("Reportes UI:  http://localhost:8000/reportes")
    print("Analytics UI: http://localhost:8000/analytics")
    print("Batches UI:   http://localhost:8000/batches")
    print("API Docs:     http://localhost:8000/docs")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    print("TORO Web - Servidor detenido")


# =========================
# RUN LOCAL
# =========================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
