import pandas as pd
import toml
from pathlib import Path
import sys
import os

# Añadir el directorio raíz al path para importar el data_loader
sys.path.append(os.getcwd())

from utils.data_loader import cargar_datos

def diagnostico():
    print("--- DIAGNÓSTICO DE CÁLCULO DE RETENIDAS ---")
    
    # Cargar configuración
    try:
        config_toml = toml.load(".streamlit/config.toml")
        ejercicio = config_toml.get('auditoria', {}).get('ejercicio_auditado', 2025)
        print(f"Ejercicio configurado: {ejercicio}")
    except Exception as e:
        print(f"Error al cargar config: {e}")
        ejercicio = 2025

    # Rutas de archivos
    datos_dir = Path("datos")
    archivos = {
        'rcf': datos_dir / "ftras-RCF.xlsx",
        'face': datos_dir / "2-Ftras FACe.xlsx",
        'anulaciones': datos_dir / "4-Anulacion de ftras.xlsx",
        'estados': datos_dir / "5-Cambio de estado de facturas.xlsx"
    }

    df_rcf = pd.read_excel(archivos['rcf'])
    df_rcf.columns = df_rcf.columns.str.strip()
    from utils.data_loader import normalizar_columnas, convertir_fechas
    df_rcf = normalizar_columnas(df_rcf, 'rcf')
    df_rcf = convertir_fechas(df_rcf, ['fecha_emision', 'fecha_anotacion_rcf'])
    
    # Contar BORRADAS antes de filtrar por año
    if 'estado' in df_rcf.columns:
        total_borradas_archivo = len(df_rcf[df_rcf['estado'].astype(str).str.upper() == 'BORRADA'])
        print(f"TOTAL facturas BORRADA en el archivo (sin filtrar): {total_borradas_archivo}")
        
    # Cargar datos usando la lógica actual (que aplica el filtro)
    print("\nCargando datos con filtro de año...")
    datos = cargar_datos(archivos['rcf'], archivos['face'], archivos['anulaciones'], archivos['estados'])
    
    df_rcf_filtrado = datos['rcf']
    df_face = datos['face']
    
    # Simular lógica de Dashboard
    df_rcf_analisis = df_rcf_filtrado.copy()
    if 'estado' in df_rcf_analisis.columns:
        borradas_filtradas = df_rcf_analisis[df_rcf_analisis['estado'].astype(str).str.upper() == 'BORRADA']
        print(f"Facturas BORRADA en RCF (año {ejercicio}): {len(borradas_filtradas)}")
        df_rcf_analisis = df_rcf_analisis[df_rcf_analisis['estado'].astype(str).str.upper() != 'BORRADA'].copy()
    
    print(f"\nResultados del RCF (Tras excluir BORRADAS):")
    print(f"Total facturas RCF para análisis: {len(df_rcf_analisis)}")
    facturas_elect_rcf = len(df_rcf_analisis[df_rcf_analisis['es_papel'] == False])
    print(f"Facturas electrónicas en RCF (No papel, No borrada): {facturas_elect_rcf}")
    
    print(f"\nResultados de FACe:")
    print(f"Total facturas FACe: {len(df_face)}")
    
    # Cálculo Dashboard
    retenidas_dashboard = len(df_face) - facturas_elect_rcf
    print(f"\nCálculo Dashboard de retenidas: {len(df_face)} - {facturas_elect_rcf} = {retenidas_dashboard}")
    
    # Cálculo real por registro
    if 'registro' in df_face.columns and 'ID_FACE' in df_rcf.columns:
        # Aseguramos que ids_rcf no incluya nulos ni vacíos
        ids_rcf = set(df_rcf[df_rcf['ID_FACE'].apply(lambda x: str(x).strip().lower() not in ['', 'nan', 'none'])]['ID_FACE'].astype(str))
        print(f"IDs de FACe encontrados en RCF (total, incluyendo otros años): {len(ids_rcf)}")
        
        df_retenidas_real = df_face[~df_face['registro'].astype(str).isin(ids_rcf)].copy()
        print(f"Cálculo REAL de retenidas (FACe no en RCF): {len(df_retenidas_real)}")
        
        if 'fecha_registro' in df_face.columns:
            face_2025 = df_face[df_face['fecha_registro'].dt.year == 2025]
            retenidas_2025 = face_2025[~face_2025['registro'].astype(str).isin(ids_rcf)]
            print(f"Cálculo REAL de retenidas de 2025: {len(retenidas_2025)}")

if __name__ == "__main__":
    diagnostico()
