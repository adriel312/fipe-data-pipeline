import logging
from pathlib import Path

LOG_DIR = Path("logs")

def configurar_logging():
    # 1. Pasta de logs
    # TODO: criar LOG_DIR se não existir (mesma técnica do salvar_json_bruto)
    LOG_DIR.mkdir(Parents=True, exist_ok=True)
    caminho_log = LOG_DIR / "pipeline.log"

    # 2. Handler do terminal
    # TODO: criar um StreamHandler
    # TODO: definir o nível dele (INFO, para o terminal ficar limpo)

    # 3. Handler do arquivo
    # TODO: criar um FileHandler apontando para um arquivo dentro de LOG_DIR
    #       (passe encoding, por causa dos acentos)
    # TODO: definir o nível dele (DEBUG, para o arquivo guardar tudo)

    # 4. Juntar tudo
    logging.basicConfig(
        level=...,      # TODO: atenção, veja a explicação abaixo
        format=...,     # TODO
        datefmt=...,    # TODO
        handlers=[...], # TODO: os dois handlers
    )

    # 5. Silenciar bibliotecas barulhentas
    # TODO: veja a explicação abaixo