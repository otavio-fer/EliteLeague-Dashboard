# pages/1_classificacao.py (Corrigido)

import dash
from dash import dcc, html, callback, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import pandas as pd
from data_store import dfs, logo_mapping

dash.register_page(__name__, path='/', name='Classificação')

# --- Funções de Processamento de Dados para a Classificação ---
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
    
    df_classificacao.insert(0, '#', [f"{i}º" for i in range(1, len(df_classificacao) + 1)])
    df_classificacao['V%'] = df_classificacao['V%'].apply(lambda x: f"{x:.3f}")

    return df_classificacao

# --- Criação da Tabela de Classificação ---
df_classificacao = processar_classificacao(dfs['ranking_equipes'].copy())

### CORREÇÃO AQUI: Removidos os colchetes extras [] que envolviam o html.Thead ###
tabela_header = html.Thead(html.Tr([html.Th(col) for col in df_classificacao.columns] + [html.Th("Histórico")]))

tabela_body = []
for i, row in df_classificacao.iterrows():
    row_class = ""
    if i < 4:
        row_class = "table-warning" 
    elif i >= len(df_classificacao) - 4:
        row_class = "table-secondary"

    logo_filename = logo_mapping.get(row['EQUIPE'], "default.png")
    
    cells = [html.Td(row[col]) for col in df_classificacao.columns if col != 'EQUIPE']
    team_cell = html.Td(
        html.Div([
            html.Img(src=f"/assets/{logo_filename}", height="30px", className="me-2"),
            row['EQUIPE']
        ], style={'display': 'flex', 'alignItems': 'center'})
    )
    cells.insert(1, team_cell)
    
    cells.append(html.Td(dbc.Button("Ver Jogos", id={'type': 'hist-button', 'index': row['EQUIPE']}, n_clicks=0, size="sm", color="primary")))
    
    tabela_body.append(html.Tr(cells, className=row_class))

# --- Layout da Página ---
layout = dbc.Container([
    dbc.Row(dbc.Col(html.H3("Tabela de Classificação", className="text-center my-4"))),
    
    dbc.Row([
        dbc.Col(dbc.Alert(children=[html.I(className="bi bi-square-fill me-2", style={"color": "#fff0c2"}), "Zona de Classificação (Série Ouro)"], color="light", className="text-center p-2")),
        dbc.Col(dbc.Alert(children=[html.I(className="bi bi-square-fill me-2", style={"color": "#e2e3e5"}), "Zona de Classificação (Série Prata)"], color="light", className="text-center p-2")),
    ], className="mb-3", justify="center"),
    
    dbc.Row(dbc.Col(dbc.Table([tabela_header, html.Tbody(tabela_body)], bordered=True, hover=True, responsive=True, striped=True), width=12)),
    
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(id="modal-body"),
    ], id="modal-historico", is_open=False, size="lg")
], fluid=True)


# --- Callback para o Modal de Histórico ---
@callback(
    Output("modal-historico", "is_open"), Output("modal-title", "children"), Output("modal-body", "children"),
    Input({'type': 'hist-button', 'index': ALL}, 'n_clicks'),
    State("modal-historico", "is_open"),
    prevent_initial_call=True
)
def show_team_history(n_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered or not any(n_clicks): return False, "", ""

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    team_name = eval(button_id)['index']
    
    jogos_time = dfs['ranking_equipes'][dfs['ranking_equipes']['EQUIPE'] == team_name].sort_values(by='DATA', ascending=False)
    
    historico_body = []
    for index, jogo in jogos_time.iterrows():
        resultado_class = "text-success fw-bold" if jogo['RESULTADO'] == 'VITÓRIA' else "text-danger fw-bold"
        historico_body.append(html.Tr([
            html.Td(jogo['ADVERSÁRIO']),
            html.Td(f"{jogo['PONTOS MARCADOS']} x {jogo['PONTOS SOFRIDOS']}", className=resultado_class)
        ]))

    modal_body = dbc.Table([html.Thead(html.Tr([html.Th("Adversário"), html.Th("Placar")])), html.Tbody(historico_body)], bordered=True, striped=True)
    
    return not is_open, f"Histórico de Jogos: {team_name}", modal_body