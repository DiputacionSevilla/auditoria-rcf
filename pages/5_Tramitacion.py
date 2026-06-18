"""
Análisis de Tramitación de Facturas - Sección V.4 de la Guía IGAE
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import COLORES, COLORES_GRAFICOS, ESTADOS_FACTURAS, CONFIGURACION_TRANSICION_2025
from utils.data_loader import (
    exportar_a_excel,
    clasificar_procedimiento,
    calcular_indicadores_procedimiento_anterior,
    calcular_indicadores_tramitacion_posterior,
)

st.set_page_config(
    page_title="Tramitación - Auditoría RCF",
    page_icon="🔄",
    layout="wide"
)

def main():
    st.title("🔄 Tramitación de Facturas")
    st.markdown("Análisis de anulaciones, estados y reconocimiento de obligaciones (Sección V.4)")
    
    # Verificar datos
    if 'datos' not in st.session_state:
        st.warning("⚠️ No hay datos cargados. Por favor, carga los archivos en la página principal.")
        if st.button("Ir a página principal"):
            st.switch_page("app.py")
        return
    
    datos = st.session_state['datos']
    df_rcf = datos['rcf'].copy()
    if 'estado' in df_rcf.columns:
        df_rcf = df_rcf[df_rcf['estado'].astype(str).str.upper() != 'BORRADA'].copy()
    df_anulaciones = datos['anulaciones'].copy()
    df_estados = datos['estados'].copy()
    
    st.markdown("---")
    
    # === INFORMACIÓN NORMATIVA ===
    with st.expander("📋 Marco Legal - Tramitación y Anulaciones"):
        st.markdown("""
        **Orden HAP/492/2014:**
        - Gestión de solicitudes de anulación
        - Trazabilidad de estados
        - Registro de comentarios y justificaciones
        
        **Obligaciones:**
        - Toda anulación debe estar justificada
        - Registro del comentario obligatorio
        - Actualización de estado en FACe
        """)
    
    # === ANÁLISIS DE ANULACIONES ===
    st.markdown("### 🗑️ Solicitudes de Anulación")
    
    # Cruzar anulaciones con RCF
    df_anulaciones_rcf = df_anulaciones.merge(
        df_rcf[['ID_FACE', 'numero_factura', 'nif_emisor', 'razon_social', 'importe_total', 'estado']],
        left_on='registro',
        right_on='ID_FACE',
        how='left'
    )
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_anulaciones = len(df_anulaciones)
        st.metric(
            "Total Solicitudes",
            f"{total_anulaciones:,}"
        )
    
    with col2:
        registradas_rcf = len(df_anulaciones_rcf[df_anulaciones_rcf['ID_FACE'].notna()])
        porc_registradas = (registradas_rcf / total_anulaciones * 100) if total_anulaciones > 0 else 0
        st.metric(
            "Registradas en RCF",
            f"{registradas_rcf:,}",
            f"{porc_registradas:.1f}%"
        )
    
    with col3:
        # Asumiendo que existe campo 'comentario' y verificamos si está lleno
        if 'comentario' in df_anulaciones.columns:
            con_comentario = len(df_anulaciones[df_anulaciones['comentario'].notna() & (df_anulaciones['comentario'] != '')])
            porc_comentario = (con_comentario / total_anulaciones * 100) if total_anulaciones > 0 else 0
            st.metric(
                "Con Comentario",
                f"{con_comentario:,}",
                f"{porc_comentario:.1f}%"
            )
    
    with col4:
        anuladas = len(df_anulaciones_rcf[df_anulaciones_rcf['estado'] == 'ANULADA'])
        porc_aceptadas = (anuladas / total_anulaciones * 100) if total_anulaciones > 0 else 0
        st.metric(
            "Anuladas (Aceptadas)",
            f"{anuladas:,}",
            f"{porc_aceptadas:.1f}%"
        )
    
    # Tabla detalle anulaciones
    st.markdown("#### 📋 Detalle de Solicitudes de Anulación")
    
    if len(df_anulaciones_rcf) > 0:
        df_anulaciones_display = df_anulaciones_rcf[[
            'registro', 'numero_factura', 'nif_emisor', 'razon_social',
            'importe_total', 'fecha_solicitud_anulacion', 'estado'
        ]].copy()
        
        df_anulaciones_display.columns = [
            'Registro FACe', 'Nº Factura', 'NIF', 'Razón Social',
            'Importe', 'Fecha Solicitud', 'Estado Actual'
        ]
        
        st.dataframe(
            df_anulaciones_display.style.format({
                'Importe': '{:,.2f} €',
                'Fecha Solicitud': lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
            }).apply(
                lambda x: ['background-color: #d4edda' if v == 'ANULADA' else '' for v in x],
                subset=['Estado Actual']
            ),
            width="stretch",
            hide_index=True
        )
        
        # Exportar anulaciones
        if st.button("📥 Exportar Solicitudes de Anulación"):
            excel_bytes = exportar_a_excel(df_anulaciones_display, "Solicitudes_Anulacion")
            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name="solicitudes_anulacion.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    st.markdown("---")
    
    # === EVOLUCIÓN DE ESTADOS ===
    st.markdown("### 📊 Análisis de Estados de Facturas")
    
    # Distribución actual de estados
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Estado Actual de Facturas")
        
        if 'estado' in df_rcf.columns:
            distribucion_estados = df_rcf['estado'].value_counts()
            
            fig = px.pie(
                values=distribucion_estados.values,
                names=distribucion_estados.index,
                title='Distribución de facturas por estado',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.markdown("#### Top 10 Estados")
        
        df_estados_table = distribucion_estados.head(10).reset_index()
        df_estados_table.columns = ['Estado', 'Cantidad']
        df_estados_table['Porcentaje'] = (df_estados_table['Cantidad'] / len(df_rcf) * 100).round(2)
        
        st.dataframe(
            df_estados_table.style.format({
                'Cantidad': '{:,.0f}',
                'Porcentaje': '{:.2f}%'
            }).background_gradient(subset=['Cantidad'], cmap='Blues'),
            width="stretch",
            hide_index=True
        )
    
    # === ANÁLISIS DE TIEMPOS POR ESTADO ===
    st.markdown("### ⏱️ Tiempos Medios por Estado")
    
    if len(df_estados) > 0:
        # Convertir códigos de estado a nombres (asegurando tipo string y sin decimales)
        df_estados['nombre_estado'] = df_estados['codigo'].astype(str).str.split('.').str[0].map(ESTADOS_FACTURAS).fillna('Desconocido')
        
        # Calcular tiempo desde registro hasta cada estado
        # Agrupamos por registro y código de estado
        df_estados_sorted = df_estados.sort_values(['registro', 'insertado'])
        
        # Obtener primer estado (registro inicial)
        primer_estado = df_estados_sorted.groupby('registro').first().reset_index()
        primer_estado = primer_estado[['registro', 'insertado']].rename(columns={'insertado': 'fecha_registro'})
        
        # Merge con todos los estados
        df_estados_tiempos = df_estados_sorted.merge(primer_estado, on='registro', how='left')
        
        # Calcular tiempo en horas
        df_estados_tiempos['tiempo_horas'] = (
            pd.to_datetime(df_estados_tiempos['insertado']) - 
            pd.to_datetime(df_estados_tiempos['fecha_registro'])
        ).dt.total_seconds() / 3600
        
        # Agrupar por estado
        tiempos_por_estado = df_estados_tiempos.groupby('nombre_estado')['tiempo_horas'].agg([
            'mean', 'median', 'min', 'max', 'count'
        ]).round(2)
        
        tiempos_por_estado.columns = ['Media (h)', 'Mediana (h)', 'Mínimo (h)', 'Máximo (h)', 'Nº Cambios']
        tiempos_por_estado = tiempos_por_estado.sort_values('Media (h)', ascending=False)
        
        # Gráfico de tiempos
        fig = px.bar(
            tiempos_por_estado.reset_index().head(10),
            x='Media (h)',
            y='nombre_estado',
            orientation='h',
            title='Tiempo medio desde registro hasta cada estado (Top 10)',
            color='Media (h)',
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            yaxis_title='Estado',
            xaxis_title='Tiempo medio (horas)',
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, width="stretch")
        
        # Tabla de tiempos
        st.markdown("#### 📊 Tabla Detallada de Tiempos")
        
        st.dataframe(
            tiempos_por_estado.style.format({
                'Media (h)': '{:.2f}',
                'Mediana (h)': '{:.2f}',
                'Mínimo (h)': '{:.2f}',
                'Máximo (h)': '{:.2f}',
                'Nº Cambios': '{:,.0f}'
            }).background_gradient(subset=['Media (h)'], cmap='YlOrRd'),
            width="stretch"
        )
        
        # Exportar tiempos
        if st.button("📥 Exportar Análisis de Tiempos"):
            excel_bytes = exportar_a_excel(
                tiempos_por_estado.reset_index(),
                "Tiempos_Por_Estado"
            )
            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name="tiempos_por_estado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    st.markdown("---")
    
    # === FLUJO DE ESTADOS (DIAGRAMA SANKEY) ===
    st.markdown("### 🔀 Flujo de Estados")
    st.info("Secuencias más frecuentes de cambios de estado")
    
    if len(df_estados) > 0:
        # Detectar retrocesos de estado: cuando una factura vuelve a un código de
        # estado anterior al máximo ya alcanzado (típico de una modificación en el RCF)
        df_estados_sorted['codigo_num'] = pd.to_numeric(
            df_estados_sorted['codigo'].astype(str).str.split('.').str[0], errors='coerce'
        )
        df_estados_sorted['cummax_codigo'] = df_estados_sorted.groupby('registro')['codigo_num'].cummax()
        df_estados_sorted['max_previo'] = df_estados_sorted.groupby('registro')['cummax_codigo'].shift(1)

        # Fecha en la que se alcanzó ese máximo previo (para medir la cercanía temporal)
        df_estados_sorted['tiempo_max_codigo'] = df_estados_sorted['insertado'].where(
            df_estados_sorted['codigo_num'] == df_estados_sorted['cummax_codigo']
        )
        df_estados_sorted['tiempo_max_codigo'] = df_estados_sorted.groupby('registro')['tiempo_max_codigo'].ffill()
        df_estados_sorted['tiempo_max_previo'] = df_estados_sorted.groupby('registro')['tiempo_max_codigo'].shift(1)
        diff_segundos = (df_estados_sorted['insertado'] - df_estados_sorted['tiempo_max_previo']).dt.total_seconds()

        es_retroceso_bruto = df_estados_sorted['codigo_num'] < df_estados_sorted['max_previo']

        # 2100 (Recibida en destino) y 1400 (Verificada en RCF) se generan de forma
        # prácticamente simultánea: si la diferencia es de 10 segundos o menos se
        # ignora como retroceso real (es un artefacto de orden de inserción)
        es_caso_simultaneo_2100_1400 = (
            (df_estados_sorted['max_previo'] == 2100) &
            (df_estados_sorted['codigo_num'] == 1400) &
            (diff_segundos <= 10)
        ).fillna(False)

        df_estados_sorted['es_retroceso'] = es_retroceso_bruto & ~es_caso_simultaneo_2100_1400

        n_facturas_con_retroceso = df_estados_sorted.loc[df_estados_sorted['es_retroceso'], 'registro'].nunique()
        n_retrocesos_total = int(df_estados_sorted['es_retroceso'].sum())
        n_facturas_total_estados = df_estados_sorted['registro'].nunique()
        porc_retroceso = (n_facturas_con_retroceso / n_facturas_total_estados * 100) if n_facturas_total_estados else 0

        st.metric(
            "🔁 Facturas con retroceso de estado",
            f"{n_facturas_con_retroceso:,}",
            f"{porc_retroceso:.1f}% del total"
        )
        st.caption(
            f"Se han depurado {n_retrocesos_total:,} cambio(s) de estado que suponían un retroceso "
            "(la factura volvió a un estado anterior al máximo ya alcanzado, típicamente por una "
            "modificación en el RCF) antes de calcular la secuencia de tramitación. El par "
            "2100→1400 (Recibida en destino / Verificada en RCF) se genera de forma prácticamente "
            "simultánea y no se cuenta como retroceso cuando la diferencia es de 10 segundos o menos."
        )

        # Obtener secuencias de estados por factura, descartando los retrocesos y
        # colapsando repeticiones consecutivas para que el flujo sea coherente
        df_estados_limpio = df_estados_sorted[~df_estados_sorted['es_retroceso']]

        def _dedupe_consecutivos(lista):
            resultado = []
            for estado in lista:
                if not resultado or resultado[-1] != estado:
                    resultado.append(estado)
            return resultado

        df_estados_seq = df_estados_limpio.groupby('registro')['nombre_estado'].apply(list).reset_index()
        df_estados_seq['nombre_estado'] = df_estados_seq['nombre_estado'].apply(_dedupe_consecutivos)
        df_estados_seq['secuencia'] = df_estados_seq['nombre_estado'].apply(lambda x: ' → '.join(x))

        # Top 10 secuencias
        conteo_secuencias = df_estados_seq['secuencia'].value_counts()
        top_secuencias = conteo_secuencias.head(10)

        df_secuencias_display = top_secuencias.reset_index()
        df_secuencias_display.columns = ['Secuencia de Estados', 'Cantidad de Facturas']

        # Agrupar el resto de secuencias (menos frecuentes) en una fila "Otras"
        resto_facturas = len(df_estados_seq) - df_secuencias_display['Cantidad de Facturas'].sum()
        if resto_facturas > 0:
            otras_secuencias = len(conteo_secuencias) - len(top_secuencias)
            df_secuencias_display.loc[len(df_secuencias_display)] = [
                f'Otras secuencias ({otras_secuencias} distintas)', resto_facturas
            ]

        df_secuencias_display['Porcentaje'] = (
            df_secuencias_display['Cantidad de Facturas'] / len(df_estados_seq) * 100
        ).round(2)
        
        st.dataframe(
            df_secuencias_display.style.format({
                'Cantidad de Facturas': '{:,.0f}',
                'Porcentaje': '{:.2f}%'
            }).background_gradient(subset=['Cantidad de Facturas'], cmap='Greens'),
            width="stretch",
            hide_index=True
        )

        # Detalle de los retrocesos detectados, para revisión individual
        if n_facturas_con_retroceso > 0:
            with st.expander(f"🔁 Detalle de retrocesos de estado ({n_retrocesos_total} cambios en {n_facturas_con_retroceso} facturas)"):
                df_retrocesos_detalle = df_estados_sorted.loc[
                    df_estados_sorted['es_retroceso'],
                    ['registro', 'insertado', 'codigo', 'nombre_estado', 'max_previo']
                ].copy()
                df_retrocesos_detalle.columns = [
                    'Registro FACe', 'Fecha cambio', 'Código estado', 'Estado', 'Código máximo previo'
                ]
                st.dataframe(df_retrocesos_detalle, width="stretch", hide_index=True)

                excel_retrocesos = exportar_a_excel(df_retrocesos_detalle, 'Retrocesos_Estado')
                st.download_button(
                    "📥 Exportar retrocesos de estado",
                    data=excel_retrocesos,
                    file_name='retrocesos_estado.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

    st.markdown("---")

    # === RECONOCIMIENTO DE OBLIGACIÓN Y PAGO ===
    st.markdown("### 💰 Reconocimiento de Obligación y Pagos")
    
    # Facturas pagadas
    facturas_pagadas = df_rcf[df_rcf['estado'] == 'PAGADA'].copy() if 'estado' in df_rcf.columns else pd.DataFrame()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_pagadas = len(facturas_pagadas)
        st.metric(
            "Facturas Pagadas",
            f"{total_pagadas:,}"
        )
    
    with col2:
        if len(facturas_pagadas) > 0 and 'importe_total' in facturas_pagadas.columns:
            importe_pagado = facturas_pagadas['importe_total'].sum()
            st.metric(
                "Importe Total Pagado",
                f"{importe_pagado:,.0f} €"
            )
    
    with col3:
        # Facturas contabilizadas (reconocimiento de obligación)
        facturas_contabilizadas = df_rcf[df_rcf['estado'] == 'CONTABILIZADA'].copy() if 'estado' in df_rcf.columns else pd.DataFrame()
        st.metric(
            "Reconocimiento Obligación",
            f"{len(facturas_contabilizadas):,}"
        )
    
    # Análisis de pagos directos vs pagos a justificar
    st.markdown("#### 📊 Análisis por Tipo de Pago")
    
    # Nota: Este análisis requiere campos específicos que pueden no estar
    # Lo dejamos como ejemplo de lo que se debería hacer
    
    st.info("""
    **Nota**: El análisis detallado de tipos de pago (directo vs. a justificar) requiere campos adicionales:
    - tipo_pago
    - numero_libramiento
    - fecha_pago
    
    Si estos campos están disponibles en tus datos, el análisis mostrará:
    - Pagos directos sin reconocimiento de obligación previo
    - Pagos a justificar sin número de libramiento
    - Pagos a justificar sin fecha de pago
    """)
    
    # Si existen los campos, hacer el análisis
    if 'tipo_pago' in df_rcf.columns:
        tipo_pago_dist = df_rcf['tipo_pago'].value_counts()
        
        fig = px.pie(
            values=tipo_pago_dist.values,
            names=tipo_pago_dist.index,
            title='Distribución por tipo de pago',
            hole=0.4
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")
    
    st.markdown("---")

    # =========================================================================
    # APARTADO 4 — Análisis de tramitación diferenciado por régimen (2025)
    # =========================================================================
    st.markdown("## 🔄 Apartado 4 — Tramitación según régimen 2025")
    st.markdown("""
    El ejercicio 2025 requiere analizar los tiempos de tramitación distinguiendo dos periodos,
    ya que el significado del intervalo medido es diferente en cada uno:

    - **Procedimiento anterior** (hasta el cambio): la actuación del área gestora condicionaba
      la generación del identificador F considerado definitivo. El tiempo S→F no es únicamente
      demora de tramitación ordinaria.
    - **Procedimiento nuevo** (desde el cambio): las facturas ya están anotadas en el RCF con F
      antes de que actúe la unidad tramitadora. El tiempo F→aceptación es tramitación posterior.
    """)

    # Obtener fecha de cambio
    fecha_cambio_cfg = CONFIGURACION_TRANSICION_2025.get('fecha_efectiva_cambio_procedimiento')
    fecha_cambio_t4 = pd.Timestamp(fecha_cambio_cfg) if fecha_cambio_cfg else None
    plazo_dias_t4 = CONFIGURACION_TRANSICION_2025.get('plazo_aceptacion_areas_dias', 2)

    # Leer la fecha configurada en la sesión si el auditor la modificó en la página 3
    if 'analisis' in st.session_state and 'anotacion' in st.session_state['analisis']:
        fecha_cambio_sesion = st.session_state['analisis']['anotacion'].get('fecha_cambio_procedimiento')
        if fecha_cambio_sesion:
            try:
                fecha_cambio_t4 = pd.Timestamp(fecha_cambio_sesion, dayfirst=True)
            except Exception:
                pass
        plazo_dias_t4 = st.session_state['analisis']['anotacion'].get('plazo_aceptacion_dias', plazo_dias_t4)

    if fecha_cambio_t4:
        st.info(f"Fecha efectiva del cambio de procedimiento: **{fecha_cambio_t4.strftime('%d/%m/%Y')}** | Plazo referencia: **{plazo_dias_t4} días**")
    else:
        st.warning("⚠️ Fecha de cambio de procedimiento no configurada. Ve a la página **Anotación RCF** para establecerla.")

    # Clasificar facturas por procedimiento
    df_rcf_clas = clasificar_procedimiento(df_rcf, fecha_cambio_t4)

    # -------------------------------------------------------------------------
    # Sub-sección: Procedimiento anterior S→F (Tablas 4.1 – 4.3)
    # -------------------------------------------------------------------------
    st.markdown("### 📊 Procedimiento anterior — Permanencia en estado previo S→F")
    st.caption("Facturas tratadas mediante código S antes del cambio de procedimiento.")

    df_tiempos_sf = calcular_indicadores_procedimiento_anterior(df_rcf_clas)

    if not df_tiempos_sf.empty:
        df_sf_val = df_tiempos_sf[~df_tiempos_sf['incidencia_temporal']].copy()
        df_sf_incid = df_tiempos_sf[df_tiempos_sf['incidencia_temporal']].copy()

        n_s_total = len(df_tiempos_sf)
        n_s_con_f = df_tiempos_sf['tiempo_face_f'].notna().sum()
        n_s_sin_f = n_s_total - n_s_con_f

        # Métricas
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Facturas con S", f"{n_s_total:,}")
        col_b.metric("Obtuvieron F", f"{n_s_con_f:,}")
        col_c.metric("Sin F al cierre", f"{n_s_sin_f:,}", delta=f"{n_s_sin_f}" if n_s_sin_f else None, delta_color="inverse" if n_s_sin_f else "off")
        if not df_sf_val.empty and 'tiempo_s_f' in df_sf_val.columns:
            t_med_sf = df_sf_val['tiempo_s_f'].mean()
            unidad = 'min' if t_med_sf < 1440 else 'd'
            val_str = f'{t_med_sf:.0f} {unidad}' if unidad == 'min' else f'{t_med_sf/1440:.1f} d'
            col_d.metric("Tiempo medio S–F", val_str)

        # Tabla 4.1 por mes
        st.markdown("#### Tabla 4.1 — Tiempo S→F por mes")
        if not df_sf_val.empty and 'tiempo_s_f' in df_sf_val.columns:
            df_sf_val['_mes_num'] = df_sf_val['fecha_registro_face'].dt.month
            grp_sf = df_sf_val.groupby('_mes_num').agg(
                n_s=('tiempo_s_f', 'count'),
                n_con_f=('tiempo_face_f', lambda x: x.notna().sum()),
                media_sf=('tiempo_s_f', 'mean'),
                mediana_sf=('tiempo_s_f', 'median'),
                max_sf=('tiempo_s_f', 'max'),
            )
            # Facturas fuera de plazo (S→F > plazo_dias * 1440 min)
            plazo_min = plazo_dias_t4 * 1440
            grp_sf['fuera_plazo'] = df_sf_val[df_sf_val['tiempo_s_f'] > plazo_min].groupby('_mes_num').size()
            grp_sf['fuera_plazo'] = grp_sf['fuera_plazo'].fillna(0).astype(int)

            NOMBRES_MESES_T = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
                               7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}

            filas_41 = []
            for mes_num in sorted(grp_sf.index):
                r = grp_sf.loc[mes_num]
                nombre = NOMBRES_MESES_T.get(mes_num, str(mes_num))
                if fecha_cambio_t4 and mes_num == fecha_cambio_t4.month:
                    nombre = f'{nombre} (hasta {fecha_cambio_t4.strftime("%d/%m")})'
                filas_41.append((nombre, [
                    f'{int(r["n_s"]):,}',
                    f'{int(r["n_con_f"]):,}',
                    f'{int(r["n_s"] - r["n_con_f"]):,}',
                    f'{r["media_sf"]/1440:.1f} d' if r["media_sf"] >= 1440 else f'{r["media_sf"]:.0f} min',
                    f'{r["mediana_sf"]/1440:.1f} d' if r["mediana_sf"] >= 1440 else f'{r["mediana_sf"]:.0f} min',
                    f'{r["max_sf"]/1440:.1f} d' if r["max_sf"] >= 1440 else f'{r["max_sf"]:.0f} min',
                    f'{int(r["fuera_plazo"]):,}',
                ]))

            filas_41.append(('Total / Media periodo', [
                f'{int(grp_sf["n_s"].sum()):,}',
                f'{int(grp_sf["n_con_f"].sum()):,}',
                f'{int((grp_sf["n_s"] - grp_sf["n_con_f"]).sum()):,}',
                f'{df_sf_val["tiempo_s_f"].mean()/1440:.1f} d' if df_sf_val["tiempo_s_f"].mean() >= 1440 else f'{df_sf_val["tiempo_s_f"].mean():.0f} min',
                f'{df_sf_val["tiempo_s_f"].median()/1440:.1f} d' if df_sf_val["tiempo_s_f"].median() >= 1440 else f'{df_sf_val["tiempo_s_f"].median():.0f} min',
                f'{df_sf_val["tiempo_s_f"].max()/1440:.1f} d' if df_sf_val["tiempo_s_f"].max() >= 1440 else f'{df_sf_val["tiempo_s_f"].max():.0f} min',
                f'{int(grp_sf["fuera_plazo"].sum()):,}',
            ]))

            # Renderizar tabla HTML
            th = 'background:#1f4e79;color:white;padding:6px 9px;border:1px solid #555;text-align:center;white-space:nowrap;font-size:12px;'
            th_l = 'background:#1f4e79;color:white;padding:6px 12px;border:1px solid #555;text-align:left;min-width:160px;font-size:12px;'
            td = 'padding:5px 9px;border:1px solid #ccc;text-align:center;font-size:12px;'
            td_l = 'padding:5px 12px;border:1px solid #ccc;text-align:left;font-size:12px;'
            cab = ['Fact. con S','Con F','Sin F','Media S–F','Mediana S–F','Máx. S–F',f'Fuera {plazo_dias_t4}d']
            thead_html = f'<thead><tr><th style="{th_l}">Mes</th>' + ''.join(f'<th style="{th}">{c}</th>' for c in cab) + '</tr></thead>'
            rows_html = ''
            for i, (lbl, vals) in enumerate(filas_41):
                is_last = i == len(filas_41) - 1
                bg = 'background:#dce6f1;font-weight:bold;' if is_last else ('background:#f5f9ff;' if i % 2 == 0 else '')
                rows_html += f'<tr><td style="{td_l}{bg}">{lbl}</td>' + ''.join(f'<td style="{td}{bg}">{v}</td>' for v in vals) + '</tr>'
            st.markdown(f'<table style="border-collapse:collapse;width:100%;">{thead_html}<tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)
            st.caption("")

            # Tabla 4.2 — Por unidad tramitadora
            st.markdown("#### Tabla 4.2 — Permanencia S→F por unidad tramitadora")
            if 'codigo_ut' in df_sf_val.columns:
                grp_ut_sf = df_sf_val.groupby('codigo_ut').agg(
                    n_s=('tiempo_s_f', 'count'),
                    n_con_f=('tiempo_face_f', lambda x: x.notna().sum()),
                    media_sf=('tiempo_s_f', 'mean'),
                    max_sf=('tiempo_s_f', 'max'),
                ).reset_index()
                grp_ut_sf.columns = ['Código UT', 'Fact. con S', 'Con S y F', 'Tiempo medio S–F', 'Tiempo máx. S–F']
                fuera_ut = df_sf_val[df_sf_val['tiempo_s_f'] > plazo_min].groupby('codigo_ut').size().reset_index()
                fuera_ut.columns = ['Código UT', 'Fuera de plazo']
                grp_ut_sf = grp_ut_sf.merge(fuera_ut, on='Código UT', how='left').fillna(0)
                grp_ut_sf['% fuera plazo'] = (grp_ut_sf['Fuera de plazo'] / grp_ut_sf['Fact. con S'] * 100).round(1)
                grp_ut_sf['Sin F'] = grp_ut_sf['Fact. con S'] - grp_ut_sf['Con S y F']
                grp_ut_sf = grp_ut_sf[['Código UT', 'Fact. con S', 'Con S y F', 'Sin F', 'Tiempo medio S–F', 'Tiempo máx. S–F', 'Fuera de plazo', '% fuera plazo']]
                grp_ut_sf = grp_ut_sf.sort_values('Tiempo medio S–F', ascending=False)
                st.dataframe(
                    grp_ut_sf.style.format({
                        'Tiempo medio S–F': lambda x: f'{x/1440:.1f} d' if x >= 1440 else f'{x:.0f} min',
                        'Tiempo máx. S–F': lambda x: f'{x/1440:.1f} d' if x >= 1440 else f'{x:.0f} min',
                        'Fuera de plazo': '{:.0f}',
                        '% fuera plazo': '{:.1f}%',
                    }).background_gradient(subset=['Tiempo medio S–F'], cmap='Reds'),
                    hide_index=True
                )

            # Gráfico S→F por UT
            if 'codigo_ut' in df_sf_val.columns:
                fig_ut_sf = px.bar(
                    grp_ut_sf.head(15),
                    x='Código UT', y='Tiempo medio S–F',
                    title='Tiempo medio S→F por unidad tramitadora (procedimiento anterior)',
                    color='% fuera plazo',
                    color_continuous_scale='Reds',
                    labels={'Tiempo medio S–F': 'Tiempo medio (min)'}
                )
                fig_ut_sf.update_layout(height=350)
                st.plotly_chart(fig_ut_sf, use_container_width=True)

            # Tabla 4.3 — Detalle facturas que requieren revisión
            st.markdown("#### Tabla 4.3 — Facturas del procedimiento anterior que requieren revisión individual")
            mask_revision = (
                df_tiempos_sf['tiempo_face_f'].isna() |
                (df_tiempos_sf.get('tiempo_s_f', pd.Series(dtype=float)) > plazo_min) |
                df_tiempos_sf['incidencia_temporal']
            )
            df_revision_43 = df_tiempos_sf[mask_revision].copy()
            if not df_revision_43.empty:
                def _motivo_revision(row):
                    motivos = []
                    if pd.isna(row.get('tiempo_face_f')):
                        motivos.append('S sin F')
                    if not pd.isna(row.get('tiempo_s_f')) and row.get('tiempo_s_f', 0) > plazo_min:
                        motivos.append('Supera plazo S–F')
                    if row.get('incidencia_temporal', False):
                        motivos.append('Fecha inconsistente')
                    return ' | '.join(motivos) if motivos else 'Revisar'
                df_revision_43['Motivo revisión'] = df_revision_43.apply(_motivo_revision, axis=1)
                cols_43 = [c for c in ['ID_FACE', 'numero_factura', 'nif_emisor', 'importe_total',
                                        'codigo_ut', 'fecha_registro_face', 'codigo_s', 'fecha_codigo_s',
                                        'codigo_f', 'fecha_codigo_f', 'tiempo_s_f', 'estado',
                                        'Motivo revisión'] if c in df_revision_43.columns]
                st.dataframe(df_revision_43[cols_43].head(100), hide_index=True)
                excel_rev = exportar_a_excel(df_revision_43[cols_43], 'Revision_Procedimiento_Anterior')
                st.download_button("📥 Exportar facturas para revisión", data=excel_rev,
                                   file_name='facturas_revision_procedimiento_anterior.xlsx',
                                   mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.info("No se han identificado facturas con procedimiento S→F en los datos cargados.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Sub-sección: Procedimiento nuevo F→aceptación (Tablas 4.4 – 4.6)
    # -------------------------------------------------------------------------
    st.markdown("### 📊 Procedimiento nuevo — Tramitación posterior de facturas ya anotadas (F→aceptación)")
    fecha_desde = fecha_cambio_t4.strftime('%d/%m/%Y') if fecha_cambio_t4 else 'fecha del cambio'
    st.caption(f"Facturas anotadas directamente con F desde el {fecha_desde}. Este indicador refleja tramitación posterior, NO tiempo de inscripción en el RCF.")

    df_tiempos_fp = calcular_indicadores_tramitacion_posterior(df_rcf_clas)

    if not df_tiempos_fp.empty:
        df_fp_val = df_tiempos_fp[~df_tiempos_fp['incidencia_temporal']].copy()

        n_f_total = len(df_tiempos_fp)
        n_f_aceptadas = df_tiempos_fp['fecha_tramitacion'].notna().sum() if 'fecha_tramitacion' in df_tiempos_fp.columns else 0
        n_f_pendientes = n_f_total - n_f_aceptadas

        # Métricas
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        col_p1.metric("Facturas F directo", f"{n_f_total:,}")
        col_p2.metric("Aceptadas / conformadas", f"{n_f_aceptadas:,}")
        col_p3.metric("Pendientes a fecha extracción", f"{n_f_pendientes:,}",
                      delta=str(n_f_pendientes) if n_f_pendientes else None, delta_color="inverse" if n_f_pendientes else "off")
        if not df_fp_val.empty and 'tiempo_f_aceptacion' in df_fp_val.columns:
            t_med_fp = df_fp_val['tiempo_f_aceptacion'].mean()
            col_p4.metric("Tiempo medio F→aceptación", f'{t_med_fp/1440:.1f} d' if t_med_fp >= 1440 else f'{t_med_fp:.0f} min')

        # Tabla 4.4 por mes
        st.markdown("#### Tabla 4.4 — Tramitación posterior F→aceptación por mes")
        if not df_fp_val.empty and 'tiempo_f_aceptacion' in df_fp_val.columns:
            df_fp_val['_mes_num'] = df_fp_val['fecha_codigo_f'].dt.month if 'fecha_codigo_f' in df_fp_val.columns else df_fp_val['fecha_tramitacion'].dt.month
            plazo_min_fp = plazo_dias_t4 * 1440
            grp_fp = df_fp_val.groupby('_mes_num').agg(
                n_anotadas=('tiempo_f_aceptacion', 'count'),
                n_aceptadas=('fecha_tramitacion', lambda x: x.notna().sum()),
                media_fp=('tiempo_f_aceptacion', 'mean'),
                mediana_fp=('tiempo_f_aceptacion', 'median'),
                max_fp=('tiempo_f_aceptacion', 'max'),
            )
            grp_fp['fuera_plazo'] = df_fp_val[df_fp_val['tiempo_f_aceptacion'] > plazo_min_fp].groupby('_mes_num').size()
            grp_fp['fuera_plazo'] = grp_fp['fuera_plazo'].fillna(0).astype(int)

            # Pendientes por mes
            if 'fecha_tramitacion' in df_tiempos_fp.columns:
                df_tiempos_fp['_mes_num'] = df_tiempos_fp['fecha_codigo_f'].dt.month if 'fecha_codigo_f' in df_tiempos_fp.columns else pd.NaT
                pendientes_mes = df_tiempos_fp[df_tiempos_fp['fecha_tramitacion'].isna()].groupby('_mes_num').size()
            else:
                pendientes_mes = pd.Series(dtype=int)

            NOMBRES_MESES_T4 = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
                                 7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
            mes_cambio_num = fecha_cambio_t4.month if fecha_cambio_t4 else 1

            filas_44 = []
            for mes_num in sorted(grp_fp.index):
                r = grp_fp.loc[mes_num]
                nombre = NOMBRES_MESES_T4.get(mes_num, str(mes_num))
                if mes_num == mes_cambio_num:
                    nombre = f'{nombre} (desde {fecha_cambio_t4.strftime("%d/%m") if fecha_cambio_t4 else ""})'
                def _fmt(v): return f'{v/1440:.1f} d' if v >= 1440 else f'{v:.0f} min'
                filas_44.append((nombre, [
                    f'{int(r["n_anotadas"]):,}',
                    f'{int(r["n_aceptadas"]):,}',
                    f'{int(pendientes_mes.get(mes_num, 0)):,}',
                    _fmt(r['media_fp']),
                    _fmt(r['mediana_fp']),
                    _fmt(r['max_fp']),
                    f'{int(r["fuera_plazo"]):,}',
                ]))

            def _fmt_t(v): return f'{v/1440:.1f} d' if v >= 1440 else f'{v:.0f} min'
            filas_44.append(('Total / Media periodo corregido', [
                f'{int(grp_fp["n_anotadas"].sum()):,}',
                f'{int(grp_fp["n_aceptadas"].sum()):,}',
                f'{int(pendientes_mes.sum()):,}',
                _fmt_t(df_fp_val['tiempo_f_aceptacion'].mean()),
                _fmt_t(df_fp_val['tiempo_f_aceptacion'].median()),
                _fmt_t(df_fp_val['tiempo_f_aceptacion'].max()),
                f'{int(grp_fp["fuera_plazo"].sum()):,}',
            ]))

            # HTML tabla
            th2 = 'background:#1f4e79;color:white;padding:6px 9px;border:1px solid #555;text-align:center;white-space:nowrap;font-size:12px;'
            th2_l = 'background:#1f4e79;color:white;padding:6px 12px;border:1px solid #555;text-align:left;min-width:160px;font-size:12px;'
            td2 = 'padding:5px 9px;border:1px solid #ccc;text-align:center;font-size:12px;'
            td2_l = 'padding:5px 12px;border:1px solid #ccc;text-align:left;font-size:12px;'
            cab44 = ['Anotadas F','Aceptadas/Conformadas','Pendientes',
                     'Media F–acept.','Mediana','Máx.',f'Fuera {plazo_dias_t4}d']
            thead44 = f'<thead><tr><th style="{th2_l}">Mes</th>' + ''.join(f'<th style="{th2}">{c}</th>' for c in cab44) + '</tr></thead>'
            rows44 = ''
            for i, (lbl, vals) in enumerate(filas_44):
                is_last = i == len(filas_44) - 1
                bg = 'background:#dce6f1;font-weight:bold;' if is_last else ('background:#f5f9ff;' if i % 2 == 0 else '')
                rows44 += f'<tr><td style="{td2_l}{bg}">{lbl}</td>' + ''.join(f'<td style="{td2}{bg}">{v}</td>' for v in vals) + '</tr>'
            st.markdown(f'<table style="border-collapse:collapse;width:100%;">{thead44}<tbody>{rows44}</tbody></table>', unsafe_allow_html=True)
            st.caption(f"**Nota:** este indicador mide la tramitación posterior a la anotación en el RCF. No debe denominarse tiempo de inscripción.")

            # Tabla 4.5 — Por UT
            st.markdown("#### Tabla 4.5 — Tramitación posterior por unidad tramitadora")
            if 'codigo_ut' in df_fp_val.columns:
                grp_ut_fp = df_fp_val.groupby('codigo_ut').agg(
                    n_f=('tiempo_f_aceptacion', 'count'),
                    n_aceptadas=('fecha_tramitacion', lambda x: x.notna().sum()),
                    media_fp=('tiempo_f_aceptacion', 'mean'),
                    max_fp=('tiempo_f_aceptacion', 'max'),
                ).reset_index()
                grp_ut_fp.columns = ['Código UT', 'Fact. F anotadas', 'Aceptadas/Conform.', 'Tiempo medio F–acept.', 'Tiempo máx.']
                fuera_ut_fp = df_fp_val[df_fp_val['tiempo_f_aceptacion'] > plazo_min_fp].groupby('codigo_ut').size().reset_index()
                fuera_ut_fp.columns = ['Código UT', 'Fuera de plazo']
                grp_ut_fp = grp_ut_fp.merge(fuera_ut_fp, on='Código UT', how='left').fillna(0)
                grp_ut_fp['% fuera plazo'] = (grp_ut_fp['Fuera de plazo'] / grp_ut_fp['Fact. F anotadas'] * 100).round(1)
                grp_ut_fp['Pendientes'] = grp_ut_fp['Fact. F anotadas'] - grp_ut_fp['Aceptadas/Conform.']
                grp_ut_fp = grp_ut_fp.sort_values('Tiempo medio F–acept.', ascending=False)

                st.dataframe(
                    grp_ut_fp.style.format({
                        'Tiempo medio F–acept.': lambda x: f'{x/1440:.1f} d' if x >= 1440 else f'{x:.0f} min',
                        'Tiempo máx.': lambda x: f'{x/1440:.1f} d' if x >= 1440 else f'{x:.0f} min',
                        'Fuera de plazo': '{:.0f}',
                        '% fuera plazo': '{:.1f}%',
                    }).background_gradient(subset=['Tiempo medio F–acept.'], cmap='Oranges'),
                    hide_index=True
                )

                fig_ut_fp = px.bar(
                    grp_ut_fp.head(15),
                    x='Código UT', y='Tiempo medio F–acept.',
                    title='Tiempo medio F→aceptación por unidad tramitadora (procedimiento nuevo)',
                    color='% fuera plazo',
                    color_continuous_scale='Oranges',
                )
                fig_ut_fp.update_layout(height=350)
                st.plotly_chart(fig_ut_fp, use_container_width=True)

            # Tabla 4.6 — Detalle demorados
            st.markdown("#### Tabla 4.6 — Facturas del procedimiento nuevo con tramitación demorada")
            if not df_fp_val.empty and 'tiempo_f_aceptacion' in df_fp_val.columns:
                df_demoradas = df_fp_val[df_fp_val['tiempo_f_aceptacion'] > plazo_min_fp].copy()
                if not df_demoradas.empty:
                    cols_46 = [c for c in ['ID_FACE', 'codigo_f', 'numero_factura', 'nif_emisor', 'importe_total',
                                            'codigo_ut', 'fecha_codigo_f', 'fecha_tramitacion',
                                            'tiempo_f_aceptacion', 'estado'] if c in df_demoradas.columns]
                    st.dataframe(df_demoradas[cols_46].head(100), hide_index=True)
                    excel_dem = exportar_a_excel(df_demoradas[cols_46], 'Facturas_Demoradas_Nuevo')
                    st.download_button("📥 Exportar facturas demoradas", data=excel_dem,
                                       file_name='facturas_demoradas_procedimiento_nuevo.xlsx',
                                       mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                else:
                    st.success(f"✅ Ninguna factura supera el plazo de referencia de {plazo_dias_t4} días en el procedimiento nuevo.")

            # Exportar detalle completo F→aceptación
            with st.expander("📥 Exportar detalle completo tramitación posterior"):
                cols_exp_fp = [c for c in ['ID_FACE', 'numero_factura', 'nif_emisor', 'importe_total',
                                            'codigo_f', 'fecha_codigo_f', 'fecha_tramitacion',
                                            'tiempo_f_aceptacion', 'resultado_auditoria_rcf',
                                            'codigo_ut', 'incidencia_temporal'] if c in df_tiempos_fp.columns]
                excel_fp = exportar_a_excel(df_tiempos_fp[cols_exp_fp], 'Tramitacion_Posterior_F')
                st.download_button("📥 Descargar tramitación posterior completa", data=excel_fp,
                                   file_name='tramitacion_posterior_f_aceptacion.xlsx',
                                   mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.info("No se han encontrado facturas con anotación directa F para el análisis de tramitación posterior.")

    st.markdown("---")

    # === EXPORTACIÓN ===
    st.markdown("### 📁 Exportación de Datos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Exportar Facturas Pagadas", width="stretch"):
            if len(facturas_pagadas) > 0:
                excel_bytes = exportar_a_excel(facturas_pagadas, "Facturas_Pagadas")
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="facturas_pagadas.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col2:
        if st.button("📥 Exportar Distribución Estados", width="stretch"):
            if 'estado' in df_rcf.columns:
                excel_bytes = exportar_a_excel(df_estados_table, "Distribucion_Estados")
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="distribucion_estados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col3:
        if st.button("📥 Exportar Secuencias Estados", width="stretch"):
            if len(df_estados) > 0:
                excel_bytes = exportar_a_excel(df_secuencias_display, "Secuencias_Estados")
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="secuencias_estados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    # Guardar análisis en session_state
    if 'analisis' not in st.session_state:
        st.session_state['analisis'] = {}

    # Preparar datos completos para el informe
    distribucion_estados_informe = pd.DataFrame()
    tiempos_estado_informe = pd.DataFrame()
    secuencias_informe = pd.DataFrame()
    anulaciones_informe = pd.DataFrame()

    if 'estado' in df_rcf.columns:
        distribucion_estados = df_rcf['estado'].value_counts()
        distribucion_estados_informe = distribucion_estados.head(10).reset_index()
        distribucion_estados_informe.columns = ['Estado', 'Cantidad']
        distribucion_estados_informe['Porcentaje'] = (distribucion_estados_informe['Cantidad'] / len(df_rcf) * 100).round(2)

    if len(df_estados) > 0 and 'tiempos_por_estado' in dir():
        tiempos_estado_informe = tiempos_por_estado.reset_index()

    if len(df_estados) > 0 and 'df_secuencias_display' in dir():
        secuencias_informe = df_secuencias_display.copy()

    if len(df_anulaciones_rcf) > 0:
        anulaciones_informe = df_anulaciones_rcf[[
            'registro', 'numero_factura', 'nif_emisor', 'razon_social',
            'importe_total', 'fecha_solicitud_anulacion', 'estado'
        ]].copy()
        anulaciones_informe.columns = [
            'Registro FACe', 'Nº Factura', 'NIF', 'Razón Social',
            'Importe', 'Fecha Solicitud', 'Estado Actual'
        ]

    # Calcular métricas resumen procedimiento anterior para informe
    n_sf_total = len(df_tiempos_sf) if not df_tiempos_sf.empty else 0
    n_sf_con_f = int(df_tiempos_sf['tiempo_face_f'].notna().sum()) if not df_tiempos_sf.empty and 'tiempo_face_f' in df_tiempos_sf.columns else 0
    n_sf_sin_f = n_sf_total - n_sf_con_f
    df_sf_val2 = df_tiempos_sf[~df_tiempos_sf['incidencia_temporal']].copy() if not df_tiempos_sf.empty and 'incidencia_temporal' in df_tiempos_sf.columns else pd.DataFrame()
    t_med_sf_inf = df_sf_val2['tiempo_s_f'].mean() if not df_sf_val2.empty and 'tiempo_s_f' in df_sf_val2.columns else None
    n_fuera_plazo_sf = int((df_sf_val2['tiempo_s_f'] > plazo_dias_t4 * 1440).sum()) if not df_sf_val2.empty and 'tiempo_s_f' in df_sf_val2.columns else 0

    # Calcular métricas resumen procedimiento nuevo para informe
    n_fp_total = len(df_tiempos_fp) if not df_tiempos_fp.empty else 0
    n_fp_aceptadas = int(df_tiempos_fp['fecha_tramitacion'].notna().sum()) if not df_tiempos_fp.empty and 'fecha_tramitacion' in df_tiempos_fp.columns else 0
    df_fp_val2 = df_tiempos_fp[~df_tiempos_fp['incidencia_temporal']].copy() if not df_tiempos_fp.empty and 'incidencia_temporal' in df_tiempos_fp.columns else pd.DataFrame()
    t_med_fp_inf = df_fp_val2['tiempo_f_aceptacion'].mean() if not df_fp_val2.empty and 'tiempo_f_aceptacion' in df_fp_val2.columns else None
    n_fuera_plazo_fp = int((df_fp_val2['tiempo_f_aceptacion'] > plazo_dias_t4 * 1440).sum()) if not df_fp_val2.empty and 'tiempo_f_aceptacion' in df_fp_val2.columns else 0

    st.session_state['analisis']['tramitacion'] = {
        # Datos existentes (anulaciones, estados, pagos)
        'total_anulaciones': total_anulaciones,
        'anulaciones_aceptadas': anuladas,
        'anulaciones_con_comentario': con_comentario if 'comentario' in df_anulaciones.columns else 0,
        'facturas_pagadas': total_pagadas,
        'importe_pagado': facturas_pagadas['importe_total'].sum() if len(facturas_pagadas) > 0 else 0,
        'facturas_contabilizadas': len(facturas_contabilizadas),
        'distribucion_estados': distribucion_estados_informe,
        'tiempos_por_estado': tiempos_estado_informe,
        'secuencias_estados': secuencias_informe,
        'detalle_anulaciones': anulaciones_informe,
        # Procedimiento anterior S→F (Apartado 4, tablas 4.1–4.3)
        'n_facturas_s_total': n_sf_total,
        'n_facturas_s_con_f': n_sf_con_f,
        'n_facturas_s_sin_f': n_sf_sin_f,
        'tiempo_medio_s_f_min': t_med_sf_inf,
        'n_fuera_plazo_procedimiento_anterior': n_fuera_plazo_sf,
        'df_tiempos_procedimiento_anterior': df_sf_val2,
        # Procedimiento nuevo F→aceptación (Apartado 4, tablas 4.4–4.6)
        'n_facturas_f_directas': n_fp_total,
        'n_facturas_f_aceptadas': n_fp_aceptadas,
        'tiempo_medio_f_aceptacion_min': t_med_fp_inf,
        'n_fuera_plazo_procedimiento_nuevo': n_fuera_plazo_fp,
        'df_tiempos_tramitacion_posterior': df_fp_val2,
        # Configuración del análisis
        'fecha_cambio_procedimiento': fecha_cambio_t4.strftime('%d/%m/%Y') if fecha_cambio_t4 else None,
        'plazo_referencia_dias': plazo_dias_t4,
    }

if __name__ == "__main__":
    main()