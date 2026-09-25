"""Baixa os dados oficiais da competição WorCAP 2026 pelo KaggleHub.

Antes de executar, faça login no Kaggle, aceite as regras da competição
e configure as credenciais conforme https://github.com/Kaggle/kagglehub.
"""

from pathlib import Path

import kagglehub


COMPETICAO = "previsao-climatica-de-precipitacao-sobre-a-america-do-sul"


def main() -> None:
    caminho = Path(kagglehub.competition_download(COMPETICAO)).resolve()
    print("\nDownload concluído.")
    print("Use este caminho no argumento --dados:")
    print(caminho)


if __name__ == "__main__":
    main()
