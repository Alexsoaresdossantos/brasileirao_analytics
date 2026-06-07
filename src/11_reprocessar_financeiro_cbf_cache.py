import importlib.util
from pathlib import Path

import pandas as pd


CBF_SCRIPT = Path("src/07_extrair_brasileirao_cbf.py")
CBF_GAMES = Path("data/processed/cbf_brasileirao/brasileirao_serie_a_jogos_2018_2025.csv")


def load_cbf_module():
    spec = importlib.util.spec_from_file_location("cbf_collector", CBF_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    cbf = load_cbf_module()
    session = cbf.make_session()
    games = pd.read_csv(CBF_GAMES)

    financial_rows = []
    for index, row in games.iterrows():
        financial = cbf.extract_financial_from_pdf(
            session=session,
            pdf_url=row.get("boletim_financeiro_url"),
            ano=int(row["ano"]),
            id_jogo=str(row["id_jogo"]),
            keep_pdfs=True,
        )
        financial_rows.append(financial)
        if (index + 1) % 100 == 0:
            print(f"Reprocessados {index + 1}/{len(games)} PDFs")

    financial_df = pd.DataFrame(financial_rows)
    for column in financial_df.columns:
        games[column] = financial_df[column]

    games.to_csv(CBF_GAMES, index=False, encoding="utf-8-sig")
    print(f"OK: financeiro reprocessado em {CBF_GAMES}")
    print(games["financeiro_status"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
