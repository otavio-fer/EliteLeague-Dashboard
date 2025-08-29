# pages/4_premios.py (Corrigido)

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from data_store import df_analise_filtrado, logo_mapping

dash.register_page(__name__, name='Prêmios')

# <<<<<<<<<<<<<<< CORREÇÃO AQUI: FUNÇÃO ATUALIZADA >>>>>>>>>>>>>>>
def criar_visual_ranking(df, stat_col, name_col, title, unit="", is_total=True, team_col=None):
    if is_total:
        agg_dict = {stat_col: 'sum'}
        if team_col: agg_dict[team_col] = 'first'
        df_processed = df.groupby(name_col, as_index=False).agg(agg_dict)
    else:
        df_processed = df
    
    top_10 = df_processed.nlargest(10, stat_col).reset_index(drop=True)

    podium_cards, table = [], None
    medals = ["🥇", "🥈", "🥉"]
    
    if len(top_10) > 0:
        cols = {}
        for i in range(min(3, len(top_10))):
            player_or_team = top_10.iloc[i]
            team_name = player_or_team.get(team_col, player_or_team.get(name_col))
            logo_filename = logo_mapping.get(team_name, "default.png")
            logo_src = f"/assets/{logo_filename}"
            
            card_style = {"height": "100%"}
            card_class = "mb-3"
            if i == 0:
                card_style.update({'transform': 'translateY(-25px)', 'zIndex': 2, 'boxShadow': '0 0 25px rgba(255, 215, 0, 0.7)'})
                card_class += " border-warning border-3"
            
            cols[str(i+1)] = dbc.Col(dbc.Card([dbc.CardBody([
                    html.H4(f"{medals[i]} {i+1}º Lugar", className="card-title text-center"),
                    html.Img(src=logo_src, height="80px", className="mx-auto d-block my-2", alt=team_name),
                    html.H5(player_or_team[name_col], className="text-center fw-bold"),
                    html.P(f"{player_or_team[stat_col]:.1f} {unit}", className="text-center fs-4")
                ])], style=card_style, className=card_class), lg=4, md=6, sm=12)
        
        podium_cards.extend([cols.get("2"), cols.get("1"), cols.get("3")])

    if len(top_10) > 3:
        table_rows = [html.Tr([html.Th(f"{i+1}º"), html.Td(top_10.iloc[i][name_col]), html.Td(f"{top_10.iloc[i][stat_col]:.1f}")]) for i in range(3, len(top_10))]
        table_header_name = "Atleta" if team_col else "Equipe"
        table = dbc.Row(dbc.Col(dbc.Table([html.Thead(html.Tr([html.Th("#"), html.Th(table_header_name), html.Th(unit)])), html.Tbody(table_rows)], color="dark", striped=True, bordered=True, hover=True, size="sm"), width=12, lg={"size": 8, "offset": 2}), className="mt-4")

    return [html.H4(title, className="text-center mt-5 mb-4"), dbc.Row([c for c in podium_cards if c], justify="center"), table]

# --- NOVA FUNÇÃO: Criar Visualização do All-Team na Quadra ---
def criar_quadra_all_team(df_team, title):
    fig = go.Figure()

    # Desenha a quadra
    fig.add_shape(type="rect", x0=-250, y0=-47.5, x1=250, y1=422.5, line=dict(color="white", width=2))
    fig.add_shape(type="circle", x0=-60, y0=130, x1=60, y1=250, line=dict(color="white", width=2))
    fig.add_shape(type="path", path="M -220,-47.5 L -220,142.5 C -220,280 220,280 220,142.5 L 220,-47.5", line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line=dict(color="white", width=2))
    fig.add_shape(type="rect", x0=-30, y0=-7.5, x1=30, y1=-47.5, line=dict(color="white", width=2), fillcolor="gray")

    # Define as posições dos 5 jogadores
    posicoes = [(-180, 50), (180, 50), (-100, 250), (100, 250), (0, 350)]
    
    for i, (index, player) in enumerate(df_team.iterrows()):
        logo_filename = logo_mapping.get(player['EQUIPE'], "default.png")
        
        # Adiciona a logo
        fig.add_layout_image(
            dict(source=f"/assets/{logo_filename}", xref="x", yref="y", x=posicoes[i][0], y=posicoes[i][1],
                 sizex=60, sizey=60, xanchor="center", yanchor="middle", sizing="contain")
        )
        # Adiciona o nome
        fig.add_annotation(
            x=posicoes[i][0], y=posicoes[i][1] - 50, # Posição abaixo da logo
            text=f"<b>{player['APELIDO']}</b>", showarrow=False, font=dict(color="white", size=14)
        )

    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-270, 270]),
        yaxis=dict(showgrid=False, zeroline=False, visible=False, range=[-100, 450]),
        paper_bgcolor="#222222", plot_bgcolor="#222222",
        height=600
    )
    return dbc.Card([dbc.CardBody(dcc.Graph(figure=fig))])

# --- Layout da Página de Prêmios ---
opcoes_premios = [
    {'label': 'Corrida para MVP', 'value': 'mvp'},
    {'label': 'Defensor do Ano', 'value': 'dpoy'},
    {'label': '1º Time Ideal', 'value': 'all_team_1'},
    {'label': '2º Time Ideal', 'value': 'all_team_2'},
]

layout = dbc.Container([
    dbc.Row(dbc.Col(html.H3("Prêmios da Temporada", className="text-center my-4"))),
    dbc.Row(dbc.Col(dcc.Dropdown(id='seletor-premio', options=opcoes_premios, value='mvp', clearable=False), width=12, lg=6, className="mx-auto my-4")),
    html.Div(id='ranking-premio-display')
], fluid=True)

# --- Callback dos Rankings de Prêmios ---
@callback(
    Output('ranking-premio-display', 'children'),
    Input('seletor-premio', 'value')
)
def update_award_ranking_display(selected_award):
    df_sorted = df_analise_filtrado.sort_values(by='ALL_TEAM_SCORE', ascending=False)

    if selected_award == 'mvp':
        return criar_visual_ranking(df_analise_filtrado, 'MVP_SCORE', "APELIDO", "Corrida para MVP", "MVP Score", is_total=False, team_col="EQUIPE")
    elif selected_award == 'dpoy':
        return criar_visual_ranking(df_analise_filtrado, 'DEF_SCORE', "APELIDO", "Prêmio Defensor do Ano", "Def Score", is_total=False, team_col="EQUIPE")
    elif selected_award == 'all_team_1':
        primeiro_time = df_sorted.head(5)
        return criar_quadra_all_team(primeiro_time, "1º Time Ideal da Liga")
    elif selected_award == 'all_team_2':
        segundo_time = df_sorted.iloc[5:10]
        return criar_quadra_all_team(segundo_time, "2º Time Ideal da Liga")
    
    return "Selecione um prêmio para ver o ranking."