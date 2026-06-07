from pathlib import Path
import re
import unicodedata

import pandas as pd


ROOT = Path(".")
OUTPUT_DIR = ROOT / "data/processed/dashboard"


GAME_COLUMNS = [
    "ano",
    "rodada",
    "data",
    "hora",
    "local",
    "mandante",
    "visitante",
    "gols_mandante",
    "gols_visitante",
    "resultado",
    "vencedor",
    "publico_a_venda",
    "publico_devolvido",
    "publico_vendido",
    "arrecadacao_bruta",
    "renda_mandante",
    "renda_visitante",
    "financeiro_status",
    "publico_informado",
    "cartoes_amarelos_mandante",
    "cartoes_vermelhos_mandante",
    "cartoes_amarelos_visitante",
    "cartoes_vermelhos_visitante",
    "id_tabela_srgoool",
    "tem_publico",
    "tem_arrecadacao",
    "tem_financeiro",
    "sumula_url",
    "boletim_financeiro_url",
    "relatorio_jogo_url",
    "fonte_esportiva",
    "fonte_financeira",
    "fonte_url",
    "status_coleta",
]


STANDING_COLUMNS = [
    "ano",
    "posicao",
    "time",
    "pts",
    "jogos",
    "vitorias",
    "empates",
    "derrotas",
    "gols_pro",
    "gols_contra",
    "saldo_gols",
    "cartoes_amarelos",
    "cartoes_vermelhos",
    "aproveitamento",
    "ingressos",
    "publico_pagante",
    "renda_bruta",
    "renda_liquida",
    "fonte_financeira",
    "fonte",
    "fonte_url",
    "status_coleta",
]


def ensure_columns(df, columns):
    for column in columns:
        if column not in df.columns:
            df[column] = pd.NA
    return df[columns]


def latest_csv(pattern):
    files = sorted(ROOT.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"Nenhum arquivo encontrado para {pattern}")
    return files[0]


def normalize_key(value):
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    ignored = {"fc", "ec", "saf", "sa", "f", "clube", "esporte", "futebol", "regatas"}
    text = " ".join(tok for tok in text.split() if tok not in ignored)
    aliases = {
        "america fc": "america",
        "america mg": "america",
        "america saf": "america",
        "athletico pr": "athletico paranaense",
        "athletico paranaense": "athletico paranaense",
        "atletico pr": "athletico paranaense",
        "atletico paranaense": "athletico paranaense",
        "atletico mg": "atletico mineiro",
        "atletico mineiro": "atletico mineiro",
        "atletico go": "atletico goianiense",
        "atletico goianiense": "atletico goianiense",
        "botafogo rj": "botafogo",
        "corinthians sp": "corinthians",
        "coritiba pr": "coritiba",
        "cruzeiro mg": "cruzeiro",
        "flamengo rj": "flamengo",
        "fluminense rj": "fluminense",
        "gremio rs": "gremio",
        "palmeiras sp": "palmeiras",
        "red bull bragantino": "bragantino",
        "bragantino": "bragantino",
        "santos fc": "santos",
        "santos sp": "santos",
        "sao caetano sp": "sao caetano",
        "sao paulo sp": "sao paulo",
        "sport pe": "sport",
        "sport recife": "sport",
        "vasco rj": "vasco",
        "vasco da gama": "vasco",
        "vitoria ba": "vitoria",
    }
    return aliases.get(text, text)


