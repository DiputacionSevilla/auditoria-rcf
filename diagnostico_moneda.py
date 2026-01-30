import pandas as pd
import sys
import os

# Añadir ruta raíz
ruta_raiz = os.getcwd()
sys.path.append(ruta_raiz)

from utils.data_loader import cargar_datos
from config.settings import CONFIGURACION

def investigar_moneda():
    print("--- Análisis de Columna 'moneda' ---")
    
    # Intentar cargar datos (esto requiere que los archivos existan en la ruta esperada o que usemos los de session_state, 
    # pero como es un script independiente, intentaremos buscar archivos excel en la carpeta actual)
    excels = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    print(f"Excels encontrados: {excels}")
    
    # En lugar de cargar todo, vamos a intentar ver qué tiene el RCF si podemos adivinar cuál es
    rcf_candidates = [f for f in excels if 'RCF' in f.upper()]
    if not rcf_candidates:
        print("No se encontró archivo RCF para diagnóstico automático.")
        return

    archivo_rcf = rcf_candidates[0]
    print(f"Analizando: {archivo_rcf}")
    
    df = pd.read_excel(archivo_rcf)
    print(f"Columnas originales: {df.columns.tolist()}")
    
    # Buscar columna moneda
    posibles = ['moneda', 'Moneda', 'divisa', 'UNIDAD MONETARIA', 'MONEDA', 'UNIDAD MONETARIA']
    col_moneda = [c for c in df.columns if c.strip() in posibles]
    
    if col_moneda:
        real_col = col_moneda[0]
        print(f"Columna detectada: {real_col}")
        print("Valores únicos:")
        print(df[real_col].unique())
    else:
        print("No se encontró ninguna columna de moneda similar a los alias.")

if __name__ == "__main__":
    investigar_moneda()
