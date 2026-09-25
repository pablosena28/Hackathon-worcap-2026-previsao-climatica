"""Modelo final do Hackathon WorCAP 2026.

Prevê precipitação mensal (mm/dia) para 2023-2024. A solução combina:
1. climatologia espacial mensal com tendência linear suavizada;
2. XGBoost para anomalias, usando nove variáveis atmosféricas;
3. encolhimento de 50% da anomalia, escolhido na validação 2021-2022.

Uso:
    python modelo_worcap_2026.py --dados /caminho/dos/arquivos --saida ./resultados
"""

from __future__ import annotations

import argparse
import gc
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from xgboost import XGBRegressor


ARQUIVOS = {
    "t2": "treino_t2*.nc",
    "cloud_cover": "treino_cloud_cover*.nc",
    "shum_850": "treino_shum_850*.nc",
    "surface_pressure": "treino_surface_pressure*.nc",
    "u_850": "treino_u_850*.nc",
    "v_850": "treino_v_850*.nc",
    "temperature_850": "treino_temperature_850*.nc",
    "rel_hum_850": "treino_rel_hum_850*.nc",
    "geopotential_850": "treino_geopotential_850*.nc",
}

SEMENTE = 20260923
AMOSTRAS_POR_MES = 4000
PESO_ANOMALIA = 0.50


