import argparse
import json
import re
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.srgoool.com.br"
PLUGIN_URL = BASE_URL + "/plugin/{ano}/Brasileirao/Serie-A"
OUTPUT_DIR = Path("data/processed/srgoool")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai jogos, publico, renda e cartoes do Brasileirao Serie A no Sr.Goool."
    )
    parser.add_argument("--ano-inicio", type=int, default=2003)
    parser.add_argument("--ano-fim", type=int, default=2025)
    parser.add_argument("--saida", default=str(OUTPUT_DIR))
    parser.add_argument("--delay", type=float, default=0.3)
    return parser.parse_args()


def make_session():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
            "Accept": "application/json,text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
    )
    return session


def request_with_retries(session, method, url, **kwargs):
    last_error = None
    for attempt in range(1, 6):
        try:
            response = session.request(method, url, timeout=60, **kwargs)
            if response.status_code < 500 and response.status_code != 429:
                response.raise_for_status()
                return response
            last_error = requests.HTTPError(f"HTTP {response.status_code} em {url}", response=response)
        except requests.RequestException as error:
            last_error = error

        if attempt < 5:
            time.sleep(min(2**attempt, 20))

    raise last_error


def parse_page_params(html):
    match = re.search(r"window\.pageParams\s*=\s*(\{.*?\});", html, flags=re.S)
    if not match:
        raise RuntimeError("window.pageParams nao encontrado")
    return json.loads(match.group(1))


def fetch_championship_id(session, ano):
    url = PLUGIN_URL.format(ano=ano)
    html = request_with_retries(session, "GET", url).text
    params = parse_page_params(html)
    return {
        "ano": ano,
        "id_campeonato": params.get("id_ano_campeonato") or params.get("c"),
        "plugin_url": url,
        "nome": params.get("campeonato"),
        "serie": params.get("serie"),
    }


def fetch_batch(session, calls):
    response = request_with_retries(
        session,
        "POST",
        BASE_URL + "/v1.3x/batch",
        json=calls,
        headers={"Content-Type": "application/json"},
    )
    return response.json()


def to_int(value):
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).replace(",", ".")))
    except ValueError:
        return None


def to_float(value):
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "."))
    except ValueError:
        return None


def split_datetime(value):
    if not value:
        return None, None
    text = str(value)
    if " " not in text:
        return text, None
    data, hora = text.split(" ", 1)
    return data, hora[:5]


def detect_winner(home_goals, away_goals, home_team, away_team):
    if home_goals is None or away_goals is None:
        return None
    if home_goals > away_goals:
        return home_team
    if away_goals > home_goals:
        return away_team
    return "Empate"


def clean_team_name(value):
    if not value:
        return None
    soup = BeautifulSoup(str(value), "html.parser")
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def normalize_key(value):
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [tok for tok in text.split() if tok not in {"fc", "ec", "saf", "sa", "f", "clube", "esporte", "futebol", "regatas"}]
    text = " ".join(tokens)
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


