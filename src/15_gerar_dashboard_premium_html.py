import json
import base64
import mimetypes
from pathlib import Path

import pandas as pd


ROOT = Path(".")
GAMES_CSV = ROOT / "data/processed/dashboard/base_jogos_brasileirao_dashboard.csv"
STANDINGS_CSV = ROOT / "data/processed/dashboard/base_classificacao_brasileirao_dashboard.csv"
OUTPUT_HTML = ROOT / "reports/dashboard/brasileirao_dashboard_premium.html"
ASSET_DIR = ROOT / "clube"


BADGE_FILES = {
    "América Mineiro": "americamineiro.svg",
    "Athletico Paranaense": "athleticoparanaense.svg",
    "Atlético Goianiense": "atleticogoianense.png",
    "Atlético Mineiro": "atleticomineiro.svg",
    "Avaí": "avai.png",
    "Bahia": "bahia.svg",
    "Botafogo": "botafogo.svg",
    "Ceará": "ceara.svg",
    "Chapecoense": "chapecoense.svg",
    "Corinthians": "corinthians.svg",
    "Coritiba": "coritiba.svg",
    "Criciúma": "criciuma.png",
    "Cruzeiro": "cruzeiro.svg",
    "Cuiabá": "cuiaba.svg",
    "Figueirense": "figueirense.png",
    "Flamengo": "flamengo.svg",
    "Fluminense": "fluminense.svg",
    "Fortaleza": "fortaleza.png",
    "Goiás": "goias.png",
    "Grêmio": "gremio.svg",
    "Internacional": "internacional.png",
    "Juventude": "juventude.png",
    "Mirassol": "mirassol.svg",
    "Palmeiras": "palmeiras.svg",
    "Paraná": "parana.svg",
    "Ponte Preta": "pontepreta.png",
    "Red Bull Bragantino": "redbullbragantino.svg",
    "Remo": "remo.svg",
    "Santos": "santos.svg",
    "São Paulo": "saopaulo.svg",
    "Sport": "sport.svg",
    "Vasco da Gama": "vascodagama.svg",
    "Vitória": "vitoria.svg",
}


def money(value):
    if pd.isna(value):
        return None
    return float(value)


def number(value):
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def bool_value(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def image_data_uri(path):
    if not path.exists():
        return None
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def load_assets():
    badges = {}
    for team, filename in BADGE_FILES.items():
        uri = image_data_uri(ASSET_DIR / filename)
        if uri:
            badges[team] = uri
    return {
        "badges": badges,
        "leagueLogo": image_data_uri(ASSET_DIR / "campeonatobrasileiro.svg"),
    }


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
                "mandante": str(row.get("mandante")),
                "visitante": str(row.get("visitante")),
                "gols_mandante": number(row.get("gols_mandante")),
                "gols_visitante": number(row.get("gols_visitante")),
                "resultado": str(row.get("resultado")),
                "vencedor": str(row.get("vencedor")),
                "publico_vendido": number(row.get("publico_vendido")),
                "arrecadacao_bruta": money(row.get("arrecadacao_bruta")),
                "renda_liquida_mandante": money(row.get("renda_mandante")),
                "cartoes_amarelos_mandante": number(row.get("cartoes_amarelos_mandante")),
                "cartoes_vermelhos_mandante": number(row.get("cartoes_vermelhos_mandante")),
                "cartoes_amarelos_visitante": number(row.get("cartoes_amarelos_visitante")),
                "cartoes_vermelhos_visitante": number(row.get("cartoes_vermelhos_visitante")),
                "financeiro_status": str(row.get("financeiro_status")),
                "tem_financeiro": bool_value(row.get("tem_financeiro")),
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
            }
        )

    return game_rows, standing_rows


