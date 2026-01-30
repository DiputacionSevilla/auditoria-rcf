import pandas as pd
import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(os.getcwd())

from utils.data_loader import normalizar_columnas, cargar_datos

def test_loading():
    datadir = 'datos'
    archivo_rcf = os.path.join(datadir, 'ftras-RCF.xlsx')
    archivo_face = os.path.join(datadir, '2-Ftras FACe.xlsx')
    archivo_anulaciones = os.path.join(datadir, '4-Anulacion de ftras.xlsx')
    archivo_estados = os.path.join(datadir, '5-Cambio de estado de facturas.xlsx')
    
    print("--- Cargando datos ---")
    # Mocking st.cache_data and st.error for the test
    import streamlit as st
    st.cache_data = lambda x: x
    st.error = print
    
    try:
        datos = cargar_datos(archivo_rcf, archivo_face, archivo_anulaciones, archivo_estados)
        df_rcf = datos['rcf']
        
        print(f"Columnas RCF después de normalizar: {list(df_rcf.columns)}")
        
        # Verificar detección de papel
        total = len(df_rcf)
        papel = df_rcf['es_papel'].sum()
        electronicas = total - papel
        
        print(f"\nTotal facturas: {total}")
        print(f"Facturas en papel detectoras: {papel}")
        print(f"Facturas electrónicas: {electronicas}")
        
        # Mostrar algunas facturas en papel para verificar
        print("\nEjemplos de ID_FACE marcados como papel (primeros 5):")
        print(df_rcf[df_rcf['es_papel']][['ID_RCF', 'ID_FACE']].head())
        
        # Verificar otras columnas críticas
        columnas_criticas = ['fecha_emision', 'importe_total', 'nif_emisor', 'razon_social', 'numero_factura']
        faltantes = [c for c in columnas_criticas if c not in df_rcf.columns]
        if faltantes:
            print(f"\nERROR: Faltan columnas críticas: {faltantes}")
        else:
            print("\nTodas las columnas críticas están presentes.")
            
    except Exception as e:
        print(f"Error durante el test: {e}")

if __name__ == "__main__":
    test_loading()
