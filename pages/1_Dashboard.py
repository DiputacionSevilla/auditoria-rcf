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

    # === RESUMEN PARA INFORME ===
    st.markdown("### 📝 Resumen para el Informe de Auditoría")
    st.info(
        "Los datos corresponden al **ejercicio completo** (sin filtros de fecha ni oficina), "
        "partiendo de los mismos totales que el Resumen Ejecutivo de la página principal."
    )

    # Nivel 1: total bruto RCF (igual que Resumen Ejecutivo en app.py)
    df_rcf_total = datos['rcf']
    total_rcf    = len(df_rcf_total)

    df_borradas      = df_rcf_total[df_rcf_total['estado'].astype(str).str.upper() == 'BORRADA']
    total_borradas   = len(df_borradas)
    borradas_elec    = len(df_borradas[df_borradas['es_papel'] == False])
    borradas_papel   = len(df_borradas[df_borradas['es_papel'] == True])
    porc_borradas    = (total_borradas / total_rcf * 100) if total_rcf > 0 else 0

    df_vivas     = df_rcf_total[df_rcf_total['estado'].astype(str).str.upper() != 'BORRADA']
    total_vivas  = len(df_vivas)
    n_anulaciones = len(datos['anulaciones'])

    # Nivel 2: desglose de vivas en electrónicas / papel
    df_elec_rcf  = df_vivas[df_vivas['es_papel'] == False]
    df_papel_rcf = df_vivas[df_vivas['es_papel'] == True]
    n_elec_rcf   = len(df_elec_rcf)
    n_papel_rcf  = len(df_papel_rcf)
    porc_elec_inf  = (n_elec_rcf  / total_vivas * 100) if total_vivas > 0 else 0
    porc_papel_inf = (n_papel_rcf / total_vivas * 100) if total_vivas > 0 else 0

    # Nivel 3: desglose de estados (rechazadas/anuladas vs en tramitación)
    estados_neg = ['RECHAZADA', 'ANULADA']
    elec_neg   = len(df_elec_rcf[df_elec_rcf['estado'].astype(str).str.upper().isin(estados_neg)])
    elec_tram  = n_elec_rcf - elec_neg
    papel_neg  = len(df_papel_rcf[df_papel_rcf['estado'].astype(str).str.upper().isin(estados_neg)])
    papel_tram = n_papel_rcf - papel_neg

    # Adicional: anuladas en FACe antes de llegar al RCF
    n_face_anuladas = len(datos.get('face_anuladas_antes_rcf', pd.DataFrame()))

    # --- Métricas en cascada ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Registros RCF", f"{total_rcf:,}")
        st.metric("Facturas Borradas (total)", f"{total_borradas:,}", f"{porc_borradas:.1f}%",
                  delta_color="inverse")
        st.metric("↳ Borradas electrónicas (FACe)", f"{borradas_elec:,}")
        st.metric("↳ Borradas en papel", f"{borradas_papel:,}")
        st.metric("Facturas Vivas", f"{total_vivas:,}")
        st.metric("Anulaciones (FACe)", f"{n_anulaciones:,}")
        if n_face_anuladas > 0:
            st.metric("Anuladas en FACe antes del RCF", f"{n_face_anuladas:,}")
    with col2:
        st.metric("Electrónicas vivas (FACe → RCF)", f"{n_elec_rcf:,}", f"{porc_elec_inf:.1f}% s/vivas")
        st.metric("↳ Rechazadas/anuladas", f"{elec_neg:,}")
        st.metric("↳ En tramitación o pagadas", f"{elec_tram:,}")
    with col3:
        st.metric("En papel vivas", f"{n_papel_rcf:,}", f"{porc_papel_inf:.1f}% s/vivas")
        st.metric("↳ Rechazadas/anuladas", f"{papel_neg:,}")
        st.metric("↳ En tramitación o pagadas", f"{papel_tram:,}")

    # --- Cuadro de desglose por entidad ---
    st.markdown("#### Desglose de facturas vivas por entidad")
    if 'entidad' in df_vivas.columns:
        tabla_entidad = (
            df_vivas.groupby('entidad')
            .apply(lambda g: pd.Series({
                'Facturas FACe':  int((g['es_papel'] == False).sum()),
                'Facturas Papel': int((g['es_papel'] == True).sum()),
            }))
            .reset_index()
            .rename(columns={'entidad': 'Entidad'})
        )
        tabla_entidad['Total'] = tabla_entidad['Facturas FACe'] + tabla_entidad['Facturas Papel']
        tabla_entidad = tabla_entidad.sort_values('Total', ascending=False)

        # Fila de totales
        fila_total = pd.DataFrame([{
            'Entidad': 'TOTAL',
            'Facturas FACe':  tabla_entidad['Facturas FACe'].sum(),
            'Facturas Papel': tabla_entidad['Facturas Papel'].sum(),
            'Total':          tabla_entidad['Total'].sum(),
        }])
        tabla_display = pd.concat([tabla_entidad, fila_total], ignore_index=True)

        st.dataframe(
            tabla_display.style.format({
                'Facturas FACe':  '{:,}',
                'Facturas Papel': '{:,}',
                'Total':          '{:,}',
            }).apply(
                lambda x: ['font-weight: bold'] * len(x)
                if x['Entidad'] == 'TOTAL' else [''] * len(x),
                axis=1
            ),
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("La columna 'entidad' no está disponible en los datos del RCF.")

    # --- Cálculos para el párrafo (total bruto, borradas absorbidas en el desglose) ---
    # El párrafo parte del total bruto y desglosa estados sobre el total (incluyendo borradas)
    df_elec_all  = df_rcf_total[df_rcf_total['es_papel'] == False]
    df_papel_all = df_rcf_total[df_rcf_total['es_papel'] == True]
    n_elec_all   = len(df_elec_all)
    n_papel_all  = len(df_papel_all)
    porc_elec_p  = (n_elec_all  / total_rcf * 100) if total_rcf > 0 else 0
    porc_papel_p = (n_papel_all / total_rcf * 100) if total_rcf > 0 else 0

    # Estados negativos: BORRADA + RECHAZADA + ANULADA (se agrupan en "rechazadas/anuladas")
    estados_neg_p = ['BORRADA', 'RECHAZADA', 'ANULADA']
    elec_neg_p   = len(df_elec_all[df_elec_all['estado'].astype(str).str.upper().isin(estados_neg_p)])
    elec_tram_p  = n_elec_all - elec_neg_p
    papel_neg_p  = len(df_papel_all[df_papel_all['estado'].astype(str).str.upper().isin(estados_neg_p)])
    papel_tram_p = n_papel_all - papel_neg_p

    # --- Párrafo listo para copiar ---
    ejercicio = CONFIGURACION.get('ejercicio_auditado', '2025')
    frase_anuladas_face = (
        f" Adicionalmente, {n_face_anuladas:,} facturas registradas en FACe fueron anuladas "
        f"antes de su descarga al RCF."
        if n_face_anuladas > 0 else ""
    )
    parrafo = (
        f"Entrando ya a exponer los resultados arrojados por las pruebas realizadas con respecto al presente "
        f"apartado lo primero a reseñar es que de los datos proporcionados por el RCF para el ejercicio "
        f"{ejercicio} se desprende la recepción de un total de {total_rcf:,} facturas, de las cuales "
        f"{n_elec_all:,} ({porc_elec_p:.2f}%) han sido recibidas por FACe en formato electrónico y "
        f"{n_papel_all:,} ({porc_papel_p:.2f}%) han sido recibidas en papel.{frase_anuladas_face} "
        f"Desglosando el total de facturas en función de su estado de tramitación, de las "
        f"{n_elec_all:,} facturas electrónicas, {elec_neg_p:,} se encuentran rechazadas/anuladas y "
        f"{elec_tram_p:,} se encuentran en tramitación o han sido pagadas, y de las {n_papel_all:,} "
        f"facturas recibidas en papel, {papel_neg_p:,} se encuentran rechazadas y "
        f"{papel_tram_p:,} se encuentran en tramitación o han sido pagadas."
    )

    st.markdown("**Párrafo para el informe** (selecciona el texto y cópialo):")
    st.text_area(
        label="Párrafo",
        value=parrafo,
        height=220,
        label_visibility="collapsed"
    )

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