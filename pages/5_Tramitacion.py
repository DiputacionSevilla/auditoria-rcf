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

from config.settings import COLORES, COLORES_GRAFICOS, ESTADOS_FACTURAS
from utils.data_loader import exportar_a_excel

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
        # Convertir códigos de estado a nombres
        df_estados['nombre_estado'] = df_estados['codigo'].map(ESTADOS_FACTURAS).fillna('Desconocido')
        
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
        # Obtener secuencias de estados por factura
        df_estados_seq = df_estados_sorted.groupby('registro')['nombre_estado'].apply(list).reset_index()
        df_estados_seq['secuencia'] = df_estados_seq['nombre_estado'].apply(lambda x: ' → '.join(x[:5]))  # Primeros 5 estados
        
        # Top 10 secuencias
        top_secuencias = df_estados_seq['secuencia'].value_counts().head(10)
        
        df_secuencias_display = top_secuencias.reset_index()
        df_secuencias_display.columns = ['Secuencia de Estados', 'Cantidad de Facturas']
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
    
    st.session_state['analisis']['tramitacion'] = {
        'total_anulaciones': total_anulaciones,
        'anulaciones_aceptadas': anuladas,
        'facturas_pagadas': total_pagadas,
        'importe_pagado': facturas_pagadas['importe_total'].sum() if len(facturas_pagadas) > 0 else 0
    }

if __name__ == "__main__":
    main()