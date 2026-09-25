# Metodologia técnica

## Problema

O desafio consiste em prever precipitação média mensal, em mm/dia, para 78.561 pontos de uma grade espacial da América do Sul durante os 24 meses de 2023 e 2024.

## Dados

O conjunto de treinamento contém 996 meses, de janeiro de 1940 a dezembro de 2022. O conjunto de teste possui 24 meses e nove variáveis atmosféricas. Todos os arquivos são fornecidos pelos organizadores no formato NetCDF.

## Referência climática

Para cada mês do calendário e ponto espacial, o pipeline estima:

- média histórica na janela de 1983 a 2022;
- tendência linear espacial;
- redução de 50% na inclinação para limitar extrapolações.

Essa referência representa sazonalidade, heterogeneidade espacial e mudança gradual de longo prazo.

## Engenharia de atributos

Para cada uma das nove variáveis atmosféricas são criados dois atributos:

1. valor bruto;
2. anomalia em relação à climatologia mensal de 1993 a 2022.

Também são incluídos latitude, longitude, seno e cosseno do mês previsto, referência climática e logaritmo da referência. O conjunto final possui 24 atributos.

## Amostragem

São selecionados 4.000 pontos sem reposição em cada mês de 1993 a 2022. A semente fixa `20260923` garante reprodutibilidade. O treinamento reúne 1.440.000 observações.

## Modelo

O XGBoost estima o resíduo entre a precipitação observada e a referência climática.

| Hiperparâmetro | Valor |
|---|---:|
| Estimadores | 600 |
| Profundidade máxima | 8 |
| Taxa de aprendizado | 0,04 |
| Subamostragem | 0,80 |
| Amostragem de colunas | 0,85 |
| Peso mínimo do nó filho | 30 |
| Regularização L2 | 20 |
| Regularização L1 | 0,10 |
| Método | hist |

A previsão final é dada por:

```text
previsão = máximo(referência climática + 0,5 × anomalia prevista, 0)
```

## Validação temporal

Janeiro de 2021 a dezembro de 2022 formam o bloco de avaliação. A referência comparada usa somente alvos até dezembro de 2020. A divisão não é aleatória.

| Método | RMSE |
|---|---:|
| Referência climática com tendência | 1,851973 |
| Modelo final | 1,839010 |

## Auditoria temporal

| Componente | Limite ou origem |
|---|---|
| Alvo de treinamento | Até dezembro de 2022 |
| Tendência climática | 1983–2022 |
| Climatologia atmosférica | 1993–2022 |
| Variáveis para cada previsão | `time_origem` do mês anterior |
| Precipitação observada em 2023–2024 | Não utilizada |
| `tp_ultima_obs` | Excluída do modelo |

## Validação da submissão

Antes da gravação final, o pipeline confirma:

- 1.885.464 linhas;
- IDs únicos e na ordem do arquivo de exemplo;
- 24 meses e 78.561 pontos por mês;
- ausência de NaN e infinito;
- ausência de precipitação negativa;
- contagem física de linhas após a gravação.

## Limitações

A validação usa um único bloco histórico de 24 meses. A amostragem reduz o custo computacional, mas não utiliza todos os pontos da grade no treinamento do XGBoost. A tendência linear é uma aproximação simples para mudanças climáticas de longo prazo.
