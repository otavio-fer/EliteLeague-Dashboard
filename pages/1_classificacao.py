# pages/1_classificacao.py (Atualizado para Múltiplas Ligas)

import dash
from dash import dcc, html, callback, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import pandas as pd
from data_store import data, logo_mapping # Importa a estrutura de dados principal

dash.register_page(__name__, path='/', name='Classificação')

# --- Funções de Processamento de Dados (sem alteração) ---
def calcular_streak(resultados):
    if not resultados: return "-"
    ultimo_resultado = resultados[-1]
    streak = 0
    for resultado in reversed(resultados):
        if resultado == ultimo_resultado: streak += 1
        else: break
    return f"{ultimo_resultado[0]}{streak}"

def calcular_ultimos_jogos(resultados):
    return " ".join([r[0] for r in resultados[-3:]])

def processar_classificacao(df_jogos):
    if df_jogos.empty:
        return pd.DataFrame()
        
    df_jogos['RESULTADO_ABREV'] = df_jogos['RESULTADO'].apply(lambda x: 'V' if x == 'VITÓRIA' else 'D')
    
    classificacao = {}
    for time in df_jogos['EQUIPE'].unique():
        jogos_time = df_jogos[df_jogos['EQUIPE'] == time].sort_values(by='DATA', ascending=True)
        vitorias = (jogos_time['RESULTADO'] == 'VITÓRIA').sum()
        derrotas = (jogos_time['RESULTADO'] == 'DERROTA').sum()
        jogos = vitorias + derrotas
        pct_vitorias = vitorias / jogos if jogos > 0 else 0
        pontos_pro = jogos_time['PONTOS MARCADOS'].sum()
        pontos_contra = jogos_time['PONTOS SOFRIDOS'].sum()
        resultados = list(jogos_time['RESULTADO_ABREV'])
        streak = calcular_streak(resultados)
        ultimos_3 = calcular_ultimos_jogos(resultados)
        
        classificacao[time] = {'J': jogos, 'V': vitorias, 'D': derrotas, 'V%': pct_vitorias,
                               'PF': pontos_pro, 'PC': pontos_contra, 'SALDO': pontos_pro - pontos_contra,
                               'SEQ': streak, 'U3': ultimos_3}
        
    df_classificacao = pd.DataFrame.from_dict(classificacao, orient='index').reset_index().rename(columns={'index': 'EQUIPE'})
    df_classificacao = df_classificacao.sort_values(by=['V%', 'SALDO'], ascending=[False, False]).reset_index(drop=True)
    
    if not df_classificacao.empty:
        df_classificacao.insert(0, '#', [f"{i}º" for i in range(1, len(df_classificacao) + 1)])
        df_classificacao['V%'] = df_classificacao['V%'].apply(lambda x: f"{x:.3f}")

    return df_classificacao

# --- Layout da Página ---
# O layout agora é uma função que retorna os componentes, para ser atualizado dinamicamente
def layout():
    return dbc.Container([
        dbc.Row(dbc.Col(html.H3("Tabela de Classificação", className="text-center my-4"))),
        dbc.Row([
            dbc.Col(dbc.Alert(children=[html.I(className="bi bi-square-fill me-2", style={"color": "#fff0c2"}), "Zona de Classificação (Série Ouro)"], color="light", className="text-center p-2")),
            dbc.Col(dbc.Alert(children=[html.I(className="bi bi-square-fill me-2", style={"color": "#e2e3e5"}), "Zona de Classificação (Série Prata)"], color="light", className="text-center p-2")),
        ], className="mb-3", justify="center"),
        
        # <<<<<<<<<< CONTEÚDO DA TABELA SERÁ INSERIDO AQUI PELO CALLBACK >>>>>>>>>
        dbc.Row(id='classification-table-content'),
        
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id="modal-title-classificacao")),
            dbc.ModalBody(id="modal-body-classificacao"),
        ], id="modal-historico-classificacao", is_open=False, size="lg")
    ], fluid=True)


# --- NOVO CALLBACK PRINCIPAL PARA ATUALIZAR A PÁGINA ---
@callback(
    Output('classification-table-content', 'children'),
    Input('league-store', 'data') # "Escuta" a mudança de liga
)
def update_classification_page(league):
    league_data = data.get(league, {})
    if not league_data or 'dfs' not in league_data or 'ranking_equipes' not in league_data['dfs']:
        return dbc.Alert("Dados para a liga selecionada não encontrados.", color="danger")
        
    df_jogos = league_data['dfs']['ranking_equipes'].copy()
    df_classificacao = processar_classificacao(df_jogos)

    if df_classificacao.empty:
        return dbc.Alert("Ainda não há dados de classificação para esta liga.", color="info")

    tabela_header = html.Thead(html.Tr([html.Th(col) for col in df_classificacao.columns] + [html.Th("Histórico")]))

    tabela_body = []
    for i, row in df_classificacao.iterrows():
        row_class = ""
        if i < 4: row_class = "table-warning" 
        elif i >= len(df_classificacao) - 4: row_class = "table-secondary"

        logo_filename = logo_mapping.get(row['EQUIPE'], "default.png")
        
        cells = [html.Td(row[col]) for col in df_classificacao.columns if col != 'EQUIPE']
        team_cell = html.Td(
            html.Div([
                html.Img(src=f"/assets/{logo_filename}", height="30px", className="me-2"),
                row['EQUIPE']
            ], style={'display': 'flex', 'alignItems': 'center'})
        )
        cells.insert(1, team_cell)
        
        cells.append(html.Td(dbc.Button("Ver Jogos", id={'type': 'hist-button-classificacao', 'index': row['EQUIPE']}, n_clicks=0, size="sm", color="primary")))
        
        tabela_body.append(html.Tr(cells, className=row_class))

    return dbc.Col(dbc.Table([tabela_header, html.Tbody(tabela_body)], bordered=True, hover=True, responsive=True, striped=True), width=12)


# --- Callback para o Modal de Histórico (com IDs atualizados) ---
@callback(
    Output("modal-historico-classificacao", "is_open"), 
    Output("modal-title-classificacao", "children"), 
    Output("modal-body-classificacao", "children"),
    Input({'type': 'hist-button-classificacao', 'index': ALL}, 'n_clicks'),
    State("modal-historico-classificacao", "is_open"),
    State('league-store', 'data'), # Precisa saber qual liga está ativa
    prevent_initial_call=True
)
def show_team_history(n_clicks, is_open, league):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks):
        return False, "", ""

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    team_name = eval(button_id)['index']
    
    df_jogos = data[league]['dfs']['ranking_equipes']
    jogos_time = df_jogos[df_jogos['EQUIPE'] == team_name].sort_values(by='DATA', ascending=False)
    
    historico_body = []
    for index, jogo in jogos_time.iterrows():
        resultado_class = "text-success fw-bold" if jogo['RESULTADO'] == 'VITÓRIA' else "text-danger fw-bold"
        historico_body.append(html.Tr([
            html.Td(jogo['ADVERSÁRIO']),
            html.Td(f"{jogo['PONTOS MARCADOS']} x {jogo['PONTOS SOFRIDOS']}", className=resultado_class)
        ]))

    modal_body = dbc.Table([html.Thead(html.Tr([html.Th("Adversário"), html.Th("Placar")])), html.Tbody(historico_body)], bordered=True, striped=True)
    
    return not is_open, f"Histórico de Jogos: {team_name}", modal_body