# app/modules/eleicoes/services/eleicoes_service.py

import logging
import httpx

from app.core.config.settings import Configuration


# Só o Presidente aceita recorte regional
CARGOS_COM_ABRANGENCIA = {"presidente"}


class EleicoesService:
    """Service responsável pelas operações com os dados eleitorais."""

    def __init__(self):
        self.config = Configuration()
        self.logger = logging.getLogger(__name__)

    # ==========================================================
    # TSE - HTTP
    # ==========================================================

    async def _buscar_tse(self, url: str):
        self.logger.info(f"TSE >>> GET {url}")

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)

            if response.status_code == 404:
                self.logger.warning(f"TSE >>> 404 (ainda não publicado): {url}")
                return None

            response.raise_for_status()
            data = response.json()

            try:
                self.logger.info(
                    f"TSE >>> OK · keys={list(data.keys())[:12]} "
                    f"and={data.get('and')} dg={data.get('dg')} hg={data.get('hg')}"
                )
            except Exception as exc:
                self.logger.warning(f"TSE >>> falha ao resumir payload: {exc}")

            return data

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _to_int(self, value, default=0):
        if value is None:
            return default
        try:
            return int(str(value).strip() or default)
        except (ValueError, TypeError, AttributeError):
            return default

    def _to_float(self, value, default=0.0):
        if value is None:
            return default
        try:
            return float(str(value).replace(",", ".").strip())
        except (ValueError, TypeError, AttributeError):
            return default

    def _to_str(self, value, default=None):
        if value is None:
            return default
        return str(value)

    def _montar_foto_url(self, sqcand, cfg_cargo):
        if not sqcand:
            return None

        origem = cfg_cargo.get("foto_origem", "tse")

        if origem == "tse":
            return (
                f"{self.config.tse_url}/"
                f"{self.config.tse_ambiente}/"
                f"{self.config.tse_ciclo}/"
                f"{cfg_cargo['eleicao']}/"
                f"fotos/"
                f"{cfg_cargo['uf']}/"
                f"{sqcand}.jpeg"
            )

        pasta = cfg_cargo.get("foto_pasta")
        if not pasta:
            return None

        return f"{self.config.backend_url}/fotos/{pasta}/{sqcand}.jpg"

    def _montar_url_ea20(self, cfg_cargo, abrangencia: str, uf: str | None):
        """
        Abrangência só existe pro Presidente.
        Demais cargos sempre usam cfg_cargo['uf'] (rj).
        """
        eleicao = cfg_cargo["eleicao"]
        codigo = cfg_cargo["codigo_cargo"]
        eleicao_fmt = str(eleicao).zfill(6)

        if abrangencia == "uf":
            uf_arq = (uf or cfg_cargo["uf"]).lower()
        else:
            uf_arq = cfg_cargo["uf"]

        nome_arquivo = f"{uf_arq}-c{codigo}-e{eleicao_fmt}-u.json"

        return (
            f"{self.config.tse_url}/"
            f"{self.config.tse_ambiente}/"
            f"{self.config.tse_ciclo}/"
            f"{eleicao}/dados/{uf_arq}/"
            f"{nome_arquivo}"
        )

    # ==========================================================
    # CONFIGURAÇÃO
    # ==========================================================

    async def obter_configuracao(self):
        url = (
            f"{self.config.tse_url}/"
            f"{self.config.tse_ambiente}/"
            f"comum/config/ele-c.json"
        )
        self.logger.info(f"CONFIG >>> {url}")
        data = await self._buscar_tse(url)

        if data is None:
            return {
                "status": "INDISPONIVEL",
                "mensagem": "Configuração do TSE ainda não disponível.",
                "url": url,
            }
        return data

    # ==========================================================
    # RESULTADO POR CARGO
    # ==========================================================

    async def obter_resultado(
        self,
        slug_cargo: str,
        abrangencia: str = "br",
        uf: str | None = None,
    ):
        self.logger.info(
            f"CARGO >>> {slug_cargo} · abrangencia={abrangencia} uf={uf}"
        )

        cfg_cargo = self.config.cargos.get(slug_cargo)
        if not cfg_cargo:
            return {
                "status": "CARGO_INVALIDO",
                "mensagem": f"Cargo '{slug_cargo}' não configurado.",
            }

        # Só Presidente aceita recorte regional
        if slug_cargo not in CARGOS_COM_ABRANGENCIA:
            abrangencia = "uf"
            uf = cfg_cargo["uf"]

        abrangencia = (abrangencia or "br").lower()
        if abrangencia not in {"br", "uf"}:
            abrangencia = "br"

        if abrangencia == "uf":
            uf = (uf or cfg_cargo["uf"]).lower()

        url = self._montar_url_ea20(cfg_cargo, abrangencia, uf)
        data = await self._buscar_tse(url)

        if data is None:
            return {
                "status": "AGUARDANDO_INICIO_DA_APURACAO",
                "contexto": self._bloco_contexto(cfg_cargo, abrangencia, uf),
                "mensagem": f"O TSE ainda não publicou o EA20 de {cfg_cargo['cargo']}.",
                "url": url,
            }

        return self._formatar_resultado(data, cfg_cargo, abrangencia, uf)

    # ==========================================================
    # BLOCOS
    # ==========================================================

    def _bloco_contexto(self, cfg_cargo, abrangencia, uf):
        return {
            "eleicao": 2026,
            "cargo": cfg_cargo["cargo"],
            "codigo_cargo": cfg_cargo["codigo_cargo"],
            "abrangencia": abrangencia,
            "uf": uf.upper() if abrangencia == "uf" else None,
            "vagas": cfg_cargo["vagas"],
            "majoritario": cfg_cargo["majoritario"],
        }

    def _bloco_progresso(self, data):
        s = data.get("s") if isinstance(data.get("s"), dict) else {}
        e = data.get("e") if isinstance(data.get("e"), dict) else {}

        return {
            "andamento": data.get("and"),
            "secoes": {
                "total": self._to_int(s.get("ts")),
                "totalizadas": self._to_int(s.get("st")),
                "percentual": self._to_float(s.get("pst")),
            },
            "eleitores": {
                "total": self._to_int(e.get("te")),
                "totalizados": self._to_int(e.get("est")),
                "percentual": self._to_float(e.get("pest")),
            },
        }

    def _bloco_fonte(self, data):
        return {
            "origem": "TSE",
            "arquivo": "EA20",
            "gerado_em": f"{data.get('dg', '')} {data.get('hg', '')}".strip(),
            "id": data.get("idg"),
        }

    # ==========================================================
    # FORMATAR
    # ==========================================================

    def _formatar_resultado(self, data, cfg_cargo, abrangencia, uf):
        candidatos = []

        for cargo in (data.get("carg") or []):
            if not isinstance(cargo, dict):
                continue

            for agrupamento in (cargo.get("agr") or []):
                if not isinstance(agrupamento, dict):
                    continue

                for partido in (agrupamento.get("par") or []):
                    if not isinstance(partido, dict):
                        continue

                    sigla_partido = partido.get("sg")
                    nome_partido = partido.get("nm")

                    for candidato in (partido.get("cand") or []):
                        if not isinstance(candidato, dict):
                            continue

                        sqcand = self._to_str(candidato.get("sqcand"))

                        candidatos.append({
                            "numero": self._to_str(candidato.get("n")),
                            "nome": self._to_str(candidato.get("nm")),
                            "nome_urna": self._to_str(candidato.get("nmu")),
                            "sqcand": sqcand,
                            "foto_url": self._montar_foto_url(sqcand, cfg_cargo),
                            "partido": sigla_partido,
                            "partido_nome": nome_partido,
                            "votos": self._to_int(candidato.get("vap")),
                            "percentual": self._to_float(candidato.get("pvap")),
                            "situacao": candidato.get("st"),
                        })

        candidatos.sort(key=lambda c: c["votos"], reverse=True)
        for idx, c in enumerate(candidatos, start=1):
            c["posicao"] = idx

        resultado = {
            "status": "OK",
            "contexto": self._bloco_contexto(cfg_cargo, abrangencia, uf),
            "progresso": self._bloco_progresso(data),
            "fonte": self._bloco_fonte(data),
            "resultado": {
                "total_candidatos": len(candidatos),
                "candidatos": candidatos,
            },
        }

        self.logger.info(
            f"FMT >>> {len(candidatos)} candidatos · "
            f"{resultado['progresso']['secoes']['totalizadas']}/"
            f"{resultado['progresso']['secoes']['total']} seções "
            f"({resultado['progresso']['secoes']['percentual']}%)"
        )

        return resultado