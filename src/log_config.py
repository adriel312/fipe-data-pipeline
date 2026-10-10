import logging
from pathlib import Path

# Diretório onde os logs do pipeline serão gravados.
LOG_DIR = Path("logs")


def configurar_logging():
    # 1. Cria a pasta de logs no caso de ela ainda não existir.
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    caminho_log = LOG_DIR / "pipeline.log"

    # 2. Handler para a saída no terminal.
    # O terminal recebe apenas eventos INFO em diante, para ficar mais limpo e útil.
    handler_terminal = logging.StreamHandler()
    handler_terminal.setLevel(logging.INFO)

    # 3. Handler para o arquivo de log.
    # Como o arquivo guardará detalhes mais completos, usamos DEBUG.
    handler_arquivo = logging.FileHandler(caminho_log, encoding="utf-8")
    handler_arquivo.setLevel(logging.DEBUG)

    # 4. Configuração final da biblioteca logging.
    # O parâmetro force=True garante que a configuração seja aplicada mesmo se algum código anterior já tenha chamado basicConfig.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[handler_terminal, handler_arquivo],
        force=True,
    )

    # 5. Silencia bibliotecas barulhentas, como requests e urllib3.
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
