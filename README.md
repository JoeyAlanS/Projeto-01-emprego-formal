# Projeto 1 - Economia e emprego formal no Ceará

Análise exploratória e dashboard com dados municipais do IBGE/SIDRA para investigar como a estrutura econômica se relaciona com emprego formal, remuneração e crescimento populacional.

**Equipe:** Joey Alan e Paulo Henrico
**Tema:** 1 - Economia e emprego formal
**Recorte:** 184 municípios do Ceará; CEMPRE 2022, PIB 2021/2022 e Censo 2022.

## Perguntas de análise

1. Como o PIB por habitante se distribui entre os municípios em 2022?
2. Como a intensidade de ocupação formal se relaciona com o PIB por habitante?
3. Municípios com maior crescimento populacional apresentam maior intensidade de ocupação formal?
4. Como a composição setorial de 2021 se associa ao emprego formal observado em 2022?

As relações são exploratórias e observacionais. Não representam causalidade. O pessoal ocupado do CEMPRE se refere às organizações formais localizadas no município e não necessariamente aos residentes empregados; por isso usamos o nome **intensidade de ocupação formal**, e não taxa de emprego.

## Estrutura

```text
dados/raw/          arquivos originais fornecidos, somente leitura
dados/processed/    dados tipados, diagnóstico e regra de limpeza
dados/analytical/   integração 1:1 por código IBGE e indicadores derivados
src/                ETL e integração reutilizáveis
notebooks/          geração das figuras e macros do relatório
app/                dashboard Streamlit
docs/               entrega parcial em LaTeX/PDF e figuras
```

## Execução

Instale as dependências e execute o pipeline a partir da raiz:

```bash
python -m pip install -r requirements.txt
python executar_tudo.py
streamlit run app/app.py
```

O pipeline não consulta API. Ele lê somente os CSVs versionados em `dados/raw/` e gera:

- `dados/processed/*.csv`: valores originais preservados em `valor` e valores tipados em `valor_numerico`;
- `dados/processed/diagnostico_qualidade.json`: linhas, níveis, duplicatas, unidades e símbolos SIDRA;
- `dados/analytical/base_analitica_municipios.csv`: uma linha por município, integrada por `territorio_codigo`;
- `dados/analytical/relatorio_integracao.json`: correspondências e não correspondências de cada junção.

Para gerar as figuras e os dados que alimentam a entrega parcial:

```bash
python notebooks/extracao_graficos_relatorio.py
```

## Dados e decisões metodológicas

| Tabela | Período | Uso | Unidade principal |
|---|---:|---|---|
| 9509 - CEMPRE | 2022 | unidades locais, empresas, ocupação, assalariados e remuneração | pessoas, unidades, mil R$ e R$ |
| 5938 - PIB municipal | 2022 | PIB total para cálculo per capita alinhado ao Censo | mil R$ |
| 5938 - estrutura econômica | 2021 | participações setoriais do VAB | % |
| 4709 - Censo | 2022 | população residente e crescimento 2010-2022 | pessoas e % |

A chave de pareamento é o código IBGE de sete dígitos em `territorio_codigo`. O nível municipal é `N6`. A tabela de estrutura setorial de 2021 é usada como associação exploratória com indicadores de 2022, pois existe defasagem de um ano. O PIB em mil reais é multiplicado por 1.000 antes do cálculo do PIB per capita. O salário médio mensal oficial da tabela 9509 é utilizado diretamente.

Os símbolos SIDRA `-`, `X`, `..` e `...` são classificados como indisponíveis (`NA`); `0` é preservado como zero informado. Os diagnósticos atuais dos arquivos fornecidos estão registrados no repositório e indicam 184 municípios por base, zero duplicatas na chave declarada e zero ocorrências desses símbolos.

## Entrega e próximos passos

O acompanhamento documenta o primeiro cruzamento, duas visualizações preliminares e um wireframe. Para a entrega final ainda devem ser atualizados o deploy público do dashboard, os slides, o vídeo extensionista e os links exigidos no AVA. Os links externos não foram inventados neste repositório; devem ser preenchidos pela equipe quando estiverem disponíveis.
