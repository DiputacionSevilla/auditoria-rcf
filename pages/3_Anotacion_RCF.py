"""
Análisis de Anotación en RCF - Sección V.2 de la Guía IGAE
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import COLORES, COLORES_GRAFICOS
from utils.data_loader import (
    calcular_tiempos_anotacion,
    identificar_facturas_retenidas,
    exportar_a_excel
)

st.set_page_config(
    page_title="Anotación RCF - Auditoría RCF",
    page_icon="⏱️",
    layout="wide"
)

def main():
    st.title("⏱️ Tiempos de Anotación en RCF")
    st.markdown("Análisis de tiempos de inscripción y facturas retenidas (Sección V.2)")
    
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
    with st.expander("📋 Marco Legal - Anotación en RCF"):
        st.markdown("""
        **Ley 25/2013, Art. 9:**
        - Anotación automática desde PGEFe (FACe)
        - Custodia de facturas originales
        - Accesibilidad para auditoría
        
        **Orden HAP/492/2014:**
        - Requisitos técnicos del RCF
        - Integración con FACe
        """)
    
    # === FACTURAS RETENIDAS EN FACE ===
    st.markdown("### 🔍 Facturas Retenidas en FACe")
    st.info("Facturas que están en FACe pero no han sido descargadas/anotadas en el RCF")
    
    df_retenidas = identificar_facturas_retenidas(
        datos['face'], 
        df_rcf, 
        ids_precalculados=datos.get('ids_face_en_rcf_total')
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Facturas en FACe",
            f"{len(datos['face']):,}"
        )
    
    with col2:
        anotadas_rcf = len(df_rcf[(df_rcf['es_papel']==False) & (df_rcf['estado'].astype(str).str.upper() != 'BORRADA')])
        st.metric(
            "Anotadas en RCF",
            f"{anotadas_rcf:,}",
            help="Facturas electrónicas vivas (no borradas) en RCF"
        )
    
    with col3:
        retenidas_count = len(df_retenidas)
        st.metric(
            "Retenidas (No anotadas)",
            f"{retenidas_count:,}",
            delta=f"{retenidas_count} facturas" if retenidas_count > 0 else "Todo OK",
            delta_color="inverse" if retenidas_count > 0 else "off"
        )
    
    if len(df_retenidas) > 0:
        st.error(f"⚠️ ALERTA: Se han detectado {len(df_retenidas)} facturas retenidas en FACe")
        
        # Mostrar tabla de retenidas
        st.markdown("#### 📋 Detalle de Facturas Retenidas")
        
        df_retenidas_display = df_retenidas[[
            'registro', 'nif_emisor', 'nombre', 'numero', 
            'importe', 'fecha_registro', 'oc'
        ]].copy()
        
        df_retenidas_display.columns = [
            'Registro FACe', 'NIF', 'Proveedor', 'Nº Factura',
            'Importe', 'Fecha Registro', 'OC'
        ]
        
        st.dataframe(
            df_retenidas_display.style.format({
                'Importe': '{:,.2f} €',
                'Fecha Registro': lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
            }),
            width="stretch",
            hide_index=True
        )
        
        # Exportar
        if st.button("📥 Exportar Facturas Retenidas"):
            excel_bytes = exportar_a_excel(df_retenidas_display, "Facturas_Retenidas")
            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name="facturas_retenidas_face.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.success("✅ No hay facturas retenidas. Todas las facturas de FACe están anotadas en RCF")
    
    st.markdown("---")
    
    # === TIEMPOS DE ANOTACIÓN ===
    st.markdown("### ⏱️ Análisis de Tiempos de Anotación")
    st.info("Tiempo transcurrido desde el registro en FACe hasta la anotación en RCF")

    df_tiempos_total = calcular_tiempos_anotacion(df_rcf, datos['face'])

    if len(df_tiempos_total) > 0:
        # Separar tiempos válidos (>=0) de anomalías (negativos)
        df_tiempos = df_tiempos_total[df_tiempos_total['tiempo_anotacion_min'] >= 0].copy()
        df_anomalias = df_tiempos_total[df_tiempos_total['tiempo_anotacion_min'] < 0].copy()

        num_anomalias = len(df_anomalias)
        num_validos = len(df_tiempos)

        # Mostrar aviso de anomalías si existen
        if num_anomalias > 0:
            st.warning(f"""
            ⚠️ **Anomalías detectadas**: Se han encontrado **{num_anomalias:,}** facturas con tiempos negativos
            (fecha de anotación en RCF anterior a fecha de registro en FACe).
            Estas facturas se excluyen de las métricas pero se muestran en la sección de anomalías para su investigación.
            """)

        # Métricas de tiempo (solo con datos válidos)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            tiempo_medio = df_tiempos['tiempo_anotacion_min'].mean() if len(df_tiempos) > 0 else 0
            st.metric(
                "Tiempo Medio",
                f"{tiempo_medio:.2f} min",
                help=f"Tiempo medio de anotación (basado en {num_validos:,} facturas válidas)"
            )

        with col2:
            tiempo_mediano = df_tiempos['tiempo_anotacion_min'].median() if len(df_tiempos) > 0 else 0
            st.metric(
                "Tiempo Mediano",
                f"{tiempo_mediano:.2f} min",
                help="Valor central de los tiempos"
            )

        with col3:
            tiempo_min = df_tiempos['tiempo_anotacion_min'].min() if len(df_tiempos) > 0 else 0
            st.metric(
                "Tiempo Mínimo",
                f"{tiempo_min:.2f} min"
            )

        with col4:
            tiempo_max = df_tiempos['tiempo_anotacion_min'].max() if len(df_tiempos) > 0 else 0
            st.metric(
                "Tiempo Máximo",
                f"{tiempo_max:.2f} min"
            )
        
        # Evolución temporal de tiempos
        st.markdown("#### 📈 Evolución Mensual de Tiempos")
        
        df_tiempos['mes'] = pd.to_datetime(df_tiempos['fecha_anotacion_rcf']).dt.to_period('M').astype(str)
        
        stats_mensuales = df_tiempos.groupby('mes')['tiempo_anotacion_min'].agg([
            'mean', 'median', 'min', 'max', 'count'
        ]).reset_index()
        
        stats_mensuales.columns = ['Mes', 'Media', 'Mediana', 'Mínimo', 'Máximo', 'Nº Facturas']
        
        # Gráfico
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=stats_mensuales['Mes'],
            y=stats_mensuales['Media'],
            mode='lines+markers',
            name='Tiempo Medio',
            line=dict(color=COLORES['primario'], width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=stats_mensuales['Mes'],
            y=stats_mensuales['Mediana'],
            mode='lines+markers',
            name='Tiempo Mediano',
            line=dict(color=COLORES['secundario'], width=2, dash='dash'),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title='Evolución mensual de tiempos de anotación',
            xaxis_title='Mes',
            yaxis_title='Tiempo (minutos)',
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, width="stretch")
        
        # Tabla estadísticas mensuales
        st.markdown("#### 📊 Estadísticas Mensuales Detalladas")
        
        st.dataframe(
            stats_mensuales.style.format({
                'Media': '{:.2f}',
                'Mediana': '{:.2f}',
                'Mínimo': '{:.2f}',
                'Máximo': '{:.2f}',
                'Nº Facturas': '{:,.0f}'
            }).background_gradient(subset=['Media'], cmap='RdYlGn_r'),
            width="stretch",
            hide_index=True
        )
        
        st.markdown("---")
        
        # === DISTRIBUCIÓN DE TIEMPOS ===
        st.markdown("### 📊 Distribución de Tiempos de Anotación")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Histograma
            fig = px.histogram(
                df_tiempos,
                x='tiempo_anotacion_min',
                nbins=50,
                title='Distribución de tiempos de anotación',
                labels={'tiempo_anotacion_min': 'Tiempo (minutos)', 'count': 'Frecuencia'},
                color_discrete_sequence=[COLORES['primario']]
            )
            
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, width="stretch")
        
        with col2:
            # Box plot
            fig = px.box(
                df_tiempos,
                y='tiempo_anotacion_min',
                title='Distribución de tiempos (Box Plot)',
                labels={'tiempo_anotacion_min': 'Tiempo (minutos)'},
                color_discrete_sequence=[COLORES['secundario']]
            )
            
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, width="stretch")
        
        st.markdown("---")
        
        # === TOP 10 MAYORES DEMORAS ===
        st.markdown("### 🐌 Top 10 Facturas con Mayor Demora")
        
        top_demoras = df_tiempos.nlargest(10, 'tiempo_anotacion_min')[[
            'entidad', 'id_fra_rcf', 'numero_factura', 'nif_emisor', 'razon_social', 
            'tiempo_anotacion_min', 'codigo_og'
        ]].copy()
        
        top_demoras.columns = [
            'Entidad', 'ID RCF', 'Nº Factura', 'NIF', 'Razón Social', 
            'Tiempo (min)', 'OG'
        ]
        
        # Convertir minutos a horas si es muy grande
        top_demoras['Tiempo (horas)'] = top_demoras['Tiempo (min)'] / 60
        
        st.dataframe(
            top_demoras.style.format({
                'Tiempo (min)': '{:.2f}',
                'Tiempo (horas)': '{:.2f}'
            }).background_gradient(subset=['Tiempo (min)'], cmap='Reds'),
            width="stretch",
            hide_index=True
        )
        
        # Gráfico de barras
        fig = px.bar(
            top_demoras.head(10),
            x='Tiempo (horas)',
            y='Nº Factura',
            orientation='h',
            title='Top 10 facturas con mayor tiempo de anotación',
            color='Tiempo (horas)',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, width="stretch")
        
        st.markdown("---")
        
        # === RANKING POR UNIDADES ===
        st.markdown("### 🏛️ Ranking de Unidades por Tiempo Medio")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Top 10 Oficinas Contables (Mayor tiempo)")
            
            if 'codigo_oc' in df_tiempos.columns:
                ranking_oc = df_tiempos.groupby('codigo_oc').agg({
                    'tiempo_anotacion_min': 'mean',
                    'id_fra_rcf': 'count'
                }).round(2)
                
                ranking_oc.columns = ['Tiempo Medio (min)', 'Nº Facturas']
                
                # Calcular diferencia con la media
                media_global = df_tiempos['tiempo_anotacion_min'].mean()
                ranking_oc['Diferencia vs Media (%)'] = (
                    (ranking_oc['Tiempo Medio (min)'] - media_global) / media_global * 100
                ).round(2)
                
                ranking_oc = ranking_oc.sort_values('Tiempo Medio (min)', ascending=False).head(10)
                
                st.dataframe(
                    ranking_oc.style.format({
                        'Tiempo Medio (min)': '{:.2f}',
                        'Nº Facturas': '{:,.0f}',
                        'Diferencia vs Media (%)': '{:+.2f}%'
                    }).background_gradient(subset=['Tiempo Medio (min)'], cmap='Reds'),
                    width="stretch"
                )
        
        with col2:
            st.markdown("#### Top 10 Unidades Tramitadoras (Mayor tiempo)")
            
            if 'codigo_ut' in df_tiempos.columns:
                ranking_ut = df_tiempos.groupby('codigo_ut').agg({
                    'tiempo_anotacion_min': 'mean',
                    'id_fra_rcf': 'count'
                }).round(2)
                
                ranking_ut.columns = ['Tiempo Medio (min)', 'Nº Facturas']
                
                ranking_ut['Diferencia vs Media (%)'] = (
                    (ranking_ut['Tiempo Medio (min)'] - media_global) / media_global * 100
                ).round(2)
                
                ranking_ut = ranking_ut.sort_values('Tiempo Medio (min)', ascending=False).head(10)
                
                st.dataframe(
                    ranking_ut.style.format({
                        'Tiempo Medio (min)': '{:.2f}',
                        'Nº Facturas': '{:,.0f}',
                        'Diferencia vs Media (%)': '{:+.2f}%'
                    }).background_gradient(subset=['Tiempo Medio (min)'], cmap='Oranges'),
                    width="stretch"
                )
        
        st.markdown("---")
        
        # === EXPORTACIÓN ===
        st.markdown("### 📁 Exportación de Datos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Exportar Estadísticas Mensuales", width="stretch"):
                excel_bytes = exportar_a_excel(stats_mensuales, "Estadisticas_Mensuales")
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="estadisticas_tiempos_mensuales.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            if st.button("📥 Exportar Top 10 Demoras", width="stretch"):
                excel_bytes = exportar_a_excel(top_demoras, "Top_10_Demoras")
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="top_10_demoras.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col3:
            if st.button("📥 Exportar Ranking Unidades", width="stretch"):
                if 'codigo_oc' in df_tiempos.columns:
                    excel_bytes = exportar_a_excel(
                        ranking_oc.reset_index(),
                        "Ranking_Unidades_Tiempos"
                    )
                    st.download_button(
                        label="Descargar Excel",
                        data=excel_bytes,
                        file_name="ranking_unidades_tiempos.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        # === SECCIÓN DE ANOMALÍAS ===
        if num_anomalias > 0:
            st.markdown("---")
            st.markdown("### ⚠️ Anomalías de Tiempos (Para Investigación)")
            st.error(f"""
            **{num_anomalias:,} facturas** tienen fecha de anotación en RCF **anterior** a la fecha de registro en FACe.
            Esto es lógicamente imposible y puede indicar:
            - Errores en los datos de origen
            - Facturas registradas manualmente en RCF antes de su llegada por FACe
            - Problemas de sincronización de fechas entre sistemas
            """)

            # Preparar tabla de anomalías
            cols_anomalias = ['entidad', 'id_fra_rcf', 'numero_factura', 'nif_emisor', 'razon_social',
                             'fecha_registro_face', 'fecha_anotacion_rcf', 'tiempo_anotacion_min']
            cols_disponibles = [c for c in cols_anomalias if c in df_anomalias.columns]

            df_anomalias_display = df_anomalias[cols_disponibles].copy()

            # Renombrar columnas para mostrar
            rename_map = {
                'entidad': 'Entidad',
                'id_fra_rcf': 'ID RCF',
                'numero_factura': 'Nº Factura',
                'nif_emisor': 'NIF',
                'razon_social': 'Proveedor',
                'fecha_registro_face': 'Fecha Reg. FACe',
                'fecha_anotacion_rcf': 'Fecha Anotación RCF',
                'tiempo_anotacion_min': 'Diferencia (min)'
            }
            df_anomalias_display = df_anomalias_display.rename(columns=rename_map)

            # Añadir columna de días para mejor comprensión
            if 'Diferencia (min)' in df_anomalias_display.columns:
                df_anomalias_display['Diferencia (días)'] = (df_anomalias_display['Diferencia (min)'] / 1440).round(1)

            # Ordenar por diferencia (los más negativos primero)
            df_anomalias_display = df_anomalias_display.sort_values('Diferencia (min)', ascending=True)

            st.dataframe(
                df_anomalias_display.head(50).style.format({
                    'Diferencia (min)': '{:,.0f}',
                    'Diferencia (días)': '{:,.1f}',
                    'Fecha Reg. FACe': lambda x: x.strftime('%d/%m/%Y %H:%M') if pd.notna(x) else '',
                    'Fecha Anotación RCF': lambda x: x.strftime('%d/%m/%Y %H:%M') if pd.notna(x) else ''
                }),
                width="stretch",
                hide_index=True
            )

            if num_anomalias > 50:
                st.caption(f"Mostrando 50 de {num_anomalias:,} anomalías. Exporta para ver todas.")

            # Botón de exportar anomalías
            col_exp1, col_exp2, col_exp3 = st.columns([1, 1, 1])
            with col_exp1:
                if st.button("📥 Exportar Anomalías", width="stretch"):
                    excel_bytes = exportar_a_excel(df_anomalias_display, "Anomalias_Tiempos")
                    st.download_button(
                        label="Descargar Excel",
                        data=excel_bytes,
                        file_name="anomalias_tiempos_anotacion.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    else:
        st.warning("No hay datos suficientes para calcular tiempos de anotación")
    
    # Guardar análisis en session_state
    if 'analisis' not in st.session_state:
        st.session_state['analisis'] = {}

    # Preparar datos completos para el informe
    df_retenidas_informe = pd.DataFrame()
    top_demoras_informe = pd.DataFrame()
    ranking_oc_tiempos_informe = pd.DataFrame()
    ranking_ut_tiempos_informe = pd.DataFrame()
    stats_mensuales_informe = pd.DataFrame()
    df_anomalias_informe = pd.DataFrame()
    num_anomalias_informe = 0

    if len(df_retenidas) > 0:
        df_retenidas_informe = df_retenidas[[
            'registro', 'nif_emisor', 'nombre', 'numero',
            'importe', 'fecha_registro', 'oc'
        ]].copy()
        df_retenidas_informe.columns = [
            'Registro FACe', 'NIF', 'Proveedor', 'Nº Factura',
            'Importe', 'Fecha Registro', 'OC'
        ]

    if len(df_tiempos_total) > 0:
        # Separar datos válidos y anomalías para el informe
        df_tiempos_validos = df_tiempos_total[df_tiempos_total['tiempo_anotacion_min'] >= 0].copy()
        df_anomalias_temp = df_tiempos_total[df_tiempos_total['tiempo_anotacion_min'] < 0].copy()
        num_anomalias_informe = len(df_anomalias_temp)

        if len(df_tiempos_validos) > 0:
            # Top demoras (solo datos válidos)
            top_demoras_informe = df_tiempos_validos.nlargest(10, 'tiempo_anotacion_min')[[
                'entidad', 'id_fra_rcf', 'numero_factura', 'nif_emisor', 'razon_social',
                'tiempo_anotacion_min', 'codigo_og'
            ]].copy()
            top_demoras_informe.columns = [
                'Entidad', 'ID RCF', 'Nº Factura', 'NIF', 'Razón Social',
                'Tiempo (min)', 'OG'
            ]
            top_demoras_informe['Tiempo (horas)'] = top_demoras_informe['Tiempo (min)'] / 60

            # Stats mensuales (solo datos válidos)
            df_tiempos_validos['mes'] = pd.to_datetime(df_tiempos_validos['fecha_anotacion_rcf']).dt.to_period('M').astype(str)
            stats_mensuales_informe = df_tiempos_validos.groupby('mes')['tiempo_anotacion_min'].agg([
                'mean', 'median', 'min', 'max', 'count'
            ]).reset_index()
            stats_mensuales_informe.columns = ['Mes', 'Media', 'Mediana', 'Mínimo', 'Máximo', 'Nº Facturas']

            # Ranking OC por tiempos (solo datos válidos)
            if 'codigo_oc' in df_tiempos_validos.columns:
                media_global = df_tiempos_validos['tiempo_anotacion_min'].mean()
                ranking_oc_tiempos_informe = df_tiempos_validos.groupby('codigo_oc').agg({
                    'tiempo_anotacion_min': 'mean',
                    'id_fra_rcf': 'count'
                }).round(2).reset_index()
                ranking_oc_tiempos_informe.columns = ['Código OC', 'Tiempo Medio (min)', 'Nº Facturas']
                ranking_oc_tiempos_informe['Diferencia vs Media (%)'] = (
                    (ranking_oc_tiempos_informe['Tiempo Medio (min)'] - media_global) / media_global * 100
                ).round(2)
                ranking_oc_tiempos_informe = ranking_oc_tiempos_informe.sort_values('Tiempo Medio (min)', ascending=False).head(10)

            # Ranking UT por tiempos (solo datos válidos)
            if 'codigo_ut' in df_tiempos_validos.columns:
                ranking_ut_tiempos_informe = df_tiempos_validos.groupby('codigo_ut').agg({
                    'tiempo_anotacion_min': 'mean',
                    'id_fra_rcf': 'count'
                }).round(2).reset_index()
                ranking_ut_tiempos_informe.columns = ['Código UT', 'Tiempo Medio (min)', 'Nº Facturas']
                ranking_ut_tiempos_informe['Diferencia vs Media (%)'] = (
                    (ranking_ut_tiempos_informe['Tiempo Medio (min)'] - media_global) / media_global * 100
                ).round(2)
                ranking_ut_tiempos_informe = ranking_ut_tiempos_informe.sort_values('Tiempo Medio (min)', ascending=False).head(10)

        # Preparar anomalías para informe
        if num_anomalias_informe > 0:
            cols_anom = ['entidad', 'id_fra_rcf', 'numero_factura', 'nif_emisor',
                        'fecha_registro_face', 'fecha_anotacion_rcf', 'tiempo_anotacion_min']
            cols_disp = [c for c in cols_anom if c in df_anomalias_temp.columns]
            df_anomalias_informe = df_anomalias_temp[cols_disp].copy()

    # Calcular métricas de tiempos válidos para el informe
    tiempo_medio = 0
    tiempo_mediano = 0
    tiempo_max = 0
    tiempo_min = 0

    if len(df_tiempos_total) > 0:
        df_validos_temp = df_tiempos_total[df_tiempos_total['tiempo_anotacion_min'] >= 0]
        if len(df_validos_temp) > 0:
            tiempo_medio = df_validos_temp['tiempo_anotacion_min'].mean()
            tiempo_mediano = df_validos_temp['tiempo_anotacion_min'].median()
            tiempo_max = df_validos_temp['tiempo_anotacion_min'].max()
            tiempo_min = df_validos_temp['tiempo_anotacion_min'].min()

    st.session_state['analisis']['anotacion'] = {
        'facturas_retenidas': len(df_retenidas),
        'df_retenidas': df_retenidas_informe,
        'tiempo_medio_min': tiempo_medio,
        'tiempo_mediano_min': tiempo_mediano,
        'tiempo_max_min': tiempo_max,
        'tiempo_min_min': tiempo_min,
        'top_demoras': top_demoras_informe,
        'stats_mensuales': stats_mensuales_informe,
        'ranking_oc_tiempos': ranking_oc_tiempos_informe,
        'ranking_ut_tiempos': ranking_ut_tiempos_informe,
        'num_anomalias': num_anomalias_informe,
        'df_anomalias': df_anomalias_informe
    }

if __name__ == "__main__":
    main()