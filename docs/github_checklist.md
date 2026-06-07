# Checklist para Publicar no GitHub

## Antes do primeiro commit

- Confirmar que `brasileirao_analytics` sera um repositorio Git independente.
- Verificar se `data/raw/` e PDFs nao serao versionados.
- Manter `clube/`, `src/`, `reports/dashboard/brasileirao_dashboard_premium.html`, `requirements.txt`, `README.md` e `docs/`.
- Abrir o dashboard e validar as abas principais.
- Atualizar capturas de tela para adicionar ao README, se desejar.

## Comandos sugeridos

Execute a partir da pasta do projeto:

```powershell
cd "C:\Users\alext\OneDrive\Área de Trabalho\Analises\Python\Projetos\brasileirao_analytics"
git init
git add .
git status
git commit -m "Primeira versao do dashboard Brasileirao Analytics"
```

Depois crie um repositorio vazio no GitHub e conecte:

```powershell
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/brasileirao_analytics.git
git push -u origin main
```

## Sugestao de descricao do repositorio

```text
Dashboard interativo de analise do Campeonato Brasileiro Serie A na era dos pontos corridos, com resultados, classificacao, publico, renda, cartoes, escudos e comparativos entre clubes.
```

## Topicos sugeridos

```text
python, pandas, data-analysis, dashboard, futebol, brasileirao, web-scraping, html-css-javascript, portfolio-project
```

