# data_store.py (Corrigido com peso do V% ajustado para 3 no feminino)

import pandas as pd
import sys

def process_league_data(filename, league_type):
    try:
        sheet_names = {
            "analise_jogadores": "2K25 ELITE LEAGUE",
            "analise_equipes": "2K25 EQUIPES ELITE LEAGUE",
            "ranking_jogadores": "ESTATÍSTICAS ATLETAS",
            "ranking_equipes": "ESTATÍSTICAS EQUIPES"
        }
        dfs = {name: pd.read_excel(filename, sheet_name=sheet) for name, sheet in sheet_names.items()}

        for df_name in dfs:
            if 'EQUIPE' in dfs[df_name].columns:
                dfs[df_name]['EQUIPE'] = dfs[df_name]['EQUIPE'].str.strip()

        for df_name in ["analise_jogadores", "analise_equipes"]:
            dfs[df_name].rename(columns={'# RPG': 'RPG', '#APG': 'APG', 'PPJ': 'PPG'}, inplace=True)

        numeric_cols = [
            'JOGOS', 'PONTOS', 'PPG', 'FGM', 'FGA', '%FG', '2PM', '2PA', '%2P',
            '3PM', '3PA', '%3P', 'FTM', 'FTA', '%FT', 'REB O', 'REB D',
            'TOTAL REB', 'RPG', 'AST', 'APG', 'ERROS', 'ROUB', 'TOCOS',
            'FALTAS C', 'FALTAS S', 'PLUS/MINUS', 'EFICIÊNCIA'
        ]

        for df_name in dfs:
            for col in numeric_cols:
                if col in dfs[df_name].columns:
                    dfs[df_name][col] = pd.to_numeric(dfs[df_name][col], errors='coerce').fillna(0)

        for df in dfs.values():
            df.columns = df.columns.astype(str).str.strip()

        df_analise = dfs["analise_jogadores"]
        df_analise['APELIDO'] = df_analise['APELIDO'].replace({
            'MBAPPE LUS': 'MBAPPE', 'CIANETO LUS': 'CIANETO', 'SCOOBY LUS': 'SCOOBY'
        })

        if 'FGM' in df_analise.columns and 'FGA' in df_analise.columns:
            df_analise['%FG'] = df_analise.apply(lambda row: row['FGM'] / row['FGA'] if row['FGA'] > 0 else 0, axis=1)

        df_status_raw = dfs["ranking_jogadores"]
        if not df_status_raw.empty and 'APELIDO' in df_status_raw.columns and 'STATUS' in df_status_raw.columns:
            status_counts = df_status_raw.groupby(['APELIDO', 'STATUS']).size().unstack(fill_value=0)
            status_counts['FUNCAO'] = status_counts.apply(
                lambda row: 'Titular' if row.get('TITULAR', 0) >= row.get('RESERVA', 0) else 'Reserva',
                axis=1
            )
            player_function = status_counts[['FUNCAO']]
            dfs["analise_jogadores"] = dfs["analise_jogadores"].merge(player_function, on='APELIDO', how='left')
            dfs["analise_jogadores"]['FUNCAO'].fillna('Indefinido', inplace=True)

        stats_df = dfs["analise_jogadores"]
        stats_df["ROUB_PG"] = (stats_df["ROUB"] / stats_df["JOGOS"]).round(2) if 'JOGOS' in stats_df and stats_df['JOGOS'].sum() > 0 else 0
        stats_df["TOCOS_PG"] = (stats_df["TOCOS"] / stats_df["JOGOS"]).round(2) if 'JOGOS' in stats_df and stats_df['JOGOS'].sum() > 0 else 0
        stats_df["EFI_PG"] = (stats_df["EFICIÊNCIA"] / stats_df["JOGOS"]).round(2) if 'JOGOS' in stats_df and stats_df['JOGOS'].sum() > 0 else 0

        total_plus_minus_liga = stats_df["PLUS/MINUS"].abs().sum()
        stats_df["MPG"] = (stats_df["PLUS/MINUS"].abs() / total_plus_minus_liga) * 40 * len(stats_df) if total_plus_minus_liga > 0 else 0

        equipes_df = dfs["analise_equipes"]
        equipes_df["SPG"] = (equipes_df["ROUB"] / equipes_df["JOGOS"]).round(2) if 'JOGOS' in equipes_df and equipes_df['JOGOS'].sum() > 0 else 0
        equipes_df["BPG"] = (equipes_df["TOCOS"] / equipes_df["JOGOS"]).round(2) if 'JOGOS' in equipes_df and equipes_df['JOGOS'].sum() > 0 else 0

        equipes_df.drop(equipes_df[equipes_df['EQUIPE'] == 'TOTAIS'].index, inplace=True, errors='ignore')
        dfs["ranking_equipes"].drop(dfs["ranking_equipes"][dfs["ranking_equipes"]['EQUIPE'] == 'TOTAIS'].index, inplace=True, errors='ignore')

        df_analise_completo = dfs["analise_jogadores"].copy()
        min_jogos_geral = 2
        jogadores_elegiveis = df_analise_completo[df_analise_completo['JOGOS'] >= min_jogos_geral]['APELIDO']
        df_analise_filtrado = df_analise_completo[df_analise_completo['APELIDO'].isin(jogadores_elegiveis)].copy()
        df_ranking_filtrado = dfs["ranking_jogadores"][dfs["ranking_jogadores"]['APELIDO'].isin(jogadores_elegiveis)].copy()

        df_premios = df_analise_completo.copy()

        if league_type == 'M':
            indices_serasa = df_premios[(df_premios['APELIDO'] == 'SERASA') & (df_premios['EQUIPE'] == 'MED USP RP')].index
            df_premios.drop(indices_serasa, inplace=True)
            outros_jogadores = ['MBAPPE', 'FIBA', 'CIANETO', 'SCOOBY']
            indices_outros = df_premios[(df_premios['APELIDO'].isin(outros_jogadores)) & (df_premios['EQUIPE'] == 'LUS USP RP')].index
            df_premios.drop(indices_outros, inplace=True)

        df_vitorias = dfs["ranking_equipes"][dfs["ranking_equipes"]["RESULTADO"] == 'VITÓRIA'].groupby('EQUIPE').size()
        df_jogos = dfs["ranking_equipes"].groupby('EQUIPE').size()
        team_win_pct = (df_vitorias / df_jogos).fillna(0)

        df_premios['V%'] = df_premios['EQUIPE'].map(team_win_pct).fillna(0)

        # <<<<<<<<<<<<<<< ALTERAÇÃO DA FÓRMULA AQUI >>>>>>>>>>>>>>>
        win_pct_weight = 3 if league_type == 'W' else 20

        df_premios['MVP_SCORE'] = (
            df_premios['EFI_PG']*1.0 +
            df_premios['PPG']*0.8 +
            df_premios['APG']*0.7 +
            df_premios['RPG']*0.4 +
            df_premios['V%'] * win_pct_weight
        )

        df_premios['DEF_SCORE'] = (df_premios['ROUB_PG']*1.5 + df_premios['TOCOS_PG']*1.5 + df_premios['RPG']*1.0)

        mvp_max, mvp_min = df_premios['MVP_SCORE'].max(), df_premios['MVP_SCORE'].min()
        def_max, def_min = df_premios['DEF_SCORE'].max(), df_premios['DEF_SCORE'].min()
        df_premios['MVP_NORM'] = (df_premios['MVP_SCORE'] - mvp_min) / (mvp_max - mvp_min) if (mvp_max - mvp_min) > 0 else 0
        df_premios['DEF_NORM'] = (df_premios['DEF_SCORE'] - def_min) / (def_max - def_min) if (def_max - def_min) > 0 else 0
        df_premios['ALL_TEAM_SCORE'] = df_premios['MVP_NORM'] + df_premios['DEF_NORM']

        min_jogos_premios = 2
        jogadores_elegiveis_premios = df_premios[df_premios['JOGOS'] >= min_jogos_premios]['APELIDO']
        df_analise_premios_filtrado = df_premios[df_premios['APELIDO'].isin(jogadores_elegiveis_premios)].copy()

        return {
            "dfs": dfs, "df_analise_completo": df_analise_completo, "df_analise_filtrado": df_analise_filtrado,
            "df_ranking_filtrado": df_ranking_filtrado, "df_analise_premios_filtrado": df_analise_premios_filtrado
        }

    except Exception as e:
        print(f"ERRO AO PROCESSAR O ARQUIVO {filename}: {e}", file=sys.stderr)
        return {
            "dfs": {}, "df_analise_completo": pd.DataFrame(), "df_analise_filtrado": pd.DataFrame(),
            "df_ranking_filtrado": pd.DataFrame(), "df_analise_premios_filtrado": pd.DataFrame()
        }

data = {
    'M': process_league_data('ESTATÍSTICAS.xlsx', 'M'),
    'W': process_league_data('W ELITE LEAGUE ESTATÍSTICAS.xlsx', 'W')
}

logo_mapping = {
    "DIREITO USP RP": "DIREITO USP RP.png", "EDUCA USP RP": "EDUCA USP RP.png", "FILÔ USP RP": "FILÔ USP RP.png",
    "LUS USP RP": "LUS USP RP.png", "MED BARÃO": "MED BARÃO.png", "MED UNAERP": "MED UNAERP.PNG",
    "MED USP RP": "MED USP RP.png", "ODONTO USP RP": "ODONTO USP RP.png",
}
cores_times = {
    "DIREITO USP RP": "#FFD700", "MED USP RP": "#87CEEB", "ODONTO USP RP": "#880e4f", "FILÔ USP RP": "#424242",
    "LUS USP RP": "#00FFFF", "MED UNAERP": "#00008B", "MED BARÃO": "#006400",
}
cor_padrao = "#66bb6a"