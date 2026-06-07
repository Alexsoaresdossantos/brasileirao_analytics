# Brasileirao Analytics

Projeto de analise de dados sobre o Campeonato Brasileiro Serie A na era dos pontos corridos, reunindo resultados, classificacoes, publico, renda, cartoes e comparativos entre clubes em um dashboard interativo.

O objetivo e transformar dados historicos do Brasileirao em uma experiencia visual de exploracao: desempenho esportivo, indicadores financeiros por mandante, ranking de clubes, calendario de partidas e confrontos diretos.

## Preview

Dashboard principal:

```text
reports/dashboard/brasileirao_dashboard_premium.html
```

Para abrir localmente pelo servidor do projeto:

```powershell
python src\14_servidor_dashboard.py
```

Depois acesse:

```text
http://127.0.0.1:8765/brasileirao_dashboard_premium.html
```

## Principais Recursos

- Historico da Serie A na era dos pontos corridos, desde 2003.
- Ranking de pontos por clube com base na classificacao consolidada.
- Cards de visao geral com jogos, gols, cartoes e publico.
- Aba de clubes com ranking, vitorias, empates, derrotas, saldo de gols e aproveitamento.
- Analise financeira com receita bruta, receita liquida, despesa estimada e ticket medio.
- Comparativo financeiro de ate tres clubes.
- Lista de partidas com escudos, placares e destaque do vencedor.
- Aba Versus para confronto direto entre dois clubes.
- Escudos dos clubes e logo do campeonato embutidos no dashboard premium.
- Botao local de atualizacao de dados via pipeline Python.

## Fontes de Dados

O projeto consolida informacoes publicas a partir de fontes como:

- CBF, para jogos recentes, sumulas, boletins financeiros, publico e arrecadacao quando disponiveis.
- Sr.Goool, para publico, renda e dados complementares.
- RSSSF/RSSSF Brasil, para historico esportivo da era dos pontos corridos.

## Observacoes Sobre Qualidade dos Dados

Dados historicos de futebol exigem validacao cuidadosa. O projeto trata casos como:

- diferencas entre soma jogo a jogo e pontuacao oficial em temporadas com ajustes;
- nomes de clubes escritos de formas diferentes;
- clubes ambiguos, como "Atletico" em diferentes temporadas;
- partidas anuladas, remarcadas ou com particularidades historicas;
- cobertura parcial de dados financeiros e cartoes em algumas temporadas.

Por isso, rankings de pontuacao usam preferencialmente a classificacao consolidada oficial/historica, enquanto resultados de partidas alimentam placares, confrontos e estatisticas de jogos.

## Estrutura do Projeto

```text
brasileirao_analytics/
  clube/                         # escudos e logo do campeonato
  data/
    processed/                   # bases tratadas e consolidadas
    raw/                         # arquivos brutos e caches locais
  docs/
    github_checklist.md
    linkedin_post.md
  notebooks/
  reports/
    dashboard/
      brasileirao_dashboard.html
      brasileirao_dashboard_premium.html
  src/
    07_extrair_brasileirao_cbf.py
    08_extrair_historico_pontos_corridos.py
    09_consolidar_bases_dashboard.py
    10_gerar_dashboard_html.py
    11_reprocessar_financeiro_cbf_cache.py
    12_extrair_publico_renda_srgoool.py
    13_atualizar_dashboard.py
    14_servidor_dashboard.py
    15_gerar_dashboard_premium_html.py
  requirements.txt
```

## Como Reproduzir

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

Execute o pipeline principal:

```powershell
python src\08_extrair_historico_pontos_corridos.py
python src\12_extrair_publico_renda_srgoool.py
python src\09_consolidar_bases_dashboard.py
python src\15_gerar_dashboard_premium_html.py
```

Para abrir com servidor local:

```powershell
python src\14_servidor_dashboard.py
```

## Dashboard

O dashboard premium e um HTML estatico com dados e imagens embutidos, o que facilita demonstracao local e publicacao como artefato de portfolio.

Arquivo:

```text
reports/dashboard/brasileirao_dashboard_premium.html
```

## Tecnologias

- Python
- Pandas
- Requests
- BeautifulSoup
- HTML
- CSS
- JavaScript

## Status

Projeto em evolucao, com foco em portfolio de analise de dados. Proximas melhorias possiveis:

- publicar uma versao navegavel via GitHub Pages ou Streamlit;
- adicionar testes automatizados de consistencia dos dados;
- incluir capturas de tela no README;
- criar uma camada de dados menor para demonstracao publica;
- documentar os principais insights encontrados.

