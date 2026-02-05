import pandas as pd
from pathlib import Path

def raw_diagnostico():
    rcf_path = Path("datos/ftras-RCF.xlsx")
    print(f"Analizando archivo RAW: {rcf_path}")
    
    df = pd.read_excel(rcf_path)
    df.columns = df.columns.str.strip()
    
    # Intentar encontrar columna de estado
    col_estado = None
    for col in df.columns:
        if str(col).upper() in ['ESTADO', 'ESTADO FACTURA', 'STATUS']:
            col_estado = col
            break
            
    if not col_estado:
        print(f"No se encontró columna de estado. Columnas: {df.columns.tolist()}")
        return

    borradas_mask = df[col_estado].astype(str).str.upper() == 'BORRADA'
    pdte_aceptar_mask = df[col_estado].astype(str).str.upper() == 'PDTE DE ACEPTAR'
    
    # Analizar fechas nulas por estado
    print("\n--- ANÁLISIS DE FECHAS NULAS POR ESTADO ---")
    nulas = df[df['FECHA REGISTRO'].isna()]
    print(f"Total registros con fecha nula: {len(nulas)}")
    print("Distribución de estados en registros con fecha nula:")
    print(nulas[col_estado].value_counts())

    # Comprobar el número mágico 12.953
    # Vivas = Todo el archivo - Borradas
    df_vivas = df[~borradas_mask]
    print(f"\nTotal facturas VIVAS (No Borradas): {len(df_vivas)}")
    
    # Vivas filtradas por ejercicio (2024 y 2025)
    ej_permitidos = [2024, 2025]
    df_vivas_ej = df_vivas[df_vivas['EJERCICIO'].isin(ej_permitidos)]
    print(f"Total VIVAS en Ejercicio 2024/2025: {len(df_vivas_ej)}")
    
    # Ver si hay alguna ENTIDAD específica o algo que reste los últimos 4
    # (12957 - 12953 = 4)
    # Quizás son los 4 registros que tienen EJERCICIO = NaN en mi diagnóstico anterior?
    nan_ejercicio = df_vivas[df_vivas['EJERCICIO'].isna()]
    print(f"Vivas con EJERCICIO nulo: {len(nan_ejercicio)}")
    
    final_count = len(df_vivas_ej)
    print(f"\nCandidato final para 'Vivas': {final_count}")

    # Comprobar FACe vs RCF sin filtros de año
    col_rcf_face = None
    for col in df.columns:
        if str(col).upper() in ['ID_FACE', 'ID FACE', 'Nº REGISTRO FACE']:
            col_rcf_face = col
            break
            
    if col_rcf_face:
        ids_rcf = set(df[df[col_rcf_face].notna()][col_rcf_face].astype(str))
        print(f"\nIDs de FACe en RCF (Total): {len(ids_rcf)}")
        
        # Leer FACe
        face_df = pd.read_excel("datos/2-Ftras FACe.xlsx")
        face_df.columns = face_df.columns.str.strip()
        col_face_reg = 'registro' if 'registro' in face_df.columns else face_df.columns[0]
        ids_face = set(face_df[col_face_reg].astype(str))
        print(f"IDs en archivo FACe: {len(ids_face)}")
        
        retenidas = ids_face - ids_rcf
        print(f"Retenidas (Cálculo total): {len(retenidas)}")

if __name__ == "__main__":
    raw_diagnostico()
