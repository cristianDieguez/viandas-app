import pandas as pd


def construir_historico(reportes):
    rows = []

    for data in reportes:
        mes = data["mes"]

        for f in data["ahorro_real"]:
            rows.append({
                "mes": mes,
                "familia": f,
                "ahorro": data["ahorro_real"][f],
                "pct": data["pct_ahorro"][f] * 100
            })

    df = pd.DataFrame(rows)

    df["mes"] = pd.to_datetime(df["mes"])
    df["anio"] = df["mes"].dt.year
    df["mes_num"] = df["mes"].dt.month

    df = df.sort_values("mes")

    # acumulados
    df["acum_anual"] = df.groupby(["familia","anio"])["ahorro"].cumsum()
    df["acum_total"] = df.groupby("familia")["ahorro"].cumsum()

    return df
