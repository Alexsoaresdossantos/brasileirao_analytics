import argparse
import csv
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup


BASE_URL = "https://www.cbf.com.br"
TABLE_URL = BASE_URL + "/futebol-brasileiro/tabelas/campeonato-brasileiro/serie-a/{ano}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extrai jogos, publico/arrecadacao e classificacao da Serie A no site da CBF."
    )
    parser.add_argument("--ano-inicio", type=int, default=2018)
    parser.add_argument("--ano-fim", type=int, default=2025)
    parser.add_argument("--rodada-inicio", type=int, default=1)
    parser.add_argument("--rodada-fim", type=int, default=None)
    parser.add_argument("--saida", default="data/processed/cbf_brasileirao")
    parser.add_argument("--delay", type=float, default=0.25)
    parser.add_argument("--sem-financeiro", action="store_true", help="Nao baixa/extrai PDFs dos boletins financeiros.")
    parser.add_argument("--guardar-pdfs", action="store_true", help="Guarda os PDFs baixados em data/raw/cbf_boletins_financeiros.")
    return parser.parse_args()


def make_session():
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
    )
    session.verify = False
    return session


def get_text(session, url):
    response = request_with_retries(session, url, timeout=60)
    response.raise_for_status()
    return response.text


def get_json(session, url):
    response = request_with_retries(session, url, timeout=60)
    response.raise_for_status()
    return response.json()


def request_with_retries(session, url, timeout=60, attempts=5):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=timeout)
            if response.status_code < 500 and response.status_code != 429:
                return response
            last_error = requests.HTTPError(f"HTTP {response.status_code} para {url}", response=response)
        except requests.RequestException as error:
            last_error = error

        if attempt < attempts:
            time.sleep(min(2 ** attempt, 30))

    if last_error:
        raise last_error
    raise RuntimeError(f"Falha desconhecida ao acessar {url}")


