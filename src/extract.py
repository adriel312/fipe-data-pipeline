"""
extract.py
Responsável apenas por buscar dados no site da FIPE e salvar as respostas brutas.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from src.log_config import configurar_logging

import requests

# =============================================================================
# CONFIGURAÇÕES
# Deixe valores "mágicos" aqui em cima, e não espalhados pelo código.
# =============================================================================

# TODO: a parte comum das URLs (aba Headers > General > Request URL).
# Repare que todos os endpoints começam igual e só muda o final.
BASE_URL = "https://veiculos.fipe.org.br/api/veiculos/"

# TODO: o caminho final do endpoint dos meses de referência.
ENDPOINT_TABELA_REFERENCIA = "ConsultarTabelaDeReferencia"

# TODO: copie dos Request Headers os que parecem relevantes
# (User-Agent, Referer, Origin, X-Requested-With...).
# Depois, no teste por eliminação, remova os que não fizerem falta.
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    "referer": "https://veiculos.fipe.org.br/",
    "origin": "https://veiculos.fipe.org.br",
    "x-requested-with": "XMLHttpRequest",
    "accept": "application/json, text/javascript, */*; q=0.01"
}

# Onde os JSONs brutos serão salvos.
# Pesquise: por que pathlib.Path em vez de concatenar strings com "/"?
RAW_DIR = Path("data/raw")

# Controle de "educação" com o servidor.
TIMEOUT_SEGUNDOS = 5     # TODO: quanto tempo esperar antes de desistir?
MAX_TENTATIVAS = 3        # TODO: quantas vezes tentar de novo em caso de erro?
PAUSA_ENTRE_TENTATIVAS = 4  # TODO: segundos de espera inicial entre tentativas

# TODO: configure o logging (nível, formato com data/hora).
# Pesquise logging.basicConfig. Dica: inclua %(asctime)s no formato.
logger = logging.getLogger(__name__)


# =============================================================================
# FUNÇÕES GENÉRICAS
# Serão reaproveitadas por TODAS as etapas da cascata (marcas, modelos...).
# =============================================================================

def criar_sessao() -> requests.Session:
    """Cria uma sessão HTTP que se comporta como o navegador."""
    # TODO: criar a Session e aplicar os HEADERS nela
    #       (pesquise session.headers.update).
    #
    # TODO (experimento): o navegador recebeu cookies ao abrir a página.
    #       Será que o servidor exige isso? Teste fazer um GET na página
    #       principal antes das consultas e compare com não fazer.
    #       Registre a conclusão num comentário.
    ...


def fazer_post(sessao: requests.Session, endpoint: str, payload: dict | None = None):
    """
    Faz um POST com retentativas e devolve o JSON da resposta.
    Recebe o payload como parâmetro para servir a todas as etapas.
    """
    # TODO: montar a URL completa (BASE_URL + endpoint).
    #
    # TODO: laço de tentativas, até MAX_TENTATIVAS:
    #   1. fazer o POST passando timeout
    #      (lembre: a tabela de referência não tem corpo; as próximas etapas
    #       terão. Qual argumento usar: data= ou json=? Depende do que você
    #       viu na aba Payload de ConsultarMarcas.)
    #   2. checar o status (pesquise raise_for_status)
    #   3. converter para JSON e devolver
    #
    # TODO: em caso de erro (pesquise quais exceções o requests lança):
    #   - registrar no log qual tentativa falhou e por quê
    #   - esperar antes de tentar de novo
    #     (pesquise "exponential backoff": por que aumentar a espera a cada falha?)
    #
    # TODO: se todas as tentativas falharem, o que fazer?
    #       Devolver None ou lançar a exceção? Pense em qual é mais seguro
    #       para o resto do pipeline e justifique.
    ...


def salvar_json_bruto(dados, nome_base: str) -> Path:
    """Salva a resposta exatamente como veio, com a data da coleta no nome."""
    # TODO: garantir que RAW_DIR exista (pesquise Path.mkdir com parents/exist_ok).
    #
    # TODO: montar o nome do arquivo com data e hora da coleta,
    #       ex.: tabela_referencia_2026-10-04_153000.json
    #
    # TODO: gravar o JSON.
    #       Atenção ao "março": pesquise o parâmetro ensure_ascii do json.dump
    #       e o encoding ao abrir o arquivo.
    #
    # TODO: registrar no log onde salvou e devolver o caminho.
    ...


# =============================================================================
# FUNÇÕES ESPECÍFICAS DE CADA ETAPA
# =============================================================================

def extrair_tabelas_referencia(sessao: requests.Session) -> list[dict]:
    """Busca a lista completa de meses de referência (2001 até hoje)."""
    # TODO: usar fazer_post com o endpoint certo (sem payload).
    #
    # TODO: uma checagem mínima antes de salvar:
    #       a resposta é uma lista? Não está vazia? Os itens têm as chaves
    #       "Codigo" e "Mes"? (validação completa fica para o transform.)
    #
    # TODO: salvar o bruto com salvar_json_bruto e devolver os dados.
    ...


# Mais tarde, as próximas etapas entram aqui, seguindo o mesmo padrão:
# def extrair_marcas(sessao, codigo_referencia): ...
# def extrair_modelos(sessao, codigo_referencia, codigo_marca): ...


# =============================================================================
# EXECUÇÃO DIRETA (para testar este módulo isoladamente)
# =============================================================================

if __name__ == "__main__":
    # TODO: criar a sessão, chamar extrair_tabelas_referencia
    #       e registrar no log quantos meses vieram.
    #       Compare com a contagem que você viu no Preview do DevTools.
    configurar_logging()