"""
Cálculo automático de análisis para el generador de informes.

Estas funciones permiten precalcular los análisis de cada sección cuando el usuario
llega a la página de generación de informes sin haber visitado previamente todas las
páginas de análisis. Se basan en la misma lógica de las páginas correspondientes.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict

from config.settings import CONFIGURACION, CONFIGURACION_TRANSICION_2025
from utils.data_loader import (
    obtener_facturas_papel_sospechosas,
    clasificar_procedimiento,
    calcular_indicadores_procedimiento_anterior,
    calcular_indicadores_procedimiento_nuevo,
    calcular_indicadores_tramitacion_posterior,
    identificar_facturas_retenidas,
)
from utils.validaciones import aplicar_todas_validaciones, analizar_rechazos


def _df_rcf_activo(datos: Dict) -> pd.DataFrame:
    """Devuelve el RCF excluyendo facturas BORRADA."""
    df_rcf = datos['rcf'].copy()
    if 'estado' in df_rcf.columns:
        df_rcf = df_rcf[df_rcf['estado'].astype(str).str.upper() != 'BORRADA'].copy()
    return df_rcf


def calcular_facturas_papel(df_rcf: pd.DataFrame) -> Dict:
    """Calcula el análisis de facturas en papel (Sección V.1)."""
    facturas_papel = df_rcf[df_rcf['es_papel'] == True].copy() if 'es_papel' in df_rcf.columns else pd.DataFrame()
    facturas_sospechosas = obtener_facturas_papel_sospechosas(df_rcf)
    tabla_sospechosas = pd.DataFrame()

    if len(facturas_sospechosas) > 0:
        cols_disp = [c for c in [
            'entidad', 'id_fra_rcf', 'numero_factura', 'fecha_emision',
            'nif_emisor', 'razon_social', 'base_imponible', 'importe_total', 'codigo_oc'
        ] if c in facturas_sospechosas.columns]
        tabla_sospechosas = facturas_sospechosas[cols_disp].copy()
        tabla_sospechosas = tabla_sospechosas.sort_values('base_imponible', ascending=False) if 'base_imponible' in tabla_sospechosas.columns else tabla_sospechosas

    top_proveedores_informe = pd.DataFrame()
    ranking_oc_informe = pd.DataFrame()
    ranking_ut_informe = pd.DataFrame()

    if len(facturas_sospechosas) > 0:
        if 'nif_emisor' in facturas_sospechosas.columns and 'razon_social' in facturas_sospechosas.columns:
            top_proveedores_informe = facturas_sospechosas.groupby(['nif_emisor', 'razon_social']).agg({
                'id_fra_rcf': 'count',
                'base_imponible': 'sum'
            }).reset_index()
            top_proveedores_informe.columns = ['NIF', 'Razón Social', 'Nº Facturas', 'BI Acumulada']
            top_proveedores_informe = top_proveedores_informe.sort_values('BI Acumulada', ascending=False).head(10)

        if 'codigo_oc' in facturas_sospechosas.columns:
            ranking_oc_informe = facturas_sospechosas.groupby('codigo_oc').agg({
                'base_imponible': 'sum',
                'id_fra_rcf': 'count'
            }).sort_values('base_imponible', ascending=False).head(10).reset_index()
            ranking_oc_informe.columns = ['Código OC', 'BI Total', 'Nº Facturas']

        if 'codigo_ut' in facturas_sospechosas.columns:
            ranking_ut_informe = facturas_sospechosas.groupby('codigo_ut').agg({
                'base_imponible': 'sum',
                'id_fra_rcf': 'count'
            }).sort_values('base_imponible', ascending=False).head(10).reset_index()
            ranking_ut_informe.columns = ['Código UT', 'BI Total', 'Nº Facturas']

    return {
        'total_papel': len(facturas_papel),
        'total_sospechosas': len(facturas_sospechosas),
        'importe_sospechoso': facturas_sospechosas['base_imponible'].sum() if len(facturas_sospechosas) > 0 and 'base_imponible' in facturas_sospechosas.columns else 0,
        'top_10_importe': tabla_sospechosas,
        'top_proveedores': top_proveedores_informe,
        'ranking_oc': ranking_oc_informe,
        'ranking_ut': ranking_ut_informe,
        'evolucion_mensual': pd.DataFrame(),
        'facturas_sospechosas': facturas_sospechosas[[
            c for c in ['entidad', 'id_fra_rcf', 'numero_factura', 'fecha_emision',
                        'nif_emisor', 'razon_social', 'base_imponible', 'importe_total', 'codigo_oc']
            if c in facturas_sospechosas.columns
        ]].copy() if len(facturas_sospechosas) > 0 else pd.DataFrame()
    }


def calcular_anotacion(datos: Dict) -> Dict:
    """Calcula el análisis de anotación en RCF (Sección V.2)."""
    df_rcf_orig = _df_rcf_activo(datos)

    fecha_cambio_cfg = CONFIGURACION_TRANSICION_2025.get('fecha_efectiva_cambio_procedimiento')
    fecha_cambio = pd.to_datetime(fecha_cambio_cfg) if fecha_cambio_cfg else pd.to_datetime('2025-10-20')
    plazo_dias = CONFIGURACION_TRANSICION_2025.get('plazo_aceptacion_areas_dias', 2)
    tipo_dias = CONFIGURACION_TRANSICION_2025.get('tipo_dias_plazo_aceptacion')

    df_rcf = clasificar_procedimiento(df_rcf_orig, fecha_cambio)

    mask_elec = df_rcf['es_papel'] == False if 'es_papel' in df_rcf.columns else pd.Series(True, index=df_rcf.index)
    df_elec = df_rcf[mask_elec].copy()

    if 'fecha_registro_face' in df_elec.columns:
        df_anterior = df_elec[df_elec['fecha_registro_face'] < fecha_cambio].copy()
        df_nuevo = df_elec[df_elec['fecha_registro_face'] >= fecha_cambio].copy()
    else:
        df_anterior = df_elec.copy()
        df_nuevo = pd.DataFrame(columns=df_elec.columns)

    df_retenidas = identificar_facturas_retenidas(
        datos['face'],
        df_rcf_orig,
        ids_precalculados=datos.get('ids_face_en_rcf_total')
    )
    retenidas_count = len(df_retenidas)

    df_ant_tiempos = calcular_indicadores_procedimiento_anterior(df_rcf)
    df_nvo_tiempos = calcular_indicadores_procedimiento_nuevo(df_rcf)

    t_medio_face_s = df_ant_tiempos[~df_ant_tiempos.get('incidencia_temporal', False)]['tiempo_face_s'].mean() if not df_ant_tiempos.empty and 'tiempo_face_s' in df_ant_tiempos.columns else None
    t_medio_s_f = df_ant_tiempos[~df_ant_tiempos.get('incidencia_temporal', False)]['tiempo_s_f'].mean() if not df_ant_tiempos.empty and 'tiempo_s_f' in df_ant_tiempos.columns else None
    t_medio_face_f_ant = df_ant_tiempos[~df_ant_tiempos.get('incidencia_temporal', False)]['tiempo_face_f'].mean() if not df_ant_tiempos.empty and 'tiempo_face_f' in df_ant_tiempos.columns else None
    t_medio_face_f_nvo = df_nvo_tiempos[~df_nvo_tiempos.get('incidencia_temporal', False)]['tiempo_face_f_directo'].mean() if not df_nvo_tiempos.empty and 'tiempo_face_f_directo' in df_nvo_tiempos.columns else None

    df_ant_val = df_ant_tiempos[~df_ant_tiempos['incidencia_temporal']].copy() if not df_ant_tiempos.empty and 'incidencia_temporal' in df_ant_tiempos.columns else pd.DataFrame()
    df_nvo_val = df_nvo_tiempos[~df_nvo_tiempos['incidencia_temporal']].copy() if not df_nvo_tiempos.empty and 'incidencia_temporal' in df_nvo_tiempos.columns else pd.DataFrame()

    n_s_postcambio_total = (df_elec.get('resultado_auditoria_rcf', pd.Series(dtype=str)) == 'POST_CAMBIO_CON_CODIGO_S').sum() if not df_elec.empty else 0
    n_sin_causa = (df_elec.get('resultado_auditoria_rcf', pd.Series(dtype=str)) == 'RECHAZADA_SIN_CAUSA_SUFICIENTE').sum() if not df_elec.empty else 0
    n_fechas_negativas_ant = len(df_ant_tiempos[df_ant_tiempos['incidencia_temporal']]) if not df_ant_tiempos.empty and 'incidencia_temporal' in df_ant_tiempos.columns else 0
    n_fechas_negativas_nvo = len(df_nvo_tiempos[df_nvo_tiempos['incidencia_temporal']]) if not df_nvo_tiempos.empty and 'incidencia_temporal' in df_nvo_tiempos.columns else 0
    n_fechas_neg = n_fechas_negativas_ant + n_fechas_negativas_nvo

    n_rechazadas = len(df_nuevo[df_nuevo['procedimiento_aplicado'] == 'RECHAZO_PREVIO_A_ANOTACION']) if not df_nuevo.empty and 'procedimiento_aplicado' in df_nuevo.columns else 0

    return {
        'fecha_cambio_procedimiento': fecha_cambio.strftime('%d/%m/%Y'),
        'plazo_aceptacion_dias': plazo_dias,
        'tipo_dias_plazo': tipo_dias,
        'facturas_retenidas': retenidas_count,
        'df_retenidas': df_retenidas if retenidas_count > 0 else pd.DataFrame(),
        'n_facturas_s': len(df_ant_tiempos) if not df_ant_tiempos.empty else 0,
        'n_facturas_s_con_f': int(df_ant_tiempos['tiempo_face_f'].notna().sum()) if not df_ant_tiempos.empty and 'tiempo_face_f' in df_ant_tiempos.columns else 0,
        'n_facturas_s_sin_f': (len(df_ant_tiempos) - int(df_ant_tiempos['tiempo_face_f'].notna().sum())) if not df_ant_tiempos.empty and 'tiempo_face_f' in df_ant_tiempos.columns else 0,
        'tiempo_medio_face_s_min': t_medio_face_s,
        'tiempo_medio_s_f_min': t_medio_s_f,
        'tiempo_medio_face_f_anterior_min': t_medio_face_f_ant,
        'df_tiempos_anterior': df_ant_val,
        'n_facturas_f_directo': len(df_nvo_tiempos) if not df_nvo_tiempos.empty else 0,
        'tiempo_medio_face_f_nuevo_min': t_medio_face_f_nvo,
        'df_tiempos_nuevo': df_nvo_val,
        'n_rechazadas_nuevo': n_rechazadas,
        'n_rechazadas_sin_causa': int(n_sin_causa),
        'n_s_postcambio': int(n_s_postcambio_total),
        'n_fechas_negativas': n_fechas_neg,
        'facturas_retenidas_count': retenidas_count,
        'tiempo_medio_min': t_medio_face_f_nvo if t_medio_face_f_nvo is not None else t_medio_face_f_ant,
        'tiempo_mediano_min': df_nvo_val['tiempo_face_f_directo'].median() if not df_nvo_val.empty and 'tiempo_face_f_directo' in df_nvo_val.columns else None,
        'tiempo_max_min': df_nvo_val['tiempo_face_f_directo'].max() if not df_nvo_val.empty and 'tiempo_face_f_directo' in df_nvo_val.columns else None,
        'tiempo_min_min': df_nvo_val['tiempo_face_f_directo'].min() if not df_nvo_val.empty and 'tiempo_face_f_directo' in df_nvo_val.columns else None,
        'num_anomalias': n_fechas_neg,
    }


def calcular_validaciones(df_rcf: pd.DataFrame) -> Dict:
    """Calcula el análisis de validaciones (Sección V.3)."""
    resultados = aplicar_todas_validaciones(df_rcf)
    rechazos = analizar_rechazos(df_rcf)
    return {
        'validaciones': resultados,
        'rechazos': rechazos
    }


def calcular_tramitacion(datos: Dict) -> Dict:
    """Calcula el análisis de tramitación (Sección V.4) de forma simplificada."""
    df_rcf = _df_rcf_activo(datos)
    df_anulaciones = datos['anulaciones'].copy()
    df_estados = datos['estados'].copy()

    fecha_cambio_cfg = CONFIGURACION_TRANSICION_2025.get('fecha_efectiva_cambio_procedimiento')
    fecha_cambio_t4 = pd.to_datetime(fecha_cambio_cfg) if fecha_cambio_cfg else pd.to_datetime('2025-10-20')
    plazo_dias_t4 = CONFIGURACION_TRANSICION_2025.get('plazo_aceptacion_areas_dias', 2)

    df_rcf_clas = clasificar_procedimiento(df_rcf, fecha_cambio_t4)

    # Anulaciones
    total_anulaciones = len(df_anulaciones)
    anuladas = 0
    con_comentario = 0
    df_anulaciones_rcf = pd.DataFrame()

    if 'registro' in df_anulaciones.columns and 'ID_FACE' in df_rcf.columns:
        df_anulaciones_rcf = df_anulaciones.merge(
            df_rcf[['ID_FACE', 'numero_factura', 'nif_emisor', 'razon_social', 'importe_total', 'estado']],
            left_on='registro',
            right_on='ID_FACE',
            how='left'
        )
        if 'estado' in df_anulaciones_rcf.columns:
            anuladas = len(df_anulaciones_rcf[df_anulaciones_rcf['estado'].astype(str).str.upper().isin(['ANULADA', '3100'])])
        if 'comentario' in df_anulaciones.columns:
            con_comentario = len(df_anulaciones[df_anulaciones['comentario'].notna() & (df_anulaciones['comentario'] != '')])

    # Distribución de estados
    distribucion_estados_informe = pd.DataFrame()
    if 'estado' in df_rcf.columns:
        distribucion_estados = df_rcf['estado'].value_counts()
        distribucion_estados_informe = distribucion_estados.head(10).reset_index()
        distribucion_estados_informe.columns = ['Estado', 'Cantidad']
        distribucion_estados_informe['Porcentaje'] = (distribucion_estados_informe['Cantidad'] / len(df_rcf) * 100).round(2)

    # Tiempos de tramitación posterior
    df_tiempos_fp = calcular_indicadores_tramitacion_posterior(df_rcf_clas)
    df_tiempos_sf = calcular_indicadores_procedimiento_anterior(df_rcf_clas)

    n_sf_total = len(df_tiempos_sf) if not df_tiempos_sf.empty else 0
    n_sf_con_f = int(df_tiempos_sf['tiempo_face_f'].notna().sum()) if not df_tiempos_sf.empty and 'tiempo_face_f' in df_tiempos_sf.columns else 0
    df_sf_val2 = df_tiempos_sf[~df_tiempos_sf['incidencia_temporal']].copy() if not df_tiempos_sf.empty and 'incidencia_temporal' in df_tiempos_sf.columns else pd.DataFrame()
    t_med_sf_inf = df_sf_val2['tiempo_s_f'].mean() if not df_sf_val2.empty and 'tiempo_s_f' in df_sf_val2.columns else None
    n_fuera_plazo_sf = int((df_sf_val2['tiempo_s_f'] > plazo_dias_t4 * 1440).sum()) if not df_sf_val2.empty and 'tiempo_s_f' in df_sf_val2.columns else 0

    n_fp_total = len(df_tiempos_fp) if not df_tiempos_fp.empty else 0
    n_fp_aceptadas = int(df_tiempos_fp['fecha_tramitacion'].notna().sum()) if not df_tiempos_fp.empty and 'fecha_tramitacion' in df_tiempos_fp.columns else 0
    df_fp_val2 = df_tiempos_fp[~df_tiempos_fp['incidencia_temporal']].copy() if not df_tiempos_fp.empty and 'incidencia_temporal' in df_tiempos_fp.columns else pd.DataFrame()
    t_med_fp_inf = df_fp_val2['tiempo_f_aceptacion'].mean() if not df_fp_val2.empty and 'tiempo_f_aceptacion' in df_fp_val2.columns else None
    n_fuera_plazo_fp = int((df_fp_val2['tiempo_f_aceptacion'] > plazo_dias_t4 * 1440).sum()) if not df_fp_val2.empty and 'tiempo_f_aceptacion' in df_fp_val2.columns else 0

    # Pagos y contabilizadas (aproximación por estado)
    estados_pagadas = ['PAGADA', '2500']
    estados_contabilizadas = ['CONTABILIZADA', 'CONTABILIZADA OBLIGACIÓN', '2400']
    facturas_pagadas = df_rcf[df_rcf['estado'].astype(str).str.upper().isin(estados_pagadas)] if 'estado' in df_rcf.columns else pd.DataFrame()
    facturas_contabilizadas = df_rcf[df_rcf['estado'].astype(str).str.upper().isin(estados_contabilizadas)] if 'estado' in df_rcf.columns else pd.DataFrame()
    total_pagadas = len(facturas_pagadas)

    # Detalle anulaciones
    anulaciones_informe = pd.DataFrame()
    if len(df_anulaciones_rcf) > 0:
        cols_anul = [c for c in ['registro', 'numero_factura', 'nif_emisor', 'razon_social',
                                  'importe_total', 'fecha_solicitud_anulacion', 'estado'] if c in df_anulaciones_rcf.columns]
        anulaciones_informe = df_anulaciones_rcf[cols_anul].copy()
        anulaciones_informe.columns = [
            'Registro FACe', 'Nº Factura', 'NIF', 'Razón Social',
            'Importe', 'Fecha Solicitud', 'Estado Actual'
        ][:len(cols_anul)]

    return {
        'total_anulaciones': total_anulaciones,
        'anulaciones_aceptadas': anuladas,
        'anulaciones_con_comentario': con_comentario,
        'facturas_pagadas': total_pagadas,
        'importe_pagado': facturas_pagadas['importe_total'].sum() if len(facturas_pagadas) > 0 and 'importe_total' in facturas_pagadas.columns else 0,
        'facturas_contabilizadas': len(facturas_contabilizadas),
        'distribucion_estados': distribucion_estados_informe,
        'tiempos_por_estado': pd.DataFrame(),
        'secuencias_estados': pd.DataFrame(),
        'detalle_anulaciones': anulaciones_informe,
        'n_facturas_s_total': n_sf_total,
        'n_facturas_s_con_f': n_sf_con_f,
        'n_facturas_s_sin_f': n_sf_total - n_sf_con_f,
        'tiempo_medio_s_f_min': t_med_sf_inf,
        'n_fuera_plazo_procedimiento_anterior': n_fuera_plazo_sf,
        'df_tiempos_procedimiento_anterior': df_sf_val2,
        'n_facturas_f_directas': n_fp_total,
        'n_facturas_f_aceptadas': n_fp_aceptadas,
        'tiempo_medio_f_aceptacion_min': t_med_fp_inf,
        'n_fuera_plazo_procedimiento_nuevo': n_fuera_plazo_fp,
        'df_tiempos_tramitacion_posterior': df_fp_val2,
        'fecha_cambio_procedimiento': fecha_cambio_t4.strftime('%d/%m/%Y'),
        'plazo_referencia_dias': plazo_dias_t4,
    }


def calcular_obligaciones(df_rcf: pd.DataFrame) -> Dict:
    """Calcula el análisis de obligaciones (Sección V.5)."""
    fecha_actual = datetime.now()
    fecha_limite = fecha_actual - timedelta(days=90)

    estados_pendientes = ['REGISTRADA', 'VERIFICADA', 'RECIBIDA', 'CONFORMADA']

    if 'fecha_anotacion_rcf' in df_rcf.columns and 'estado' in df_rcf.columns:
        df_rcf['fecha_anotacion_rcf'] = pd.to_datetime(df_rcf['fecha_anotacion_rcf'])
        facturas_pendientes_3m = df_rcf[
            (df_rcf['fecha_anotacion_rcf'] <= fecha_limite) &
            (df_rcf['estado'].isin(estados_pendientes))
        ].copy()
        facturas_pendientes_3m['dias_pendiente'] = (fecha_actual - facturas_pendientes_3m['fecha_anotacion_rcf']).dt.days
    else:
        facturas_pendientes_3m = pd.DataFrame()

    df_pendientes_informe = pd.DataFrame()
    ranking_oc_pendientes_informe = pd.DataFrame()
    ranking_ut_pendientes_informe = pd.DataFrame()
    distribucion_antiguedad_informe = pd.DataFrame()

    if len(facturas_pendientes_3m) > 0:
        cols_pend = [c for c in [
            'entidad', 'id_fra_rcf', 'numero_factura', 'fecha_anotacion_rcf',
            'dias_pendiente', 'nif_emisor', 'razon_social', 'importe_total',
            'estado', 'codigo_oc'
        ] if c in facturas_pendientes_3m.columns]
        df_pendientes_informe = facturas_pendientes_3m[cols_pend].copy()
        df_pendientes_informe.columns = [
            'Entidad', 'ID RCF', 'Nº Factura', 'Fecha Anotación', 'Días Pendiente',
            'NIF', 'Razón Social', 'Importe', 'Estado', 'OC'
        ][:len(cols_pend)]

        if 'codigo_oc' in facturas_pendientes_3m.columns:
            ranking_oc_pendientes_informe = facturas_pendientes_3m.groupby('codigo_oc').agg({
                'importe_total': 'sum',
                'id_fra_rcf': 'count',
                'dias_pendiente': 'mean'
            }).round(2).reset_index()
            ranking_oc_pendientes_informe.columns = ['Código OC', 'Importe Total', 'Nº Facturas', 'Días Medio']
            ranking_oc_pendientes_informe = ranking_oc_pendientes_informe.sort_values('Importe Total', ascending=False).head(10)

        if 'codigo_ut' in facturas_pendientes_3m.columns:
            ranking_ut_pendientes_informe = facturas_pendientes_3m.groupby('codigo_ut').agg({
                'importe_total': 'sum',
                'id_fra_rcf': 'count',
                'dias_pendiente': 'mean'
            }).round(2).reset_index()
            ranking_ut_pendientes_informe.columns = ['Código UT', 'Importe Total', 'Nº Facturas', 'Días Medio']
            ranking_ut_pendientes_informe = ranking_ut_pendientes_informe.sort_values('Importe Total', ascending=False).head(10)

    return {
        'facturas_3_meses': len(facturas_pendientes_3m),
        'importe_pendiente': facturas_pendientes_3m['importe_total'].sum() if len(facturas_pendientes_3m) > 0 and 'importe_total' in facturas_pendientes_3m.columns else 0,
        'dias_medio_pendiente': facturas_pendientes_3m['dias_pendiente'].mean() if len(facturas_pendientes_3m) > 0 and 'dias_pendiente' in facturas_pendientes_3m.columns else 0,
        'dias_max_pendiente': facturas_pendientes_3m['dias_pendiente'].max() if len(facturas_pendientes_3m) > 0 and 'dias_pendiente' in facturas_pendientes_3m.columns else 0,
        'detalle_pendientes': df_pendientes_informe,
        'ranking_oc_pendientes': ranking_oc_pendientes_informe,
        'ranking_ut_pendientes': ranking_ut_pendientes_informe,
        'distribucion_antiguedad': distribucion_antiguedad_informe,
        'morosidad': {}
    }


def precalcular_analisis_faltantes(datos: Dict, analisis: Dict) -> Dict:
    """Precalcula los análisis que no estén presentes en session_state."""
    df_rcf = _df_rcf_activo(datos)

    if 'facturas_papel' not in analisis:
        analisis['facturas_papel'] = calcular_facturas_papel(df_rcf)

    if 'anotacion' not in analisis:
        analisis['anotacion'] = calcular_anotacion(datos)

    if 'validaciones' not in analisis:
        analisis.update(calcular_validaciones(df_rcf))

    if 'tramitacion' not in analisis:
        analisis['tramitacion'] = calcular_tramitacion(datos)

    if 'obligaciones' not in analisis:
        analisis['obligaciones'] = calcular_obligaciones(df_rcf)

    return analisis
