import argparse
import csv
import html
import re
import time
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup


RSSSF_BRASIL_URL = "https://rsssfbrasil.com/tablesae/br{ano}.htm"
RSSSF_ORG_URL = "https://www.rsssf.org/tablesb/braz{ano}.html"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai jogos e classificacao do Brasileirao Serie A na era dos pontos corridos."
    )
    parser.add_argument("--ano-inicio", type=int, default=2003)
    parser.add_argument("--ano-fim", type=int, default=2025)
    parser.add_argument("--saida", default="data/processed/pontos_corridos")
    parser.add_argument("--delay", type=float, default=0.2)
    return parser.parse_args()


def make_session():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    session.verify = False
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; brasileirao-analytics/1.0)",
            "Accept": "text/html,text/plain,*/*",
        }
    )
    return session


def expected_games(ano):
    if ano in (2003, 2004):
        return 552
    if ano == 2005:
        return 462
    if ano == 2016:
        return 379
    return 380


def decode_response(response):
    raw_head = response.content[:700].lower()
    if b"charset=utf-8" in raw_head:
        encoding = "utf-8"
    else:
        encoding = response.apparent_encoding or response.encoding or "windows-1252"
    return response.content.decode(encoding, errors="replace")


def get_source_text(session, url):
    response = session.get(url, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(decode_response(response), "html.parser")
    pre_blocks = soup.find_all("pre")
    if pre_blocks:
        text = "\n".join(block.get_text("\n") for block in pre_blocks)
    else:
        text = soup.get_text("\n")
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def clean_team_name(value):
    value = re.sub(r"\s+\[.*$", "", value.strip())
    value = re.sub(r"\s{2,}", " ", value)
    return value


def game_section(text):
    start = re.search(r"(?im)^Round\s+1\b", text)
    if not start:
        return text

    section = text[start.start() :]
    final_after_games = re.search(r"(?im)^Final Table:?", section)
    if final_after_games:
        section = section[: final_after_games.start()]
    return section


def parse_games(text, ano, fonte_url):
    games = []
    rodada = None
    data_rsssf = None

    for raw_line in game_section(text).splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        round_match = re.match(r"^Round\s+(\d+)\b", stripped, flags=re.IGNORECASE)
        if round_match:
            rodada = int(round_match.group(1))
            data_rsssf = None
            continue

        date_match = re.match(
            r"^\[((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b[^\]]*)\]",
            stripped,
            flags=re.IGNORECASE,
        )
        if date_match:
            data_rsssf = date_match.group(1)
            continue

        if not rodada or re.match(r"^\d+\.", stripped):
            continue

        score_match = re.match(
            r"^\s*(?P<mandante>.+?)\s+(?P<gols_mandante>\d+)\s*-\s*(?P<gols_visitante>\d+)\s+(?P<visitante>.+?)\s*$",
            line,
        )
        if not score_match:
            continue

        mandante = clean_team_name(score_match.group("mandante"))
        visitante = clean_team_name(score_match.group("visitante"))
        if not mandante or not visitante:
            continue

        gols_mandante = int(score_match.group("gols_mandante"))
        gols_visitante = int(score_match.group("gols_visitante"))
        if gols_mandante > gols_visitante:
            vencedor = mandante
        elif gols_visitante > gols_mandante:
            vencedor = visitante
        else:
            vencedor = "Empate"

        games.append(
            {
                "ano": ano,
                "rodada": rodada,
                "data_rsssf": data_rsssf,
                "mandante": mandante,
                "visitante": visitante,
                "gols_mandante": gols_mandante,
                "gols_visitante": gols_visitante,
                "resultado": f"{gols_mandante} x {gols_visitante}",
                "vencedor": vencedor,
                "fonte": "RSSSF",
                "fonte_url": fonte_url,
            }
        )

    return games


def parse_standings(text, ano, fonte_url):
    rows = []
    standing_pattern = re.compile(
        r"^\s*(?P<posicao>\d+)\.(?P<time>.+?)\s+"
        r"(?P<jogos>\d+)\s+(?P<vitorias>\d+)\s+(?P<empates>\d+)\s+(?P<derrotas>\d+)\s+"
        r"(?P<gols_pro>\d+)\s*-\s*(?P<gols_contra>\d+)\s+(?P<pts>-?\d+)\b"
    )
    standing_pattern_alt = re.compile(
        r"^\s*(?P<posicao>\d+)(?P<time>[A-Za-zÀ-ÿ0-9/ .'-]+?)\s+"
        r"(?P<pts>-?\d+)\s+(?P<jogos>\d+)\s+(?P<vitorias>\d+)\s+(?P<empates>\d+)\s+"
        r"(?P<derrotas>\d+)\s+(?P<gols_pro>\d+)\s+(?P<gols_contra>\d+)\s+(?P<saldo_gols>-?\d+)\b"
    )

    for line in text.splitlines():
        match = standing_pattern.match(line)
        alternate_layout = False
        if not match:
            match = standing_pattern_alt.match(line)
            alternate_layout = bool(match)
        if not match:
            continue

        if alternate_layout:
            saldo_gols = int(match.group("saldo_gols"))
        else:
            saldo_gols = int(match.group("gols_pro")) - int(match.group("gols_contra"))

        rows.append(
            {
                "ano": ano,
                "posicao": int(match.group("posicao")),
                "time": clean_team_name(match.group("time")),
                "pts": int(match.group("pts")),
                "jogos": int(match.group("jogos")),
                "vitorias": int(match.group("vitorias")),
                "empates": int(match.group("empates")),
                "derrotas": int(match.group("derrotas")),
                "gols_pro": int(match.group("gols_pro")),
                "gols_contra": int(match.group("gols_contra")),
                "saldo_gols": saldo_gols,
                "fonte": "RSSSF",
                "fonte_url": fonte_url,
            }
        )

    if not rows:
        rows = parse_vertical_standings(text, ano, fonte_url)

    # Some pages repeat the final table after the fixtures. Keep the most complete first block.
    if rows:
        max_teams = 24 if ano in (2003, 2004) else 22 if ano == 2005 else 20
        rows = rows[:max_teams]
    return rows


def parse_vertical_standings(text, ano, fonte_url):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    try:
        start = next(index for index, line in enumerate(lines) if line.lower() == "standings")
    except StopIteration:
        return []

    rows = []
    index = start + 1
    while index < len(lines):
        if not re.fullmatch(r"\d{1,2}", lines[index]):
            index += 1
            continue

        if index + 9 >= len(lines):
            break

        posicao = int(lines[index])
        time = lines[index + 1]
        numeric_values = lines[index + 2 : index + 10]
        if not all(re.fullmatch(r"-?\d+", value) for value in numeric_values):
            index += 1
            continue

        pts, jogos, vitorias, empates, derrotas, gols_pro, gols_contra, saldo_gols = [
            int(value) for value in numeric_values
        ]
        rows.append(
            {
                "ano": ano,
                "posicao": posicao,
                "time": clean_team_name(time),
                "pts": pts,
                "jogos": jogos,
                "vitorias": vitorias,
                "empates": empates,
                "derrotas": derrotas,
                "gols_pro": gols_pro,
                "gols_contra": gols_contra,
                "saldo_gols": saldo_gols,
                "fonte": "RSSSF",
                "fonte_url": fonte_url,
            }
        )
        index += 14

    return rows


def candidate_urls(ano):
    urls = [RSSSF_BRASIL_URL.format(ano=ano)]
    if ano >= 2010:
        urls.append(RSSSF_ORG_URL.format(ano=ano))
    return urls


def collect_year(session, ano):
    expected = expected_games(ano)
    candidates = []

    for url in candidate_urls(ano):
        try:
            text = get_source_text(session, url)
        except requests.RequestException:
            continue

        games = parse_games(text, ano, url)
        standings = parse_standings(text, ano, url)
        candidates.append(
            {
                "url": url,
                "text": text,
                "games": games,
                "standings": standings,
                "distance": abs(len(games) - expected),
            }
        )

    if not candidates:
        raise RuntimeError(f"Nenhuma fonte disponivel para {ano}")

    exact = [candidate for candidate in candidates if len(candidate["games"]) == expected]
    if exact:
        chosen = exact[0]
    else:
        chosen = min(candidates, key=lambda item: item["distance"])

    status = "ok" if len(chosen["games"]) == expected else "divergente"
    for row in chosen["games"]:
        row["status_coleta"] = status
        row["jogos_esperados_ano"] = expected
        row["jogos_extraidos_ano"] = len(chosen["games"])

    for row in chosen["standings"]:
        row["status_coleta"] = status
        row["jogos_esperados_ano"] = expected
        row["jogos_extraidos_ano"] = len(chosen["games"])

    return chosen


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()
    session = make_session()
    output_dir = Path(args.saida)
    all_games = []
    all_standings = []

    for ano in range(args.ano_inicio, args.ano_fim + 1):
        chosen = collect_year(session, ano)
        all_games.extend(chosen["games"])
        all_standings.extend(chosen["standings"])
        print(
            f"{ano}: jogos={len(chosen['games'])} classificacao={len(chosen['standings'])} "
            f"fonte={chosen['url']}"
        )
        time.sleep(args.delay)

    write_csv(output_dir / f"brasileirao_pontos_corridos_jogos_{args.ano_inicio}_{args.ano_fim}.csv", all_games)
    write_csv(
        output_dir / f"brasileirao_pontos_corridos_classificacao_{args.ano_inicio}_{args.ano_fim}.csv",
        all_standings,
    )
    print(f"OK: {len(all_games)} jogos e {len(all_standings)} linhas de classificacao em {output_dir}")


if __name__ == "__main__":
    main()
