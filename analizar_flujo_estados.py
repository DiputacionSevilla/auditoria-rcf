"""
Genera un Excel de análisis del Flujo de Estados: para cada factura calcula su
secuencia completa de estados (aplicando la regla de retroceso usada en
pages/5_Tramitacion.py) y totaliza cuántas facturas comparten cada secuencia.

Calcula el resultado de dos formas para poder comparar:
  - "Producción": usando utils.data_loader.cargar_datos(), igual que la app
    real (filtra 'estados' al ejercicio auditado, 2025).
  - "Completo": usando el archivo de estados sin el filtro de ejercicio.

Uso:
    python analizar_flujo_estados.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent))

from config.settings import ESTADOS_FACTURAS
from utils.data_loader import cargar_datos

DATOS_DIR = Path("datos")
ARCHIVO_RCF = DATOS_DIR / "1-ftras-RCF.xlsx"
ARCHIVO_FACE = DATOS_DIR / "2-Ftras FACe.xlsx"
ARCHIVO_ANULACIONES = DATOS_DIR / "3-Anulacion de ftras.xlsx"
ARCHIVO_ESTADOS = DATOS_DIR / "4-Cambio de estado de facturas.xlsx"
ARCHIVO_SALIDA = Path("analisis_flujo_estados.xlsx")


def _dedupe_consecutivos(lista):
    resultado = []
    for estado in lista:
        if not resultado or resultado[-1] != estado:
            resultado.append(estado)
    return resultado


def calcular_secuencias(df_estados: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df_estados.copy()
    df.columns = df.columns.str.strip()
    if 'insertado_h' in df.columns and 'insertado' not in df.columns:
        df = df.rename(columns={'insertado_h': 'insertado'})
    df['insertado'] = pd.to_datetime(df['insertado'], errors='coerce')

    df['nombre_estado'] = (
        df['codigo'].astype(str).str.split('.').str[0].map(ESTADOS_FACTURAS).fillna('Desconocido')
    )
    df = df.sort_values(['registro', 'insertado'])

    df['codigo_num'] = pd.to_numeric(df['codigo'].astype(str).str.split('.').str[0], errors='coerce')
    df['cummax_codigo'] = df.groupby('registro')['codigo_num'].cummax()
    df['max_previo'] = df.groupby('registro')['cummax_codigo'].shift(1)

    # Fecha en la que se alcanzó ese máximo previo (para medir la cercanía temporal)
    df['tiempo_max_codigo'] = df['insertado'].where(df['codigo_num'] == df['cummax_codigo'])
    df['tiempo_max_codigo'] = df.groupby('registro')['tiempo_max_codigo'].ffill()
    df['tiempo_max_previo'] = df.groupby('registro')['tiempo_max_codigo'].shift(1)
    diff_segundos = (df['insertado'] - df['tiempo_max_previo']).dt.total_seconds()

    es_retroceso_bruto = df['codigo_num'] < df['max_previo']

    # 2100 (Recibida en destino) y 1400 (Verificada en RCF) se generan de forma
    # prácticamente simultánea: si la diferencia es de 10 segundos o menos se
    # ignora como retroceso real (es un artefacto de orden de inserción)
    es_caso_simultaneo_2100_1400 = (
        (df['max_previo'] == 2100) &
        (df['codigo_num'] == 1400) &
        (diff_segundos <= 10)
    ).fillna(False)

    df['es_retroceso'] = es_retroceso_bruto & ~es_caso_simultaneo_2100_1400

    # Secuencia "limpia": se descartan los retrocesos y se colapsan repeticiones consecutivas
    df_limpio = df[~df['es_retroceso']]
    df_seq = df_limpio.groupby('registro')['nombre_estado'].apply(list).reset_index()
    df_seq['nombre_estado'] = df_seq['nombre_estado'].apply(_dedupe_consecutivos)
    df_seq['secuencia'] = df_seq['nombre_estado'].apply(lambda x: ' → '.join(x))

    df_detalle = df_seq[['registro', 'secuencia']].rename(
        columns={'registro': 'Registro FACe', 'secuencia': 'Secuencia de Estados'}
    )

    conteo = df_seq['secuencia'].value_counts().reset_index()
    conteo.columns = ['Secuencia de Estados', 'Cantidad de Facturas']
    conteo['Porcentaje'] = (conteo['Cantidad de Facturas'] / len(df_seq) * 100).round(2)
    conteo = conteo.sort_values('Cantidad de Facturas', ascending=False).reset_index(drop=True)

    return df_detalle, conteo


def main():
    for archivo in (ARCHIVO_RCF, ARCHIVO_FACE, ARCHIVO_ANULACIONES, ARCHIVO_ESTADOS):
        if not archivo.exists():
            raise FileNotFoundError(f"No se encuentra el archivo de entrada: {archivo}")

    # --- Versión "Producción": mismo pipeline que usa la app (filtra por ejercicio 2025) ---
    datos = cargar_datos(ARCHIVO_RCF, ARCHIVO_FACE, ARCHIVO_ANULACIONES, ARCHIVO_ESTADOS)
    df_estados_prod = datos['estados']
    df_detalle_prod, df_resumen_prod = calcular_secuencias(df_estados_prod)

    # --- Versión "Completo": archivo de estados sin filtrar por ejercicio ---
    df_estados_completo = pd.read_excel(ARCHIVO_ESTADOS)
    df_detalle_completo, df_resumen_completo = calcular_secuencias(df_estados_completo)

    with pd.ExcelWriter(ARCHIVO_SALIDA, engine='openpyxl') as writer:
        df_resumen_prod.to_excel(writer, sheet_name='Resumen_Produccion', index=False)
        df_detalle_prod.to_excel(writer, sheet_name='Detalle_Produccion', index=False)
        df_resumen_completo.to_excel(writer, sheet_name='Resumen_Completo', index=False)
        df_detalle_completo.to_excel(writer, sheet_name='Detalle_Completo', index=False)

    print("=== Producción (igual que la app: estados filtrados al ejercicio 2025) ===")
    print(f"Facturas analizadas: {len(df_detalle_prod):,}")
    print(f"Secuencias distintas: {len(df_resumen_prod):,}")
    print()
    print("=== Completo (archivo de estados sin filtrar por ejercicio) ===")
    print(f"Facturas analizadas: {len(df_detalle_completo):,}")
    print(f"Secuencias distintas: {len(df_resumen_completo):,}")
    print()
    n_filas_excluidas = len(df_estados_completo) - len(df_estados_prod)
    print(f"Filas de 'estados' excluidas por el filtro de ejercicio: {n_filas_excluidas:,}")
    print(f"Excel generado: {ARCHIVO_SALIDA.resolve()}")


if __name__ == "__main__":
    main()
