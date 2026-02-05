"""
Dashboard Ejecutivo - Vista general de todas las métricas
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import COLORES, COLORES_GRAFICOS, CONFIGURACION
from utils.data_loader import filtrar_por_periodo, es_persona_juridica

st.set_page_config(
    page_title="Dashboard - Auditoría RCF",
    page_icon="📊",
    layout="wide"
)

# CSS personalizado
st.markdown(f"""
    <style>
    .metric-card {{
        background-color: {COLORES['card']};
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid {COLORES['primario']};
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .metric-value {{
        font-size: 32px;
        font-weight: bold;
        color: {COLORES['primario']};
    }}
    .metric-label {{
        font-size: 14px;
        color: {COLORES['texto']};
        margin-bottom: 5px;
    }}
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("📊 Dashboard Ejecutivo")
    st.markdown("Vista general de las métricas principales de auditoría")
    
    # Verificar datos cargados
    if 'datos' not in st.session_state:
        st.warning("⚠️ No hay datos cargados. Por favor, carga los archivos en la página principal.")
        if st.button("Ir a página principal"):
            st.switch_page("app.py")
        return
    
    datos = st.session_state['datos']
    
    # Datos RCF filtrando BORRADAS para el análisis general
    df_rcf = datos['rcf'].copy()
    if 'estado' in df_rcf.columns:
        df_rcf = df_rcf[df_rcf['estado'].astype(str).str.upper() != 'BORRADA'].copy()

    # Filtros
    st.sidebar.title("🔍 Filtros")
    
    # Filtro de fecha
    if 'fecha_anotacion_rcf' in df_rcf.columns:
        fecha_min = pd.to_datetime(df_rcf['fecha_anotacion_rcf']).min()
        fecha_max = pd.to_datetime(df_rcf['fecha_anotacion_rcf']).max()
        
        fecha_inicio = st.sidebar.date_input(
            "Fecha inicio",
            value=fecha_min,
            min_value=fecha_min,
            max_value=fecha_max
        )
        
        fecha_fin = st.sidebar.date_input(
            "Fecha fin",
            value=fecha_max,
            min_value=fecha_min,
            max_value=fecha_max
        )
        
        # Aplicar filtro
        # Para evitar perder registros sin fecha (como los 'PDTE DE ACEPTAR'),
        # el filtro de fecha solo actúa si hay fecha.
        df_con_fecha = df_rcf[df_rcf['fecha_anotacion_rcf'].notna()]
        df_sin_fecha = df_rcf[df_rcf['fecha_anotacion_rcf'].isna()]
        
        df_filtrado_con = filtrar_por_periodo(
            df_con_fecha,
            'fecha_anotacion_rcf',
            fecha_inicio,
            fecha_fin
        )
        
        # Unimos los filtrados por fecha con los que no tienen fecha (pero que pasaron el filtro de ejercicio)
        df_filtrado = pd.concat([df_filtrado_con, df_sin_fecha]).drop_duplicates().copy()
    else:
        df_filtrado = df_rcf.copy()
    
    # Filtro por unidad
    if 'codigo_oc' in df_filtrado.columns:
        oficinas = ['Todas'] + sorted(df_filtrado['codigo_oc'].dropna().unique().tolist())
        oficina_sel = st.sidebar.selectbox("Oficina Contable", oficinas)
        
        if oficina_sel != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['codigo_oc'] == oficina_sel]
    
    # === MÉTRICAS PRINCIPALES ===
    st.markdown("### 📈 Métricas Principales")
    
    # Excluir BORRADAS para métricas generales (según feedback del usuario)
    df_vivas = df_filtrado[df_filtrado['estado'].astype(str).str.upper() != 'BORRADA']
    total_facturas = len(df_vivas)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            "Total Facturas",
            f"{total_facturas:,}",
            help="Total facturas vivas (excluyendo borradas)"
        )
    
    with col2:
        facturas_electronicas = len(df_vivas[df_vivas['es_papel'] == False])
        porc_elect = (facturas_electronicas / total_facturas * 100) if total_facturas > 0 else 0
        st.metric(
            "Electrónicas",
            f"{facturas_electronicas:,}",
            f"{porc_elect:.1f}%"
        )
    
    with col3:
        facturas_papel = len(df_vivas[df_vivas['es_papel'] == True])
        porc_papel = (facturas_papel / total_facturas * 100) if total_facturas > 0 else 0
        st.metric(
            "En Papel",
            f"{facturas_papel:,}",
            f"{porc_papel:.1f}%"
        )
    
    with col4:
        if 'importe_total' in df_vivas.columns:
            importe_total = df_vivas['importe_total'].sum()
            st.metric(
                "Importe Total",
                f"{importe_total:,.0f} €",
                help="Suma de importes de facturas vivas"
            )
    
    with col5:
        facturas_rechazadas = len(df_filtrado[df_filtrado['estado'] == 'RECHAZADA'])
        porc_rechazadas = (facturas_rechazadas / total_facturas * 100) if total_facturas > 0 else 0
        st.metric(
            "Rechazadas",
            f"{facturas_rechazadas:,}",
            f"{porc_rechazadas:.1f}%",
            delta_color="inverse"
        )
    
    with col6:
        anulaciones = len(datos['anulaciones'])
        st.metric(
            "Anulaciones",
            f"{anulaciones:,}",
            help="Solicitudes de anulación"
        )
    
    st.markdown("---")
    
    # === GRÁFICOS PRINCIPALES ===
    
    # Fila 1: Evolución temporal y distribución por estado
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 Evolución Temporal")
        
        if 'fecha_anotacion_rcf' in df_filtrado.columns:
            df_filtrado['mes'] = pd.to_datetime(df_filtrado['fecha_anotacion_rcf']).dt.to_period('M').astype(str)
            
            evolucion = df_filtrado.groupby(['mes', 'es_papel']).size().reset_index(name='cantidad')
            evolucion['tipo'] = evolucion['es_papel'].map({True: 'Papel', False: 'Electrónicas'})
            
            fig = px.line(
                evolucion,
                x='mes',
                y='cantidad',
                color='tipo',
                markers=True,
                title='Evolución mensual de facturas',
                color_discrete_map={
                    'Papel': COLORES_GRAFICOS['papel'],
                    'Electrónicas': COLORES_GRAFICOS['electronicas']
                }
            )
            
            fig.update_layout(
                xaxis_title="Mes",
                yaxis_title="Número de facturas",
                legend_title="Tipo",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.markdown("### 🎯 Distribución por Estado")
        
        if 'estado' in df_filtrado.columns:
            estados = df_filtrado['estado'].value_counts()
            
            fig = go.Figure(data=[go.Pie(
                labels=estados.index,
                values=estados.values,
                hole=0.4,
                marker=dict(
                    colors=[
                        COLORES_GRAFICOS.get(estado.lower(), COLORES['secundario'])
                        for estado in estados.index
                    ]
                )
            )])
            
            fig.update_layout(
                title='Facturas por estado',
                showlegend=True
            )
            
            st.plotly_chart(fig, width="stretch")
    
    # Fila 2: Top proveedores y distribución por importe
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏢 Top 10 Proveedores por Importe")
        
        if 'razon_social' in df_filtrado.columns and 'importe_total' in df_filtrado.columns:
            top_proveedores = df_filtrado.groupby('razon_social').agg({
                'importe_total': 'sum',
                'id_fra_rcf': 'count'
            }).sort_values('importe_total', ascending=False).head(10)
            
            fig = px.bar(
                top_proveedores.reset_index(),
                x='importe_total',
                y='razon_social',
                orientation='h',
                title='Importes acumulados por proveedor',
                color='importe_total',
                color_continuous_scale='Blues'
            )
            
            fig.update_layout(
                xaxis_title="Importe (€)",
                yaxis_title="Proveedor",
                showlegend=False
            )
            
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.markdown("### 💰 Distribución de Importes")
        
        if 'importe_total' in df_filtrado.columns:
            # Crear rangos de importe
            df_filtrado['rango_importe'] = pd.cut(
                df_filtrado['importe_total'],
                bins=[0, 1000, 5000, 10000, 50000, float('inf')],
                labels=['< 1K', '1K-5K', '5K-10K', '10K-50K', '> 50K']
            )
            
            rangos = df_filtrado['rango_importe'].value_counts().sort_index()
            
            fig = px.bar(
                x=rangos.index.astype(str),
                y=rangos.values,
                title='Facturas por rango de importe',
                color=rangos.values,
                color_continuous_scale='Oranges'
            )
            
            fig.update_layout(
                xaxis_title="Rango de importe (€)",
                yaxis_title="Número de facturas",
                showlegend=False
            )
            
            st.plotly_chart(fig, width="stretch")
    
    # Fila 3: Análisis por unidades
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏛️ Top 10 Oficinas Contables")
        
        if 'codigo_oc' in df_filtrado.columns:
            top_oc = df_filtrado['codigo_oc'].value_counts().head(10)
            
            fig = px.bar(
                x=top_oc.values,
                y=top_oc.index,
                orientation='h',
                title='Facturas por Oficina Contable',
                color=top_oc.values,
                color_continuous_scale='Greens'
            )
            
            fig.update_layout(
                xaxis_title="Número de facturas",
                yaxis_title="Código OC",
                showlegend=False
            )
            
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.markdown("### 📊 Top 10 Unidades Tramitadoras")
        
        if 'codigo_ut' in df_filtrado.columns:
            top_ut = df_filtrado['codigo_ut'].value_counts().head(10)
            
            fig = px.bar(
                x=top_ut.values,
                y=top_ut.index,
                orientation='h',
                title='Facturas por Unidad Tramitadora',
                color=top_ut.values,
                color_continuous_scale='Purples'
            )
            
            fig.update_layout(
                xaxis_title="Número de facturas",
                yaxis_title="Código UT",
                showlegend=False
            )
            
            st.plotly_chart(fig, width="stretch")
    
    st.markdown("---")
    
    # === RESUMEN DE ALERTAS ===
    st.markdown("### ⚠️ Alertas y Observaciones")
    
    alertas = []
    
    # Facturas en papel con importe alto
    if 'es_papel' in df_filtrado.columns and 'base_imponible' in df_filtrado.columns:
        umbral = CONFIGURACION['importe_minimo_obligatorio']
        condicion_papel_alto = (df_filtrado['es_papel'] == True) & (df_filtrado['base_imponible'] > umbral)
        
        # Filtrar por tipo_persona o NIF (Personas Jurídicas)
        if 'tipo_persona' in df_filtrado.columns and (df_filtrado['tipo_persona'] == 'J').any():
            condicion_papel_alto &= (df_filtrado['tipo_persona'] == 'J')
        else:
            # Fallback a NIF
            condicion_papel_alto &= (df_filtrado['nif_emisor'].apply(es_persona_juridica))
            
        # Excluir facturas RECHAZADAS o ANULADAS (para consistencia con Facturas Papel)
        if 'estado' in df_filtrado.columns:
             condicion_papel_alto &= (~df_filtrado['estado'].astype(str).str.upper().isin(['RECHAZADA', 'ANULADA']))
            
        papel_alto = df_filtrado[condicion_papel_alto]
        
        if len(papel_alto) > 0:
            msg = f"🟡 {len(papel_alto)} facturas en papel"
            msg += f" de PJ con BI > {umbral:,}€ (posible incumplimiento)"
            alertas.append({
                'tipo': 'warning',
                'mensaje': msg
            })
    
    # Facturas rechazadas
    if facturas_rechazadas > 0:
        alertas.append({
            'tipo': 'error',
            'mensaje': f"🔴 {facturas_rechazadas} facturas rechazadas requieren análisis"
        })
    
    # Facturas retenidas en FACe
    from utils.data_loader import identificar_facturas_retenidas
    df_retenidas = identificar_facturas_retenidas(
        datos['face'], 
        df_rcf, 
        ids_precalculados=datos.get('ids_face_en_rcf_total')
    )
    retenidas = len(df_retenidas)
    if retenidas > 0:
        alertas.append({
            'tipo': 'warning',
            'mensaje': f"🟡 {retenidas} facturas potencialmente retenidas en FACe"
        })
    
    if alertas:
        for alerta in alertas:
            if alerta['tipo'] == 'error':
                st.error(alerta['mensaje'])
            elif alerta['tipo'] == 'warning':
                st.warning(alerta['mensaje'])
            else:
                st.info(alerta['mensaje'])
    else:
        st.success("✅ No se han detectado alertas en el periodo seleccionado")

    st.markdown("---")

    # === TABLA FACTURAS EJERCICIOS ANTERIORES ===
    st.markdown("### 📜 Facturas de años anteriores registradas en el ejercicio")
    st.info("Estas facturas han sido registradas en el año auditado pero su fecha de expedición/emisión es de años anteriores.")

    import toml
    try:
        config_toml = toml.load(str(Path(__file__).parent.parent / ".streamlit" / "config.toml"))
        ejercicio_auditado = int(config_toml.get('auditoria', {}).get('ejercicio_auditado', 2025))
    except:
        ejercicio_auditado = 2025

    if 'fecha_emision' in df_filtrado.columns and 'fecha_anotacion_rcf' in df_filtrado.columns:
        # Una factura es de "años anteriores" si:
        # 1. Su EJERCICIO es anterior al auditado
        # 2. Su FECHA EMISIÓN es anterior al año auditado
        ejercicio_col = 'ejercicio' if 'ejercicio' in df_filtrado.columns else None
        
        cond_anterior = (df_filtrado['fecha_emision'].dt.year < ejercicio_auditado)
        if ejercicio_col:
            cond_anterior |= (df_filtrado[ejercicio_col] < ejercicio_auditado)
            
        df_anteriores = df_filtrado[cond_anterior].copy()

        if not df_anteriores.empty:
            cols_show = ['entidad', 'id_fra_rcf', 'numero_factura', 'fecha_emision', 'fecha_anotacion_rcf', 'nif_emisor', 'razon_social', 'importe_total']
            df_show = df_anteriores[cols_show].copy()
            df_show.columns = ['Entidad', 'ID RCF', 'Nº Factura', 'Fecha Emisión', 'Fecha Registro RCF', 'NIF Emisor', 'Razón Social', 'Importe (€)']
            
            st.dataframe(
                df_show.style.format({
                    'Importe (€)': '{:,.2f}',
                    'Fecha Emisión': lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else '',
                    'Fecha Registro RCF': lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else ''
                }),
                width="stretch",
                hide_index=True
            )
            st.caption(f"Total: {len(df_anteriores)} facturas de años anteriores.")
        else:
            st.success("No se han encontrado facturas de años anteriores registradas en este ejercicio.")
    else:
        st.warning("No se pueden calcular las facturas de años anteriores por falta de columnas de fecha.")
    
    st.markdown("---")
    
    # Navegación
    st.markdown("### 🧭 Ir a Análisis Detallado")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Facturas Papel", width="stretch"):
            st.switch_page("pages/2_Facturas_Papel.py")
    
    with col2:
        if st.button("⏱️ Anotación RCF", width="stretch"):
            st.switch_page("pages/3_Anotacion_RCF.py")
    
    with col3:
        if st.button("✅ Validaciones", width="stretch"):
            st.switch_page("pages/4_Validaciones.py")
    
    with col4:
        if st.button("📑 Generar Informe", width="stretch"):
            st.switch_page("pages/7_Generar_Informe.py")

if __name__ == "__main__":
    main()