# src/modules/__init__.py

# Controllers
from app.modules.eleicoes.controllers.eleicoes_controller import EleicoesController

def register_routes(app):
    # Rotas
    app.include_router(EleicoesController(), prefix="/api/eleicoes", tags=["Rota Eleições"])
 
  
