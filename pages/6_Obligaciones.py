"""
Obligaciones de Control - Sección V.5 de la Guía IGAE
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import COLORES, COLORES_GRAFICOS, CONFIGURACION
from utils.data_loader import exportar_a_excel

st.set_page_config(
    page_title="Obligaciones - Auditoría RCF",
    page_icon="📋",
    layout="wide"
)

def main():
    st.title("📋 Obligaciones de Control")
    st.markdown("Facturas pendientes y control de morosidad (Sección V.5)")
    
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
    
    st.markdown("---")
    
    # === INFORMACIÓN NORMATIVA ===
    with st.expander("📋 Marco Legal - Control y Morosidad"):
        st.markdown("""
        **Ley 25/2013, Art. 12.3:**
        - Control trimestral de facturas pendientes
        - Alertas automáticas de morosidad
        - Informes periódicos al órgano de control
        
        **Ley 15/2010 (Morosidad):**
        - Plazo máximo de pago: 30 días (60 días hasta 31/12/2012)
        - Intereses de demora en caso de retraso
        - Control específico de facturas >3 meses sin reconocimiento
        """)
    
    # === FACTURAS PENDIENTES >3 MESES ===
    st.markdown("### ⚠️ Facturas sin Reconocimiento >3 Meses")
    st.info("Facturas anotadas hace más de 3 meses sin reconocimiento de obligación")
    
    # Calcular fecha límite (3 meses atrás)
    fecha_actual = datetime.now()
    fecha_limite = fecha_actual - timedelta(days=90)
    
    # Filtrar facturas pendientes
    estados_pendientes = ['REGISTRADA', 'VERIFICADA', 'RECIBIDA', 'CONFORMADA']
    
    if 'fecha_anotacion_rcf' in df_rcf.columns and 'estado' in df_rcf.columns:
        df_rcf['fecha_anotacion_rcf'] = pd.to_datetime(df_rcf['fecha_anotacion_rcf'])
        
        facturas_pendientes_3m = df_rcf[
            (df_rcf['fecha_anotacion_rcf'] <= fecha_limite) &
            (df_rcf['estado'].isin(estados_pendientes))
        ].copy()
        
        # Calcular días transcurridos
        facturas_pendientes_3m['dias_pendiente'] = (
            fecha_actual - facturas_pendientes_3m['fecha_anotacion_rcf']
        ).dt.days
    else:
        facturas_pendientes_3m = pd.DataFrame()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_pendientes = len(facturas_pendientes_3m)
        st.metric(
            "Facturas >3 Meses",
            f"{total_pendientes:,}",
            delta=f"{total_pendientes} pendientes" if total_pendientes > 0 else "Todo OK",
            delta_color="inverse" if total_pendientes > 0 else "off"
        )
    
    with col2:
        if len(facturas_pendientes_3m) > 0 and 'importe_total' in facturas_pendientes_3m.columns:
            importe_pendiente = facturas_pendientes_3m['importe_total'].sum()
            st.metric(
                "Importe Pendiente",
                f"{importe_pendiente:,.0f} €"
            )
    
    with col3:
        if len(facturas_pendientes_3m) > 0:
            dias_medio = facturas_pendientes_3m['dias_pendiente'].mean()
            st.metric(
                "Días Medio",
                f"{dias_medio:.0f} días"
            )
    
    with col4:
        if len(facturas_pendientes_3m) > 0:
            dias_max = facturas_pendientes_3m['dias_pendiente'].max()
            st.metric(
                "Antigüedad Máxima",
                f"{dias_max:.0f} días",
                delta_color="inverse"
            )
    
    # Detalle de facturas pendientes
    if len(facturas_pendientes_3m) > 0:
        st.markdown("#### 📋 Detalle de Facturas Pendientes >3 Meses")
        
        # Ordenar por antigüedad
        facturas_pendientes_3m = facturas_pendientes_3m.sort_values('dias_pendiente', ascending=False)
        
        df_pendientes_display = facturas_pendientes_3m[[
            'numero_factura', 'fecha_anotacion_rcf', 'dias_pendiente',
            'nif_emisor', 'razon_social', 'importe_total', 'estado', 'codigo_oc'
        ]].copy()
        
        df_pendientes_display.columns = [
            'Nº Factura', 'Fecha Anotación', 'Días Pendiente',
            'NIF', 'Razón Social', 'Importe', 'Estado', 'OC'
        ]
        
        st.dataframe(
            df_pendientes_display.style.format({
                'Fecha Anotación': lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else '',
                'Días Pendiente': '{:.0f}',
                'Importe': '{:,.2f} €'
            }).background_gradient(subset=['Días Pendiente'], cmap='Reds'),
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico de distribución por antigüedad
        st.markdown("#### 📊 Distribución por Antigüedad")
        
        # Crear rangos
        facturas_pendientes_3m['rango_dias'] = pd.cut(
            facturas_pendientes_3m['dias_pendiente'],
            bins=[90, 120, 180, 365, float('inf')],
            labels=['90-120 días', '120-180 días', '180-365 días', '>365 días']
        )
        
        distribucion_antigüedad = facturas_pendientes_3m['rango_dias'].value_counts().sort_index()
        
        fig = px.bar(
            x=distribucion_antigüedad.index.astype(str),
            y=distribucion_antigüedad.values,
            title='Facturas pendientes por rango de antigüedad',
            labels={'x': 'Rango de antigüedad', 'y': 'Número de facturas'},
            color=distribucion_antigüedad.values,
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Exportar
        if st.button("📥 Exportar Facturas Pendientes >3 Meses"):
            excel_bytes = exportar_a_excel(df_pendientes_display, "Facturas_Pendientes_3m")
            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name="facturas_pendientes_3_meses.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.success("✅ No hay facturas con más de 3 meses pendientes de reconocimiento de obligación")
    
    st.markdown("---")
    
    # === RANKING POR UNIDADES ===
    st.markdown("### 🏛️ Ranking de Unidades con Facturas Pendientes")
    
    if len(facturas_pendientes_3m) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top 10 Oficinas Contables")
            
            if 'codigo_oc' in facturas_pendientes_3m.columns:
                ranking_oc = facturas_pendientes_3m.groupby('codigo_oc').agg({
                    'importe_total': 'sum',
                    'ID_RCF': 'count',
                    'dias_pendiente': 'mean'
                }).round(2)
                
                ranking_oc.columns = ['Importe Total', 'Nº Facturas', 'Días Medio']
                ranking_oc = ranking_oc.sort_values('Importe Total', ascending=False).head(10)
                
                st.dataframe(
                    ranking_oc.style.format({
                        'Importe Total': '{:,.2f} €',
                        'Nº Facturas': '{:,.0f}',
                        'Días Medio': '{:.0f}'
                    }).background_gradient(subset=['Importe Total'], cmap='Oranges'),
                    use_container_width=True
                )
                
                # Gráfico
                fig = px.bar(
                    ranking_oc.reset_index().head(10),
                    x='Importe Total',
                    y='codigo_oc',
                    orientation='h',
                    title='Top 10 OC por importe pendiente',
                    color='Importe Total',
                    color_continuous_scale='Oranges'
                )
                
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Top 10 Unidades Tramitadoras")
            
            if 'codigo_ut' in facturas_pendientes_3m.columns:
                ranking_ut = facturas_pendientes_3m.groupby('codigo_ut').agg({
                    'importe_total': 'sum',
                    'ID_RCF': 'count',
                    'dias_pendiente': 'mean'
                }).round(2)
                
                ranking_ut.columns = ['Importe Total', 'Nº Facturas', 'Días Medio']
                ranking_ut = ranking_ut.sort_values('Importe Total', ascending=False).head(10)
                
                st.dataframe(
                    ranking_ut.style.format({
                        'Importe Total': '{:,.2f} €',
                        'Nº Facturas': '{:,.0f}',
                        'Días Medio': '{:.0f}'
                    }).background_gradient(subset=['Importe Total'], cmap='Purples'),
                    use_container_width=True
                )
                
                # Gráfico
                fig = px.bar(
                    ranking_ut.reset_index().head(10),
                    x='Importe Total',
                    y='codigo_ut',
                    orientation='h',
                    title='Top 10 UT por importe pendiente',
                    color='Importe Total',
                    color_continuous_scale='Purples'
                )
                
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === ANÁLISIS DE MOROSIDAD ===
    st.markdown("### 📉 Análisis de Morosidad")
    st.info("Facturas que superan los plazos legales de pago (30 días)")
    
    # Facturas pagadas con retraso
    if 'fecha_emision' in df_rcf.columns and 'fecha_pago' in df_rcf.columns:
        facturas_pagadas = df_rcf[df_rcf['estado'] == 'PAGADA'].copy()
        
        if len(facturas_pagadas) > 0:
            facturas_pagadas['fecha_emision'] = pd.to_datetime(facturas_pagadas['fecha_emision'])
            facturas_pagadas['fecha_pago'] = pd.to_datetime(facturas_pagadas['fecha_pago'])
            
            facturas_pagadas['dias_pago'] = (
                facturas_pagadas['fecha_pago'] - facturas_pagadas['fecha_emision']
            ).dt.days
            
            # Facturas con retraso (>30 días)
            facturas_retraso = facturas_pagadas[facturas_pagadas['dias_pago'] > 30].copy()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Facturas con Retraso",
                    f"{len(facturas_retraso):,}",
                    f"{len(facturas_retraso)/len(facturas_pagadas)*100:.1f}%" if len(facturas_pagadas) > 0 else "0%"
                )
            
            with col2:
                if len(facturas_retraso) > 0:
                    dias_retraso_medio = facturas_retraso['dias_pago'].mean()
                    st.metric(
                        "Días Medio de Retraso",
                        f"{dias_retraso_medio:.0f} días"
                    )
            
            with col3:
                if len(facturas_retraso) > 0:
                    dias_retraso_max = facturas_retraso['dias_pago'].max()
                    st.metric(
                        "Retraso Máximo",
                        f"{dias_retraso_max:.0f} días"
                    )
            
            if len(facturas_retraso) > 0:
                # Distribución de tiempos de pago
                fig = px.histogram(
                    facturas_pagadas,
                    x='dias_pago',
                    nbins=50,
                    title='Distribución de plazos de pago',
                    labels={'dias_pago': 'Días hasta el pago', 'count': 'Número de facturas'},
                    color_discrete_sequence=[COLORES['primario']]
                )
                
                # Añadir línea vertical en 30 días (plazo legal)
                fig.add_vline(x=30, line_dash="dash", line_color="red", annotation_text="Plazo legal (30 días)")
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hay datos suficientes de fechas de pago para analizar morosidad")
    
    st.markdown("---")
    
    # === CONTROLES AUTOMATIZADOS ===
    st.markdown("### ⚙️ Controles Automatizados")
    
    st.info("""
    **Verificaciones requeridas según la Guía IGAE:**
    
    ✅ Sistema genera alertas automáticas para facturas >3 meses  
    ✅ Informes trimestrales enviados al órgano de control  
    ✅ Registro de acciones correctivas tomadas  
    ✅ Seguimiento de facturas en situación de morosidad  
    
    **Nota**: Esta verificación requiere acceso a logs del sistema y evidencias documentales de los controles establecidos.
    """)
    
    # === EXPORTACIÓN ===
    st.markdown("### 📁 Exportación de Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Exportar Ranking Unidades", use_container_width=True):
            if len(facturas_pendientes_3m) > 0 and 'codigo_oc' in facturas_pendientes_3m.columns:
                excel_bytes = exportar_a_excel(
                    ranking_oc.reset_index(),
                    "Ranking_Unidades_Pendientes"
                )
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="ranking_unidades_pendientes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col2:
        if st.button("📥 Exportar Análisis Morosidad", use_container_width=True):
            if 'facturas_retraso' in locals() and len(facturas_retraso) > 0:
                excel_bytes = exportar_a_excel(facturas_retraso, "Analisis_Morosidad")
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="analisis_morosidad.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    # Guardar análisis en session_state
    if 'analisis' not in st.session_state:
        st.session_state['analisis'] = {}
    
    st.session_state['analisis']['obligaciones'] = {
        'facturas_3_meses': len(facturas_pendientes_3m),
        'importe_pendiente': facturas_pendientes_3m['importe_total'].sum() if len(facturas_pendientes_3m) > 0 else 0,
        'dias_medio_pendiente': facturas_pendientes_3m['dias_pendiente'].mean() if len(facturas_pendientes_3m) > 0 else 0
    }

if __name__ == "__main__":
    main()