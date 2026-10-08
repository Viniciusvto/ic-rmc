from pathlib import Path
import pandas as pd

# Define a pasta raiz do projeto (onde está o analise.py)
BASE_DIR = Path(__file__).parent

# Mapeia as pastas de dados
DIR_BRUTOS = BASE_DIR / "brutos"
DIR_INTERMEDIARIOS = BASE_DIR / "intermediarios"
DIR_TRATADOS = BASE_DIR / "tratados"

# Exemplo de leitura e salvamento mantendo o fluxo da pipeline
def carregar_dados():
    # 1. Carregar arquivo bruto
    df_bruto = pd.read_csv(DIR_BRUTOS / "rpe_organizacoes_rmc.csv")
    
    # 2. Carregar arquivo tratado para análise final
    df_analise = pd.read_csv(DIR_TRATADOS / "rmc_inventarios_analise.csv")
    
    return df_bruto, df_analise

if __name__ == "__main__":
    df_bruto, df_analise = carregar_dados()
    print("--- Dados brutos ---")
    print(df_bruto.info())
    print("\n--- Dados da análise final ---")
    print(df_analise.info())
