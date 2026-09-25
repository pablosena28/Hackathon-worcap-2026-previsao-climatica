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
├── scripts/
│   └── baixar_dados.py
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

## Como reproduzir o projeto

A maneira mais simples é executar o notebook dentro do Kaggle. Também é possível reproduzir todo o pipeline em um computador local. Em ambos os casos, é necessário possuir uma conta gratuita no Kaggle e aceitar as regras da competição para ter acesso autorizado aos dados.

### Opção 1  Executar no Kaggle

1. Entre na [página da competição](https://www.kaggle.com/competitions/previsao-climatica-de-precipitacao-sobre-a-america-do-sul), faça login e aceite as regras.
2. Baixe [notebooks/Notebook_WorCAP_2026.ipynb](notebooks/Notebook_WorCAP_2026.ipynb) neste repositório.
3. No Kaggle, escolha **Create > New Notebook** e use **File > Import Notebook** para enviar o arquivo.
4. No painel direito do notebook, selecione **Add Input** e procure por **Previsão Climática de Precipitação sobre a América do Sul**.
5. Confirme que a pasta de entrada é:

```text
/kaggle/input/previsao-climatica-de-precipitacao-sobre-a-america-do-sul
```

6. Escolha **Run All**. O notebook instalará as dependências, auditará os dados, treinará o modelo e criará a submissão.
7. Ao final, abra a pasta `/kaggle/working/resultados_worcap` para baixar os arquivos gerados.

### Opção 2  Executar localmente

#### 1  Pré requisitos

- Python 3.10 ou superior;
- Git;
- pelo menos 16 GB de memória RAM recomendados;
- conta no Kaggle com as regras da competição aceitas;
- credenciais da API do Kaggle configuradas no computador.

#### 2  Clonar o repositório

```bash
git clone https://github.com/pablosena28/Hackathon-worcap-2026-previsao-climatica.git
cd Hackathon-worcap-2026-previsao-climatica
```

#### 3  Criar o ambiente e instalar as dependências

Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 4  Configurar o acesso ao Kaggle

Na sua conta do Kaggle, abra **Settings > API** e gere uma credencial. Siga as instruções exibidas pelo Kaggle para autenticar o `kagglehub`. A conta precisa ter aceitado as regras da competição.

#### 5  Baixar os dados oficiais

```bash
python scripts/baixar_dados.py
```

O comando exibirá no terminal o caminho completo da pasta em que os arquivos foram armazenados. Copie esse caminho para o próximo passo.

#### 6  Executar o pipeline

```bash
python src/modelo_worcap_2026.py \
  --dados "CAMINHO_EXIBIDO_PELO_DOWNLOAD" \
  --saida ./resultados_worcap
```

No Windows PowerShell, use uma única linha:

```powershell
python src/modelo_worcap_2026.py --dados "CAMINHO_EXIBIDO_PELO_DOWNLOAD" --saida .\resultados_worcap
```

#### 7  Conferir os resultados

Depois da execução, a pasta `resultados_worcap` conterá:

- `submission_worcap_2026.csv`, com 1.885.464 previsões;
- `modelo_xgboost_worcap.json`, com o modelo treinado;
- `metricas_modelo.json`, com métricas e estatísticas da execução.

Uma execução bem-sucedida termina com o resumo das métricas no terminal. O código interrompe automaticamente a execução se encontrar IDs duplicados, valores ausentes, previsões negativas ou um CSV truncado.

## Solução de problemas

- **Acesso negado ao baixar os dados:** confirme que entrou na página da competição e aceitou as regras.
- **Arquivo não encontrado:** use exatamente a pasta impressa por `scripts/baixar_dados.py` no argumento `--dados`.
- **Memória insuficiente:** execute o notebook no Kaggle, que é a rota recomendada.
- **PowerShell bloqueou a ativação:** execute `Set-ExecutionPolicy -Scope Process Bypass` e tente ativar novamente.
- **Pacote ausente:** confirme que o ambiente virtual está ativo e repita `pip install -r requirements.txt`.

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
