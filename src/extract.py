"""Módulo responsável pela extração dos dados brutos da API da FIPE.

Fluxo principal:
1. abrir uma sessão HTTP simulando um navegador;
2. enviar o POST para o endpoint solicitado;
3. validar a resposta recebida;
4. salvar o JSON em data/raw;
5. devolver os dados para a próxima etapa do pipeline.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import requests

from src.log_config import configurar_logging

# -----------------------------------------------------------------------------
# Configurações globais
# -----------------------------------------------------------------------------

# URL base da API da FIPE. Todos os endpoints são montados a partir dela.
BASE_URL = "https://veiculos.fipe.org.br/api/veiculos/"

# Endpoint da tabela de referência
ENDPOINT_TABELA_REFERENCIA = "ConsultarTabelaDeReferencia"

# Headers que imitam um navegador real
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    "referer": "https://veiculos.fipe.org.br/",
    "origin": "https://veiculos.fipe.org.br",
    "x-requested-with": "XMLHttpRequest",
    "accept": "application/json, text/javascript, */*; q=0.01",
}
RAW_DIR = Path("data/raw")

TIMEOUT_SEGUNDOS = 5
MAX_TENTATIVAS = 3
PAUSA_ENTRE_TENTATIVAS = 4

# Logger do módulo. A configuração final é feita em src/log_config.py.
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Funções reutilizáveis
# -----------------------------------------------------------------------------

def criar_sessao() -> requests.Session:
    #Cria uma sessão HTTP com os headers do navegador e inicializa o contexto.
    sessao = requests.Session()
    sessao.headers.update(HEADERS)

    # Abrir a página inicial da FIPE ajuda a preencher cookies e a simular um uso real do site antes da chamada à API.
    try:
        sessao.get("https://veiculos.fipe.org.br/", timeout=TIMEOUT_SEGUNDOS)
        logger.debug("Página inicial da FIPE acessada para iniciar a sessão.")
    except requests.RequestException as exc:
        logger.warning("Não foi possível acessar a página inicial da FIPE: %s", exc)

    return sessao


def fazer_post(sessao: requests.Session, endpoint: str, payload: dict | None = None):
    #Envia uma requisição POST com retentativas e retorna o JSON da resposta.
    url_completa = f"{BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = sessao.post(url_completa, json=payload, timeout=TIMEOUT_SEGUNDOS)
            resposta.raise_for_status()
            return resposta.json()
        except requests.RequestException as erro:
            logger.error("Tentativa %s falhou para %s: %s", tentativa, url_completa, erro)

            if tentativa < MAX_TENTATIVAS:
                # Backoff exponencial para não saturar o servidor e dar tempo para a conexão se estabilizar.
                espera = PAUSA_ENTRE_TENTATIVAS * (2 ** (tentativa - 1))
                logger.info("Aguardando %s segundos antes da próxima tentativa...", espera)
                time.sleep(espera)
            else:
                logger.error("Todas as tentativas falharam para o endpoint %s.", url_completa)
                raise


def salvar_json_bruto(dados, nome_base: str) -> Path:
    #Salva a resposta recebida em um arquivo JSON com timestamp no nome.
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Formato do nome: nome_base_DD-MM-YYYY_HHMMSS.json
    arquivo_nome = f"{nome_base}_{datetime.now().strftime('%d-%m-%Y_%H%M%S')}.json"
    caminho_arquivo = RAW_DIR / arquivo_nome

    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)

    logger.info("Arquivo bruto salvo em: %s", caminho_arquivo)
    return caminho_arquivo


# -----------------------------------------------------------------------------
# Extração de dados específicos
# -----------------------------------------------------------------------------

def extrair_tabelas_referencia(sessao: requests.Session) -> list[dict]:
    #Busca a tabela de referência de meses disponíveis na FIPE.
    dados = fazer_post(sessao, ENDPOINT_TABELA_REFERENCIA)

    # A API deve responder com uma lista. Se não for isso, a coleta não pode prosseguir.
    if not isinstance(dados, list):
        raise ValueError("Resposta esperada como lista para tabelas de referência.")

    if not dados:
        logger.warning("A API respondeu com uma lista vazia para tabelas de referência.")

    for item in dados:
        if not isinstance(item, dict) or "Codigo" not in item or "Mes" not in item:
            logger.warning("Item inesperado na resposta da tabela de referência: %s", item)

    salvar_json_bruto(dados, "tabelas_referencia")
    logger.info("Tabela de referência extraída com %s registros.", len(dados))
    return dados

def extrair_marcas(sessao, codigo_referencia: int) -> list[dict]:
    """Busca as marcas de carros disponíveis em um mês de referência."""
    # TODO: montar o dicionário de payload com os dois parâmetros
    #       (nomes exatamente como no DevTools)
    payload = {
        "codigoTabelaReferencia": codigo_referencia,
        "codigoTipoVeiculo": 1,  # 1 = Carros, 2 = Motos, 3 = Caminhões
    }
    # TODO: chamar fazer_post com o endpoint de marcas
    ENDPOINT_MARCAS = "ConsultarMarcas"
    dados = fazer_post(sessao, ENDPOINT_MARCAS, payload)
    # TODO: checagem mínima: é lista? não está vazia? tem "Label" e "Value"?
    if not isinstance(dados, list):
        raise ValueError("Resposta esperada como lista para marcas.")
    if not dados:
        logger.warning("A API respondeu com uma lista vazia para marcas.")
    for item in dados:
        if not isinstance(item, dict) or "Label" not in item or "Value" not in item:
            logger.warning("Item inesperado na resposta de marcas: %s", item)
    # TODO: salvar o bruto com um nome que inclua o código do mês
    #       (senão, o arquivo de um mês sobrescreve o do outro)
    salvar_json_bruto(dados, f"marcas_{codigo_referencia}")
    logger.info("Marcas extraídas com %s registros para referência %s.", len(dados), codigo_referencia)
    return dados

# Futuras etapas seguem o mesmo padrão:
# def extrair_marcas(sessao, codigo_referencia): ...
# def extrair_modelos(sessao, codigo_referencia, codigo_marca): ...


# -----------------------------------------------------------------------------
# Execução direta para testes do módulo
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    configurar_logging()
    sessao = criar_sessao()
    #dados = extrair_tabelas_referencia(sessao)
    #logger.info("Coleta finalizada. Total de meses recebidos: %s", len(dados))
    marcas_outubro = extrair_marcas(sessao, 338)
    time.sleep(5)
    marcas_setembro = extrair_marcas(sessao, 337)