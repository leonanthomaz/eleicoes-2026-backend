# app/modules/eleicoes/controllers/eleicoes_controller.py

import logging
from typing import Dict, Optional
from fastapi import APIRouter, Query

from app.modules.eleicoes.services.eleicoes_service import EleicoesService
from app.core.config.settings import Configuration
from app.shared.utils.retornar_timestamp import get_current_timestamp


class EleicoesController(APIRouter):
    """Controller para operações com Eleições"""

    def __init__(self):
        super().__init__()

        self.config = Configuration()
        self.service = EleicoesService()
        self.logger = logging.getLogger(__name__)

        self.add_api_route(
            path="/health",
            endpoint=self.health_check,
            methods=["GET"],
            summary="Health check",
        )

        self.add_api_route(
            path="/2026/configuracao",
            endpoint=self.configuracao_2026,
            methods=["GET"],
            summary="Configuração das eleições 2026",
        )

        # Presidente — aceita abrangência (br | uf) e uf opcional
        self.add_api_route(
            path="/2026/presidente",
            endpoint=self.presidente_2026,
            methods=["GET"],
            summary="Presidente 2026 (Brasil ou UF)",
        )

        # Cargos estaduais — fixos em RJ
        self.add_api_route(
            path="/2026/governador/rj",
            endpoint=self.governador_rj_2026,
            methods=["GET"],
            summary="Governador RJ 2026",
        )

        self.add_api_route(
            path="/2026/senador/rj",
            endpoint=self.senador_rj_2026,
            methods=["GET"],
            summary="Senador RJ 2026",
        )

        self.add_api_route(
            path="/2026/deputado-federal/rj",
            endpoint=self.deputado_federal_rj_2026,
            methods=["GET"],
            summary="Deputado Federal RJ 2026",
        )

        self.add_api_route(
            path="/2026/deputado-estadual/rj",
            endpoint=self.deputado_estadual_rj_2026,
            methods=["GET"],
            summary="Deputado Estadual RJ 2026",
        )

    # ==========================================================
    # ENDPOINTS
    # ==========================================================

    def health_check(self) -> Dict[str, str]:
        return {
            "status": "ONLINE",
            "service": "ELEICOES API",
            "timestamp": get_current_timestamp(),
        }

    async def configuracao_2026(self):
        return await self.service.obter_configuracao()

    async def presidente_2026(
        self,
        abrangencia: str = Query("br", description="br | uf"),
        uf: Optional[str] = Query(None, description="UF quando abrangencia=uf"),
    ):
        return await self.service.obter_resultado(
            "presidente", abrangencia=abrangencia, uf=uf
        )

    async def governador_rj_2026(self):
        return await self.service.obter_resultado("governador")

    async def senador_rj_2026(self):
        return await self.service.obter_resultado("senador")

    async def deputado_federal_rj_2026(self):
        return await self.service.obter_resultado("deputado-federal")

    async def deputado_estadual_rj_2026(self):
        return await self.service.obter_resultado("deputado-estadual")