def canonical_team_name(value):
    if pd.isna(value):
        return value
    original = str(value).strip()
    if not original or original.lower() == "nan":
        return original
    if normalize_key(original) == "empate":
        return "Empate"

    key = normalize_key(original)
    startswith_aliases = [
        ("gremio prudente", "Prudente"),
        ("gremio", "Grêmio"),
        ("vitoria", "Vitória"),
        ("palmeiras", "Palmeiras"),
        ("parana", "Paraná"),
        ("ponte preta", "Ponte Preta"),
        ("portuguesa", "Portuguesa"),
        ("santos", "Santos"),
        ("sport", "Sport"),
        ("sao paulo", "São Paulo"),
        ("vasco", "Vasco da Gama"),
        ("america", "América Mineiro"),
        ("flamengo", "Flamengo"),
        ("fluminense", "Fluminense"),
        ("fortaleza", "Fortaleza"),
        ("avai", "Avaí"),
        ("bahia", "Bahia"),
        ("chapecoense", "Chapecoense"),
        ("botafogo", "Botafogo"),
        ("cruzeiro", "Cruzeiro"),
        ("corinthians", "Corinthians"),
        ("coritiba", "Coritiba"),
        ("figueirense", "Figueirense"),
        ("sao caetano", "São Caetano"),
        ("bragantino", "Red Bull Bragantino"),
        ("goias", "Goiás"),
        ("ceara", "Ceará"),
        ("cuiaba", "Cuiabá"),
        ("criciuma", "Criciúma"),
        ("juventude", "Juventude"),
        ("nautico", "Náutico"),
        ("guarani", "Guarani"),
        ("paysandu", "Paysandu"),
        ("santa cruz", "Santa Cruz"),
        ("santo andre", "Santo André"),
        ("brasiliense", "Brasiliense"),
        ("barueri", "Barueri"),
        ("ipatinga", "Ipatinga"),
        ("joinville", "Joinville"),
        ("prudente", "Prudente"),
        ("csa", "CSA"),
        ("mirassol", "Mirassol"),
    ]
    for prefix, canonical in startswith_aliases:
        if key.startswith(prefix):
            return canonical

    exact_aliases = {
        "athletico pr": "Athletico Paranaense",
        "athletico paranaense": "Athletico Paranaense",
        "atletico pr": "Athletico Paranaense",
        "atletico paranaense": "Athletico Paranaense",
        "atletico go": "Atlético Goianiense",
        "atletico goianiense": "Atlético Goianiense",
        "atletico mg": "Atlético Mineiro",
        "atletico mineiro": "Atlético Mineiro",
        "atletico": "Atlético Mineiro",
    }
    if key in exact_aliases:
        return exact_aliases[key]

    if key.startswith("atletico goianiense"):
        return "Atlético Goianiense"
    if key.startswith("atletico mineiro"):
        return "Atlético Mineiro"
    return original


def canonical_team_name_for_row(row, column):
    value = row.get(column)
    if pd.isna(value):
        return value
    key = normalize_key(value)
    if key != "atletico":
        return canonical_team_name(value)

    ano = pd.to_numeric(row.get("ano"), errors="coerce")
    ano = int(ano) if pd.notna(ano) else None
    fonte = str(row.get("fonte_esportiva", row.get("fonte", ""))).upper()
    pts = pd.to_numeric(row.get("pts"), errors="coerce")

    if ano == 2006 and fonte == "RSSSF":
        return "Athletico Paranaense"
    if ano in {2021, 2022}:
        return "AtlÃ©tico Goianiense"
    if ano == 2020 and pd.notna(pts):
        return "AtlÃ©tico Goianiense" if int(pts) == 50 else "AtlÃ©tico Mineiro"
    if ano in {2020, 2021, 2022}:
        return "AtlÃ©tico Goianiense"
    return "AtlÃ©tico Mineiro"


def canonical_team_name_for_row(row, column):
    value = row.get(column)
    if pd.isna(value):
        return value
    key = normalize_key(value)
    if key != "atletico":
        return canonical_team_name(value)

    ano = pd.to_numeric(row.get("ano"), errors="coerce")
    ano = int(ano) if pd.notna(ano) else None
    fonte = str(row.get("fonte_esportiva", row.get("fonte", ""))).upper()
    pts = pd.to_numeric(row.get("pts"), errors="coerce")

    if ano == 2006 and fonte == "RSSSF":
        return "Athletico Paranaense"
    if ano in {2021, 2022}:
        return "Atl\u00e9tico Goianiense"
    if ano == 2020 and pd.notna(pts):
        return "Atl\u00e9tico Goianiense" if int(pts) == 50 else "Atl\u00e9tico Mineiro"
    if ano in {2020, 2021, 2022}:
        return "Atl\u00e9tico Goianiense"
    return "Atl\u00e9tico Mineiro"


