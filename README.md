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

### Critério de Intensidade de Ocupação Formal e Classificação Socioeconômica

A **intensidade de ocupação formal** é definida como o número de postos formais existentes no município para cada mil habitantes residentes:

$$\text{Intensidade de ocupação formal} = \frac{\text{Pessoal Ocupado Total (CEMPRE 2022)}}{\text{População Residente (Censo 2022)}} \times 1.000$$

#### Por que a classificação por Tercis (Opção A)?
Inicialmente, utilizava-se um corte binário simples na mediana estadual (102,8 postos/mil hab.). Essa abordagem apresentava duas limitações analíticas:
1. **Dicotomia artificial:** Municípios com níveis muito próximos (ex.: 101 e 105 postos/mil hab.) eram colocados em categorias opostas ("baixa" e "alta"), ocultando a similaridade de suas estruturas produtivas;
2. **Ignorava o núcleo do interior:** A maioria das cidades cearenses possui perfil intermediário, que ficava invisível na separação binária.

Para solucionar essas limitações, a intensidade formal foi segmentada em **três tercis homogêneos** (distribuição 61 / 62 / 61 municípios):
* **Baixa intensidade** ($< 91,0$ postos/mil hab. — 61 municípios): localidades com mercado formal muito incipiente;
* **Média intensidade** ($91,0$ a $116,8$ postos/mil hab. — 62 municípios): o patamar típico da maior parte do interior do estado;
* **Alta intensidade** ($> 116,8$ postos/mil hab. — 61 municípios): municípios com mercado de trabalho formal mais dinâmico em relação ao contexto cearense.

#### Matriz Econômica (PIB per capita × Faixas de Intensidade)
Combinando a posição do PIB per capita em relação à mediana estadual (R$ 13.087,74) com os três tercis de intensidade, o projeto classifica os 184 municípios em 6 perfis socioeconômicos:
* **Alto PIB / alta intensidade (52 municípios):** polos regionais, capitais e cidades industriais consolidadas;
* **Baixo PIB / baixa intensidade (48 municípios):** municípios de maior vulnerabilidade econômica e fraca formalização;
* **Baixo PIB / média intensidade (35 municípios):** economia do interior tradicional com formalização dentro da média, mas baixa geração de renda per capita;
* **Alto PIB / média intensidade (27 municípios):** municípios com renda razoável e absorção formal mediana;
* **Alto PIB / baixa intensidade (13 municípios):** enclaves econômicos com alta geração de valor agregado (ex.: parques eólicos, mineração, agropecuária de capital intensivo) que geram poucos postos de trabalho formais locais;
* **Baixo PIB / alta intensidade (9 municípios):** economias com alta densidade de vínculos formais (ex.: forte presença do setor público municipal ou polos produtivos de baixa remuneração), porém com baixo PIB per capita global.

#### Benchmarks de Nível Superior (Ceará e Brasil)
Apesar do rótulo relativo de "alta intensidade" cearense ($> 116,8$), os dados de nível superior evidenciam a profunda assimetria regional:
* **Média ponderada do Ceará (`N3`):** **217,9** postos por mil hab. Apenas **11 municípios** cearenses superam a média do próprio estado (Aquiraz, Eusébio, Fortaleza, Frecheirinha, Horizonte, Jijoca de Jericoacoara, Juazeiro do Norte, Maracanaú, Pereiro, São Gonçalo do Amarante e Sobral).
* **Média nacional do Brasil (`N1`):** **309,0** postos por mil hab. (e PIB per capita de R$ 49.633,83). Apenas **3 municípios** do estado superam a média nacional de formalização (Eusébio, Fortaleza e Pereiro).

Os símbolos SIDRA `-`, `X`, `..` e `...` são classificados como indisponíveis (`NA`); `0` é preservado como zero informado. Os diagnósticos atuais dos arquivos fornecidos estão registrados no repositório e indicam 184 municípios por base, zero duplicatas na chave declarada e zero ocorrências desses símbolos.

## Entrega e próximos passos

O acompanhamento documenta o primeiro cruzamento, duas visualizações preliminares e um wireframe. Para a entrega final ainda devem ser atualizados o deploy público do dashboard, os slides, o vídeo extensionista e os links exigidos no AVA. Os links externos não foram inventados neste repositório; devem ser preenchidos pela equipe quando estiverem disponíveis.
