"""
Análisis de Facturas en Papel - Sección V.1 de la Guía IGAE
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import COLORES, COLORES_GRAFICOS, CONFIGURACION
from utils.data_loader import (
    obtener_facturas_papel_sospechosas,
    exportar_a_excel,
    es_persona_juridica,
    excluir_facturas_borradas,
    agregar_columna_entidad
)

st.set_page_config(
    page_title="Facturas en Papel - Auditoría RCF",
    page_icon="📄",
    layout="wide"
)

def main():
    st.title("📄 Análisis de Facturas en Papel")
    st.markdown("Cumplimiento de la obligatoriedad de factura electrónica (Ley 25/2013)")
    
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
    with st.expander("📋 Marco Legal - Obligatoriedad Factura Electrónica"):
        st.markdown("""
        **Ley 25/2013, Art. 4 - Obligatoriedad:**
        - Obligatoria para personas jurídicas
        - Desde el 15 de enero de 2015
        - Facturas de importe superior a 3.000€ (Base Imponible)
        
        **Circular 1/2015 IGAE:**
        - Establece los criterios de aplicación
        - Excepciones: Servicios en el exterior, contratos secretos/clasificados
        """)
    
    # === MÉTRICAS PRINCIPALES ===
    st.markdown("### 📊 Resumen de Facturas en Papel")
    
    facturas_papel = df_rcf[df_rcf['es_papel'] == True].copy()
    facturas_sospechosas = obtener_facturas_papel_sospechosas(df_rcf)
    tabla_sospechosas = pd.DataFrame()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_papel = len(facturas_papel)
        total_facturas = len(df_rcf)
        porc_papel = (total_papel / total_facturas * 100) if total_facturas > 0 else 0
        st.metric(
            "Total en Papel",
            f"{total_papel:,}",
            f"{porc_papel:.1f}% del total"
        )
    
    with col2:
        sospechosas = len(facturas_sospechosas)
        porc_sosp = (sospechosas / total_papel * 100) if total_papel > 0 else 0
        st.metric(
            "Susceptibles Incumplimiento",
            f"{sospechosas:,}",
            f"{porc_sosp:.1f}% del papel",
            delta_color="inverse"
        )
    
    with col3:
        if len(facturas_sospechosas) > 0:
            importe_sosp = facturas_sospechosas['importe_total'].sum()
            st.metric(
                "Importe Sospechoso",
                f"{importe_sosp:,.0f} €"
            )
    
    with col4:
        if 'tipo_persona' in facturas_papel.columns:
            tiene_j = (facturas_papel['tipo_persona'] == 'J').any()
            if tiene_j:
                personas_juridicas = len(facturas_papel[facturas_papel['tipo_persona'] == 'J'])
            else:
                personas_juridicas = len(facturas_papel[facturas_papel['nif_emisor'].apply(es_persona_juridica)])
            
            st.metric(
                "PJ en Papel",
                f"{personas_juridicas:,}",
                help="Personas Jurídicas identificadas por tipo o NIF"
            )
        else:
            personas_juridicas = len(facturas_papel[facturas_papel['nif_emisor'].apply(es_persona_juridica)])
            st.metric("PJ en Papel", f"{personas_juridicas:,}", help="Identificadas por prefijo de NIF")
    
    st.markdown("---")
    
    # === EVOLUCIÓN TEMPORAL ===
    st.markdown("### 📈 Evolución Temporal de Facturas Susceptibles")

    evolucion = pd.DataFrame()
    if len(facturas_sospechosas) > 0 and 'fecha_anotacion_rcf' in facturas_sospechosas.columns:
        # Evolución mensual
        facturas_sospechosas['mes'] = pd.to_datetime(
            facturas_sospechosas['fecha_anotacion_rcf']
        ).dt.to_period('M').astype(str)
        
        # Total mensual
        total_mensual = df_rcf.groupby(
            pd.to_datetime(df_rcf['fecha_anotacion_rcf']).dt.to_period('M').astype(str)
        ).size()
        
        # Sospechosas mensuales
        sosp_mensual = facturas_sospechosas.groupby('mes').size()
        
        # Combinar
        evolucion = pd.DataFrame({
            'total': total_mensual,
            'sospechosas': sosp_mensual
        }).fillna(0)
        
        evolucion['porcentaje'] = (evolucion['sospechosas'] / evolucion['total'] * 100).round(2)
        
        # Gráfico combinado
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=evolucion.index,
                y=evolucion['sospechosas'],
                name='Facturas sospechosas',
                marker_color=COLORES_GRAFICOS['papel']
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=evolucion.index,
                y=evolucion['porcentaje'],
                name='Porcentaje',
                mode='lines+markers',
                marker_color=COLORES_GRAFICOS['rechazadas'],
                line=dict(width=3)
            ),
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="Mes")
        fig.update_yaxes(title_text="Número de facturas", secondary_y=False)
        fig.update_yaxes(title_text="Porcentaje (%)", secondary_y=True)
        
        fig.update_layout(
            title='Evolución mensual de facturas susceptibles de incumplimiento',
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, width="stretch")
        
        # Tabla resumen
        st.markdown("#### 📋 Tabla Resumen Mensual")
        
        evolucion_display = evolucion.copy()
        evolucion_display.columns = ['Total Facturas', 'Facturas Sospechosas', 'Porcentaje (%)']
        evolucion_display.index.name = 'Mes'
        
        st.dataframe(
            evolucion_display.style.format({
                'Total Facturas': '{:,.0f}',
                'Facturas Sospechosas': '{:,.0f}',
                'Porcentaje (%)': '{:.2f}%'
            }).background_gradient(subset=['Porcentaje (%)'], cmap='Reds'),
            width="stretch"
        )
    else:
        st.info("No hay facturas susceptibles de incumplimiento en el periodo")
    
    st.markdown("---")
    
    # === TODAS LAS FACTURAS SOSPECHOSAS POR IMPORTE ===
    st.markdown("### 💰 Facturas Sospechosas por Importe")

    if len(facturas_sospechosas) > 0:
        tabla_sospechosas = facturas_sospechosas.sort_values('base_imponible', ascending=False)[[
            'entidad', 'id_fra_rcf', 'numero_factura', 'fecha_emision', 'nif_emisor', 'razon_social',
            'base_imponible', 'importe_total', 'codigo_oc'
        ]].copy()

        tabla_sospechosas.columns = ['Entidad', 'ID RCF', 'Nº Factura', 'Fecha', 'NIF', 'Razón Social', 'Base Imponible (€)', 'Total (€)', 'OC']

        st.dataframe(
            tabla_sospechosas.style.format({
                'Base Imponible (€)': '{:,.2f}',
                'Total (€)': '{:,.2f}',
                'Fecha': lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
            }),
            width="stretch",
            hide_index=True
        )

        # Botón exportar
        if st.button("📥 Exportar Todas a Excel"):
            excel_bytes = exportar_a_excel(tabla_sospechosas, "Facturas_Papel_Sospechosas_Importe")
            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name="facturas_papel_sospechosas_importe.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    st.markdown("---")
    
    # === TOP 10 PROVEEDORES ===
    st.markdown("### 🏢 Top 10 Proveedores por Base Imponible Acumulada")
    
    if len(facturas_sospechosas) > 0:
        top_proveedores = facturas_sospechosas.groupby(['nif_emisor', 'razon_social']).agg({
            'id_fra_rcf': 'count',
            'base_imponible': 'sum'
        }).reset_index()
        
        top_proveedores.columns = ['NIF', 'Razón Social', 'Nº Facturas', 'BI Acumulada']
        top_proveedores = top_proveedores.sort_values('BI Acumulada', ascending=False).head(10)
        
        # Gráfico
        fig = px.bar(
            top_proveedores,
            x='BI Acumulada',
            y='Razón Social',
            orientation='h',
            text='Nº Facturas',
            title='Proveedores con mayor BI acumulada en facturas sospechosas',
            color='BI Acumulada',
            color_continuous_scale='Reds'
        )
        
        fig.update_traces(texttemplate='%{text} facturas', textposition='outside')
        fig.update_layout(showlegend=False, height=400)
        
        st.plotly_chart(fig, width="stretch")
        
        # Tabla
        st.dataframe(
            top_proveedores.style.format({
                'Importe Acumulado': '{:,.2f} €',
                'Nº Facturas': '{:,.0f}'
            }),
            width="stretch",
            hide_index=True
        )
    
    st.markdown("---")
    
    # === RANKING POR UNIDADES ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏛️ Top 10 Oficinas Contables")
        
        if len(facturas_sospechosas) > 0 and 'codigo_oc' in facturas_sospechosas.columns:
            ranking_oc = facturas_sospechosas.groupby('codigo_oc').agg({
                'base_imponible': 'sum',
                'id_fra_rcf': 'count'
            }).sort_values('base_imponible', ascending=False).head(10)
            
            ranking_oc.columns = ['BI Total', 'Nº Facturas']
            ranking_oc.index.name = 'Código OC'
            
            st.dataframe(
                ranking_oc.style.format({
                    'BI Total': '{:,.2f} €',
                    'Nº Facturas': '{:,.0f}'
                }).background_gradient(subset=['BI Total'], cmap='Oranges'),
                width="stretch"
            )
    
    with col2:
        st.markdown("### 📊 Top 10 Unidades Tramitadoras")
        
        if len(facturas_sospechosas) > 0 and 'codigo_ut' in facturas_sospechosas.columns:
            ranking_ut = facturas_sospechosas.groupby('codigo_ut').agg({
                'base_imponible': 'sum',
                'id_fra_rcf': 'count'
            }).sort_values('base_imponible', ascending=False).head(10)
            
            ranking_ut.columns = ['BI Total', 'Nº Facturas']
            ranking_ut.index.name = 'Código UT'
            
            st.dataframe(
                ranking_ut.style.format({
                    'BI Total': '{:,.2f} €',
                    'Nº Facturas': '{:,.0f}'
                }).background_gradient(subset=['BI Total'], cmap='Purples'),
                width="stretch"
            )
    
    st.markdown("---")
    
    # === EXPORTACIÓN COMPLETA ===
    st.markdown("### 📁 Exportación de Datos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Exportar Todas las Sospechosas", width="stretch"):
            if len(facturas_sospechosas) > 0:
                excel_bytes = exportar_a_excel(
                    facturas_sospechosas,
                    "Facturas_Papel_Sospechosas"
                )
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="facturas_papel_sospechosas_completo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col2:
        if st.button("📥 Exportar Ranking Proveedores", width="stretch"):
            if len(facturas_sospechosas) > 0:
                excel_bytes = exportar_a_excel(
                    top_proveedores,
                    "Ranking_Proveedores"
                )
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="ranking_proveedores.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col3:
        if st.button("📥 Exportar Ranking Unidades", width="stretch"):
            if len(facturas_sospechosas) > 0 and 'codigo_oc' in facturas_sospechosas.columns:
                excel_bytes = exportar_a_excel(
                    ranking_oc.reset_index(),
                    "Ranking_Unidades"
                )
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="ranking_unidades.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    # Guardar análisis en session_state para el informe
    if 'analisis' not in st.session_state:
        st.session_state['analisis'] = {}

    # Preparar datos completos para el informe
    top_proveedores_informe = pd.DataFrame()
    ranking_oc_informe = pd.DataFrame()
    ranking_ut_informe = pd.DataFrame()

    if len(facturas_sospechosas) > 0:
        # Top proveedores
        top_proveedores_informe = facturas_sospechosas.groupby(['nif_emisor', 'razon_social']).agg({
            'id_fra_rcf': 'count',
            'base_imponible': 'sum'
        }).reset_index()
        top_proveedores_informe.columns = ['NIF', 'Razón Social', 'Nº Facturas', 'BI Acumulada']
        top_proveedores_informe = top_proveedores_informe.sort_values('BI Acumulada', ascending=False).head(10)

        # Ranking OC
        if 'codigo_oc' in facturas_sospechosas.columns:
            ranking_oc_informe = facturas_sospechosas.groupby('codigo_oc').agg({
                'base_imponible': 'sum',
                'id_fra_rcf': 'count'
            }).sort_values('base_imponible', ascending=False).head(10).reset_index()
            ranking_oc_informe.columns = ['Código OC', 'BI Total', 'Nº Facturas']

        # Ranking UT
        if 'codigo_ut' in facturas_sospechosas.columns:
            ranking_ut_informe = facturas_sospechosas.groupby('codigo_ut').agg({
                'base_imponible': 'sum',
                'id_fra_rcf': 'count'
            }).sort_values('base_imponible', ascending=False).head(10).reset_index()
            ranking_ut_informe.columns = ['Código UT', 'BI Total', 'Nº Facturas']

    st.session_state['analisis']['facturas_papel'] = {
        'total_papel': len(facturas_papel),
        'total_sospechosas': len(facturas_sospechosas),
        'importe_sospechoso': facturas_sospechosas['base_imponible'].sum() if len(facturas_sospechosas) > 0 else 0,
        'top_10_importe': tabla_sospechosas if len(facturas_sospechosas) > 0 else pd.DataFrame(),
        'top_proveedores': top_proveedores_informe,
        'ranking_oc': ranking_oc_informe,
        'ranking_ut': ranking_ut_informe,
        'evolucion_mensual': evolucion if len(facturas_sospechosas) > 0 else pd.DataFrame(),
        'facturas_sospechosas': facturas_sospechosas[['entidad', 'id_fra_rcf', 'numero_factura', 'fecha_emision',
                                                       'nif_emisor', 'razon_social', 'base_imponible', 'importe_total',
                                                       'codigo_oc']].copy() if len(facturas_sospechosas) > 0 else pd.DataFrame()
    }

if __name__ == "__main__":
    main()