def canonicalize_names(games, standings):
    games = games.copy()
    standings = standings.copy()
    for column in ["mandante", "visitante", "vencedor"]:
        games[column] = games.apply(lambda row: canonical_team_name_for_row(row, column), axis=1)
    standings["time"] = standings.apply(lambda row: canonical_team_name_for_row(row, "time"), axis=1)
    invalid_pattern = r"(?i)teams placed|power failure|qualified to|match annulled|except santos"
    valid_games = ~(
        games["mandante"].astype(str).str.contains(invalid_pattern, na=False)
        | games["visitante"].astype(str).str.contains(invalid_pattern, na=False)
    )
    games = games[valid_games].copy()
    return games, standings


def to_numeric_key(series):
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def prepare_historical_games():
    df = pd.read_csv(latest_csv("data/processed/pontos_corridos/brasileirao_pontos_corridos_jogos_*.csv"))
    df = df[df["ano"] < 2018].copy()
    df["data"] = df.get("data_rsssf")
    df["hora"] = pd.NA
    df["local"] = pd.NA
    df["publico_a_venda"] = pd.NA
    df["publico_devolvido"] = pd.NA
    df["publico_vendido"] = pd.NA
    df["arrecadacao_bruta"] = pd.NA
    df["renda_mandante"] = pd.NA
    df["renda_visitante"] = pd.NA
    df["financeiro_status"] = "fora_cobertura_cbf"
    df["publico_informado"] = pd.NA
    df["cartoes_amarelos_mandante"] = pd.NA
    df["cartoes_vermelhos_mandante"] = pd.NA
    df["cartoes_amarelos_visitante"] = pd.NA
    df["cartoes_vermelhos_visitante"] = pd.NA
    df["id_tabela_srgoool"] = pd.NA
    df["tem_publico"] = False
    df["tem_arrecadacao"] = False
    df["tem_financeiro"] = False
    df["sumula_url"] = pd.NA
    df["boletim_financeiro_url"] = pd.NA
    df["relatorio_jogo_url"] = pd.NA
    df["fonte_esportiva"] = "RSSSF"
    df["fonte_financeira"] = pd.NA
    return ensure_columns(df, GAME_COLUMNS)


def prepare_cbf_games():
    df = pd.read_csv(latest_csv("data/processed/cbf_brasileirao/brasileirao_serie_a_jogos_*.csv"))
    df = df.copy()
    df["fonte_esportiva"] = "CBF"
    df["fonte_financeira"] = "CBF - Boletim Financeiro"
    df["fonte_url"] = df["boletim_financeiro_url"]
    df["status_coleta"] = "ok"
    df["tem_publico"] = df["publico_vendido"].notna()
    df["tem_arrecadacao"] = df["arrecadacao_bruta"].notna()
    df["tem_financeiro"] = df["tem_publico"] & df["tem_arrecadacao"]
    return ensure_columns(df, GAME_COLUMNS)


def prepare_historical_standings():
    df = pd.read_csv(latest_csv("data/processed/pontos_corridos/brasileirao_pontos_corridos_classificacao_*.csv"))
    df = df[df["ano"] < 2018].copy()
    df["cartoes_amarelos"] = pd.NA
    df["cartoes_vermelhos"] = pd.NA
    df["aproveitamento"] = pd.NA
    df["ingressos"] = pd.NA
    df["publico_pagante"] = pd.NA
    df["renda_bruta"] = pd.NA
    df["renda_liquida"] = pd.NA
    df["fonte_financeira"] = pd.NA
    return ensure_columns(df, STANDING_COLUMNS)


