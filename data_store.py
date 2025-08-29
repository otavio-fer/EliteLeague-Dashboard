# data_store.py (Corrigido)

import pandas as pd
import sys

def load_data():
    try:
        sheet_names = {
            "analise_jogadores": "2K25 ELITE LEAGUE",
            "analise_equipes": "2K25 EQUIPES ELITE LEAGUE",
            "ranking_jogadores": "ESTATÍSTICAS ATLETAS",
            "ranking_equipes": "ESTATÍSTICAS EQUIPES"
        }
        dfs = {name: pd.read_excel("ESTATÍSTICAS.xlsx", sheet_name=sheet) for name, sheet in sheet_names.items()}

        for df in dfs.values():
            df.columns = df.columns.astype(str).str.strip()
            if "EQUIPE" in df.columns:
                df["EQUIPE"] = df["EQUIPE"].str.strip()
        
        dfs["analise_jogadores"].rename(columns={'# RPG': 'RPG', '#APG': 'APG'}, inplace=True)
        dfs["analise_equipes"].rename(columns={'# RPG': 'RPG', '#APG': 'APG'}, inplace=True)
        
        # Cálculos de médias de jogadores
        dfs["analise_jogadores"]["ROUB_PG"] = (dfs["analise_jogadores"]["ROUB"] / dfs["analise_jogadores"]["JOGOS"]).round(2)
        dfs["analise_jogadores"]["TOCOS_PG"] = (dfs["analise_jogadores"]["TOCOS"] / dfs["analise_jogadores"]["JOGOS"]).round(2)
        dfs["analise_jogadores"]["EFI_PG"] = (dfs["analise_jogadores"]["EFICIÊNCIA"] / dfs["analise_jogadores"]["JOGOS"]).round(2)
        
        # <<<<<<<<<<<<<<< CORREÇÃO AQUI: ADICIONADO CÁLCULO DE MPG >>>>>>>>>>>>>>>
        # Estimativa de Minutos por Jogo (MPG)
        total_plus_minus_liga = dfs["analise_jogadores"]["PLUS/MINUS"].abs().sum()
        if total_plus_minus_liga > 0:
             dfs["analise_jogadores"]["MPG"] = (dfs["analise_jogadores"]["PLUS/MINUS"].abs() / total_plus_minus_liga) * 40 * len(dfs["analise_jogadores"])
        else:
             dfs["analise_jogadores"]["MPG"] = 0


        # Cálculos de médias de equipes
        dfs["analise_equipes"]["SPG"] = (dfs["analise_equipes"]["ROUB"] / dfs["analise_equipes"]["JOGOS"]).round(2)
        dfs["analise_equipes"]["BPG"] = (dfs["analise_equipes"]["TOCOS"] / dfs["analise_equipes"]["JOGOS"]).round(2)

        dfs["analise_equipes"] = dfs["analise_equipes"][dfs["analise_equipes"]["EQUIPE"] != 'TOTAIS'].copy()
        dfs["ranking_equipes"] = dfs["ranking_equipes"][dfs["ranking_equipes"]["EQUIPE"] != 'TOTAIS'].copy()

        return dfs

    except Exception as e:
        print(f"ERRO AO LER O ARQUIVO EXCEL: {e}", file=sys.stderr)
        sys.exit()

# Carrega os dados uma vez quando o aplicativo inicia
dfs = load_data()

# Dicionários e Mapeamentos
logo_mapping = {
    "DIREITO USP RP": "DIREITO USP RP.png", "EDUCA USP RP": "EDUCA USP RP.png",
    "FILÔ USP RP": "FILÔ USP RP.png", "LUS USP RP": "LUS USP RP.png",
    "MED BARÃO": "MED BARÃO.png", "MED UNAERP": "MED UNAERP.PNG",
    "MED USP RP": "MED USP RP.png", "ODONTO USP RP": "ODONTO USP RP.png",
}
cores_times = {
    "DIREITO USP RP": "#FFD700", "MED USP RP": "#87CEEB", "ODONTO USP RP": "#880e4f",
    "FILÔ USP RP": "#424242", "LUS USP RP": "#00FFFF", "MED UNAERP": "#00008B", "MED BARÃO": "#006400",
}
cor_padrao = "#66bb6a"

# --- LÓGICA DE CÁLCULO PARA PRÊMIOS ---
df_vitorias = dfs["ranking_equipes"][dfs["ranking_equipes"]["RESULTADO"] == 'VITÓRIA'].groupby('EQUIPE').size()
df_jogos = dfs["ranking_equipes"].groupby('EQUIPE').size()
team_win_pct = (df_vitorias / df_jogos).fillna(0)

df_jogadores_com_vitorias = dfs["analise_jogadores"].copy()
df_jogadores_com_vitorias['V%'] = df_jogadores_com_vitorias['EQUIPE'].map(team_win_pct).fillna(0)

df_jogadores_com_vitorias['MVP_SCORE'] = (
    df_jogadores_com_vitorias['EFI_PG'] * 1.0 + df_jogadores_com_vitorias['PPG'] * 0.8 +
    df_jogadores_com_vitorias['APG'] * 0.7 + df_jogadores_com_vitorias['RPG'] * 0.4 +
    df_jogadores_com_vitorias['V%'] * 20
)
df_jogadores_com_vitorias['DEF_SCORE'] = (
    df_jogadores_com_vitorias['ROUB_PG'] * 1.5 + df_jogadores_com_vitorias['TOCOS_PG'] * 1.5 +
    df_jogadores_com_vitorias['RPG'] * 1.0
)

# --- NOVO: Cálculo do All-Team Score ---
# Normaliza os scores para que tenham a mesma escala (0 a 1) antes de somar
mvp_max = df_jogadores_com_vitorias['MVP_SCORE'].max()
mvp_min = df_jogadores_com_vitorias['MVP_SCORE'].min()
def_max = df_jogadores_com_vitorias['DEF_SCORE'].max()
def_min = df_jogadores_com_vitorias['DEF_SCORE'].min()

df_jogadores_com_vitorias['MVP_NORM'] = (df_jogadores_com_vitorias['MVP_SCORE'] - mvp_min) / (mvp_max - mvp_min)
df_jogadores_com_vitorias['DEF_NORM'] = (df_jogadores_com_vitorias['DEF_SCORE'] - def_min) / (def_max - def_min)

# O score final é a soma dos scores normalizados
df_jogadores_com_vitorias['ALL_TEAM_SCORE'] = df_jogadores_com_vitorias['MVP_NORM'] + df_jogadores_com_vitorias['DEF_NORM']


# --- Criação dos DataFrames Finais ---
df_analise_completo = df_jogadores_com_vitorias.copy()

min_jogos = 2
jogadores_elegiveis = df_analise_completo[df_analise_completo['JOGOS'] >= min_jogos]['APELIDO']
df_analise_filtrado = df_analise_completo[df_analise_completo['APELIDO'].isin(jogadores_elegiveis)].copy()
df_ranking_filtrado = dfs["ranking_jogadores"][dfs["ranking_jogadores"]['APELIDO'].isin(jogadores_elegiveis)].copy()