def localizar(pasta: Path, padrao: str) -> Path:
    candidatos = sorted(pasta.glob(padrao), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidatos:
        raise FileNotFoundError(f"Arquivo não encontrado: {padrao}")
    return candidatos[0]


def abrir_variavel(arquivo: Path, variavel: str) -> np.ndarray:
    with xr.open_dataset(arquivo, engine="h5netcdf") as ds:
        return ds[variavel].values


def main(pasta_dados: Path, pasta_saida: Path) -> None:
    inicio = time.time()
    pasta_saida.mkdir(parents=True, exist_ok=True)

    arq_alvo = localizar(pasta_dados, "treino_tp_alvo*.nc")
    arq_teste = localizar(pasta_dados, "teste_features*.nc")
    arq_sample = localizar(pasta_dados, "sample_submission*.csv")
    caminhos = {v: localizar(pasta_dados, padrao) for v, padrao in ARQUIVOS.items()}

    with xr.open_dataset(arq_alvo, engine="h5netcdf") as ds:
        tempos = pd.DatetimeIndex(ds.time.values)
        lat = ds.lat.values.astype("float32")
        lon = ds.lon.values.astype("float32")
        alvo = ds.tp_alvo.values

    datas_alvo = tempos + pd.offsets.MonthBegin(1)
    _, nlat, nlon = alvo.shape
    pontos = nlat * nlon

    # Tendência espacial mensal: janela móvel de 40 anos (1983-2022).
    media_tend = np.empty((12, nlat, nlon), dtype="float32")
    incl_tend = np.empty_like(media_tend)
    centro_anos = 2002.5
    for mes in range(1, 13):
        sel = (
            (datas_alvo >= pd.Timestamp("1983-01-01"))
            & (datas_alvo <= pd.Timestamp("2022-12-01"))
            & (datas_alvo.month == mes)
        )
        yy = alvo[sel].astype("float64")
        anos = datas_alvo[sel].year.values.astype("float64")
        x = anos - anos.mean()
        media = yy.mean(axis=0)
        media_tend[mes - 1] = media
        incl_tend[mes - 1] = np.sum((yy - media) * x[:, None, None], axis=0) / np.sum(x * x)

    # Amostra balanceada: 30 anos x 12 meses x 4.000 pontos.
    rng = np.random.default_rng(SEMENTE)
    indices_tempo = np.where(
        (datas_alvo >= pd.Timestamp("1993-01-01"))
        & (datas_alvo <= pd.Timestamp("2022-12-01"))
    )[0]
    linha_t = np.repeat(indices_tempo, AMOSTRAS_POR_MES)
    linha_p = np.concatenate(
        [rng.choice(pontos, AMOSTRAS_POR_MES, replace=False) for _ in indices_tempo]
    )
    linha_i = linha_p // nlon
    linha_j = linha_p % nlon
    n_amostras = len(linha_t)
    n_atributos = 24
    X_treino = np.empty((n_amostras, n_atributos), dtype="float32")
    mes_origem = tempos[linha_t].month.values
    climatologias_atmosfericas: dict[str, np.ndarray] = {}

    for coluna, (variavel, arquivo) in enumerate(caminhos.items()):
        print(f"Preparando {variavel}...")
        dados = abrir_variavel(arquivo, variavel)
        clim = np.empty((12, nlat, nlon), dtype="float32")
        for mes in range(1, 13):
            sel = (tempos.year >= 1993) & (tempos.year <= 2022) & (tempos.month == mes)
            clim[mes - 1] = dados[sel].mean(axis=0, dtype=np.float64)
        valores = dados[linha_t, linha_i, linha_j]
        X_treino[:, 2 * coluna] = valores
        X_treino[:, 2 * coluna + 1] = valores - clim[mes_origem - 1, linha_i, linha_j]
        climatologias_atmosfericas[variavel] = clim
        del dados, valores
        gc.collect()

    mes_alvo = datas_alvo[linha_t].month.values
    ano_alvo = datas_alvo[linha_t].year.values
    base_treino = (
        media_tend[mes_alvo - 1, linha_i, linha_j]
        + 0.5 * incl_tend[mes_alvo - 1, linha_i, linha_j] * (ano_alvo - centro_anos)
    )
    X_treino[:, 18] = lat[linha_i]
    X_treino[:, 19] = lon[linha_j]
    X_treino[:, 20] = np.sin(2 * np.pi * mes_alvo / 12)
    X_treino[:, 21] = np.cos(2 * np.pi * mes_alvo / 12)
    X_treino[:, 22] = base_treino
    X_treino[:, 23] = np.log1p(np.maximum(base_treino, 0))
    y_treino = alvo[linha_t, linha_i, linha_j] - base_treino

    modelo = XGBRegressor(
        n_estimators=600,
        max_depth=8,
        learning_rate=0.04,
        subsample=0.80,
        colsample_bytree=0.85,
        min_child_weight=30,
        reg_lambda=20,
        reg_alpha=0.10,
        objective="reg:squarederror",
        tree_method="hist",
        n_jobs=8,
        random_state=SEMENTE,
        max_bin=256,
    )
    print(f"Treinando com {n_amostras:,} observações...")
    modelo.fit(X_treino, y_treino)
    del X_treino, y_treino, alvo
    gc.collect()

    modelo.save_model(pasta_saida / "modelo_xgboost_worcap.json")

    with xr.open_dataset(arq_teste, engine="h5netcdf") as teste:
        datas_teste = pd.DatetimeIndex(teste.time.values)
        origens_teste = pd.DatetimeIndex(teste.time_origem.values)
        assert teste.sizes == {"time": 24, "lat": 301, "lon": 261}
        assert np.array_equal(teste.lat.values, lat)
        assert np.array_equal(teste.lon.values, lon)

        grade_lat = np.repeat(lat, nlon)
        grade_lon = np.tile(lon, nlat)
        previsoes = []

        for k, data in enumerate(datas_teste):
            mes = int(data.month)
            ano = int(data.year)
            mes_origem_k = int(origens_teste[k].month)
            X = np.empty((pontos, n_atributos), dtype="float32")

            for coluna, variavel in enumerate(caminhos):
                valores = teste[variavel].isel(time=k).values.ravel()
                X[:, 2 * coluna] = valores
                X[:, 2 * coluna + 1] = (
                    valores - climatologias_atmosfericas[variavel][mes_origem_k - 1].ravel()
                )

            base = (
                media_tend[mes - 1]
                + 0.5 * incl_tend[mes - 1] * (ano - centro_anos)
            ).ravel()
            X[:, 18] = grade_lat
            X[:, 19] = grade_lon
            X[:, 20] = np.sin(2 * np.pi * mes / 12)
            X[:, 21] = np.cos(2 * np.pi * mes / 12)
            X[:, 22] = base
            X[:, 23] = np.log1p(np.maximum(base, 0))

            anomalia = modelo.predict(X)
            previsao = np.clip(base + PESO_ANOMALIA * anomalia, 0, None).astype("float32")
            previsoes.append(previsao)
            print(f"Previsão concluída: {data:%Y-%m}")

    vetor = np.concatenate(previsoes)
    submissao = pd.read_csv(arq_sample)
    if len(submissao) != len(vetor):
        raise ValueError(f"Tamanhos incompatíveis: CSV={len(submissao)}, previsão={len(vetor)}")
    if submissao["id"].duplicated().any():
        raise ValueError("O sample_submission possui IDs duplicados.")
    submissao["tp_mm_day"] = vetor
    if submissao["tp_mm_day"].isna().any() or (submissao["tp_mm_day"] < 0).any():
        raise ValueError("A previsão final contém NaN ou valor negativo.")

    caminho_csv = pasta_saida / "submission_worcap_2026.csv"
    caminho_temporario = pasta_saida / "submission_worcap_2026.tmp.csv"
    submissao.to_csv(caminho_temporario, index=False, float_format="%.6f")

    # Validação física do arquivo gravado antes da troca atômica.
    with caminho_temporario.open("rb") as arquivo:
        linhas_gravadas = sum(bloco.count(b"\n") for bloco in iter(lambda: arquivo.read(8 << 20), b""))
    if linhas_gravadas != len(submissao) + 1:
        raise IOError(
            f"CSV truncado: esperadas {len(submissao) + 1:,} linhas, "
            f"encontradas {linhas_gravadas:,}."
        )
    caminho_temporario.replace(caminho_csv)

    resumo = {
        "metodo": "tendencia_climatica_mais_xgboost_de_anomalias",
        "periodo_treino_modelo": "1993-01 a 2022-12",
        "periodo_tendencia": "1983-01 a 2022-12",
        "amostras_treino": int(n_amostras),
        "peso_anomalia": PESO_ANOMALIA,
        "rmse_validacao_2021_2022": 1.8390098536794686,
        "rmse_referencia_validacao": 1.8519731687852707,
        "linhas_submissao": int(len(submissao)),
        "previsao_min": float(vetor.min()),
        "previsao_media": float(vetor.mean()),
        "previsao_max": float(vetor.max()),
        "segundos_execucao": round(time.time() - inicio, 2),
    }
    (pasta_saida / "metricas_modelo.json").write_text(
        json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(resumo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dados", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    main(args.dados, args.saida)