def prepare_cbf_standings():
    df = pd.read_csv(latest_csv("data/processed/cbf_brasileirao/brasileirao_serie_a_classificacao_*.csv"))
    df = df.copy()
    df["fonte"] = "CBF"
    df["fonte_url"] = pd.NA
    df["status_coleta"] = "ok"
    df["ingressos"] = pd.NA
    df["publico_pagante"] = pd.NA
    df["renda_bruta"] = pd.NA
    df["renda_liquida"] = pd.NA
    df["fonte_financeira"] = pd.NA
    return ensure_columns(df, STANDING_COLUMNS)


def srgoool_games_for_missing_years(games):
    try:
        srgoool_games = latest_csv("data/processed/srgoool/brasileirao_srgoool_jogos_*.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=GAME_COLUMNS)

    sr = pd.read_csv(srgoool_games)
    existing_years = set(pd.to_numeric(games["ano"], errors="coerce").dropna().astype(int))
    sr["ano_num"] = pd.to_numeric(sr["ano"], errors="coerce")
    sr = sr[~sr["ano_num"].isin(existing_years)].copy()
    if sr.empty:
        return pd.DataFrame(columns=GAME_COLUMNS)

    played = (
        sr.get("publico_informado", pd.Series(index=sr.index, dtype=object)).astype(str).str.upper().eq("S")
        | sr["publico_vendido"].notna()
        | sr["arrecadacao_bruta"].notna()
    )
    sr = sr[played].copy()
    if sr.empty:
        return pd.DataFrame(columns=GAME_COLUMNS)

    df = pd.DataFrame(
        {
            "ano": sr["ano"],
            "rodada": sr["rodada"],
            "data": sr["data"].replace("0000-00-00", pd.NA),
            "hora": sr["hora"].replace("00:00", pd.NA),
            "local": pd.NA,
            "mandante": sr["mandante"],
            "visitante": sr["visitante"],
            "gols_mandante": sr["gols_mandante"],
            "gols_visitante": sr["gols_visitante"],
            "resultado": sr["resultado"],
            "vencedor": sr["vencedor"],
            "publico_a_venda": sr["publico_a_venda"],
            "publico_devolvido": pd.NA,
            "publico_vendido": sr["publico_vendido"],
            "arrecadacao_bruta": sr["arrecadacao_bruta"],
            "renda_mandante": sr["renda_mandante"],
            "renda_visitante": sr["renda_visitante"],
            "financeiro_status": "ok_srgoool",
            "publico_informado": sr["publico_informado"],
            "cartoes_amarelos_mandante": sr["cartoes_amarelos_mandante"],
            "cartoes_vermelhos_mandante": sr["cartoes_vermelhos_mandante"],
            "cartoes_amarelos_visitante": sr["cartoes_amarelos_visitante"],
            "cartoes_vermelhos_visitante": sr["cartoes_vermelhos_visitante"],
            "id_tabela_srgoool": sr["id_tabela_srgoool"],
            "tem_publico": sr["publico_vendido"].notna(),
            "tem_arrecadacao": sr["arrecadacao_bruta"].notna(),
            "tem_financeiro": sr["publico_vendido"].notna() & sr["arrecadacao_bruta"].notna(),
            "sumula_url": pd.NA,
            "boletim_financeiro_url": sr["fonte_url"],
            "relatorio_jogo_url": pd.NA,
            "fonte_esportiva": "Sr.Goool",
            "fonte_financeira": "Sr.Goool",
            "fonte_url": sr["fonte_url"],
            "status_coleta": "ok",
        }
    )
    df.loc[~df["tem_financeiro"], "financeiro_status"] = "srgoool_sem_financeiro"
    return ensure_columns(df, GAME_COLUMNS)


def srgoool_standings_for_missing_years(standings):
    try:
        srgoool_standings = latest_csv("data/processed/srgoool/brasileirao_srgoool_classificacao_*.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=STANDING_COLUMNS)

    sr = pd.read_csv(srgoool_standings)
    existing_years = set(pd.to_numeric(standings["ano"], errors="coerce").dropna().astype(int))
    sr["ano_num"] = pd.to_numeric(sr["ano"], errors="coerce")
    sr = sr[~sr["ano_num"].isin(existing_years)].copy()
    if sr.empty:
        return pd.DataFrame(columns=STANDING_COLUMNS)

    df = pd.DataFrame(
        {
            "ano": sr["ano"],
            "posicao": sr["posicao"],
            "time": sr["time"],
            "pts": sr["pts"],
            "jogos": sr["jogos"],
            "vitorias": sr["vitorias"],
            "empates": sr["empates"],
            "derrotas": sr["derrotas"],
            "gols_pro": sr["gols_pro"],
            "gols_contra": sr["gols_contra"],
            "saldo_gols": sr["saldo_gols"],
            "cartoes_amarelos": sr["cartoes_amarelos"],
            "cartoes_vermelhos": sr["cartoes_vermelhos"],
            "aproveitamento": sr["aproveitamento"],
            "ingressos": sr["ingressos"],
            "publico_pagante": sr["publico_pagante"],
            "renda_bruta": sr["renda_bruta"],
            "renda_liquida": sr["renda_liquida"],
            "fonte_financeira": "Sr.Goool",
            "fonte": "Sr.Goool",
            "fonte_url": sr["fonte_url"],
            "status_coleta": "ok",
        }
    )
    return ensure_columns(df, STANDING_COLUMNS)


def enrich_games_with_srgoool(games):
    try:
        srgoool_games = latest_csv("data/processed/srgoool/brasileirao_srgoool_jogos_*.csv")
    except FileNotFoundError:
        return games, 0

    sr = pd.read_csv(srgoool_games)
    key_columns = ["ano", "rodada", "mandante_norm", "visitante_norm", "gols_mandante", "gols_visitante"]
    games = games.copy()
    games["mandante_norm"] = games["mandante"].map(normalize_key)
    games["visitante_norm"] = games["visitante"].map(normalize_key)
    for col in ["ano", "rodada", "gols_mandante", "gols_visitante"]:
        games[col] = to_numeric_key(games[col])
        sr[col] = to_numeric_key(sr[col])

    sr = sr.dropna(subset=key_columns)
    sr = sr.drop_duplicates(key_columns, keep="first")
    sr_columns = key_columns + [
        "publico_a_venda",
        "publico_vendido",
        "arrecadacao_bruta",
        "renda_mandante",
        "renda_visitante",
        "publico_informado",
        "cartoes_amarelos_mandante",
        "cartoes_vermelhos_mandante",
        "cartoes_amarelos_visitante",
        "cartoes_vermelhos_visitante",
        "id_tabela_srgoool",
        "fonte_url",
    ]
    merged = games.merge(sr[sr_columns], on=key_columns, how="left", suffixes=("", "_srgoool"))
    matched = merged["id_tabela_srgoool_srgoool"].notna()

    for col in [
        "publico_a_venda",
        "publico_vendido",
        "arrecadacao_bruta",
        "renda_mandante",
        "renda_visitante",
        "publico_informado",
        "cartoes_amarelos_mandante",
        "cartoes_vermelhos_mandante",
        "cartoes_amarelos_visitante",
        "cartoes_vermelhos_visitante",
        "id_tabela_srgoool",
    ]:
        sr_col = f"{col}_srgoool"
        if sr_col in merged.columns:
            merged[col] = merged[sr_col].combine_first(merged[col])

    financial_match = matched & (
        merged["publico_vendido_srgoool"].notna() | merged["arrecadacao_bruta_srgoool"].notna()
    )
    merged.loc[financial_match, "financeiro_status"] = "ok_srgoool"
    merged.loc[financial_match, "fonte_financeira"] = "Sr.Goool"
    merged.loc[financial_match, "boletim_financeiro_url"] = merged.loc[financial_match, "fonte_url_srgoool"]
    merged["tem_publico"] = merged["publico_vendido"].notna()
    merged["tem_arrecadacao"] = merged["arrecadacao_bruta"].notna()
    merged["tem_financeiro"] = merged["tem_publico"] & merged["tem_arrecadacao"]

    drop_cols = [
        col
        for col in merged.columns
        if col.endswith("_srgoool") and col not in GAME_COLUMNS
    ]
    merged = merged.drop(columns=drop_cols + ["mandante_norm", "visitante_norm"])
    return ensure_columns(merged, GAME_COLUMNS), int(matched.sum())


def enrich_standings_with_srgoool(standings):
    try:
        srgoool_standings = latest_csv("data/processed/srgoool/brasileirao_srgoool_classificacao_*.csv")
    except FileNotFoundError:
        return standings, 0

    sr = pd.read_csv(srgoool_standings)
    standings = standings.copy()
    standings["time_norm"] = standings["time"].map(normalize_key)
    standings["ano"] = to_numeric_key(standings["ano"])
    sr["ano"] = to_numeric_key(sr["ano"])
    sr = sr.dropna(subset=["ano", "time_norm"]).drop_duplicates(["ano", "time_norm"], keep="first")
    sr_columns = [
        "ano",
        "time_norm",
        "cartoes_amarelos",
        "cartoes_vermelhos",
        "aproveitamento",
        "ingressos",
        "publico_pagante",
        "renda_bruta",
        "renda_liquida",
        "fonte_url",
    ]
    merged = standings.merge(sr[sr_columns], on=["ano", "time_norm"], how="left", suffixes=("", "_srgoool"))
    matched = merged["fonte_url_srgoool"].notna()

    for col in [
        "cartoes_amarelos",
        "cartoes_vermelhos",
        "aproveitamento",
        "ingressos",
        "publico_pagante",
        "renda_bruta",
        "renda_liquida",
    ]:
        sr_col = f"{col}_srgoool"
        if sr_col in merged.columns:
            merged[col] = merged[sr_col].combine_first(merged[col])

    merged.loc[matched, "fonte_financeira"] = "Sr.Goool"
    drop_cols = [
        col
        for col in merged.columns
        if col.endswith("_srgoool") and col not in STANDING_COLUMNS
    ]
    merged = merged.drop(columns=drop_cols + ["time_norm"])
    return ensure_columns(merged, STANDING_COLUMNS), int(matched.sum())


def write_csv(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def main():
    games = pd.concat([prepare_historical_games(), prepare_cbf_games()], ignore_index=True)
    standings = pd.concat([prepare_historical_standings(), prepare_cbf_standings()], ignore_index=True)
    games, srgoool_games_matched = enrich_games_with_srgoool(games)
    standings, srgoool_standings_matched = enrich_standings_with_srgoool(standings)
    games = pd.concat([games, srgoool_games_for_missing_years(games)], ignore_index=True)
    standings = pd.concat([standings, srgoool_standings_for_missing_years(standings)], ignore_index=True)
    games, standings = canonicalize_names(games, standings)

    games = games.sort_values(["ano", "rodada", "mandante", "visitante"]).reset_index(drop=True)
    standings = standings.sort_values(["ano", "posicao"]).reset_index(drop=True)

    write_csv(OUTPUT_DIR / "base_jogos_brasileirao_dashboard.csv", games)
    write_csv(OUTPUT_DIR / "base_classificacao_brasileirao_dashboard.csv", standings)

    print(f"Jogos consolidados: {len(games)}")
    print(f"Classificacao consolidada: {len(standings)}")
    print(f"Jogos cruzados com Sr.Goool: {srgoool_games_matched}")
    print(f"Classificacao cruzada com Sr.Goool: {srgoool_standings_matched}")
    print(f"Jogos com publico/arrecadacao: {int(games['tem_financeiro'].sum())}")
    print(f"Saida: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