def extract_year(session, metadata, delay):
    ano = metadata["ano"]
    championship_id = metadata["id_campeonato"]
    calls = [
        {"url": f"campeonato/{championship_id}", "params": {}},
        {"url": f"campeonato/{championship_id}/fase", "params": {}},
        {"url": f"campeonato/{championship_id}/clube", "params": {}},
    ]
    base_result = fetch_batch(session, calls)
    championship = base_result[0].get("result") or {}
    fases = base_result[1].get("result") or []
    clubes = base_result[2].get("result") or []
    fase = next((item for item in fases if str(item.get("exibe_classificacao")) == "1"), fases[0] if fases else {})
    fase_id = fase.get("id") or championship.get("last_fase_classificacao") or "1"
    rodada = to_int(fase.get("max_rodada") or fase.get("last_rodada")) or 38

    time.sleep(delay)
    classification_result = fetch_batch(
        session,
        [
            {
                "url": f"campeonato/{championship_id}/classificacao",
                "params": {"fase": str(fase_id), "rodada": rodada, "simulados": {}},
            }
        ],
    )[0].get("result") or {}

    club_map = {str(item.get("id")): clean_team_name(item.get("name")) for item in clubes}
    games = []
    for item in classification_result.get("jogos") or []:
        home = club_map.get(str(item.get("id_clubem"))) or clean_team_name(item.get("clubem"))
        away = club_map.get(str(item.get("id_clubev"))) or clean_team_name(item.get("clubev"))
        data, hora = split_datetime(item.get("datahora"))
        home_goals = to_int(item.get("placarm_tn"))
        away_goals = to_int(item.get("placarv_tn"))
        games.append(
            {
                "ano": ano,
                "id_campeonato_srgoool": championship_id,
                "id_tabela_srgoool": item.get("id_tabela"),
                "rodada": to_int(item.get("rodada")),
                "data": data,
                "hora": hora,
                "mandante": home,
                "visitante": away,
                "mandante_norm": normalize_key(home),
                "visitante_norm": normalize_key(away),
                "gols_mandante": home_goals,
                "gols_visitante": away_goals,
                "resultado": f"{home_goals} x {away_goals}" if home_goals is not None and away_goals is not None else None,
                "vencedor": detect_winner(home_goals, away_goals, home, away),
                "publico_a_venda": to_int(item.get("in")),
                "publico_vendido": to_int(item.get("pu")),
                "arrecadacao_bruta": to_float(item.get("rb")),
                "renda_mandante": to_float(item.get("renda_mandante")),
                "renda_visitante": to_float(item.get("renda_visitante")),
                "publico_informado": item.get("publico_informado"),
                "cartoes_amarelos_mandante": to_int(item.get("ca_m")),
                "cartoes_vermelhos_mandante": to_int(item.get("cv_m")),
                "cartoes_amarelos_visitante": to_int(item.get("ca_v")),
                "cartoes_vermelhos_visitante": to_int(item.get("cv_v")),
                "fonte_url": metadata["plugin_url"],
                "status_coleta": "ok",
            }
        )

    standings = []
    for item in classification_result.get("list") or []:
        team = clean_team_name(item.get("nome_clube")) or club_map.get(str(item.get("id_clube")))
        standings.append(
            {
                "ano": ano,
                "id_campeonato_srgoool": championship_id,
                "posicao": to_int(item.get("posicao")),
                "time": team,
                "time_norm": normalize_key(team),
                "pts": to_int(item.get("pg")),
                "jogos": to_int(item.get("jg")),
                "vitorias": to_int(item.get("vi")),
                "empates": to_int(item.get("em")),
                "derrotas": to_int(item.get("de")),
                "gols_pro": to_int(item.get("gp")),
                "gols_contra": to_int(item.get("gc")),
                "saldo_gols": to_int(item.get("sg")),
                "cartoes_amarelos": to_int(item.get("ca")),
                "cartoes_vermelhos": to_int(item.get("cv")),
                "aproveitamento": to_float(item.get("apr")),
                "ingressos": to_int(item.get("in")),
                "publico_pagante": to_int(item.get("pu")),
                "renda_bruta": to_float(item.get("rb")),
                "renda_liquida": to_float(item.get("rl")),
                "publico_informado": to_int(item.get("publico_informado")),
                "fonte_url": metadata["plugin_url"],
                "status_coleta": "ok",
            }
        )

    return games, standings


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def main():
    args = parse_args()
    output_dir = Path(args.saida)
    session = make_session()
    ids = []
    games = []
    standings = []
    failures = []

    for ano in range(args.ano_inicio, args.ano_fim + 1):
        try:
            metadata = fetch_championship_id(session, ano)
            ids.append(metadata)
            year_games, year_standings = extract_year(session, metadata, args.delay)
            games.extend(year_games)
            standings.extend(year_standings)
            print(f"{ano}: {len(year_games)} jogos, {len(year_standings)} classificacao")
        except Exception as error:
            failures.append({"ano": ano, "erro": str(error)})
            print(f"{ano}: erro - {error}")
        time.sleep(args.delay)

    suffix = f"{args.ano_inicio}_{args.ano_fim}"
    write_csv(output_dir / f"brasileirao_srgoool_ids_{suffix}.csv", ids)
    write_csv(output_dir / f"brasileirao_srgoool_jogos_{suffix}.csv", games)
    write_csv(output_dir / f"brasileirao_srgoool_classificacao_{suffix}.csv", standings)
    if failures:
        write_csv(output_dir / f"brasileirao_srgoool_falhas_{suffix}.csv", failures)

    print(f"Jogos Sr.Goool: {len(games)}")
    print(f"Classificacao Sr.Goool: {len(standings)}")
    print(f"Saida: {output_dir}")


if __name__ == "__main__":
    main()
