# app/__init__.py

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config.settings import Configuration
from app.modules import register_routes

configuration = Configuration()


def create_app():
    logging.info("SISTEMA >>> Inicializando...")
    logging.info(f"AMBIENTE >>> {configuration.environment.upper()}")

    app = FastAPI(
        title="Eleições API",
        version="1.0.0",
        redirect_slashes=False,
        docs_url="/api/eleicoes/docs" if configuration.environment == "PRODUCAO" else "/docs",
        openapi_url="/api/eleicoes/openapi.json" if configuration.environment == "PRODUCAO" else "/openapi.json",
    )

    # Em desenvolvimento, o Vite roda em localhost:5173
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Filename"],
    )

    register_routes(app)
    return app