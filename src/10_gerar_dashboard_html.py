import json
from pathlib import Path

import pandas as pd


ROOT = Path(".")
GAMES_CSV = ROOT / "data/processed/dashboard/base_jogos_brasileirao_dashboard.csv"
STANDINGS_CSV = ROOT / "data/processed/dashboard/base_classificacao_brasileirao_dashboard.csv"
OUTPUT_HTML = ROOT / "reports/dashboard/brasileirao_dashboard.html"


def money(value):
    if pd.isna(value):
        return None
    return float(value)


def number(value):
    if pd.isna(value):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def bool_value(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def load_data():
    games = pd.read_csv(GAMES_CSV)
    standings = pd.read_csv(STANDINGS_CSV)

    game_rows = []
    for row in games.to_dict("records"):
        game_rows.append(
            {
                "ano": number(row.get("ano")),
                "rodada": number(row.get("rodada")),
                "data": None if pd.isna(row.get("data")) else str(row.get("data")),
                "hora": None if pd.isna(row.get("hora")) else str(row.get("hora")),
                "local": None if pd.isna(row.get("local")) else str(row.get("local")),
                "mandante": str(row.get("mandante")),
                "visitante": str(row.get("visitante")),
                "gols_mandante": number(row.get("gols_mandante")),
                "gols_visitante": number(row.get("gols_visitante")),
                "resultado": str(row.get("resultado")),
                "vencedor": str(row.get("vencedor")),
                "publico_vendido": number(row.get("publico_vendido")),
                "arrecadacao_bruta": money(row.get("arrecadacao_bruta")),
                "renda_liquida_mandante": money(row.get("renda_mandante")),
                "renda_liquida_visitante": money(row.get("renda_visitante")),
                "cartoes_amarelos_mandante": number(row.get("cartoes_amarelos_mandante")),
                "cartoes_vermelhos_mandante": number(row.get("cartoes_vermelhos_mandante")),
                "cartoes_amarelos_visitante": number(row.get("cartoes_amarelos_visitante")),
                "cartoes_vermelhos_visitante": number(row.get("cartoes_vermelhos_visitante")),
                "financeiro_status": str(row.get("financeiro_status")),
                "tem_financeiro": bool_value(row.get("tem_financeiro")),
                "fonte_esportiva": str(row.get("fonte_esportiva")),
                "boletim_financeiro_url": None
                if pd.isna(row.get("boletim_financeiro_url"))
                else str(row.get("boletim_financeiro_url")),
            }
        )

    standing_rows = []
    for row in standings.to_dict("records"):
        standing_rows.append(
            {
                "ano": number(row.get("ano")),
                "posicao": number(row.get("posicao")),
                "time": str(row.get("time")),
                "pts": number(row.get("pts")),
                "jogos": number(row.get("jogos")),
                "vitorias": number(row.get("vitorias")),
                "empates": number(row.get("empates")),
                "derrotas": number(row.get("derrotas")),
                "gols_pro": number(row.get("gols_pro")),
                "gols_contra": number(row.get("gols_contra")),
                "saldo_gols": number(row.get("saldo_gols")),
                "cartoes_amarelos": number(row.get("cartoes_amarelos")),
                "cartoes_vermelhos": number(row.get("cartoes_vermelhos")),
                "aproveitamento": number(row.get("aproveitamento")),
            }
        )

    return game_rows, standing_rows


def build_html(game_rows, standing_rows):
    max_year = max(row.get("ano") or 0 for row in game_rows)
    payload = {
        "games": game_rows,
        "standings": standing_rows,
    }
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    return f"""<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Brasileirão Analytics</title>
  <style>
    :root {{
      --bg: #f5f7f2;
      --surface: #ffffff;
      --surface-2: #eef2e8;
      --text: #18211f;
      --muted: #66716c;
      --line: #d9dfd5;
      --green: #138a4c;
      --blue: #2364aa;
      --yellow: #d99a12;
      --red: #b93d3d;
      --ink: #102820;
    }}

    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
      letter-spacing: 0;
    }}

    header {{
      background: var(--ink);
      color: white;
      padding: 22px 28px 16px;
      border-bottom: 4px solid var(--yellow);
    }}

    h1 {{
      margin: 0;
      font-size: 28px;
      line-height: 1.15;
      font-weight: 760;
    }}

    .subtitle {{
      margin-top: 6px;
      color: #c9d8cf;
      font-size: 14px;
    }}

    main {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 18px 20px 28px;
    }}

    .toolbar {{
      display: grid;
      grid-template-columns: repeat(7, minmax(120px, 1fr));
      gap: 10px;
      align-items: end;
      padding: 14px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}

    label {{
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}

    select,
    input[type="search"] {{
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      color: var(--text);
      background: white;
      font-size: 14px;
    }}

    .checkline {{
      min-height: 38px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text);
      font-size: 14px;
      text-transform: none;
    }}

    .button {{
      min-height: 38px;
      border: 0;
      border-radius: 6px;
      background: var(--green);
      color: white;
      font-weight: 700;
      cursor: pointer;
    }}

    .tabs {{
      display: flex;
      gap: 8px;
      margin: 18px 0 12px;
      border-bottom: 1px solid var(--line);
    }}

    .tab {{
      border: 1px solid transparent;
      border-bottom: 0;
      padding: 10px 14px;
      border-radius: 6px 6px 0 0;
      background: transparent;
      color: var(--muted);
      font-weight: 700;
      cursor: pointer;
    }}

    .tab.active {{
      background: var(--surface);
      border-color: var(--line);
      color: var(--text);
    }}

    .metrics {{
      display: grid;
      grid-template-columns: repeat(6, minmax(130px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }}

    .metric {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-height: 86px;
    }}

    .metric span {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}

    .metric strong {{
      display: block;
      margin-top: 8px;
      font-size: 24px;
      line-height: 1;
    }}

    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }}

    .panel {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-width: 0;
    }}

    .panel h2 {{
      margin: 0 0 12px;
      font-size: 16px;
    }}

    .bar-row {{
      display: grid;
      grid-template-columns: minmax(80px, 150px) 1fr minmax(56px, auto);
      gap: 10px;
      align-items: center;
      margin: 7px 0;
      font-size: 13px;
    }}

    .bar-track {{
      height: 12px;
      background: var(--surface-2);
      border-radius: 4px;
      overflow: hidden;
    }}

    .bar {{
      height: 100%;
      min-width: 2px;
      background: var(--blue);
    }}

    .bar.green {{ background: var(--green); }}
    .bar.yellow {{ background: var(--yellow); }}
    .bar.red {{ background: var(--red); }}

    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}

    th,
    td {{
      padding: 8px 7px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}

    th {{
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      background: #fafbf8;
    }}

    .hidden {{ display: none; }}
    .status {{
      color: var(--muted);
      font-size: 12px;
      margin-top: 8px;
    }}

    .compare-controls {{
      display: grid;
      grid-template-columns: repeat(3, minmax(160px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }}

    .compare-table td,
    .compare-table th {{
      text-align: right;
    }}

    .compare-table td:first-child,
    .compare-table th:first-child {{
      text-align: left;
    }}

    .compare-charts {{
      margin-top: 14px;
    }}

    @media (max-width: 1100px) {{
      .toolbar {{ grid-template-columns: repeat(3, minmax(120px, 1fr)); }}
      .metrics {{ grid-template-columns: repeat(3, minmax(130px, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
    }}

    @media (max-width: 700px) {{
      header {{ padding: 18px 14px; }}
      main {{ padding: 12px; }}
      .toolbar,
      .metrics {{ grid-template-columns: 1fr 1fr; }}
      .compare-controls {{ grid-template-columns: 1fr; }}
      .tabs {{ overflow-x: auto; }}
      h1 {{ font-size: 23px; }}
      table {{ font-size: 12px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Brasileirão Analytics</h1>
    <div class="subtitle">Era dos pontos corridos, 2003-{max_year}</div>
  </header>

  <main>
    <section class="toolbar">
      <label>Ano inicial<select id="yearStart"></select></label>
      <label>Ano final<select id="yearEnd"></select></label>
      <label>Clube<select id="club"></select></label>
      <label>Busca<input id="search" type="search" placeholder="Time, estádio ou placar"></label>
      <label class="checkline"><input id="financeOnly" type="checkbox"> Com financeiro</label>
      <button class="button" id="reset">Limpar</button>
      <button class="button" id="updateData" type="button">Atualizar dados</button>
    </section>
    <div class="status" id="updateStatus"></div>

    <nav class="tabs">
      <button class="tab active" data-view="overview">Visão Geral</button>
      <button class="tab" data-view="clubs">Clubes</button>
      <button class="tab" data-view="finance">Financeiro</button>
      <button class="tab" data-view="compareFinance">Comparativo</button>
      <button class="tab" data-view="matches">Partidas</button>
    </nav>

    <section class="metrics" id="metrics"></section>

    <section id="overview" class="view">
      <div class="grid">
        <div class="panel">
          <h2>Gols Por Ano</h2>
          <div id="goalsByYear"></div>
        </div>
        <div class="panel">
          <h2>Resultados</h2>
          <div id="resultMix"></div>
        </div>
      </div>
    </section>

    <section id="clubs" class="view hidden">
      <div class="grid">
        <div class="panel">
          <h2>Pontos Acumulados</h2>
          <div id="pointsByClub"></div>
        </div>
        <div class="panel">
          <h2>Saldo De Gols</h2>
          <div id="goalDiffByClub"></div>
        </div>
        <div class="panel">
          <h2>Cartoes Amarelos</h2>
          <div id="yellowCardsByClub"></div>
        </div>
        <div class="panel">
          <h2>Cartoes Vermelhos</h2>
          <div id="redCardsByClub"></div>
        </div>
      </div>
    </section>

    <section id="finance" class="view hidden">
      <div class="grid">
        <div class="panel">
          <h2>Renda Bruta Por Ano</h2>
          <div id="revenueByYear"></div>
        </div>
        <div class="panel">
          <h2>Renda Liquida Por Ano</h2>
          <div id="netRevenueByYear"></div>
        </div>
        <div class="panel">
          <h2>Público Por Ano</h2>
          <div id="attendanceByYear"></div>
        </div>
      </div>
    </section>

    <section id="compareFinance" class="view hidden">
      <div class="panel">
        <h2>Comparacao Financeira</h2>
        <div class="compare-controls">
          <label>Clube 1<select id="compareClub1"></select></label>
          <label>Clube 2<select id="compareClub2"></select></label>
          <label>Clube 3<select id="compareClub3"></select></label>
        </div>
        <div id="compareTable"></div>
      </div>
      <div class="grid compare-charts">
        <div class="panel">
          <h2>Renda Bruta</h2>
          <div id="compareGrossRevenue"></div>
        </div>
        <div class="panel">
          <h2>Renda Liquida</h2>
          <div id="compareNetRevenue"></div>
        </div>
        <div class="panel">
          <h2>Ticket Medio</h2>
          <div id="compareAvgTicket"></div>
        </div>
      </div>
    </section>

    <section id="matches" class="view hidden">
      <div class="panel">
        <h2>Partidas</h2>
        <div id="matchesTable"></div>
        <div class="status" id="tableStatus"></div>
      </div>
    </section>
  </main>

  <script id="data" type="application/json">{data_json}</script>
  <script>
    const DATA = JSON.parse(document.getElementById('data').textContent);
    const games = DATA.games;
    const standings = DATA.standings;
    const years = [...new Set(games.map(d => d.ano))].sort((a, b) => a - b);
    const clubs = [...new Set(games.flatMap(d => [d.mandante, d.visitante]))].sort();

    const fmtInt = new Intl.NumberFormat('pt-BR', {{ maximumFractionDigits: 0 }});
    const fmtMoney = new Intl.NumberFormat('pt-BR', {{ style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }});

    function fillSelect(id, values, allLabel) {{
      const el = document.getElementById(id);
      el.innerHTML = '';
      if (allLabel) {{
        const option = document.createElement('option');
        option.value = '';
        option.textContent = allLabel;
        el.appendChild(option);
      }}
      values.forEach(value => {{
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value;
        el.appendChild(option);
      }});
    }}

    fillSelect('yearStart', years);
    fillSelect('yearEnd', years);
    fillSelect('club', clubs, 'Todos');
    fillSelect('compareClub1', clubs, 'Selecionar');
    fillSelect('compareClub2', clubs, 'Selecionar');
    fillSelect('compareClub3', clubs, 'Selecionar');
    document.getElementById('yearStart').value = Math.min(...years);
    document.getElementById('yearEnd').value = Math.max(...years);
    const defaultCompareClubs = ['Flamengo', 'Palmeiras', 'Corinthians'].filter(club => clubs.includes(club));
    ['compareClub1', 'compareClub2', 'compareClub3'].forEach((id, index) => {{
      document.getElementById(id).value = defaultCompareClubs[index] || '';
    }});

    function filteredGames() {{
      const start = Number(document.getElementById('yearStart').value);
      const end = Number(document.getElementById('yearEnd').value);
      const club = document.getElementById('club').value;
      const term = document.getElementById('search').value.trim().toLowerCase();
      const financeOnly = document.getElementById('financeOnly').checked;

      return games.filter(d => {{
        if (d.ano < start || d.ano > end) return false;
        if (club && d.mandante !== club && d.visitante !== club) return false;
        if (financeOnly && !d.tem_financeiro) return false;
        if (term) {{
          const haystack = [d.mandante, d.visitante, d.local, d.resultado, d.financeiro_status].join(' ').toLowerCase();
          if (!haystack.includes(term)) return false;
        }}
        return true;
      }});
    }}

    function selectedClub() {{
      return document.getElementById('club').value;
    }}

    function filteredStandings() {{
      const start = Number(document.getElementById('yearStart').value);
      const end = Number(document.getElementById('yearEnd').value);
      const club = selectedClub();
      return standings.filter(d => d.ano >= start && d.ano <= end && (!club || d.time === club || d.time.startsWith(club + '/')));
    }}

    function sumField(rows, field) {{
      return rows.reduce((sum, d) => sum + (d[field] || 0), 0);
    }}

    function attendanceRows(rows) {{
      const club = selectedClub();
      return rows.filter(d => d.publico_vendido !== null && (!club || d.mandante === club));
    }}

    function attendanceValue(d) {{
      const club = selectedClub();
      if (club && d.mandante !== club) return 0;
      return d.publico_vendido || 0;
    }}

    function grossRevenueRows(rows) {{
      const club = selectedClub();
      return rows.filter(d => d.arrecadacao_bruta !== null && (!club || d.mandante === club));
    }}

    function grossRevenueValue(d) {{
      const club = selectedClub();
      if (club && d.mandante !== club) return 0;
      return d.arrecadacao_bruta || 0;
    }}

    function netRevenueRows(rows) {{
      const club = selectedClub();
      return rows.filter(d => d.renda_liquida_mandante !== null && (!club || d.mandante === club));
    }}

    function netRevenueValue(d) {{
      const club = selectedClub();
      if (club && d.mandante !== club) return 0;
      return d.renda_liquida_mandante || 0;
    }}

    function yellowCardsValue(d) {{
      const club = selectedClub();
      if (club) {{
        if (d.mandante === club) return d.cartoes_amarelos_mandante || 0;
        if (d.visitante === club) return d.cartoes_amarelos_visitante || 0;
        return 0;
      }}
      return (d.cartoes_amarelos_mandante || 0) + (d.cartoes_amarelos_visitante || 0);
    }}

    function redCardsValue(d) {{
      const club = selectedClub();
      if (club) {{
        if (d.mandante === club) return d.cartoes_vermelhos_mandante || 0;
        if (d.visitante === club) return d.cartoes_vermelhos_visitante || 0;
        return 0;
      }}
      return (d.cartoes_vermelhos_mandante || 0) + (d.cartoes_vermelhos_visitante || 0);
    }}

    function selectedCompareClubs() {{
      const values = ['compareClub1', 'compareClub2', 'compareClub3']
        .map(id => document.getElementById(id).value)
        .filter(Boolean);
      return [...new Set(values)];
    }}

    function comparisonRowsForClub(club) {{
      const start = Number(document.getElementById('yearStart').value);
      const end = Number(document.getElementById('yearEnd').value);
      return games.filter(d => (
        d.ano >= start &&
        d.ano <= end &&
        d.mandante === club &&
        (d.arrecadacao_bruta !== null || d.renda_liquida_mandante !== null || d.publico_vendido !== null)
      ));
    }}

    function financialComparisonData() {{
      return selectedCompareClubs().map(club => {{
        const rows = comparisonRowsForClub(club);
        const gross = rows.reduce((sum, d) => sum + (d.arrecadacao_bruta || 0), 0);
        const net = rows.reduce((sum, d) => sum + (d.renda_liquida_mandante || 0), 0);
        const attendance = rows.reduce((sum, d) => sum + (d.publico_vendido || 0), 0);
        const avgTicket = attendance ? gross / attendance : 0;
        return {{
          key: club,
          jogos: rows.length,
          publico: attendance,
          rendaBruta: gross,
          rendaLiquida: net,
          ticketMedio: avgTicket,
        }};
      }});
    }}

    function renderFinancialComparison() {{
      const rows = financialComparisonData();
      if (!rows.length) {{
        document.getElementById('compareTable').innerHTML = '<div class="status">Selecione ate tres clubes.</div>';
        renderBars('compareGrossRevenue', [], {{ color: 'yellow', formatter: fmtMoney.format }});
        renderBars('compareNetRevenue', [], {{ color: 'blue', formatter: fmtMoney.format }});
        renderBars('compareAvgTicket', [], {{ color: 'green', formatter: fmtMoney.format }});
        return;
      }}

      document.getElementById('compareTable').innerHTML = `<table class="compare-table">
        <thead><tr><th>Clube</th><th>Jogos</th><th>Publico</th><th>Renda Bruta</th><th>Renda Liquida</th><th>Ticket Medio</th></tr></thead>
        <tbody>${{rows.map(d => `<tr>
          <td>${{d.key}}</td>
          <td>${{fmtInt.format(d.jogos)}}</td>
          <td>${{fmtInt.format(d.publico)}}</td>
          <td>${{fmtMoney.format(d.rendaBruta)}}</td>
          <td>${{fmtMoney.format(d.rendaLiquida)}}</td>
          <td>${{fmtMoney.format(d.ticketMedio)}}</td>
        </tr>`).join('')}}</tbody>
      </table>`;
      renderBars('compareGrossRevenue', rows.map(d => ({{ key: d.key, value: d.rendaBruta }})), {{ color: 'yellow', formatter: fmtMoney.format }});
      renderBars('compareNetRevenue', rows.map(d => ({{ key: d.key, value: d.rendaLiquida }})), {{ color: 'blue', formatter: fmtMoney.format }});
      renderBars('compareAvgTicket', rows.map(d => ({{ key: d.key, value: d.ticketMedio }})), {{ color: 'green', formatter: fmtMoney.format }});
    }}

    function setMetrics(rows) {{
      const club = selectedClub();
      const tableRows = filteredStandings();
      const totalGames = rows.length;
      const goals = club && tableRows.length
        ? sumField(tableRows, 'gols_pro')
        : rows.reduce((sum, d) => sum + (d.gols_mandante || 0) + (d.gols_visitante || 0), 0);
      const draws = club && tableRows.length
        ? sumField(tableRows, 'empates')
        : rows.filter(d => d.vencedor === 'Empate').length;
      const gamesBase = club && tableRows.length ? sumField(tableRows, 'jogos') : totalGames;
      const pointsBase = tableRows.length ? sumField(tableRows, 'pts') : 0;
      const pointsMax = tableRows.length ? sumField(tableRows, 'jogos') * 3 : 0;
      const performance = pointsMax ? (pointsBase / pointsMax) * 100 : 0;
      const withFinance = rows.filter(d => d.tem_financeiro).length;
      const publicRows = attendanceRows(rows);
      const revenueRows = grossRevenueRows(rows);
      const liquidRows = netRevenueRows(rows);
      const attendance = publicRows.reduce((s, d) => s + attendanceValue(d), 0);
      const revenue = revenueRows.reduce((s, d) => s + grossRevenueValue(d), 0);
      const liquidRevenue = liquidRows.reduce((s, d) => s + netRevenueValue(d), 0);
      const yellowCards = tableRows.length ? sumField(tableRows, 'cartoes_amarelos') : rows.reduce((s, d) => s + yellowCardsValue(d), 0);
      const redCards = tableRows.length ? sumField(tableRows, 'cartoes_vermelhos') : rows.reduce((s, d) => s + redCardsValue(d), 0);

      const items = [
        ['Jogos', fmtInt.format(totalGames)],
        ['Gols', fmtInt.format(goals)],
        ['Média De Gols', gamesBase ? (goals / gamesBase).toFixed(2).replace('.', ',') : '0'],
        ['Aproveitamento', performance.toFixed(1).replace('.', ',') + '%'],
        ['Empates', fmtInt.format(draws)],
        ['Com Financeiro', fmtInt.format(withFinance)],
        ['Publico Pagante', fmtInt.format(attendance)],
        ['Renda Bruta', fmtMoney.format(revenue)],
        ['Renda Liquida', fmtMoney.format(liquidRevenue)],
        ['Cartoes Amarelos', fmtInt.format(yellowCards)],
        ['Cartoes Vermelhos', fmtInt.format(redCards)],
      ];

      document.getElementById('metrics').innerHTML = items.map(([label, value]) =>
        `<div class="metric"><span>${{label}}</span><strong>${{value}}</strong></div>`
      ).join('');
    }}

    function grouped(rows, keyFn, valueFn) {{
      const map = new Map();
      rows.forEach(row => {{
        const key = keyFn(row);
        map.set(key, (map.get(key) || 0) + valueFn(row));
      }});
      return [...map.entries()].map(([key, value]) => ({{ key, value }}));
    }}

    function renderBars(id, rows, options = {{}}) {{
      const limit = options.limit || rows.length;
      const color = options.color || '';
      const formatter = options.formatter || (v => fmtInt.format(v));
      const sorted = [...rows].sort((a, b) => b.value - a.value).slice(0, limit);
      const max = Math.max(1, ...sorted.map(d => Math.abs(d.value)));
      document.getElementById(id).innerHTML = sorted.map(d => {{
        const width = Math.max(2, (Math.abs(d.value) / max) * 100);
        return `<div class="bar-row">
          <span>${{d.key}}</span>
          <div class="bar-track"><div class="bar ${{color}}" style="width:${{width}}%"></div></div>
          <strong>${{formatter(d.value)}}</strong>
        </div>`;
      }}).join('');
    }}

    function renderMatches(rows) {{
      const sorted = [...rows].sort((a, b) => b.ano - a.ano || b.rodada - a.rodada).slice(0, 200);
      document.getElementById('matchesTable').innerHTML = `<table>
        <thead><tr><th>Ano</th><th>Rodada</th><th>Partida</th><th>Placar</th><th>Público</th><th>CA</th><th>CV</th><th>Renda Bruta</th><th>Renda Liquida</th><th>Status</th></tr></thead>
        <tbody>${{sorted.map(d => `<tr>
          <td>${{d.ano}}</td>
          <td>${{d.rodada}}</td>
          <td>${{d.mandante}} x ${{d.visitante}}</td>
          <td>${{d.resultado}}</td>
          <td>${{d.publico_vendido === null ? '' : fmtInt.format(d.publico_vendido)}}</td>
          <td>${{fmtInt.format(yellowCardsValue(d))}}</td>
          <td>${{fmtInt.format(redCardsValue(d))}}</td>
          <td>${{d.arrecadacao_bruta === null ? '' : fmtMoney.format(d.arrecadacao_bruta)}}</td>
          <td>${{d.renda_liquida_mandante === null ? '' : fmtMoney.format(d.renda_liquida_mandante)}}</td>
          <td>${{d.financeiro_status}}</td>
        </tr>`).join('')}}</tbody>
      </table>`;
      document.getElementById('tableStatus').textContent = `${{fmtInt.format(sorted.length)}} de ${{fmtInt.format(rows.length)}} partidas`;
    }}

    function render() {{
      const rows = filteredGames();
      const tableRows = filteredStandings();
      const club = selectedClub();
      setMetrics(rows);

      if (club && tableRows.length) {{
        renderBars('goalsByYear', grouped(tableRows, d => d.ano, d => d.gols_pro || 0), {{ color: 'green' }});
        renderBars('resultMix', [
          {{ key: 'Vitória', value: sumField(tableRows, 'vitorias') }},
          {{ key: 'Empate', value: sumField(tableRows, 'empates') }},
          {{ key: 'Derrota', value: sumField(tableRows, 'derrotas') }},
        ], {{ color: 'yellow' }});
      }} else {{
        renderBars('goalsByYear', grouped(tableRows, d => d.ano, d => d.gols_pro || 0), {{ color: 'green' }});
        renderBars('resultMix', grouped(rows, d => d.vencedor === 'Empate' ? 'Empate' : 'Com vencedor', () => 1), {{ color: 'yellow' }});
      }}
      renderBars('pointsByClub', grouped(tableRows, d => d.time, d => d.pts || 0), {{ limit: 20, color: 'green' }});
      renderBars('goalDiffByClub', grouped(tableRows, d => d.time, d => d.saldo_gols || 0), {{ limit: 20, color: 'blue' }});
      renderBars('yellowCardsByClub', grouped(tableRows, d => d.time, d => d.cartoes_amarelos || 0), {{ limit: 20, color: 'yellow' }});
      renderBars('redCardsByClub', grouped(tableRows, d => d.time, d => d.cartoes_vermelhos || 0), {{ limit: 20, color: 'red' }});
      renderBars('revenueByYear', grouped(grossRevenueRows(rows), d => d.ano, d => grossRevenueValue(d)), {{ color: 'yellow', formatter: fmtMoney.format }});
      renderBars('netRevenueByYear', grouped(netRevenueRows(rows), d => d.ano, d => netRevenueValue(d)), {{ color: 'blue', formatter: fmtMoney.format }});
      renderBars('attendanceByYear', grouped(attendanceRows(rows), d => d.ano, d => attendanceValue(d)), {{ color: 'green' }});
      renderFinancialComparison();
      renderMatches(rows);
    }}

    document.querySelectorAll('.tab').forEach(tab => {{
      tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab').forEach(item => item.classList.remove('active'));
        tab.classList.add('active');
        document.querySelectorAll('.view').forEach(view => view.classList.add('hidden'));
        document.getElementById(tab.dataset.view).classList.remove('hidden');
      }});
    }});

    ['yearStart', 'yearEnd', 'club', 'search', 'financeOnly', 'compareClub1', 'compareClub2', 'compareClub3'].forEach(id => {{
      document.getElementById(id).addEventListener('input', render);
      document.getElementById(id).addEventListener('change', render);
    }});

    document.getElementById('reset').addEventListener('click', () => {{
      document.getElementById('yearStart').value = Math.min(...years);
      document.getElementById('yearEnd').value = Math.max(...years);
      document.getElementById('club').value = '';
      document.getElementById('search').value = '';
      document.getElementById('financeOnly').checked = false;
      ['compareClub1', 'compareClub2', 'compareClub3'].forEach((id, index) => {{
        document.getElementById(id).value = defaultCompareClubs[index] || '';
      }});
      render();
    }});

    document.getElementById('updateData').addEventListener('click', async () => {{
      const button = document.getElementById('updateData');
      const status = document.getElementById('updateStatus');
      button.disabled = true;
      status.textContent = 'Atualizando dados. Isso pode levar alguns minutos...';
      try {{
        const response = await fetch('/api/atualizar', {{ method: 'POST' }});
        const payload = await response.json();
        if (!response.ok || !payload.ok) {{
          throw new Error(payload.error || payload.output || 'Falha ao atualizar.');
        }}
        status.textContent = 'Atualizacao concluida. Recarregando dashboard...';
        setTimeout(() => window.location.reload(), 900);
      }} catch (error) {{
        status.textContent = 'Para usar este botao, abra pelo servidor local: python src/14_servidor_dashboard.py';
        console.error(error);
        button.disabled = false;
      }}
    }});

    render();
  </script>
</body>
</html>"""


def main():
    game_rows, standing_rows = load_data()
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(build_html(game_rows, standing_rows), encoding="utf-8")
    print(f"Dashboard gerado: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
