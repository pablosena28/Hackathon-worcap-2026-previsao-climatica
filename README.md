# Previsão climática de precipitação na América do Sul

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![XGBoost](https://img.shields.io/badge/Modelo-XGBoost-EB5B28)](https://xgboost.readthedocs.io/)
[![NetCDF](https://img.shields.io/badge/Dados-NetCDF-2E8B57)](https://www.unidata.ucar.edu/software/netcdf/)
[![Kaggle](https://img.shields.io/badge/Competição-Kaggle-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/competitions/previsao-climatica-de-precipitacao-sobre-a-america-do-sul)
[![License](https://img.shields.io/badge/Código-MIT-green.svg)](LICENSE)

Solução desenvolvida para o **Hackathon WorCAP 2026**, promovido pelo Instituto Nacional de Pesquisas Espaciais. O projeto estima a precipitação média mensal em uma grade de 0,25° sobre a América do Sul para 2023 e 2024.

O pipeline combina uma referência climática espacial com tendência suavizada e um modelo XGBoost treinado para prever anomalias de precipitação a partir de variáveis atmosféricas.

## Destaques do projeto

- processamento de séries climáticas multidimensionais em arquivos NetCDF;
- engenharia de 24 atributos espaciais, temporais e atmosféricos;
- treinamento de XGBoost com **1.440.000 observações**;
- validação estritamente temporal em 2021 e 2022;
- controle explícito contra vazamento de dados;
- geração automatizada de **1.885.464 previsões**;
- verificações de integridade, ordem dos IDs e plausibilidade física;
- notebook pronto para execução no Kaggle.

## Resultado da validação

| Método | RMSE |
|---|---:|
| Referência climática com tendência | 1,85197 |
| Modelo final de anomalias | **1,83901** |
| Redução relativa aproximada | **0,70%** |

> Os valores representam validação histórica e não a pontuação oficial do conjunto privado do Kaggle.

## Arquitetura da solução

1. **Referência climática:** média espacial mensal e tendência linear calculadas entre 1983 e 2022.
2. **Anomalias atmosféricas:** valores comparados à climatologia mensal de 1993 a 2022.
3. **Atributos:** nove variáveis brutas, nove anomalias, latitude, longitude, sazonalidade e duas representações da referência climática.
4. **Aprendizado:** XGBoost treinado sobre o resíduo entre a precipitação observada e a referência climática.
5. **Previsão final:** referência climática + 50% da anomalia estimada, limitada inferiormente a zero.

## Variáveis atmosféricas

| Variável | Descrição |
|---|---|
| `t2` | Temperatura a 2 metros |
| `cloud_cover` | Cobertura de nuvens |
| `shum_850` | Umidade específica em 850 hPa |
| `surface_pressure` | Pressão na superfície |
| `u_850` e `v_850` | Componentes zonal e meridional do vento em 850 hPa |
| `temperature_850` | Temperatura em 850 hPa |
| `rel_hum_850` | Umidade relativa em 850 hPa |
| `geopotential_850` | Geopotencial em 850 hPa |

## Prevenção de vazamento temporal

A solução foi estruturada para que a previsão de cada mês utilize apenas informações associadas ao fim do mês anterior:

- o alvo de treinamento termina em dezembro de 2022;
- tendências e climatologias são calculadas apenas com o conjunto de treinamento;
- as variáveis de teste usam o campo `time_origem`, correspondente ao mês anterior;
- `tp_ultima_obs` foi excluída dos atributos para evitar uso recursivo ou interpretação temporal inadequada;
- a validação mantém 2021–2022 fora do período usado pela referência avaliada.

Mais detalhes estão em [docs/METODOLOGIA.md](docs/METODOLOGIA.md).

## Estrutura do repositório

```text
.
├── notebooks/
│   └── Notebook_WorCAP_2026.ipynb
├── src/
│   └── modelo_worcap_2026.py
├── resultados/
│   └── metricas_modelo.json
├── docs/
│   └── METODOLOGIA.md
├── .gitignore
├── LICENSE
├── requirements.txt
└── README.md
```

## Como executar

### Kaggle

1. Acesse a [competição](https://www.kaggle.com/competitions/previsao-climatica-de-precipitacao-sobre-a-america-do-sul).
2. Adicione os dados da competição como entrada de um notebook.
3. Importe [notebooks/Notebook_WorCAP_2026.ipynb](notebooks/Notebook_WorCAP_2026.ipynb).
4. Confirme o caminho de `DATA_DIR`.
5. Execute todas as células.

### Linha de comando

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/modelo_worcap_2026.py \
  --dados /caminho/para/dados_worcap \
  --saida ./resultados
```

No Windows, ative o ambiente com `.venv\Scripts\activate`.

## Arquivos gerados

A execução produz:

- `submission_worcap_2026.csv`;
- `modelo_xgboost_worcap.json`;
- `metricas_modelo.json`.

Os dados originais, o modelo treinado e o CSV final não são versionados devido ao tamanho e às regras de distribuição da competição.

## Tecnologias e competências demonstradas

- Python, NumPy, pandas e xarray;
- processamento de dados NetCDF;
- machine learning com XGBoost;
- engenharia de atributos;
- séries temporais e climatologia;
- validação temporal;
- controle de data leakage;
- otimização de memória;
- automação e validação de arquivos;
- documentação técnica e reprodutibilidade.

## Dados

Foram utilizados somente os arquivos oficiais fornecidos pela competição. Não foram incorporados dados externos.

- [Hackathon WorCAP 2026 no INPE](https://www.gov.br/inpe/pt-br/eventos/worcap-2026/hackathon)
- [Competição no Kaggle](https://www.kaggle.com/competitions/previsao-climatica-de-precipitacao-sobre-a-america-do-sul)

## Autor

**Pablo Matheus Sena dos Santos**

Projeto de portfólio em ciência de dados, aprendizado de máquina e análise climática.
