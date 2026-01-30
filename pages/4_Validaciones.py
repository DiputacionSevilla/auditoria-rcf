"""
Validaciones de Contenido - Sección V.3 de la Guía IGAE
Orden HAP/1650/2015
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import COLORES, COLORES_GRAFICOS, VALIDACIONES_HAP, CONFIGURACION
from utils.validaciones import aplicar_todas_validaciones, analizar_rechazos
from utils.data_loader import exportar_a_excel

st.set_page_config(
    page_title="Validaciones - Auditoría RCF",
    page_icon="✅",
    layout="wide"
)

def main():
    st.title("✅ Validaciones de Contenido")
    st.markdown("Cumplimiento de la Orden HAP/1650/2015 (Sección V.3)")
    
    # Verificar datos
    if 'datos' not in st.session_state:
        st.warning("⚠️ No hay datos cargados. Por favor, carga los archivos en la página principal.")
        if st.button("Ir a página principal"):
            st.switch_page("app.py")
        return
    
    datos = st.session_state['datos']
    df_rcf = datos['rcf'].copy()
    
    st.markdown("---")
    
    # === INFORMACIÓN NORMATIVA ===
    with st.expander("📋 Marco Legal - Validaciones HAP/1650/2015"):
        st.markdown("""
        **Orden HAP/1650/2015 - Disposición Adicional 4ª:**
        
        Aplicable a facturas con fecha de expedición posterior al **15 de octubre de 2015**.
        
        **Validaciones obligatorias:**
        
        - **Apartado 4c**: No duplicidad de facturas (NIF + Número + Serie + Fecha)
        - **Apartado 5f**: NIF emisor diferente de NIF cesionario
        - **Apartado 6a**: Importes de líneas con máximo 2 decimales
        - **Apartado 6b**: Importes de factura con máximo 2 decimales
        - **Apartado 6c**: Código de moneda válido (ISO 4217:2001 Alpha 3)
        - **Apartado 6d**: Si importe bruto > 0, impuestos retenidos >= 0
        - **Apartado 6e**: Total bruto = Total bruto - Descuentos + Cargos
        - **Apartado 6f**: Total factura = Total bruto + Repercutidos - Retenidos
        """)
    
    # === APLICAR VALIDACIONES ===
    st.markdown("### 🔍 Ejecución de Validaciones")
    
    with st.spinner("Aplicando validaciones..."):
        resultados = aplicar_todas_validaciones(df_rcf)
    
    # === MÉTRICAS PRINCIPALES ===
    st.markdown("### 📊 Resumen de Validaciones")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Facturas Validadas",
            f"{resultados['total_facturas_validadas']:,}",
            help="Facturas electrónicas posteriores a 15/10/2015"
        )
    
    with col2:
        st.metric(
            "Total Incumplimientos",
            f"{resultados['total_incumplimientos']:,}",
            delta=f"{resultados['total_incumplimientos']} errores",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Cumplimiento",
            f"{resultados['porcentaje_cumplimiento']:.2f}%",
            delta=f"{resultados['porcentaje_cumplimiento']:.1f}%",
            delta_color="normal"
        )
    
    with col4:
        validaciones_ok = sum(
            1 for v in resultados['validaciones'].values() 
            if v['num_incumplimientos'] == 0
        )
        st.metric(
            "Validaciones OK",
            f"{validaciones_ok}/8",
            help="Validaciones sin incumplimientos"
        )
    
    st.markdown("---")
    
    # === TABLA RESUMEN VALIDACIONES ===
    st.markdown("### 📋 Detalle de Validaciones")
    
    # Preparar datos para tabla
    tabla_validaciones = []
    for codigo, resultado in resultados['validaciones'].items():
        tabla_validaciones.append({
            'Código': codigo,
            'Validación': resultado['nombre'],
            'Incumplimientos': resultado['num_incumplimientos'],
            'Porcentaje': resultado['porcentaje'],
            'Estado': '✅' if resultado['num_incumplimientos'] == 0 else '❌'
        })
    
    df_validaciones = pd.DataFrame(tabla_validaciones)
    
    st.dataframe(
        df_validaciones.style.format({
            'Incumplimientos': '{:,.0f}',
            'Porcentaje': '{:.2f}%'
        }).background_gradient(subset=['Porcentaje'], cmap='RdYlGn_r').apply(
            lambda x: ['background-color: #d4edda' if v == '✅' else 'background-color: #f8d7da' 
                      for v in x], subset=['Estado']
        ),
        use_container_width=True,
        hide_index=True
    )
    
    # === GRÁFICO DE VALIDACIONES ===
    st.markdown("### 📊 Visualización de Incumplimientos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de barras
        fig = px.bar(
            df_validaciones,
            x='Incumplimientos',
            y='Código',
            orientation='h',
            title='Número de incumplimientos por validación',
            color='Incumplimientos',
            color_continuous_scale='Reds',
            text='Incumplimientos'
        )
        
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        fig.update_layout(showlegend=False, height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico circular de cumplimiento
        cumple = resultados['total_facturas_validadas'] - resultados['total_incumplimientos']
        no_cumple = resultados['total_incumplimientos']
        
        fig = go.Figure(data=[go.Pie(
            labels=['Cumplen', 'No cumplen'],
            values=[cumple, no_cumple],
            hole=0.4,
            marker=dict(colors=[COLORES_GRAFICOS['conformadas'], COLORES_GRAFICOS['rechazadas']])
        )])
        
        fig.update_layout(
            title='Porcentaje de cumplimiento global',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === DETALLE DE CADA VALIDACIÓN ===
    st.markdown("### 🔎 Detalle de Incumplimientos por Validación")
    
    for codigo, resultado in resultados['validaciones'].items():
        with st.expander(f"{codigo} - {resultado['nombre']} ({resultado['num_incumplimientos']} incumplimientos)"):
            if resultado['num_incumplimientos'] > 0:
                st.warning(f"Se han encontrado {resultado['num_incumplimientos']} incumplimientos ({resultado['porcentaje']:.2f}%)")
                
                if resultado['facturas']:
                    df_incumplimientos = pd.DataFrame(resultado['facturas'])
                    
                    st.dataframe(
                        df_incumplimientos.head(20),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    if len(resultado['facturas']) > 20:
                        st.info(f"Mostrando 20 de {len(resultado['facturas'])} incumplimientos. Exporta para ver el listado completo.")
                    
                    # Botón exportar
                    if st.button(f"📥 Exportar incumplimientos {codigo}", key=f"export_{codigo}"):
                        excel_bytes = exportar_a_excel(
                            df_incumplimientos,
                            f"Incumplimientos_{codigo}"
                        )
                        st.download_button(
                            label="Descargar Excel",
                            data=excel_bytes,
                            file_name=f"incumplimientos_{codigo}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_{codigo}"
                        )
                
                if 'nota' in resultado:
                    st.info(f"ℹ️ {resultado['nota']}")
            else:
                st.success("✅ Validación cumplida correctamente. No se han encontrado incumplimientos.")
    
    st.markdown("---")
    
    # === ANÁLISIS DE RECHAZOS ===
    st.markdown("### ❌ Análisis de Facturas Rechazadas")
    
    analisis_rechazos = analizar_rechazos(df_rcf)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Rechazadas",
            f"{analisis_rechazos['total_rechazadas']:,}"
        )
    
    with col2:
        st.metric(
            "Porcentaje",
            f"{analisis_rechazos['porcentaje']:.2f}%"
        )
    
    with col3:
        motivos_distintos = len(analisis_rechazos['por_motivo'])
        st.metric(
            "Motivos Distintos",
            f"{motivos_distintos}"
        )
    
    if analisis_rechazos['por_motivo']:
        st.markdown("#### 📊 Causas de Rechazo")
        
        df_motivos = pd.DataFrame(
            list(analisis_rechazos['por_motivo'].items()),
            columns=['Motivo', 'Cantidad']
        ).sort_values('Cantidad', ascending=False)
        
        # Gráfico de barras
        fig = px.bar(
            df_motivos.head(10),
            x='Cantidad',
            y='Motivo',
            orientation='h',
            title='Top 10 motivos de rechazo',
            color='Cantidad',
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla
        st.dataframe(
            df_motivos.style.format({'Cantidad': '{:,.0f}'}),
            use_container_width=True,
            hide_index=True
        )
        
        # Exportar
        if st.button("📥 Exportar Análisis de Rechazos"):
            excel_bytes = exportar_a_excel(df_motivos, "Analisis_Rechazos")
            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name="analisis_rechazos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    st.markdown("---")
    
    # === EXPORTACIÓN COMPLETA ===
    st.markdown("### 📁 Exportación de Resultados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Exportar Resumen Validaciones", use_container_width=True):
            excel_bytes = exportar_a_excel(df_validaciones, "Resumen_Validaciones")
            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name="resumen_validaciones.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("📥 Exportar Todas las Facturas Rechazadas", use_container_width=True):
            if analisis_rechazos['facturas']:
                df_rechazadas = pd.DataFrame(analisis_rechazos['facturas'])
                excel_bytes = exportar_a_excel(df_rechazadas, "Facturas_Rechazadas")
                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="facturas_rechazadas_completo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    # Guardar análisis en session_state
    if 'analisis' not in st.session_state:
        st.session_state['analisis'] = {}
    
    st.session_state['analisis']['validaciones'] = resultados
    st.session_state['analisis']['rechazos'] = analisis_rechazos

if __name__ == "__main__":
    main()