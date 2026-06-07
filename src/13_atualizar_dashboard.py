import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(description="Atualiza dados Sr.Goool, consolida bases e regenera o dashboard.")
    parser.add_argument("--ano-inicio", type=int, default=2003)
    parser.add_argument("--ano-fim", type=int, default=date.today().year)
    parser.add_argument("--delay", type=float, default=0.2)
    return parser.parse_args()


def run_step(command):
    print("Executando:", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    args = parse_args()
    python = sys.executable
    run_step(
        [
            python,
            "src/12_extrair_publico_renda_srgoool.py",
            "--ano-inicio",
            str(args.ano_inicio),
            "--ano-fim",
            str(args.ano_fim),
            "--delay",
            str(args.delay),
        ]
    )
    run_step([python, "src/09_consolidar_bases_dashboard.py"])
    run_step([python, "src/10_gerar_dashboard_html.py"])
    print("Atualizacao concluida.", flush=True)


if __name__ == "__main__":
    main()
