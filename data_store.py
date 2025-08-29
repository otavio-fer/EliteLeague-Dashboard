# data_store.py (Atualizado)

import pandas as pd
import sys

def load_data():
    """
    Carrega todos os dados do arquivo Excel e os prepara para o dashboard.
    Retorna um dicionário de DataFrames.
    """
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
        
        # --- NOVOS CÁLCULOS AQUI ---
        # Médias de Jogadores
        dfs["analise_jogadores"]["ROUB_PG"] = (dfs["analise_jogadores"]["ROUB"] / dfs["analise_jogadores"]["JOGOS"]).round(2)
        dfs["analise_jogadores"]["TOCOS_PG"] = (dfs["analise_jogadores"]["TOCOS"] / dfs["analise_jogadores"]["JOGOS"]).round(2)
        dfs["analise_jogadores"]["EFI_PG"] = (dfs["analise_jogadores"]["EFICIÊNCIA"] / dfs["analise_jogadores"]["JOGOS"]).round(2)
        # Estimativa de Minutos por Jogo (MPG)
        total_plus_minus_liga = dfs["analise_jogadores"]["PLUS/MINUS"].abs().sum()
        dfs["analise_jogadores"]["MPG"] = (dfs["analise_jogadores"]["PLUS/MINUS"].abs() / total_plus_minus_liga) * 40 * len(dfs["analise_jogadores"]) # Estimativa baseada na proporção
        
        # Médias de Equipes
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

# Cria cópias separadas para diferentes lógicas de filtro
df_analise_completo = dfs["analise_jogadores"].copy()

min_jogos = 2
jogadores_elegiveis = dfs["analise_jogadores"][dfs["analise_jogadores"]['JOGOS'] >= min_jogos]['APELIDO']
df_analise_filtrado = dfs["analise_jogadores"][dfs["analise_jogadores"]['APELIDO'].isin(jogadores_elegiveis)].copy()
df_ranking_filtrado = dfs["ranking_jogadores"][dfs["ranking_jogadores"]['APELIDO'].isin(jogadores_elegiveis)].copy()