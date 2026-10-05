"""
extract.py
Responsável apenas por buscar dados no site da FIPE e salvar as respostas brutas.

O fluxo é simples:
1. criar uma sessão com os headers do navegador;
2. fazer um POST para o endpoint da API;
3. validar a resposta;
4. salvar o JSON em data/raw;
5. devolver os dados para as próximas etapas do pipeline.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import requests

from src.log_config import configurar_logging

# =============================================================================
# CONFIGURAÇÕES
# Deixe valores “mágicos” aqui em cima, e não espalhados pelo código.
# =============================================================================

# URL base da API da FIPE. Todos os endpoints são montados a partir dela.
BASE_URL = "https://veiculos.fipe.org.br/api/veiculos/"

# Endpoint da tabela de referência. Esse valor precisa ser passado sem a barra inicial
# porque a própria função monta a URL completa de forma segura.
ENDPOINT_TABELA_REFERENCIA = "ConsultarTabelaDeReferencia"

# Reproduzimos os principais headers usados no navegador para que o servidor aceite
# a requisição como se fosse um cliente real.
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    "referer": "https://veiculos.fipe.org.br/",
    "origin": "https://veiculos.fipe.org.br",
    "x-requested-with": "XMLHttpRequest",
    "accept": "application/json, text/javascript, */*; q=0.01",
}

# Diretório para armazenar os JSONs crus. O uso de Path é melhor do que concatenar
# strings manualmente, porque ele cuida de separadores, caminhos relativos e sistemas
# operacionais diferentes.
RAW_DIR = Path("data/raw")

# Controle de educação com o servidor: tempo de timeout, número de tentativas e tempo
# de espera antes de repetir a chamada.
TIMEOUT_SEGUNDOS = 5
MAX_TENTATIVAS = 3
PAUSA_ENTRE_TENTATIVAS = 4

# Logger do módulo. A configuração completa é feita em src/log_config.py.
logger = logging.getLogger(__name__)


# =============================================================================
# FUNÇÕES GENÉRICAS
# Serão reaproveitadas por TODAS as etapas da cascata (marcas, modelos...).
# =============================================================================

def criar_sessao() -> requests.Session:
    """Cria uma sessão HTTP que se comporta como o navegador."""
    sessao = requests.Session()
    sessao.headers.update(HEADERS)

    # Experimento útil: abrir a página principal pode preencher cookies e simular o
    # comportamento do navegador. Em muitos casos isso não é estritamente obrigatório,
    # mas ajuda quando a API exige contexto da sessão.
    try:
        sessao.get("https://veiculos.fipe.org.br/", timeout=TIMEOUT_SEGUNDOS)
        logger.debug("Página principal da FIPE acessada para inicializar a sessão.")
    except requests.RequestException as exc:
        logger.warning("Não foi possível acessar a página principal da FIPE: %s", exc)

    return sessao


def fazer_post(sessao: requests.Session, endpoint: str, payload: dict | None = None):
    """
    Faz um POST com retentativas e devolve o JSON da resposta.

    A função recebe o endpoint final e, opcionalmente, um payload. A ideia é reaproveitar
    a mesma lógica para todas as etapas da coleta (tabelas, marcas, modelos, anos...).
    """
    url_completa = f"{BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            # Quando o endpoint não exige corpo, usamos json=None; quando exige, passamos
            # os dados em json=payload. Isso funciona para as chamadas da FIPE que usam
            # JSON no body.
            resposta = sessao.post(url_completa, json=payload, timeout=TIMEOUT_SEGUNDOS)
            resposta.raise_for_status()
            return resposta.json()
        except requests.RequestException as erro:
            logger.error("Tentativa %s falhou para %s: %s", tentativa, url_completa, erro)

            if tentativa < MAX_TENTATIVAS:
                # Backoff exponencial: a espera aumenta a cada falha para evitar sobrecarregar
                # o servidor e dar tempo para a conexão estabilizar.
                espera = PAUSA_ENTRE_TENTATIVAS * (2 ** (tentativa - 1))
                logger.info("Aguardando %s segundos antes da próxima tentativa...", espera)
                time.sleep(espera)
            else:
                # Se todas falham, o melhor é propagar a exceção para que a chamada seja
                # tratada no ponto do pipeline ao invés de continuar com dados inválidos.
                logger.error("Todas as tentativas falharam para o endpoint %s.", url_completa)
                raise


def salvar_json_bruto(dados, nome_base: str) -> Path:
    """Salva a resposta exatamente como veio, com a data da coleta no nome."""
    # Garante que o diretório exista antes de abrir o arquivo.
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Nome do arquivo com data e hora no formato DD-MM-YYYY_HHMMSS.
    arquivo_nome = f"{nome_base}_{datetime.now().strftime('%d-%m-%Y_%H%M%S')}.json"
    caminho_arquivo = RAW_DIR / arquivo_nome

    # Salva no formato JSON indentado e sem escapar caracteres UTF-8.
    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=4)

    logger.info("Arquivo bruto salvo em: %s", caminho_arquivo)
    return caminho_arquivo


# =============================================================================
# FUNÇÕES ESPECÍFICAS DE CADA ETAPA
# =============================================================================

def extrair_tabelas_referencia(sessao: requests.Session) -> list[dict]:
    """Busca a lista completa de meses de referência (2001 até hoje)."""
    dados = fazer_post(sessao, ENDPOINT_TABELA_REFERENCIA)

    # Validação mínima: a resposta deve ser uma lista e cada item deve ter ao menos os
    # campos essenciais para a próxima etapa.
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


# Mais tarde, as próximas etapas entram aqui, seguindo o mesmo padrão:
# def extrair_marcas(sessao, codigo_referencia): ...
# def extrair_modelos(sessao, codigo_referencia, codigo_marca): ...


# =============================================================================
# EXECUÇÃO DIRETA (para testar este módulo isoladamente)
# =============================================================================

if __name__ == "__main__":
    # A chamada direta serve para testar o módulo sozinho.
    configurar_logging()
    sessao = criar_sessao()
    dados = extrair_tabelas_referencia(sessao)
    logger.info("Coleta finalizada. Total de meses recebidos: %s", len(dados))