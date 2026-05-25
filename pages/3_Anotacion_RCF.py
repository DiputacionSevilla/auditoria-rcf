"""
Análisis de Anotación en RCF - Sección V.2 de la Guía IGAE
Ejercicio 2025: año de transición con dos procedimientos diferenciados.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import COLORES, CONFIGURACION_TRANSICION_2025
from utils.data_loader import (
    clasificar_procedimiento,
    calcular_indicadores_procedimiento_anterior,
    calcular_indicadores_procedimiento_nuevo,
    identificar_facturas_retenidas,
    exportar_a_excel,
)

st.set_page_config(
    page_title="Anotación RCF - Auditoría RCF",
    page_icon="⏱️",
    layout="wide"
)

NOMBRES_MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


# ---------------------------------------------------------------------------
# Helpers de presentación
# ---------------------------------------------------------------------------

def _fmt_min(val):
    if pd.isna(val):
        return '—'
    if abs(val) >= 1440:
        return f'{val/1440:.1f} d'
    if abs(val) >= 60:
        return f'{val/60:.1f} h'
    return f'{val:.0f} min'


def _fmt_int(val):
    return '—' if pd.isna(val) else f'{int(val):,}'


def _alerta(codigo, condicion, mensaje):
    if condicion:
        st.error(f'**[{codigo}]** {mensaje}')


def _info_alerta(codigo, condicion, mensaje):
    if condicion:
        st.info(f'**[{codigo}]** {mensaje}')


# ---------------------------------------------------------------------------
# Tabla HTML estilo informe
# ---------------------------------------------------------------------------

def _html_tabla(filas, cabecera_cols, titulo_col_izq='', bold_ultima_fila=True):
    th = 'background:#1f4e79;color:white;padding:7px 10px;border:1px solid #555;text-align:center;white-space:nowrap;'
    th_lbl = 'background:#1f4e79;color:white;padding:7px 14px;border:1px solid #555;text-align:left;min-width:220px;'
    td = 'padding:6px 10px;border:1px solid #ccc;text-align:center;'
    td_lbl = 'padding:6px 14px;border:1px solid #ccc;text-align:left;font-size:13px;'

    cols_html = ''.join(f'<th style="{th}">{c}</th>' for c in cabecera_cols)
    thead = f'<thead><tr><th style="{th_lbl}">{titulo_col_izq}</th>{cols_html}</tr></thead>'

    rows_html = ''
    for i, (label, valores) in enumerate(filas):
        is_last = bold_ultima_fila and i == len(filas) - 1
        bg = 'background:#dce6f1;font-weight:bold;' if is_last else ('background:#f5f9ff;' if i % 2 == 0 else '')
        celdas = ''.join(f'<td style="{td}{bg}">{v}</td>' for v in valores)
        rows_html += f'<tr><td style="{td_lbl}{bg}">{label}</td>{celdas}</tr>'

    return (
        f'<table style="border-collapse:collapse;font-size:13px;width:100%;">'
        f'{thead}<tbody>{rows_html}</tbody></table>'
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.title("⏱️ Tiempos de Anotación en RCF")
    st.markdown("Análisis de tiempos de inscripción y facturas retenidas (Sección V.2) — **Ejercicio 2025**")

    if 'datos' not in st.session_state:
        st.warning("⚠️ No hay datos cargados. Por favor, carga los archivos en la página principal.")
        if st.button("Ir a página principal"):
            st.switch_page("app.py")
        return

    datos = st.session_state['datos']
    df_rcf_orig = datos['rcf'].copy()
    if 'estado' in df_rcf_orig.columns:
        df_rcf_orig = df_rcf_orig[df_rcf_orig['estado'].astype(str).str.upper() != 'BORRADA'].copy()

    # -----------------------------------------------------------------------
    # Configuración de la fecha de cambio de procedimiento
    # -----------------------------------------------------------------------
    st.markdown("---")
    with st.expander("⚙️ Configuración del año de transición 2025", expanded=True):
        st.markdown("""
        El ejercicio 2025 coexistieron dos procedimientos diferenciados de recepción y anotación
        de facturas electrónicas desde FACe. Esta fecha es el parámetro central del análisis.
        """)

        fecha_cambio_cfg = CONFIGURACION_TRANSICION_2025.get('fecha_efectiva_cambio_procedimiento')
        fecha_default = pd.to_datetime(fecha_cambio_cfg).date() if fecha_cambio_cfg else None

        col_fecha, col_plazo, col_tipo = st.columns(3)
        with col_fecha:
            fecha_cambio_input = st.date_input(
                "Fecha efectiva del cambio de procedimiento",
                value=fecha_default,
                min_value=pd.Timestamp('2025-01-02').date(),
                max_value=pd.Timestamp('2025-12-31').date(),
                help="Fecha en que entró en producción el nuevo procedimiento de anotación directa F."
            )
        with col_plazo:
            plazo_dias = st.number_input(
                "Plazo máximo de aceptación (días)",
                min_value=1, max_value=30,
                value=CONFIGURACION_TRANSICION_2025.get('plazo_aceptacion_areas_dias', 2),
                help="Conforme a las Bases de ejecución del presupuesto aplicables."
            )
        with col_tipo:
            tipo_dias = st.selectbox(
                "Tipo de días del plazo",
                options=['hábiles', 'naturales', 'Sin validar'],
                index=2 if CONFIGURACION_TRANSICION_2025.get('tipo_dias_plazo_aceptacion') is None else 0,
                help="Validar con el texto literal de las Bases de ejecución antes de cerrar el informe."
            )

        if tipo_dias == 'Sin validar':
            st.warning("⚠️ El tipo de días del plazo no está validado. No se podrán cerrar los textos conclusivos del Apartado 4 hasta su confirmación.")

    fecha_cambio = pd.Timestamp(fecha_cambio_input)

    # -----------------------------------------------------------------------
    # Marco legal
    # -----------------------------------------------------------------------
    with st.expander("📋 Marco legal — Anotación en RCF (Art. 9 Ley 25/2013)"):
        st.markdown("""
        Los artículos 9.1 y 9.2 de la Ley 25/2013, de 27 de diciembre, establecen que toda factura
        electrónica remitida por el PGEFe deberá ser puesta a disposición o remitida automáticamente
        al RCF correspondiente, el cual, una vez recibida y superadas las validaciones aplicables,
        procederá a su anotación generando un código de identificación que deberá ser comunicado al
        Punto General de Entrada.

        El artículo 12.3 exige que la auditoría anual verifique que no quedan facturas retenidas en
        ninguna fase del proceso e incluya un análisis de los tiempos medios de inscripción y del
        número y causas de las facturas rechazadas en la fase de anotación.

        **Particularidad de 2025:** en la auditoría del ejercicio 2024 se detectó que el procedimiento
        implantado asignaba inicialmente un identificador S —comunicado a FACe— mientras que la entidad
        no consideraba producida la anotación definitiva hasta la posterior generación del identificador F.
        Desde **{fecha}** ese procedimiento fue corregido y las facturas válidas se anotan directamente con F.
        """.format(fecha=fecha_cambio.strftime('%d/%m/%Y')))

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Clasificar facturas por procedimiento
    # -----------------------------------------------------------------------
    df_rcf = clasificar_procedimiento(df_rcf_orig, fecha_cambio)

    mask_elec = df_rcf['es_papel'] == False if 'es_papel' in df_rcf.columns else pd.Series(True, index=df_rcf.index)
    df_elec = df_rcf[mask_elec].copy()

    # Los datos usan "FECHA RECEPCION FACE" (fecha_codigo_s) para distinguir procedimientos.
    # No se necesita un campo codigo_s; la clasificación es exclusivamente por fecha.
    tiene_cols_sf = 'fecha_codigo_s' in df_elec.columns or 'fecha_anotacion_rcf' in df_elec.columns

    # Separar por periodo
    if 'fecha_registro_face' in df_elec.columns:
        df_anterior = df_elec[df_elec['fecha_registro_face'] < fecha_cambio].copy()
        df_nuevo = df_elec[df_elec['fecha_registro_face'] >= fecha_cambio].copy()
    else:
        df_anterior = df_elec.copy()
        df_nuevo = pd.DataFrame(columns=df_elec.columns)

    # -----------------------------------------------------------------------
    # Sección: Facturas retenidas en FACe
    # -----------------------------------------------------------------------
    st.markdown("### 🔍 Facturas Retenidas en FACe")
    st.info("Facturas registradas en FACe que no constan en el RCF ni han sido rechazadas con trazabilidad.")

    df_retenidas = identificar_facturas_retenidas(
        datos['face'],
        df_rcf_orig,
        ids_precalculados=datos.get('ids_face_en_rcf_total')
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Facturas en FACe", f"{len(datos['face']):,}")
    c2.metric("Electrónicas en RCF (no borradas)", f"{len(df_elec):,}")
    retenidas_count = len(df_retenidas)
    c3.metric(
        "Retenidas / No anotadas",
        f"{retenidas_count:,}",
        delta=f"{retenidas_count} facturas" if retenidas_count > 0 else "Sin incidencias",
        delta_color="inverse" if retenidas_count > 0 else "off"
    )

    _alerta('ALERTA_RCF_002', retenidas_count > 0,
            f'Se han identificado **{retenidas_count}** facturas en FACe sin correspondencia en el RCF ni rechazo acreditado.')

    if retenidas_count > 0:
        cols_ret = [c for c in ['registro', 'nif_emisor', 'nombre', 'numero', 'importe', 'fecha_registro', 'oc'] if c in df_retenidas.columns]
        df_ret_disp = df_retenidas[cols_ret].copy()
        rename_ret = {'registro': 'Registro FACe', 'nif_emisor': 'NIF', 'nombre': 'Proveedor',
                      'numero': 'Nº Factura', 'importe': 'Importe', 'fecha_registro': 'Fecha Registro', 'oc': 'OC'}
        df_ret_disp = df_ret_disp.rename(columns={k: v for k, v in rename_ret.items() if k in df_ret_disp.columns})
        st.dataframe(df_ret_disp, hide_index=True)
        excel_ret = exportar_a_excel(df_ret_disp, 'Facturas_Retenidas')
        st.download_button("📥 Exportar retenidas", data=excel_ret,
                           file_name='facturas_retenidas_face.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.success("✅ No hay facturas retenidas. Todas las facturas de FACe constan en el RCF o tienen rechazo acreditado.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # TABLA 2.1 — Cruce FACe–RCF diferenciando procedimientos
    # -----------------------------------------------------------------------
    st.markdown("### 📋 Tabla 2.1 — Cruce FACe–RCF diferenciando procedimientos")

    if tiene_cols_sf:
        # Conteos procedimiento anterior
        n_face_ant = len(df_anterior)
        n_s_ant = (df_anterior['procedimiento_aplicado'] == 'PROCEDIMIENTO_ANTERIOR_S_F').sum()
        n_f_ant = df_anterior['procedimiento_aplicado'].isin([
            'TRAMITADA_REGIMEN_ANTERIOR_S_F', 'PROCEDIMIENTO_ANTERIOR_S_F'
        ]).sum() if 'codigo_f' in df_anterior.columns else (
            df_anterior['resultado_auditoria_rcf'] == 'TRAMITADA_REGIMEN_ANTERIOR_S_F'
        ).sum()
        # Contar F reales (tienen codigo_f no vacío)
        if 'codigo_f' in df_anterior.columns:
            n_f_ant = df_anterior['codigo_f'].notna().sum()
        n_rechazo_ant = (df_anterior['procedimiento_aplicado'] == 'RECHAZO_PREVIO_A_ANOTACION').sum()
        n_incidencia_ant = (df_anterior['resultado_auditoria_rcf'] == 'INCIDENCIA_MANUAL').sum()

        # Conteos procedimiento nuevo
        n_face_nvo = len(df_nuevo)
        n_s_postcambio = (df_nuevo['resultado_auditoria_rcf'] == 'POST_CAMBIO_CON_CODIGO_S').sum()
        n_f_directo = (df_nuevo['procedimiento_aplicado'] == 'ANOTACION_DIRECTA_F').sum()
        n_rechazo_nvo = (df_nuevo['procedimiento_aplicado'] == 'RECHAZO_PREVIO_A_ANOTACION').sum()
        n_incidencia_nvo = (df_nuevo['resultado_auditoria_rcf'] == 'INCIDENCIA_MANUAL').sum()

        filas_21 = [
            ('Facturas electrónicas recibidas desde FACe',
             [_fmt_int(n_face_ant), _fmt_int(n_face_nvo), _fmt_int(n_face_ant + n_face_nvo)]),
            ('Facturas con identificador previo S',
             [_fmt_int(n_s_ant), _fmt_int(n_s_postcambio), _fmt_int(n_s_ant + n_s_postcambio)]),
            ('Facturas anotadas con identificador F',
             [_fmt_int(n_f_ant), _fmt_int(n_f_directo), _fmt_int(n_f_ant + n_f_directo)]),
            ('Facturas rechazadas antes de anotación',
             [_fmt_int(n_rechazo_ant), _fmt_int(n_rechazo_nvo), _fmt_int(n_rechazo_ant + n_rechazo_nvo)]),
            ('Facturas retenidas en FACe pendientes de descarga',
             [_fmt_int(retenidas_count), '0', _fmt_int(retenidas_count)]),
            ('Incidencias sin justificar',
             [_fmt_int(n_incidencia_ant), _fmt_int(n_incidencia_nvo), _fmt_int(n_incidencia_ant + n_incidencia_nvo)]),
        ]
        st.markdown(
            _html_tabla(
                filas_21,
                cabecera_cols=[
                    f'Procedimiento anterior S–F<br><small>Hasta {fecha_cambio.strftime("%d/%m/%Y")}</small>',
                    f'Procedimiento nuevo: F directo<br><small>Desde {fecha_cambio.strftime("%d/%m/%Y")}</small>',
                    'Total ejercicio'
                ],
                titulo_col_izq='Concepto',
                bold_ultima_fila=False
            ),
            unsafe_allow_html=True
        )
        st.caption("")

        # Alertas de la tabla 2.1
        _alerta('ALERTA_RCF_001', n_s_postcambio > 0,
                f'Se detectan **{n_s_postcambio}** registros con identificador previo S tras la implantación del procedimiento corregido ({fecha_cambio.strftime("%d/%m/%Y")}). Revisar subsistencia del circuito anterior.')
        _alerta('ALERTA_RCF_003', (df_elec.get('resultado_auditoria_rcf', pd.Series(dtype=str)) == 'RECHAZADA_SIN_CAUSA_SUFICIENTE').sum() > 0,
                f'Existen rechazos sin causa reglamentaria identificable o sin trazabilidad suficiente.')
        _info_alerta('INFO_RCF_201',
                     (df_anterior.get('resultado_auditoria_rcf', pd.Series(dtype=str)) == 'ANOTADA_DIRECTA_F_CORRECTA').sum() > 0,
                     'Existen facturas anteriores a la fecha de cambio con anotación directa F. Verificar si corresponden a pruebas previas o excepciones justificadas.')

        # Exportar detalle cruce
        with st.expander("📥 Exportar detalle cruce FACe–RCF"):
            cols_exp = [c for c in ['ID_FACE', 'numero_factura', 'nif_emisor', 'importe_total',
                                     'fecha_registro_face', 'codigo_s', 'fecha_codigo_s',
                                     'codigo_f', 'fecha_codigo_f', 'procedimiento_aplicado',
                                     'resultado_auditoria_rcf', 'codigo_ut'] if c in df_elec.columns]
            df_exp_cruce = df_elec[cols_exp].copy()
            excel_cruce = exportar_a_excel(df_exp_cruce, 'Cruce_FACe_RCF')
            st.download_button("📥 Descargar detalle completo", data=excel_cruce,
                               file_name='cruce_face_rcf_2025.xlsx',
                               mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.warning("⚠️ Los datos del RCF no contienen la columna 'FECHA RECEPCION FACE' ni 'FECHA REGISTRO'. Carga un fichero con esos campos para el análisis diferenciado.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # TABLA 2.2 — Tiempos procedimiento anterior (S→F)
    # -----------------------------------------------------------------------
    st.markdown("### 📊 Tabla 2.2 — Tiempos del procedimiento anterior (S→F)")
    st.caption(f"Solo facturas tratadas mediante código S, hasta el {fecha_cambio.strftime('%d/%m/%Y')}.")

    df_ant_tiempos = calcular_indicadores_procedimiento_anterior(df_rcf)

    if not df_ant_tiempos.empty:
        df_ant_validos = df_ant_tiempos[~df_ant_tiempos['incidencia_temporal']].copy()
        df_ant_incid = df_ant_tiempos[df_ant_tiempos['incidencia_temporal']].copy()

        n_total_s = len(df_ant_tiempos)
        n_s_con_f = df_ant_tiempos['tiempo_face_f'].notna().sum()
        n_s_sin_f = n_total_s - n_s_con_f
        n_excluidos = len(df_ant_incid)

        st.caption(f"Facturas con código S: **{n_total_s:,}** | Con código F: **{n_s_con_f:,}** | Sin código F: **{n_s_sin_f:,}** | Excluidas por incidencia temporal: **{n_excluidos:,}**")

        _alerta('ALERTA_RCF_101', n_s_sin_f > 0,
                f'**{n_s_sin_f}** facturas permanecen en estado previo S sin haber obtenido identificador F a la fecha de extracción.')
        _alerta('ALERTA_RCF_104', n_excluidos > 0,
                f'**{n_excluidos}** registros con fechas negativas o inconsistentes excluidos de las medias.')

        if not df_ant_validos.empty:
            df_ant_validos['_mes_num'] = df_ant_validos['fecha_registro_face'].dt.month
            df_ant_validos['_mes_nombre'] = df_ant_validos['_mes_num'].map(NOMBRES_MESES)

            # Solo meses hasta el de la fecha de cambio
            mes_cambio = fecha_cambio.month
            df_ant_validos = df_ant_validos[df_ant_validos['_mes_num'] <= mes_cambio]

            grp = df_ant_validos.groupby('_mes_num').agg(
                n_s=('tiempo_face_s', 'count'),
                n_sf=('tiempo_face_f', lambda x: x.notna().sum()),
                media_face_s=('tiempo_face_s', 'mean'),
                media_s_f=('tiempo_s_f', 'mean'),
                media_face_f=('tiempo_face_f', 'mean'),
                max_face_f=('tiempo_face_f', 'max'),
            )

            filas_22 = []
            for mes_num in sorted(grp.index):
                r = grp.loc[mes_num]
                nombre = NOMBRES_MESES.get(mes_num, str(mes_num))
                if mes_num == mes_cambio:
                    nombre = f'{nombre} (hasta {fecha_cambio.strftime("%d/%m")})'
                filas_22.append((nombre, [
                    _fmt_int(r['n_s']),
                    _fmt_int(r['n_sf']),
                    _fmt_int(r['n_s'] - r['n_sf']),
                    _fmt_min(r['media_face_s']),
                    _fmt_min(r['media_s_f']),
                    _fmt_min(r['media_face_f']),
                    _fmt_min(r['max_face_f']),
                ]))

            # Fila de totales/medias
            filas_22.append(('Total / Media periodo anterior', [
                _fmt_int(grp['n_s'].sum()),
                _fmt_int(grp['n_sf'].sum()),
                _fmt_int((grp['n_s'] - grp['n_sf']).sum()),
                _fmt_min(df_ant_validos['tiempo_face_s'].mean()),
                _fmt_min(df_ant_validos['tiempo_s_f'].mean()),
                _fmt_min(df_ant_validos['tiempo_face_f'].mean()),
                _fmt_min(df_ant_validos['tiempo_face_f'].max()),
            ]))

            st.markdown(
                _html_tabla(
                    filas_22,
                    cabecera_cols=['Fact. con S', 'Con S y F', 'S sin F',
                                   'Tiempo medio FACe–S', 'Tiempo medio S–F',
                                   'Tiempo medio FACe–F', 'Tiempo máx. FACe–F'],
                    titulo_col_izq='Mes'
                ),
                unsafe_allow_html=True
            )
            st.caption("""
            **FACe–S**: tiempo de descarga o incorporación técnica inicial desde FACe.
            **S–F**: tiempo de permanencia en el estado previo (cuantificación de la incidencia de 2024).
            **FACe–F**: tiempo total hasta la anotación considerada definitiva por la entidad durante el procedimiento anterior.
            """)

            # Gráfico evolución S→F por mes
            fig_ant = go.Figure()
            meses_labels = [NOMBRES_MESES.get(m, str(m)) for m in grp.index]
            fig_ant.add_trace(go.Bar(
                x=meses_labels, y=grp['n_s'], name='Facturas con S',
                marker_color=COLORES.get('advertencia', '#FFC107')
            ))
            fig_ant.add_trace(go.Bar(
                x=meses_labels, y=grp['n_sf'], name='Facturas con S y F',
                marker_color=COLORES.get('primario', '#0066CC')
            ))
            fig_ant.update_layout(
                title='Procedimiento anterior — Facturas con S vs S+F por mes',
                barmode='group', height=350, xaxis_title='Mes', yaxis_title='Nº facturas'
            )
            st.plotly_chart(fig_ant, use_container_width=True)

            # Exportar
            with st.expander("📥 Exportar detalle tiempos procedimiento anterior"):
                cols_exp_ant = [c for c in [
                    'ID_FACE', 'numero_factura', 'nif_emisor', 'importe_total',
                    'fecha_registro_face', 'codigo_s', 'fecha_codigo_s',
                    'codigo_f', 'fecha_codigo_f', 'tiempo_face_s', 'tiempo_s_f',
                    'tiempo_face_f', 'resultado_auditoria_rcf', 'codigo_ut', 'incidencia_temporal'
                ] if c in df_ant_tiempos.columns]
                excel_ant = exportar_a_excel(df_ant_tiempos[cols_exp_ant], 'Tiempos_Procedimiento_Anterior')
                st.download_button("📥 Descargar tiempos S→F completo", data=excel_ant,
                                   file_name='tiempos_procedimiento_anterior_sf.xlsx',
                                   mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

            # Detalle facturas S sin F (requieren revisión individual)
            if n_s_sin_f > 0:
                st.markdown("#### ⚠️ Detalle — Facturas S sin código F (requieren revisión)")
                mask_s_sin_f = df_ant_tiempos['tiempo_face_f'].isna()
                cols_s_sin_f = [c for c in ['ID_FACE', 'numero_factura', 'nif_emisor', 'importe_total',
                                             'fecha_registro_face', 'codigo_s', 'fecha_codigo_s',
                                             'estado', 'codigo_ut'] if c in df_ant_tiempos.columns]
                st.dataframe(df_ant_tiempos[mask_s_sin_f][cols_s_sin_f].head(100), hide_index=True)
                excel_s_sin_f = exportar_a_excel(df_ant_tiempos[mask_s_sin_f][cols_s_sin_f], 'S_sin_F')
                st.download_button("📥 Exportar facturas S sin F", data=excel_s_sin_f,
                                   file_name='facturas_s_sin_f.xlsx',
                                   mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.info("No se han encontrado facturas con procedimiento S→F en los datos cargados.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # TABLA 2.3 — Tiempos procedimiento nuevo (F directo)
    # -----------------------------------------------------------------------
    st.markdown("### 📊 Tabla 2.3 — Tiempos de inscripción: procedimiento corregido (F directo)")
    st.caption(f"Solo facturas anotadas directamente con F, desde el {fecha_cambio.strftime('%d/%m/%Y')}.")

    df_nvo_tiempos = calcular_indicadores_procedimiento_nuevo(df_rcf)

    if not df_nvo_tiempos.empty:
        df_nvo_validos = df_nvo_tiempos[~df_nvo_tiempos['incidencia_temporal']].copy()
        df_nvo_incid = df_nvo_tiempos[df_nvo_tiempos['incidencia_temporal']].copy()

        n_nvo = len(df_nvo_tiempos)
        n_excl_nvo = len(df_nvo_incid)

        st.caption(f"Facturas con F directo: **{n_nvo:,}** | Excluidas por incidencia temporal: **{n_excl_nvo:,}**")
        _alerta('ALERTA_RCF_104', n_excl_nvo > 0,
                f'**{n_excl_nvo}** registros del procedimiento nuevo con fechas negativas o inconsistentes excluidos de las medias.')

        # Métricas principales
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Facturas F directo", f"{n_nvo:,}")
        col_m2.metric("Tiempo medio FACe–F", _fmt_min(df_nvo_validos['tiempo_face_f_directo'].mean()))
        col_m3.metric("Tiempo mediano", _fmt_min(df_nvo_validos['tiempo_face_f_directo'].median()))
        col_m4.metric("Tiempo máximo", _fmt_min(df_nvo_validos['tiempo_face_f_directo'].max()))

        if not df_nvo_validos.empty:
            df_nvo_validos['_mes_num'] = df_nvo_validos['fecha_registro_face'].dt.month
            grp_nvo = df_nvo_validos.groupby('_mes_num').agg(
                n_recibidas=('tiempo_face_f_directo', 'count'),
                media_face_f=('tiempo_face_f_directo', 'mean'),
                max_face_f=('tiempo_face_f_directo', 'max'),
            )

            # Añadir rechazo y S post-cambio por mes
            if 'fecha_registro_face' in df_nuevo.columns:
                df_nuevo['_mes_num'] = df_nuevo['fecha_registro_face'].dt.month
                rechazo_nvo_mes = df_nuevo[df_nuevo['procedimiento_aplicado'] == 'RECHAZO_PREVIO_A_ANOTACION'].groupby('_mes_num').size()
                s_postcambio_mes = df_nuevo[df_nuevo['resultado_auditoria_rcf'] == 'POST_CAMBIO_CON_CODIGO_S'].groupby('_mes_num').size()
            else:
                rechazo_nvo_mes = pd.Series(dtype=int)
                s_postcambio_mes = pd.Series(dtype=int)

            mes_cambio = fecha_cambio.month
            filas_23 = []
            for mes_num in sorted(grp_nvo.index):
                r = grp_nvo.loc[mes_num]
                nombre = NOMBRES_MESES.get(mes_num, str(mes_num))
                if mes_num == mes_cambio:
                    nombre = f'{nombre} (desde {fecha_cambio.strftime("%d/%m")})'
                filas_23.append((nombre, [
                    _fmt_int(r['n_recibidas'] + rechazo_nvo_mes.get(mes_num, 0)),
                    _fmt_int(r['n_recibidas']),
                    _fmt_int(rechazo_nvo_mes.get(mes_num, 0)),
                    _fmt_int(s_postcambio_mes.get(mes_num, 0)),
                    _fmt_min(r['media_face_f']),
                    _fmt_min(r['max_face_f']),
                ]))

            filas_23.append(('Total / Media periodo corregido', [
                _fmt_int(grp_nvo['n_recibidas'].sum() + rechazo_nvo_mes.sum()),
                _fmt_int(grp_nvo['n_recibidas'].sum()),
                _fmt_int(rechazo_nvo_mes.sum()),
                _fmt_int(s_postcambio_mes.sum()),
                _fmt_min(df_nvo_validos['tiempo_face_f_directo'].mean()),
                _fmt_min(df_nvo_validos['tiempo_face_f_directo'].max()),
            ]))

            st.markdown(
                _html_tabla(
                    filas_23,
                    cabecera_cols=['Fact. recibidas FACe', 'Anotadas F directo',
                                   'Rechazadas antes anotación', 'Con S detectadas',
                                   'Tiempo medio FACe–F directo', 'Tiempo máx. FACe–F directo'],
                    titulo_col_izq='Mes'
                ),
                unsafe_allow_html=True
            )
            st.caption("")

            # Gráfico tiempos medios F directo por mes
            fig_nvo = go.Figure()
            meses_nvo = [NOMBRES_MESES.get(m, str(m)) for m in grp_nvo.index]
            fig_nvo.add_trace(go.Scatter(
                x=meses_nvo, y=grp_nvo['media_face_f'],
                mode='lines+markers', name='Tiempo medio FACe–F (min)',
                line=dict(color=COLORES.get('exito', '#28A745'), width=3),
                marker=dict(size=8)
            ))
            fig_nvo.update_layout(
                title='Procedimiento corregido — Tiempo medio FACe–F directo por mes',
                height=350, xaxis_title='Mes', yaxis_title='Tiempo (minutos)'
            )
            st.plotly_chart(fig_nvo, use_container_width=True)

            # Exportar
            with st.expander("📥 Exportar detalle tiempos procedimiento nuevo"):
                cols_exp_nvo = [c for c in [
                    'ID_FACE', 'numero_factura', 'nif_emisor', 'importe_total',
                    'fecha_registro_face', 'codigo_f', 'fecha_codigo_f',
                    'tiempo_face_f_directo', 'resultado_auditoria_rcf', 'codigo_ut', 'incidencia_temporal'
                ] if c in df_nvo_tiempos.columns]
                excel_nvo = exportar_a_excel(df_nvo_tiempos[cols_exp_nvo], 'Tiempos_Procedimiento_Nuevo')
                st.download_button("📥 Descargar tiempos F directo completo", data=excel_nvo,
                                   file_name='tiempos_procedimiento_nuevo_f.xlsx',
                                   mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.info("No se han encontrado facturas con anotación directa F en los datos cargados.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # TABLA 2.4 — Facturas rechazadas antes de anotación
    # -----------------------------------------------------------------------
    st.markdown("### 📋 Tabla 2.4 — Facturas rechazadas antes de anotación (procedimiento nuevo)")

    df_rechazadas = df_nuevo[df_nuevo['procedimiento_aplicado'] == 'RECHAZO_PREVIO_A_ANOTACION'].copy() if not df_nuevo.empty else pd.DataFrame()

    n_rechazadas = len(df_rechazadas)
    n_recibidas_nvo = len(df_nuevo) if not df_nuevo.empty else 0

    if n_rechazadas > 0:
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric("Rechazadas antes de anotación", f"{n_rechazadas:,}")
        col_r2.metric("% sobre recibidas FACe (periodo nuevo)", f"{n_rechazadas/n_recibidas_nvo*100:.1f}%" if n_recibidas_nvo > 0 else '—')
        sin_causa = (df_rechazadas['resultado_auditoria_rcf'] == 'RECHAZADA_SIN_CAUSA_SUFICIENTE').sum()
        col_r3.metric("Sin causa suficiente", f"{sin_causa:,}")

        _alerta('ALERTA_RCF_003', sin_causa > 0,
                f'**{sin_causa}** rechazos sin causa reglamentaria identificable o sin trazabilidad bastante.')

        campo_motivo = next((c for c in ['motivo_rechazo_rcf', 'motivo_rechazo'] if c in df_rechazadas.columns), None)
        if campo_motivo:
            grp_rechazo = df_rechazadas.groupby(campo_motivo).agg(
                n=('resultado_auditoria_rcf', 'count'),
                importe=('importe_total', 'sum') if 'importe_total' in df_rechazadas.columns else ('resultado_auditoria_rcf', 'count')
            ).reset_index()
            grp_rechazo.columns = ['Causa de rechazo', 'Nº facturas', 'Importe total']
            grp_rechazo['% sobre rechazadas'] = (grp_rechazo['Nº facturas'] / n_rechazadas * 100).round(1)
            grp_rechazo['% sobre recibidas FACe'] = (grp_rechazo['Nº facturas'] / n_recibidas_nvo * 100).round(1) if n_recibidas_nvo > 0 else '—'
            grp_rechazo = grp_rechazo.sort_values('Nº facturas', ascending=False)
            st.dataframe(grp_rechazo.style.format({'Importe total': '{:,.2f} €', '% sobre rechazadas': '{:.1f}%', '% sobre recibidas FACe': '{:.1f}%'}), hide_index=True)

        excel_rej = exportar_a_excel(df_rechazadas, 'Rechazos_Previos_Anotacion')
        st.download_button("📥 Exportar rechazos detalle", data=excel_rej,
                           file_name='rechazos_previos_anotacion.xlsx',
                           mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.info("No se han identificado facturas rechazadas antes de anotación en el periodo posterior al cambio.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # TABLA 2.5 — Incidencias de correspondencia y calidad de datos
    # -----------------------------------------------------------------------
    st.markdown("### 📋 Tabla 2.5 — Incidencias de correspondencia FACe–RCF y calidad de datos")

    n_s_postcambio_total = (df_elec.get('resultado_auditoria_rcf', pd.Series(dtype=str)) == 'POST_CAMBIO_CON_CODIGO_S').sum() if not df_elec.empty else 0
    n_sin_causa = (df_elec.get('resultado_auditoria_rcf', pd.Series(dtype=str)) == 'RECHAZADA_SIN_CAUSA_SUFICIENTE').sum() if not df_elec.empty else 0

    n_fechas_negativas_ant = len(df_ant_tiempos[df_ant_tiempos['incidencia_temporal']]) if not df_ant_tiempos.empty and 'incidencia_temporal' in df_ant_tiempos.columns else 0
    n_fechas_negativas_nvo = len(df_nvo_tiempos[df_nvo_tiempos['incidencia_temporal']]) if not df_nvo_tiempos.empty and 'incidencia_temporal' in df_nvo_tiempos.columns else 0
    n_fechas_neg = n_fechas_negativas_ant + n_fechas_negativas_nvo

    filas_25 = [
        ('Facturas FACe sin correspondencia en RCF',
         [_fmt_int(retenidas_count), 'Sí', 'Posible retención o falta de incorporación.']),
        ('Registros posteriores al cambio con código S',
         [_fmt_int(n_s_postcambio_total), 'Sí', 'Posible subsistencia del procedimiento anterior.']),
        ('Rechazos sin causa acreditada',
         [_fmt_int(n_sin_causa), 'Sí', 'Incumplimiento de trazabilidad.']),
        ('Fechas negativas o inconsistentes',
         [_fmt_int(n_fechas_neg), 'Sí', 'Excluidos de medias hasta aclaración.']),
    ]
    st.markdown(
        _html_tabla(
            filas_25,
            cabecera_cols=['Nº registros', 'Revisión individual', 'Observación automática'],
            titulo_col_izq='Tipo de incidencia',
            bold_ultima_fila=False
        ),
        unsafe_allow_html=True
    )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Gráfico comparativo anual: evolución S vs F con línea de corte
    # -----------------------------------------------------------------------
    if tiene_cols_sf and not df_elec.empty and 'fecha_registro_face' in df_elec.columns:
        st.markdown("### 📈 Evolución mensual — Facturas con S y F directas (con hito de cambio)")
        df_elec['_mes_num'] = df_elec['fecha_registro_face'].dt.month
        ev_s = df_elec[df_elec['procedimiento_aplicado'] == 'PROCEDIMIENTO_ANTERIOR_S_F'].groupby('_mes_num').size()
        ev_f = df_elec[df_elec['procedimiento_aplicado'] == 'ANOTACION_DIRECTA_F'].groupby('_mes_num').size()

        todos_meses = list(range(1, 13))
        fig_ev = go.Figure()
        fig_ev.add_trace(go.Bar(
            x=[NOMBRES_MESES[m] for m in todos_meses],
            y=[ev_s.get(m, 0) for m in todos_meses],
            name='Código S (procedimiento anterior)',
            marker_color=COLORES.get('advertencia', '#FFC107')
        ))
        fig_ev.add_trace(go.Bar(
            x=[NOMBRES_MESES[m] for m in todos_meses],
            y=[ev_f.get(m, 0) for m in todos_meses],
            name='F directo (procedimiento nuevo)',
            marker_color=COLORES.get('exito', '#28A745')
        ))
        fig_ev.add_vline(
            x=NOMBRES_MESES[fecha_cambio.month],
            line_dash='dash', line_color='red',
            annotation_text=f'Cambio {fecha_cambio.strftime("%d/%m")}',
            annotation_position='top right'
        )
        fig_ev.update_layout(
            title='Evolución mensual: desaparición del código S y aparición del F directo',
            barmode='stack', height=400,
            xaxis_title='Mes', yaxis_title='Nº facturas'
        )
        st.plotly_chart(fig_ev, use_container_width=True)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Guardar en session_state para el generador de informe
    # -----------------------------------------------------------------------
    if 'analisis' not in st.session_state:
        st.session_state['analisis'] = {}

    # Calcular métricas resumen para el informe
    t_medio_face_s = df_ant_tiempos[~df_ant_tiempos.get('incidencia_temporal', False)]['tiempo_face_s'].mean() if not df_ant_tiempos.empty and 'tiempo_face_s' in df_ant_tiempos.columns else None
    t_medio_s_f = df_ant_tiempos[~df_ant_tiempos.get('incidencia_temporal', False)]['tiempo_s_f'].mean() if not df_ant_tiempos.empty and 'tiempo_s_f' in df_ant_tiempos.columns else None
    t_medio_face_f_ant = df_ant_tiempos[~df_ant_tiempos.get('incidencia_temporal', False)]['tiempo_face_f'].mean() if not df_ant_tiempos.empty and 'tiempo_face_f' in df_ant_tiempos.columns else None
    t_medio_face_f_nvo = df_nvo_tiempos[~df_nvo_tiempos.get('incidencia_temporal', False)]['tiempo_face_f_directo'].mean() if not df_nvo_tiempos.empty and 'tiempo_face_f_directo' in df_nvo_tiempos.columns else None

    df_ant_val = df_ant_tiempos[~df_ant_tiempos['incidencia_temporal']].copy() if not df_ant_tiempos.empty and 'incidencia_temporal' in df_ant_tiempos.columns else pd.DataFrame()
    df_nvo_val = df_nvo_tiempos[~df_nvo_tiempos['incidencia_temporal']].copy() if not df_nvo_tiempos.empty and 'incidencia_temporal' in df_nvo_tiempos.columns else pd.DataFrame()

    st.session_state['analisis']['anotacion'] = {
        # Configuración del análisis
        'fecha_cambio_procedimiento': fecha_cambio.strftime('%d/%m/%Y'),
        'plazo_aceptacion_dias': plazo_dias,
        'tipo_dias_plazo': tipo_dias,
        # Facturas retenidas
        'facturas_retenidas': retenidas_count,
        'df_retenidas': df_retenidas if retenidas_count > 0 else pd.DataFrame(),
        # Procedimiento anterior S→F
        'n_facturas_s': len(df_ant_tiempos) if not df_ant_tiempos.empty else 0,
        'n_facturas_s_con_f': int(df_ant_tiempos['tiempo_face_f'].notna().sum()) if not df_ant_tiempos.empty and 'tiempo_face_f' in df_ant_tiempos.columns else 0,
        'n_facturas_s_sin_f': n_s_sin_f if not df_ant_tiempos.empty else 0,
        'tiempo_medio_face_s_min': t_medio_face_s,
        'tiempo_medio_s_f_min': t_medio_s_f,
        'tiempo_medio_face_f_anterior_min': t_medio_face_f_ant,
        'df_tiempos_anterior': df_ant_val,
        # Procedimiento nuevo F directo
        'n_facturas_f_directo': len(df_nvo_tiempos) if not df_nvo_tiempos.empty else 0,
        'tiempo_medio_face_f_nuevo_min': t_medio_face_f_nvo,
        'df_tiempos_nuevo': df_nvo_val,
        # Rechazos
        'n_rechazadas_nuevo': n_rechazadas,
        'n_rechazadas_sin_causa': int(n_sin_causa),
        # Incidencias
        'n_s_postcambio': int(n_s_postcambio_total),
        'n_fechas_negativas': n_fechas_neg,
        'facturas_retenidas_count': retenidas_count,
        # Claves de compatibilidad con el generador de informe
        'tiempo_medio_min': t_medio_face_f_nvo if t_medio_face_f_nvo else t_medio_face_f_ant,
        'tiempo_mediano_min': df_nvo_val['tiempo_face_f_directo'].median() if not df_nvo_val.empty and 'tiempo_face_f_directo' in df_nvo_val.columns else None,
        'tiempo_max_min': df_nvo_val['tiempo_face_f_directo'].max() if not df_nvo_val.empty and 'tiempo_face_f_directo' in df_nvo_val.columns else None,
        'tiempo_min_min': df_nvo_val['tiempo_face_f_directo'].min() if not df_nvo_val.empty and 'tiempo_face_f_directo' in df_nvo_val.columns else None,
        'num_anomalias': n_fechas_neg,
    }


if __name__ == "__main__":
    main()
