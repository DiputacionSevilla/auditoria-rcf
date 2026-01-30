"""
Módulo para validaciones de la Orden HAP/1650/2015
Basado en el campo MOTIVO RECHAZO y el mapeo de validaciones.csv
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List
from config.settings import CONFIGURACION, VALIDACIONES_HAP

def cargar_mapeo_validaciones() -> Dict[str, str]:
    """Carga el mapeo desde validaciones.csv (PREFIX -> CODE)"""
    ruta_csv = os.path.join(os.getcwd(), 'validaciones.csv')
    if not os.path.exists(ruta_csv):
        return {}
    
    try:
        df_csv = pd.read_csv(ruta_csv, header=None, names=['prefix', 'code'])
        # Limpiar espacios y asegurar strings
        df_csv['prefix'] = df_csv['prefix'].astype(str).str.strip()
        df_csv['code'] = df_csv['code'].astype(str).str.strip()
        return dict(zip(df_csv['prefix'], df_csv['code']))
    except Exception:
        return {}

def aplicar_todas_validaciones(df_rcf: pd.DataFrame) -> Dict:
    """
    Identifica incumplimientos basándose en el campo MOTIVO RECHAZO
    y el archivo de mapeo validaciones.csv
    """
    fecha_validaciones = pd.to_datetime(CONFIGURACION['fecha_inicio_validaciones'])
    
    # Filtrar facturas del periodo que NO son papel (según guía V.3)
    # Nota: No filtramos por estado != RECHAZADA porque los incumplimientos suelen estar en facturas rechazadas
    df_periodo = df_rcf[
        (df_rcf['es_papel'] == False) &
        (df_rcf['fecha_emision'] > fecha_validaciones)
    ].copy()
    
    total_facturas = len(df_periodo)
    mapeo = cargar_mapeo_validaciones()
    
    # Inicializar estructura de resultados
    resultados = {
        'total_facturas_validadas': total_facturas,
        'total_incumplimientos': 0,
        'validaciones': {
            k: {
                'nombre': v,
                'num_incumplimientos': 0,
                'porcentaje': 0,
                'facturas': []
            } for k, v in VALIDACIONES_HAP.items()
        }
    }
    
    if total_facturas == 0 or not mapeo:
        return resultados

    # Procesar motivo_rechazo
    if 'motivo_rechazo' in df_periodo.columns:
        # Extraer prefijo (primeros 8 caracteres) para comparación
        df_periodo['prefix_rechazo'] = df_periodo['motivo_rechazo'].fillna('').astype(str).str[:8]
        
        # Identificar qué validación incumple usando el mapeo
        for prefix, code in mapeo.items():
            if code in resultados['validaciones']:
                # Facturas que tienen este prefijo exacto en los primeros 8 caracteres
                mask = df_periodo['prefix_rechazo'] == prefix
                df_incumplimiento = df_periodo[mask].copy()
                
                if len(df_incumplimiento) > 0:
                    # Acumular incumplimientos (una factura puede incumplir varias si tuviera varios mapeos, 
                    # pero aquí el prefijo es único por fila)
                    resultados['validaciones'][code]['num_incumplimientos'] += len(df_incumplimiento)
                    resultados['validaciones'][code]['porcentaje'] = (resultados['validaciones'][code]['num_incumplimientos'] / total_facturas * 100)
                    
                    # Añadir facturas al listado de este código
                    nuevas_facturas = df_incumplimiento[[
                        'ID_RCF', 'numero_factura', 'nif_emisor', 'fecha_emision', 'motivo_rechazo'
                    ]].to_dict('records')
                    resultados['validaciones'][code]['facturas'].extend(nuevas_facturas)
    
    # Totales globales
    total_incumplimientos = sum([v['num_incumplimientos'] for v in resultados['validaciones'].values()])
    resultados['total_incumplimientos'] = total_incumplimientos
    resultados['porcentaje_cumplimiento'] = ((total_facturas - total_incumplimientos) / total_facturas * 100) if total_facturas > 0 else 100
    
    return resultados

def analizar_rechazos(df_rcf: pd.DataFrame) -> Dict:
    """
    Analiza las causas de rechazo de facturas (General)
    Incluye tanto 'RECHAZADA' como 'BORRADA' ya que ambos pueden contener motivos de rechazo.
    """
    rechazadas = df_rcf[df_rcf['estado'].astype(str).str.upper().isin(['RECHAZADA', 'BORRADA'])].copy()
    
    # Agrupar por motivo de rechazo (si existe la columna)
    if 'motivo_rechazo' in rechazadas.columns:
        por_motivo = rechazadas.groupby('motivo_rechazo').size().sort_values(ascending=False)
    else:
        por_motivo = pd.Series(dtype=int)
    
    return {
        'total_rechazadas': len(rechazadas),
        'porcentaje': (len(rechazadas) / len(df_rcf) * 100) if len(df_rcf) > 0 else 0,
        'por_motivo': por_motivo.to_dict() if len(por_motivo) > 0 else {},
        'facturas': rechazadas[['ID_RCF', 'numero_factura', 'fecha_emision', 'importe_total']].to_dict('records') if len(rechazadas) > 0 else []
    }