def money_to_float(value):
    if not value:
        return None
    value = value.replace("R$", "").strip()
    value = value.replace(".", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return None


def int_or_none(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def br_int_to_int(value):
    if not value:
        return None
    value = str(value).replace(".", "").strip()
    return int_or_none(value)


def extract_competition_metadata(html, ano):
    patterns = {
        "competition_id": r'competitionId\\?":\\?"(\d+)',
        "championship_id": r'championshipId\\?":\\?"(\d+)',
        "category_id": r'categoryId\\?":\\?"(\d+)',
        "fase_id": r'fase_id\\?":\\?"(\d+)',
        "rodadas_qtd": r'rodadas_qtd\\?":\\?"(\d+)',
        "partidas": r'partidas\\?":\\?"(\d+)',
    }
    metadata = {"ano": ano}
    for key, pattern in patterns.items():
        match = re.search(pattern, html)
        metadata[key] = match.group(1) if match else None

    missing = [key for key in ("competition_id", "fase_id", "rodadas_qtd") if not metadata.get(key)]
    if missing:
        raise RuntimeError(f"Metadados ausentes para {ano}: {', '.join(missing)}")
    return metadata


def extract_classificacao(html, ano):
    soup = BeautifulSoup(html, "html.parser")
    classificacao = []

    for table in soup.find_all("table"):
        headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
        if not headers or "PTS Pontos" not in headers:
            continue

        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if len(cells) < 12:
                continue

            team_link = row.find("a")
            team_name = team_link.get_text(" ", strip=True) if team_link else re.sub(r"^\d+\s*", "", cells[0]).strip()
            position_match = re.search(r"\d+", cells[0])

            classificacao.append(
                {
                    "ano": ano,
                    "posicao": int_or_none(position_match.group(0) if position_match else None),
                    "time": team_name,
                    "pts": int_or_none(cells[1]),
                    "jogos": int_or_none(cells[2]),
                    "vitorias": int_or_none(cells[3]),
                    "empates": int_or_none(cells[4]),
                    "derrotas": int_or_none(cells[5]),
                    "gols_pro": int_or_none(cells[6]),
                    "gols_contra": int_or_none(cells[7]),
                    "saldo_gols": int_or_none(cells[8]),
                    "cartoes_amarelos": int_or_none(cells[9]),
                    "cartoes_vermelhos": int_or_none(cells[10]),
                    "aproveitamento": int_or_none(cells[11]),
                }
            )
        break

    return classificacao


def find_document_url(game, title):
    title = title.lower()
    for document in game.get("documentos") or []:
        if title in (document.get("title") or "").lower():
            return document.get("url")
    return None


def detect_winner(home_goals, away_goals, home_team, away_team):
    home_goals = int_or_none(home_goals)
    away_goals = int_or_none(away_goals)
    if home_goals is None or away_goals is None:
        return None
    if home_goals > away_goals:
        return home_team
    if away_goals > home_goals:
        return away_team
    return "Empate"


def parse_financial_totals(text):
    receita_text = re.split(r"\bDESPESAS\b", text, maxsplit=1, flags=re.IGNORECASE)[0]
    total_rows = list(
        re.finditer(
            r"(?im)^\s*TOTAIS?\s+(\d+)\s+(\d+)\s+(\d+)\s+(?:R\$\s*[\d\.\,]+\s+)?R\$\s*([\d\.\,]+)\s*$",
            receita_text,
        )
    )
    if total_rows:
        match = max(total_rows, key=lambda item: int(item.group(3)))
        return {
            "publico_a_venda": int(match.group(1)),
            "publico_devolvido": int(match.group(2)),
            "publico_vendido": int(match.group(3)),
            "arrecadacao_bruta": money_to_float(match.group(4)),
            "financeiro_status": "ok_total_linha",
        }

    total_blocks = list(
        re.finditer(
            r"(?im)^\s*TOTAL\s+([\d\.]+)(?:\s+[\d\.]+)?\s*$\s*^\s*([\d\.]+)\s+([\d\.]+,\d{2})\s*$",
            receita_text,
        )
    )
    if total_blocks:
        match = max(total_blocks, key=lambda item: br_int_to_int(item.group(2)) or 0)
        publico_vendido = br_int_to_int(match.group(2))
        return {
            "publico_a_venda": br_int_to_int(match.group(1)),
            "publico_devolvido": None,
            "publico_vendido": publico_vendido,
            "arrecadacao_bruta": money_to_float(match.group(3)),
            "financeiro_status": "ok_total_quebrado",
        }

    window_total = parse_total_window(receita_text)
    if window_total:
        return window_total

    total_publico = [
        br_int_to_int(match.group(1))
        for match in re.finditer(r"(?im)^\s*TOTAL(?:ES)?\s+([\d\.]+)\s*$", receita_text)
    ]
    valores_monetarios = [
        money_to_float(match.group(0))
        for match in re.finditer(r"\b\d{1,3}(?:\.\d{3})+,\d{2}\b", receita_text)
    ]
    total_publico = [value for value in total_publico if value is not None]
    valores_monetarios = [value for value in valores_monetarios if value is not None]
    if total_publico and valores_monetarios:
        publico_vendido = max(total_publico)
        return {
            "publico_a_venda": publico_vendido,
            "publico_devolvido": None,
            "publico_vendido": publico_vendido,
            "arrecadacao_bruta": max(valores_monetarios),
            "financeiro_status": "ok_total_sem_r",
        }

    return {
        "publico_a_venda": None,
        "publico_devolvido": None,
        "publico_vendido": None,
        "arrecadacao_bruta": None,
        "financeiro_status": "totais_nao_encontrados",
    }


def parse_total_window(receita_text):
    lines = receita_text.splitlines()
    for index, line in enumerate(lines):
        if not re.search(r"\bTOTAIS?\b", line, flags=re.IGNORECASE):
            continue

        window = "\n".join(lines[max(0, index - 5) : min(len(lines), index + 45)])
        triple_candidates = []
        for match in re.finditer(r"\b(\d{1,6})\s+(\d{1,6})\s+(\d{1,6})\b", window):
            a_venda = int(match.group(1))
            devolvidos = int(match.group(2))
            vendidos = int(match.group(3))
            if devolvidos <= a_venda and vendidos >= 100:
                triple_candidates.append((a_venda, devolvidos, vendidos))

        money_candidates = [
            money_to_float(match.group(0))
            for match in re.finditer(r"\b\d{1,3}(?:\.\d{3})+,\d{2}\b", window)
        ]
        money_candidates = [value for value in money_candidates if value is not None and value > 0]

        if triple_candidates and money_candidates:
            a_venda, devolvidos, vendidos = max(triple_candidates, key=lambda item: item[2])
            return {
                "publico_a_venda": a_venda,
                "publico_devolvido": devolvidos,
                "publico_vendido": vendidos,
                "arrecadacao_bruta": max(money_candidates),
                "financeiro_status": "ok_total_janela",
            }

    return None


def extract_financial_from_pdf(session, pdf_url, ano, id_jogo, keep_pdfs):
    if not pdf_url:
        return {
            "publico_a_venda": None,
            "publico_devolvido": None,
            "publico_vendido": None,
            "arrecadacao_bruta": None,
            "financeiro_status": "sem_boletim_financeiro",
        }

    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        pdftotext = r"C:\Program Files\Git\mingw64\bin\pdftotext.exe"
    if not Path(pdftotext).exists():
        return {
            "publico_a_venda": None,
            "publico_devolvido": None,
            "publico_vendido": None,
            "arrecadacao_bruta": None,
            "financeiro_status": "pdftotext_nao_encontrado",
        }

    cache_path = Path("data/raw/cbf_boletins_financeiros") / str(ano) / f"{id_jogo}.pdf"
    if keep_pdfs and cache_path.exists() and cache_path.stat().st_size > 0:
        pdf_content = cache_path.read_bytes()
    else:
        try:
            response = request_with_retries(session, pdf_url, timeout=90, attempts=3)
            response.raise_for_status()
            pdf_content = response.content
        except requests.RequestException:
            return {
                "publico_a_venda": None,
                "publico_devolvido": None,
                "publico_vendido": None,
                "arrecadacao_bruta": None,
                "financeiro_status": "erro_download_pdf",
            }

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / f"{ano}_{id_jogo}.pdf"
        txt_path = Path(tmp) / f"{ano}_{id_jogo}.txt"
        pdf_path.write_bytes(pdf_content)

        if keep_pdfs:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            if not cache_path.exists() or cache_path.stat().st_size == 0:
                cache_path.write_bytes(pdf_content)

        result = subprocess.run(
            [pdftotext, "-layout", str(pdf_path), str(txt_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not txt_path.exists():
            return {
                "publico_a_venda": None,
                "publico_devolvido": None,
                "publico_vendido": None,
                "arrecadacao_bruta": None,
                "financeiro_status": "erro_pdftotext",
            }

        text = txt_path.read_text(encoding="utf-8", errors="replace")
        if len(text.strip()) < 50:
            return {
                "publico_a_venda": None,
                "publico_devolvido": None,
                "publico_vendido": None,
                "arrecadacao_bruta": None,
                "financeiro_status": "pdf_sem_texto_ocr_necessario",
            }
        return parse_financial_totals(text)


def fetch_round_games(session, metadata, rodada):
    endpoint = (
        BASE_URL
        + f"/api/cbf/jogos/campeonato/{metadata['competition_id']}/rodada/{rodada}/fase/{metadata['fase_id']}"
    )
    payload = get_json(session, endpoint)
    games = []
    for group in payload.get("jogos") or []:
        for game in group.get("jogo") or []:
            games.append(game)
    return games


def flatten_game(game, ano):
    mandante = game.get("mandante") or {}
    visitante = game.get("visitante") or {}
    gols_mandante = mandante.get("gols")
    gols_visitante = visitante.get("gols")
    sumula_url = find_document_url(game, "Súmula") or find_document_url(game, "Sumula")
    boletim_url = find_document_url(game, "Boletim Financeiro")
    relatorio_url = find_document_url(game, "Relatório") or find_document_url(game, "Relatorio")

    return {
        "ano": ano,
        "id_jogo": game.get("id_jogo"),
        "num_jogo": game.get("num_jogo"),
        "rodada": int_or_none(game.get("rodada")),
        "grupo": game.get("grupo"),
        "data": (game.get("data") or "").strip(),
        "hora": game.get("hora"),
        "local": game.get("local"),
        "mandante_id": mandante.get("id"),
        "mandante": mandante.get("nome"),
        "visitante_id": visitante.get("id"),
        "visitante": visitante.get("nome"),
        "gols_mandante": int_or_none(gols_mandante),
        "gols_visitante": int_or_none(gols_visitante),
        "resultado": f"{gols_mandante} x {gols_visitante}" if gols_mandante is not None and gols_visitante is not None else None,
        "vencedor": detect_winner(gols_mandante, gols_visitante, mandante.get("nome"), visitante.get("nome")),
        "sumula_url": sumula_url,
        "boletim_financeiro_url": boletim_url,
        "relatorio_jogo_url": relatorio_url,
    }


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
    games_path = output_dir / f"brasileirao_serie_a_jogos_{args.ano_inicio}_{args.ano_fim}.csv"
    standings_path = output_dir / f"brasileirao_serie_a_classificacao_{args.ano_inicio}_{args.ano_fim}.csv"
    errors_path = output_dir / f"brasileirao_serie_a_erros_{args.ano_inicio}_{args.ano_fim}.csv"
    all_games = []
    all_standings = []
    errors = []

    for ano in range(args.ano_inicio, args.ano_fim + 1):
        print(f"Coletando {ano}...")
        try:
            html = get_text(session, TABLE_URL.format(ano=ano))
            metadata = extract_competition_metadata(html, ano)
        except Exception as error:
            errors.append({"ano": ano, "rodada": None, "etapa": "metadados", "erro": str(error)})
            print(f"  erro em metadados de {ano}: {error}")
            write_csv(errors_path, errors)
            continue

        all_standings.extend(extract_classificacao(html, ano))

        total_rounds = int(metadata["rodadas_qtd"])
        rodada_inicio = max(1, args.rodada_inicio)
        rodada_fim = min(total_rounds, args.rodada_fim or total_rounds)
        for rodada in range(rodada_inicio, rodada_fim + 1):
            try:
                games = fetch_round_games(session, metadata, rodada)
            except Exception as error:
                errors.append({"ano": ano, "rodada": rodada, "etapa": "jogos_rodada", "erro": str(error)})
                print(f"  rodada {rodada:02d}: erro ao coletar jogos ({error})")
                write_csv(errors_path, errors)
                continue

            for game in games:
                row = flatten_game(game, ano)
                if args.sem_financeiro:
                    financial = {
                        "publico_a_venda": None,
                        "publico_devolvido": None,
                        "publico_vendido": None,
                        "arrecadacao_bruta": None,
                        "financeiro_status": "nao_extraido",
                    }
                else:
                    financial = extract_financial_from_pdf(
                        session,
                        row["boletim_financeiro_url"],
                        ano,
                        row["id_jogo"],
                        args.guardar_pdfs,
                    )
                    time.sleep(args.delay)
                row.update(financial)
                all_games.append(row)

            print(f"  rodada {rodada:02d}: {len(games)} jogos")
            write_csv(games_path, all_games)
            write_csv(standings_path, all_standings)
            if errors:
                write_csv(errors_path, errors)
            time.sleep(args.delay)

    write_csv(games_path, all_games)
    write_csv(standings_path, all_standings)
    if errors:
        write_csv(errors_path, errors)
    print(f"OK: {len(all_games)} jogos e {len(all_standings)} linhas de classificacao em {output_dir}")
    if errors:
        print(f"Aviso: {len(errors)} erros foram registrados em {errors_path}")


if __name__ == "__main__":
    main()
