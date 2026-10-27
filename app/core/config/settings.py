# app/core/config/settings.py
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv(dotenv_path=".env", encoding="utf-8")


class Configuration:
    """Configuração centralizada - Singleton"""

    _instance: Optional['Configuration'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._setup_logging()
        self._load_environment_variables()

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"✅ Configuration inicializada - Ambiente: {self.environment}")

    def _setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"app_{datetime.now():%Y%m%d}.log"

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
        )

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.handlers.clear()
        root.addHandler(console_handler)
        root.addHandler(file_handler)

    def _load_environment_variables(self):
        self.environment = os.getenv("APP_ENVIRONMENT", "development").upper()

        # Groq
        self.groq_url = os.getenv("GROQ_URL")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL")

        # URL do próprio backend (usado apenas se hospedar fotos localmente)
        self.backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

        # TSE - Eleições 2026
        self.tse_url = os.getenv("TSE_URL", "https://resultados.tse.jus.br")
        self.tse_ambiente = os.getenv("TSE_AMBIENTE", "oficial")
        self.tse_ciclo = os.getenv("TSE_CICLO", "ele2026")
        self.tse_uf = os.getenv("TSE_UF", "rj")

        # Códigos das eleições
        self.tse_eleicao_federal = os.getenv("TSE_ELEICAO_FEDERAL", "6257")
        self.tse_eleicao_estadual = os.getenv("TSE_ELEICAO_ESTADUAL", "6259")

        # Mapa de cargos
        # uf_padrao: usado quando a abrangência é "uf" (recorte regional)
        # foto_origem: "tse" (busca direto do TSE) ou "local" (busca em /fotos/<pasta>)
        self.cargos = {
            "presidente": {
                "cargo": "PRESIDENTE",
                "codigo_cargo": "0001",
                "eleicao": self.tse_eleicao_federal,
                "uf": "br",
                "foto_origem": "tse",
                "foto_pasta": "presidente",
                "vagas": 1,
                "majoritario": True,
            },
            "governador": {
                "cargo": "GOVERNADOR",
                "codigo_cargo": "0003",
                "eleicao": self.tse_eleicao_estadual,
                "uf": self.tse_uf,
                "foto_origem": "tse",
                "foto_pasta": "rj",
                "vagas": 1,
                "majoritario": True,
            },
            "senador": {
                "cargo": "SENADOR",
                "codigo_cargo": "0005",
                "eleicao": self.tse_eleicao_estadual,
                "uf": self.tse_uf,
                "foto_origem": "tse",
                "foto_pasta": "rj",
                "vagas": 2,
                "majoritario": True,
            },
            "deputado-federal": {
                "cargo": "DEPUTADO FEDERAL",
                "codigo_cargo": "0006",
                "eleicao": self.tse_eleicao_estadual,
                "uf": self.tse_uf,
                "foto_origem": "tse",
                "foto_pasta": "rj",
                "vagas": 46,
                "majoritario": False,
            },
            "deputado-estadual": {
                "cargo": "DEPUTADO ESTADUAL",
                "codigo_cargo": "0007",
                "eleicao": self.tse_eleicao_estadual,
                "uf": self.tse_uf,
                "foto_origem": "tse",
                "foto_pasta": "rj",
                "vagas": 70,
                "majoritario": False,
            },
        }


_config: Optional[Configuration] = None

def get_config() -> Configuration:
    global _config
    if _config is None:
        _config = Configuration()
    return _config