def build_html(game_rows, standing_rows):
    max_year = max(row.get("ano") or 0 for row in game_rows)
    payload = {"games": game_rows, "standings": standing_rows, **load_assets()}
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    template = r"""<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Brasileirao Analytics Premium</title>
  <style>
    :root {
      --blue:#0066ff; --cyan:#00d9ff; --purple:#7c3aed; --green:#00ff88;
      --amber:#ffb800; --red:#ff2e63; --bg:#0a0e27; --surface:#1a1f3a;
      --surface2:#252d4a; --text:#e4e7eb; --muted:#9ca3af; --soft:#6b7280;
      --border:rgba(0,217,255,.16); --glass:rgba(255,255,255,.055);
    }
    *{box-sizing:border-box}
    body{margin:0;overflow-x:hidden;background:linear-gradient(135deg,#0a0e27 0%,#1a1f3a 52%,#0a0e27 100%);color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif;letter-spacing:0}
    body:before{content:"";position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(0,217,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(0,217,255,.035) 1px,transparent 1px);background-size:38px 38px;mask-image:linear-gradient(#000,transparent 88%)}
    .shell{display:grid;grid-template-columns:300px minmax(0,1fr);min-height:100vh}
    .sidebar{position:sticky;top:0;height:100vh;overflow:auto;padding:26px 22px;border-right:1px solid rgba(0,217,255,.12);background:linear-gradient(180deg,#0a0e27 0%,#1a1f3a 100%);box-shadow:inset 0 0 60px rgba(0,217,255,.05)}
    .brand{display:flex;gap:12px;align-items:center;margin-bottom:28px}.pulse{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,var(--blue),var(--cyan));box-shadow:0 0 28px rgba(0,217,255,.32);display:grid;place-items:center;color:#071024;font-weight:900}.pulse img{width:34px;height:34px;object-fit:contain;filter:drop-shadow(0 4px 10px rgba(0,0,0,.22))}.brand h1{font-size:22px;margin:0;background:linear-gradient(135deg,var(--cyan),var(--blue));-webkit-background-clip:text;color:transparent}.brand p{margin:2px 0 0;color:var(--muted);font:600 12px Consolas,monospace;text-transform:uppercase}
    .nav{display:grid;gap:9px}.nav button{border:1px solid transparent;background:transparent;color:var(--muted);text-align:left;padding:13px 14px;border-radius:12px;font-weight:700;cursor:pointer;transition:.25s}.nav button.active,.nav button:hover{color:var(--cyan);border-color:rgba(0,217,255,.25);background:rgba(0,102,255,.13);box-shadow:0 0 20px rgba(0,217,255,.12)}
    .main{min-width:0}.topbar{position:sticky;top:0;z-index:5;padding:22px 30px;border-bottom:1px solid rgba(0,217,255,.12);backdrop-filter:blur(12px);background:linear-gradient(90deg,rgba(10,14,39,.88),rgba(0,102,255,.04))}
    .title-row{display:flex;justify-content:space-between;gap:18px;align-items:center;margin-bottom:18px}.title-row h2{font-size:clamp(24px,3vw,30px);margin:0}.title-row span{font:600 12px Consolas,monospace;color:var(--cyan);text-transform:uppercase}
    .filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px;align-items:end}.filters .field:nth-child(4){grid-column:span 2}.field{display:grid;gap:5px;min-width:0;color:var(--muted);font:700 11px Consolas,monospace;text-transform:uppercase}.field select,.field input{width:100%;box-sizing:border-box;min-height:40px;border:1px solid rgba(0,217,255,.18);border-radius:12px;background:rgba(255,255,255,.055);color:var(--text);padding:8px 10px;outline:none}.field option{color:#111}.check{display:flex;align-items:center;gap:8px;min-height:40px;color:var(--text);font-size:13px;white-space:nowrap}.btn{border:0;border-radius:12px;background:linear-gradient(135deg,var(--blue),var(--cyan));color:#071024;font-weight:900;min-height:40px;padding:8px 14px;cursor:pointer;box-shadow:0 6px 18px rgba(0,102,255,.28)}
    .content{padding:24px 30px 34px}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:14px;margin-bottom:18px}.metric{position:relative;overflow:hidden;border:1.5px solid rgba(0,217,255,.28);border-radius:16px;padding:18px;background:linear-gradient(135deg,rgba(0,102,255,.10),rgba(0,217,255,.04));box-shadow:0 0 20px rgba(0,217,255,.13)}.metric:before{content:"";position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent,var(--cyan),transparent)}.metric span{font:700 11px Consolas,monospace;color:var(--muted);text-transform:uppercase}.metric strong{display:block;margin-top:10px;font:800 clamp(22px,3vw,28px) Consolas,monospace}
    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.grid.three{grid-template-columns:repeat(3,minmax(0,1fr))}.panel{min-width:0;overflow-x:auto;border:1px solid var(--border);border-radius:16px;background:linear-gradient(135deg,rgba(0,102,255,.05),rgba(0,217,255,.025));padding:20px;box-shadow:inset 0 1px 0 rgba(255,255,255,.08)}.panel h3{margin:0 0 16px;font-size:18px}.view{display:none}.view.active{display:block}
    .club-label{display:inline-flex;align-items:center;gap:8px;min-width:0;max-width:100%}.club-label.home{justify-content:flex-end;text-align:right}.club-label.away{justify-content:flex-start;text-align:left}.club-label span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.club-badge{width:24px;height:24px;object-fit:contain;flex:0 0 auto;filter:drop-shadow(0 3px 8px rgba(0,0,0,.28))}.club-badge.large{width:34px;height:34px}.club-badge.match{width:30px;height:30px}.versus-pair{display:inline-flex;align-items:center;gap:9px;white-space:nowrap}.versus-x{color:var(--muted);font-weight:800}.bar-row{display:grid;grid-template-columns:minmax(120px,200px) minmax(0,1fr) minmax(70px,auto);gap:10px;align-items:center;margin:9px 0;font-size:13px}.bar-row>span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bar-track{height:13px;border-radius:5px;background:rgba(255,255,255,.07);overflow:hidden}.bar{height:100%;min-width:2px;border-radius:5px;background:linear-gradient(90deg,var(--blue),var(--cyan));box-shadow:0 0 12px rgba(0,217,255,.24)}.bar.green{background:linear-gradient(90deg,var(--green),var(--cyan))}.bar.yellow{background:linear-gradient(90deg,var(--amber),#ff9500)}.bar.red{background:linear-gradient(90deg,var(--red),#ff6b6b)}.bar.purple{background:linear-gradient(90deg,var(--purple),var(--blue))}
    .rank-grid{display:grid;grid-template-columns:repeat(3,minmax(260px,1fr));gap:28px}.rank-card{position:relative;min-height:300px;border:1.5px solid var(--cyan);border-radius:18px;padding:28px 30px;background:linear-gradient(135deg,rgba(0,102,255,.10),rgba(255,255,255,.03));box-shadow:0 18px 44px rgba(0,0,0,.23),0 0 20px rgba(0,217,255,.12)}.rank-card .medal{position:absolute;right:-1px;top:-1px;width:56px;height:56px;border-radius:0 18px 0 28px;display:grid;place-items:center;background:#ffad00;color:#0a0e27;font-weight:900}.rank-card h3{font-size:26px;margin:6px 0 30px}.rank-card .pts{position:absolute;right:30px;top:92px;font:900 30px Consolas,monospace}.rank-line{display:grid;grid-template-columns:1fr 1fr 1fr;text-align:center;margin:26px 0}.rank-line label,.rank-card small{display:block;color:var(--soft);font:700 13px Consolas,monospace;text-transform:uppercase}.rank-line strong{font:900 24px Consolas,monospace}.good{color:var(--green)}.warn{color:var(--amber)}.bad{color:var(--red)}.rank-foot{border-top:1px solid rgba(0,217,255,.12);padding-top:14px;display:grid;gap:16px}.rank-foot div{display:flex;justify-content:space-between;color:var(--muted);font:600 14px Consolas,monospace}.rank-foot strong{color:var(--green)}
    .line-controls{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px}.period-bars{display:grid;gap:8px;overflow:visible;padding-right:0}.period-bars .bar-row{grid-template-columns:minmax(120px,160px) minmax(0,1fr) minmax(58px,auto)}.legend{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px}.legend span{font:700 12px Consolas,monospace;color:var(--muted)}.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
    table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px 9px;border-bottom:1px solid rgba(255,255,255,.07);text-align:left}th{font:700 11px Consolas,monospace;color:var(--muted);text-transform:uppercase;background:rgba(255,255,255,.03)}.compare-controls,.versus-controls{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}.status{margin-top:10px;color:var(--muted);font-size:12px}
    .match-list{display:grid;gap:18px}.match-card{display:grid;grid-template-columns:170px minmax(260px,1fr) 170px minmax(260px,1fr) 180px;gap:20px;align-items:center;border:1px solid rgba(0,217,255,.16);border-radius:18px;background:linear-gradient(135deg,rgba(0,102,255,.07),rgba(0,217,255,.025));padding:22px 28px}.match-meta{display:grid;gap:12px;color:#aac0d8;font:700 14px Consolas,monospace}.team-name{font-size:26px;font-weight:800;min-width:0}.team-home{justify-self:end;text-align:right}.team-away{justify-self:start;text-align:left}.team-home .club-label{justify-content:flex-end}.team-away .club-label{justify-content:flex-start}.score-box{justify-self:center;border:1px solid rgba(0,217,255,.28);border-radius:16px;background:rgba(0,102,255,.12);padding:16px 30px;font:900 44px Consolas,monospace;white-space:nowrap}.score-box .win{color:var(--green)}.score-box em{font-style:normal;color:var(--muted);font-size:22px;margin:0 12px}.match-extra{text-align:right;color:var(--muted);font:700 13px Consolas,monospace}.badge{display:inline-block;padding:7px 14px;border-radius:999px;background:rgba(0,255,136,.14);color:var(--green);margin-bottom:8px}
    @media(max-width:1180px){.shell{grid-template-columns:1fr}.sidebar{position:relative;height:auto;padding:18px 22px;border-right:0;border-bottom:1px solid rgba(0,217,255,.12)}.brand{margin-bottom:16px}.nav{grid-template-columns:repeat(6,minmax(118px,1fr));overflow-x:auto;padding-bottom:4px}.nav button{text-align:center;white-space:nowrap}.topbar{position:relative}.filters{grid-template-columns:repeat(auto-fit,minmax(160px,1fr))}.grid,.grid.three,.rank-grid{grid-template-columns:1fr}.match-card{grid-template-columns:1fr;text-align:left}.team-home,.team-away,.score-box{justify-self:start;text-align:left}.club-label.home{justify-content:flex-start;text-align:left}.match-extra{text-align:left}}@media(max-width:720px){.topbar,.content{padding:16px}.title-row{display:grid;gap:14px}.title-row .btn{width:100%}.filters,.filters .field:nth-child(4),.metrics,.compare-controls,.versus-controls{grid-template-columns:1fr;grid-column:auto}.check{align-items:center}.metric{padding:16px}.panel{padding:16px}.period-bars .bar-row,.bar-row{grid-template-columns:1fr;gap:7px}.bar-row span{white-space:normal}.bar-row strong{justify-self:start}.score-box{font-size:34px;padding:14px 22px}.team-name{font-size:22px}.versus-pair{white-space:normal;flex-wrap:wrap}}@media(max-width:420px){.brand h1{font-size:20px}.pulse{width:40px;height:40px}.nav{grid-template-columns:repeat(3,minmax(110px,1fr))}.metric strong{font-size:22px}.rank-card{padding:22px 20px}.rank-card h3{font-size:22px}.rank-card .pts{position:static;margin-bottom:14px}}
  </style>
</head>
<body>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand"><div class="pulse" id="leagueMark">BR</div><div><h1>Brasileirao</h1><p>Analytics</p></div></div>
      <nav class="nav">
        <button class="active" data-view="overview">Visao Geral</button>
        <button data-view="clubs">Clubes</button>
        <button data-view="finance">Financeiro</button>
        <button data-view="compare">Comparativo</button>
        <button data-view="matches">Partidas</button>
        <button data-view="versus">Versus</button>
      </nav>
    </aside>
    <main class="main">
      <header class="topbar">
        <div class="title-row"><div><span>Era dos pontos corridos 2003-__MAX_YEAR__</span><h2>Dashboard Brasileiro Serie A</h2></div><button class="btn" id="updateData">Atualizar dados</button></div>
        <section class="filters">
          <label class="field">Ano inicial<select id="yearStart"></select></label>
          <label class="field">Ano final<select id="yearEnd"></select></label>
          <label class="field">Clube<select id="club"></select></label>
          <label class="field">Busca<input id="search" type="search" placeholder="Time ou placar"></label>
          <label class="check"><input id="financeOnly" type="checkbox"> Com financeiro</label>
          <button class="btn" id="reset">Limpar</button>
        </section>
        <div class="status" id="updateStatus"></div>
      </header>
      <section class="content">
        <div class="metrics" id="metrics"></div>

        <section id="overview" class="view active">
          <div class="panel">
            <div class="line-controls">
              <h3>Pontos por clube</h3>
            </div>
            <div id="pointsPeriodBars" class="period-bars"></div>
          </div>
        </section>

        <section id="clubs" class="view">
          <div id="clubRankingCards" class="rank-grid"></div>
        </section>

        <section id="finance" class="view">
          <div class="grid">
            <div class="panel"><h3>Receita Bruta por clube</h3><div id="financeGrossByClub"></div></div>
            <div class="panel"><h3>Receita Liquida por clube</h3><div id="financeNetByClub"></div></div>
            <div class="panel"><h3>Despesa por clube</h3><div id="financeExpenseByClub"></div></div>
            <div class="panel"><h3>Ticket Medio por clube</h3><div id="financeTicketByClub"></div></div>
          </div>
        </section>

        <section id="compare" class="view">
          <div class="panel"><h3>Comparacao</h3><div class="compare-controls"><label class="field">Clube 1<select id="compareClub1"></select></label><label class="field">Clube 2<select id="compareClub2"></select></label><label class="field">Clube 3<select id="compareClub3"></select></label></div><div id="compareTable"></div></div>
          <div class="grid" style="margin-top:16px"><div class="panel"><h3>Renda Bruta</h3><div id="compareGrossRevenue"></div></div><div class="panel"><h3>Renda Liquida</h3><div id="compareNetRevenue"></div></div><div class="panel"><h3>Ticket Medio</h3><div id="compareAvgTicket"></div></div></div>
        </section>

        <section id="matches" class="view">
          <div class="match-list" id="matchesList"></div>
          <div class="status" id="tableStatus"></div>
        </section>

        <section id="versus" class="view">
          <div class="panel">
            <h3>Confronto direto</h3>
            <div class="versus-controls"><label class="field">Time A<select id="versusClub1"></select></label><label class="field">Time B<select id="versusClub2"></select></label></div>
            <div class="metrics" id="versusMetrics"></div>
            <div id="versusMatches"></div>
          </div>
        </section>
      </section>
    </main>
  </div>
  <script id="data" type="application/json">__DATA__</script>
  <script>
    const DATA=JSON.parse(document.getElementById('data').textContent),games=DATA.games,standings=DATA.standings;
    const years=[...new Set(games.map(d=>d.ano))].sort((a,b)=>a-b),clubs=[...new Set(games.flatMap(d=>[d.mandante,d.visitante]))].sort();
    const fmtInt=new Intl.NumberFormat('pt-BR',{maximumFractionDigits:0}),fmtMoney=new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL',maximumFractionDigits:0});
    const colors=['#00D9FF','#00FF88','#FFB800','#7C3AED','#FF2E63','#0066FF'];
    const badges=DATA.badges||{};
    const monthMap={Jan:0,Feb:1,Mar:2,Apr:3,May:4,Jun:5,Jul:6,Aug:7,Sep:8,Oct:9,Nov:10,Dec:11};
    if(DATA.leagueLogo)document.getElementById('leagueMark').innerHTML=`<img src="${DATA.leagueLogo}" alt="Campeonato Brasileiro">`;
    function teamLabel(team,size=''){const src=badges[team];return `<span class="club-label">${src?`<img class="club-badge ${size}" src="${src}" alt="">`:''}<span>${team}</span></span>`}
    function teamHomeLabel(team,size='match'){const src=badges[team];return `<span class="club-label home"><span>${team}</span>${src?`<img class="club-badge ${size}" src="${src}" alt="">`:''}</span>`}
    function teamAwayLabel(team,size='match'){const src=badges[team];return `<span class="club-label away">${src?`<img class="club-badge ${size}" src="${src}" alt="">`:''}<span>${team}</span></span>`}
    function matchupLabel(home,away,size='match'){return `<span class="versus-pair">${teamHomeLabel(home,size)}<span class="versus-x">x</span>${teamAwayLabel(away,size)}</span>`}
    function scoreHtml(d){const homeWin=d.gols_mandante>d.gols_visitante,awayWin=d.gols_visitante>d.gols_mandante;return `<span class="${homeWin?'win':''}">${d.gols_mandante}</span><em>x</em><span class="${awayWin?'win':''}">${d.gols_visitante}</span>`}
    function fillSelect(id,values,all){const el=document.getElementById(id);el.innerHTML='';if(all){const o=document.createElement('option');o.value='';o.textContent=all;el.appendChild(o)}values.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;el.appendChild(o)})}
    ['yearStart','yearEnd'].forEach(id=>fillSelect(id,years));['club','compareClub1','compareClub2','compareClub3','versusClub1','versusClub2'].forEach(id=>fillSelect(id,clubs,id==='club'?'Todos':'Selecionar'));
    yearStart.value=Math.min(...years);yearEnd.value=Math.max(...years);['Flamengo','Palmeiras','Corinthians'].forEach((c,i)=>{const el=document.getElementById('compareClub'+(i+1));if(clubs.includes(c))el.value=c});if(clubs.includes('Palmeiras'))versusClub1.value='Palmeiras';if(clubs.includes('Flamengo'))versusClub2.value='Flamengo';
    function selectedClub(){return club.value}
    function filteredGames(){const s=+yearStart.value,e=+yearEnd.value,c=club.value,t=search.value.trim().toLowerCase(),fin=financeOnly.checked;return games.filter(d=>d.ano>=s&&d.ano<=e&&(!c||d.mandante===c||d.visitante===c)&&(!fin||d.tem_financeiro)&&(!t||[d.mandante,d.visitante,d.resultado,d.financeiro_status].join(' ').toLowerCase().includes(t)))}
    function filteredStandings(){const s=+yearStart.value,e=+yearEnd.value,c=selectedClub();return standings.filter(d=>d.ano>=s&&d.ano<=e&&(!c||d.time===c||d.time.startsWith(c+'/')))}
    const sum=(rows,f)=>rows.reduce((a,d)=>a+(d[f]||0),0);
    function homeRows(rows,field){const c=selectedClub();return rows.filter(d=>d[field]!=null&&(!c||d.mandante===c))}
    function homeVal(d,field){const c=selectedClub();return c&&d.mandante!==c?0:(d[field]||0)}
    function yellowFor(d,team){if(!team)return(d.cartoes_amarelos_mandante||0)+(d.cartoes_amarelos_visitante||0);return d.mandante===team?(d.cartoes_amarelos_mandante||0):d.visitante===team?(d.cartoes_amarelos_visitante||0):0}
    function redFor(d,team){if(!team)return(d.cartoes_vermelhos_mandante||0)+(d.cartoes_vermelhos_visitante||0);return d.mandante===team?(d.cartoes_vermelhos_mandante||0):d.visitante===team?(d.cartoes_vermelhos_visitante||0):0}
    function visibleView(){return document.querySelector('.view.active')?.id||'overview'}
    function metricItems(rows){const v=visibleView(),tr=filteredStandings(),team=selectedClub();if(v==='finance'){const gross=homeRows(rows,'arrecadacao_bruta').reduce((s,d)=>s+homeVal(d,'arrecadacao_bruta'),0),net=homeRows(rows,'renda_liquida_mandante').reduce((s,d)=>s+homeVal(d,'renda_liquida_mandante'),0),pub=homeRows(rows,'publico_vendido').reduce((s,d)=>s+homeVal(d,'publico_vendido'),0);return[['Receita Bruta',fmtMoney.format(gross)],['Receita Liquida',fmtMoney.format(net)],['Despesa',fmtMoney.format(gross-net)],['Ticket Medio',fmtMoney.format(pub?gross/pub:0)]]} if(v!=='overview')return[];const goals=team&&tr.length?sum(tr,'gols_pro'):rows.reduce((s,d)=>s+(d.gols_mandante||0)+(d.gols_visitante||0),0),pub=homeRows(rows,'publico_vendido').reduce((s,d)=>s+homeVal(d,'publico_vendido'),0);return[['Jogos',fmtInt.format(rows.length)],['Gols',fmtInt.format(goals)],['Cartoes Vermelhos',fmtInt.format(team?rows.reduce((s,d)=>s+redFor(d,team),0):rows.reduce((s,d)=>s+redFor(d,''),0))],['Cartoes Amarelos',fmtInt.format(team?rows.reduce((s,d)=>s+yellowFor(d,team),0):rows.reduce((s,d)=>s+yellowFor(d,''),0))],['Publico',fmtInt.format(pub)]]}
    function renderMetrics(rows){const items=metricItems(rows);metrics.style.display=items.length?'grid':'none';metrics.innerHTML=items.map(([l,v])=>`<div class="metric"><span>${l}</span><strong>${v}</strong></div>`).join('')}
    function grouped(rows,k,v){const m=new Map();rows.forEach(r=>m.set(k(r),(m.get(k(r))||0)+v(r)));return[...m.entries()].map(([key,value])=>({key,value}))}
    function renderBars(id,rows,opt={}){const f=opt.formatter||((v)=>fmtInt.format(v)),color=opt.color||'',sorted=[...rows].sort((a,b)=>b.value-a.value).slice(0,opt.limit||rows.length),max=Math.max(1,...sorted.map(d=>Math.abs(d.value)));document.getElementById(id).innerHTML=sorted.map(d=>`<div class="bar-row"><span>${teamLabel(d.key)}</span><div class="bar-track"><div class="bar ${color}" style="width:${Math.max(2,Math.abs(d.value)/max*100)}%"></div></div><strong>${f(d.value)}</strong></div>`).join('')}
    function parseDate(d){if(d.data&&/^\d{4}-\d{2}-\d{2}/.test(d.data))return new Date(d.data+'T12:00:00');const m=String(d.data||'').match(/([A-Za-z]{3})\s+(\d{1,2})/);return m?new Date(d.ano,monthMap[m[1]]??0,+m[2]):new Date(d.ano,0,1)}
    function weekNumber(dt){const d=new Date(Date.UTC(dt.getFullYear(),dt.getMonth(),dt.getDate()));const day=d.getUTCDay()||7;d.setUTCDate(d.getUTCDate()+4-day);const y=new Date(Date.UTC(d.getUTCFullYear(),0,1));return Math.ceil((((d-y)/86400000)+1)/7)}
    function periodKey(dt,mode){const y=dt.getFullYear(),m=dt.getMonth()+1;if(mode==='week')return `${y}-S${String(weekNumber(dt)).padStart(2,'0')}`;if(mode==='month')return `${y}-${String(m).padStart(2,'0')}`;if(mode==='quarter')return `${y}-T${Math.ceil(m/3)}`;if(mode==='semester')return `${y}-S${m<=6?1:2}`;return String(y)}
    function gamePoints(d){return d.gols_mandante>d.gols_visitante?[3,0]:d.gols_mandante<d.gols_visitante?[0,3]:[1,1]}
    function renderPointsBars(rows){const data=aggregateStandings().map(d=>({key:d.time,value:d.pts}));renderBars('pointsPeriodBars',data,{limit:30,color:'green',formatter:fmtInt.format})}
    function aggregateStandings(){const m=new Map();filteredStandings().forEach(r=>{const a=m.get(r.time)||{time:r.time,pts:0,jogos:0,vitorias:0,empates:0,derrotas:0,sg:0,ca:0,cv:0,gp:0};a.pts+=r.pts||0;a.jogos+=r.jogos||0;a.vitorias+=r.vitorias||0;a.empates+=r.empates||0;a.derrotas+=r.derrotas||0;a.sg+=r.saldo_gols||0;a.ca+=r.cartoes_amarelos||0;a.cv+=r.cartoes_vermelhos||0;a.gp+=r.gols_pro||0;m.set(r.time,a)});return[...m.values()].map(a=>({...a,apr:a.jogos?a.pts/(a.jogos*3)*100:0})).sort((a,b)=>b.pts-a.pts||b.sg-a.sg)}
    function renderClubCards(){clubRankingCards.innerHTML=aggregateStandings().slice(0,12).map((d,i)=>`<article class="rank-card"><div class="medal">${i+1}</div><small>Pontos</small><h3>${teamLabel(d.time,'large')}</h3><div class="pts">${fmtInt.format(d.pts)}</div><div class="rank-line"><div><label>V</label><strong class="good">${fmtInt.format(d.vitorias)}</strong></div><div><label>E</label><strong class="warn">${fmtInt.format(d.empates)}</strong></div><div><label>D</label><strong class="bad">${fmtInt.format(d.derrotas)}</strong></div></div><div class="rank-foot"><div><span>Saldo de Gols</span><strong>${d.sg>=0?'+':''}${fmtInt.format(d.sg)}</strong></div><div><span>Aproveitamento</span><strong>${d.apr.toFixed(0)}%</strong></div><div><span>CA / CV</span><strong>${fmtInt.format(d.ca)} / ${fmtInt.format(d.cv)}</strong></div></div></article>`).join('')}
    function financeByClub(){const m=new Map(),team=selectedClub();filteredGames().forEach(d=>{if(team&&d.mandante!==team)return;if(d.arrecadacao_bruta==null&&d.renda_liquida_mandante==null&&d.publico_vendido==null)return;const a=m.get(d.mandante)||{key:d.mandante,gross:0,net:0,publico:0};a.gross+=d.arrecadacao_bruta||0;a.net+=d.renda_liquida_mandante||0;a.publico+=d.publico_vendido||0;m.set(d.mandante,a)});return[...m.values()].map(d=>({...d,expense:d.gross-d.net,ticket:d.publico?d.gross/d.publico:0}))}
    function renderFinance(){const r=financeByClub();renderBars('financeGrossByClub',r.map(d=>({key:d.key,value:d.gross})),{limit:20,color:'yellow',formatter:fmtMoney.format});renderBars('financeNetByClub',r.map(d=>({key:d.key,value:d.net})),{limit:20,color:'purple',formatter:fmtMoney.format});renderBars('financeExpenseByClub',r.map(d=>({key:d.key,value:d.expense})),{limit:20,color:'red',formatter:fmtMoney.format});renderBars('financeTicketByClub',r.map(d=>({key:d.key,value:d.ticket})),{limit:20,color:'green',formatter:fmtMoney.format})}
    function compareData(){return[...new Set(['compareClub1','compareClub2','compareClub3'].map(id=>document.getElementById(id).value).filter(Boolean))].map(team=>{const fin=games.filter(d=>d.ano>=+yearStart.value&&d.ano<=+yearEnd.value&&d.mandante===team&&(d.publico_vendido!=null||d.arrecadacao_bruta!=null)),st=aggregateStandings().find(d=>d.time===team)||{};const gross=sum(fin,'arrecadacao_bruta'),net=sum(fin,'renda_liquida_mandante'),pub=sum(fin,'publico_vendido');return{key:team,jogos:fin.length,publico:pub,rendaBruta:gross,rendaLiquida:net,ticketMedio:pub?gross/pub:0,gols:st.gp||0,vitorias:st.vitorias||0,empates:st.empates||0}})}
    function renderCompare(){const r=compareData();compareTable.innerHTML=`<table><thead><tr><th>Clube</th><th>Jogos</th><th>Publico</th><th>Renda Bruta</th><th>Renda Liquida</th><th>Ticket Medio</th><th>Gols</th><th>V</th><th>E</th></tr></thead><tbody>${r.map(d=>`<tr><td>${teamLabel(d.key)}</td><td>${fmtInt.format(d.jogos)}</td><td>${fmtInt.format(d.publico)}</td><td>${fmtMoney.format(d.rendaBruta)}</td><td>${fmtMoney.format(d.rendaLiquida)}</td><td>${fmtMoney.format(d.ticketMedio)}</td><td>${fmtInt.format(d.gols)}</td><td>${fmtInt.format(d.vitorias)}</td><td>${fmtInt.format(d.empates)}</td></tr>`).join('')}</tbody></table>`;renderBars('compareGrossRevenue',r.map(d=>({key:d.key,value:d.rendaBruta})),{color:'yellow',formatter:fmtMoney.format});renderBars('compareNetRevenue',r.map(d=>({key:d.key,value:d.rendaLiquida})),{color:'purple',formatter:fmtMoney.format});renderBars('compareAvgTicket',r.map(d=>({key:d.key,value:d.ticketMedio})),{color:'green',formatter:fmtMoney.format})}
    function renderMatches(rows){const r=[...rows].sort((a,b)=>b.ano-a.ano||b.rodada-a.rodada).slice(0,80);matchesList.innerHTML=r.map(d=>`<article class="match-card"><div class="match-meta"><div>RODADA ${d.rodada}</div><div>${d.data||''}</div><div>${d.hora||''}</div></div><div class="team-name team-home">${teamHomeLabel(d.mandante,'match')}</div><div class="score-box">${scoreHtml(d)}</div><div class="team-name team-away">${teamAwayLabel(d.visitante,'match')}</div><div class="match-extra"><span class="badge">FINALIZADA</span><div>PUBLICO: <strong style="color:var(--cyan)">${d.publico_vendido==null?'':fmtInt.format(d.publico_vendido)}</strong></div></div></article>`).join('');tableStatus.textContent=`${fmtInt.format(r.length)} de ${fmtInt.format(rows.length)} partidas`}
    function renderVersus(){const a=versusClub1.value,b=versusClub2.value;if(!a||!b||a===b){versusMetrics.innerHTML='';versusMatches.innerHTML='<div class="status">Escolha dois times diferentes.</div>';return}const rows=games.filter(d=>d.ano>=+yearStart.value&&d.ano<=+yearEnd.value&&((d.mandante===a&&d.visitante===b)||(d.mandante===b&&d.visitante===a)));let va=0,vb=0,e=0,ca=0,cv=0,ga=0,gb=0;rows.forEach(d=>{if(d.vencedor==='Empate')e++;else if(d.vencedor===a)va++;else if(d.vencedor===b)vb++;ga+=d.mandante===a?(d.gols_mandante||0):(d.gols_visitante||0);gb+=d.mandante===b?(d.gols_mandante||0):(d.gols_visitante||0);ca+=yellowFor(d,'');cv+=redFor(d,'')});versusMetrics.innerHTML=[['Jogos',rows.length],['Vitorias '+a,va],['Vitorias '+b,vb],['Empates',e],['Gols '+a,ga],['Gols '+b,gb],['Cartoes Amarelos',ca],['Cartoes Vermelhos',cv]].map(([l,v])=>`<div class="metric"><span>${l}</span><strong>${fmtInt.format(v)}</strong></div>`).join('');versusMatches.innerHTML=`<table><thead><tr><th>Ano</th><th>Rodada</th><th>Partida</th><th>Placar</th><th>CA</th><th>CV</th></tr></thead><tbody>${rows.sort((x,y)=>y.ano-x.ano||y.rodada-x.rodada).map(d=>`<tr><td>${d.ano}</td><td>${d.rodada}</td><td>${matchupLabel(d.mandante,d.visitante)}</td><td>${d.resultado}</td><td>${yellowFor(d,'')}</td><td>${redFor(d,'')}</td></tr>`).join('')}</tbody></table>`}
    function render(){const rows=filteredGames();renderMetrics(rows);renderPointsBars(rows);renderClubCards();renderFinance();renderCompare();renderMatches(rows);renderVersus()}
    document.querySelectorAll('.nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));document.getElementById(b.dataset.view).classList.add('active');render()});
    ['yearStart','yearEnd','club','search','financeOnly','compareClub1','compareClub2','compareClub3','versusClub1','versusClub2'].forEach(id=>document.getElementById(id).addEventListener('change',render));search.addEventListener('input',render);
    reset.onclick=()=>{yearStart.value=Math.min(...years);yearEnd.value=Math.max(...years);club.value='';search.value='';financeOnly.checked=false;render()};updateData.onclick=async()=>{updateStatus.textContent='Atualizando dados...';try{const r=await fetch('/api/atualizar',{method:'POST'});if(!r.ok)throw new Error();updateStatus.textContent='Atualizacao concluida';setTimeout(()=>location.reload(),800)}catch(e){updateStatus.textContent='Abra pelo servidor local para atualizar.'}};render();
  </script>
</body>
</html>"""
    return template.replace("__DATA__", data_json).replace("__MAX_YEAR__", str(max_year))


def main():
    game_rows, standing_rows = load_data()
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(build_html(game_rows, standing_rows), encoding="utf-8")
    print(f"Dashboard premium gerado: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
