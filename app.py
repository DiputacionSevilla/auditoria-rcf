import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os

# Añadir el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from config.settings import CONFIGURACION, COLORES
from utils.data_loader import cargar_datos, validar_archivos

# Configuración de la página
st.set_page_config(
    page_title="Auditoría RCF - Diputación de Sevilla",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown(f"""
    <style>
    /* El fondo se maneja automáticamente por el tema de Streamlit */
    .stMetric {{
        background-color: rgba(128, 128, 128, 0.1);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid {COLORES['primario']};
    }}
    h1 {{
        color: {COLORES['primario']};
    }}
    h2 {{
        color: {COLORES['secundario']};
    }}
    .upload-info {{
        background-color: rgba(23, 162, 184, 0.1);
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid {COLORES['primario']};
    }}
    </style>
""", unsafe_allow_html=True)

def main():
    # Título principal
    st.title("🏛️ Sistema de Auditoría de Facturas Electrónicas")
    st.subheader("Registro Contable de Facturas (RCF) - Diputación de Sevilla")
    
    st.markdown("---")
    
    # Información de bienvenida
    st.info("""
    **📋 Guía de uso:**
    1. Carga los 4 archivos Excel requeridos en la barra lateral
    2. La aplicación validará automáticamente los datos
    3. Navega por las diferentes secciones usando el menú lateral
    4. Genera el informe completo en la última sección
    """)
    
    # Configuración de rutas por defecto
    DATOS_DIR = Path("datos")
    RUTAS_DEFAULT = {
        'rcf': DATOS_DIR / "ftras-RCF.xlsx",
        'face': DATOS_DIR / "2-Ftras FACe.xlsx",
        'anulaciones': DATOS_DIR / "4-Anulacion de ftras.xlsx",
        'estados': DATOS_DIR / "5-Cambio de estado de facturas.xlsx"
    }
    
    # Sidebar - Carga de archivos
    st.sidebar.title("📁 Gestión de Datos")
    
    def obtener_archivo_y_estado(clave, etiqueta, help_text):
        archivo_subido = st.sidebar.file_uploader(etiqueta, type=['xlsx'], help=help_text)
        ruta_local = RUTAS_DEFAULT[clave]
        existe_local = ruta_local.exists()
        
        if archivo_subido:
            st.sidebar.caption(f"✅ Usando archivo subido: `{archivo_subido.name}`")
            return archivo_subido, True
        elif existe_local:
            st.sidebar.caption(f"🏠 Detectado en local: `{ruta_local.name}`")
            return ruta_local, True
        else:
            st.sidebar.warning(f"⚠️ Falta archivo: `{ruta_local.name}`")
            return None, False

    st.sidebar.markdown("### 1️⃣ Facturas RCF")
    archivo_rcf, rcf_ok = obtener_archivo_y_estado('rcf', "Subir ftras-RCF.xlsx", "Archivo con todas las facturas del RCF")
    
    st.sidebar.markdown("### 2️⃣ Facturas FACe")
    archivo_face, face_ok = obtener_archivo_y_estado('face', "Subir Facturas FACe", "Facturas registradas en la plataforma FACe")
    
    st.sidebar.markdown("### 3️⃣ Anulaciones")
    archivo_anulaciones, anul_ok = obtener_archivo_y_estado('anulaciones', "Subir Anulaciones", "Solicitudes de anulación de facturas")
    
    st.sidebar.markdown("### 4️⃣ Cambios de Estado")
    archivo_estados, est_ok = obtener_archivo_y_estado('estados', "Subir Cambios de Estado", "Histórico de cambios de estado de facturas")
    
    # Verificar si tenemos todos los archivos (ya sean locales o subidos)
    todos_disponibles = all([rcf_ok, face_ok, anul_ok, est_ok])
    
    st.sidebar.markdown("---")
    
    # Botón para procesar / inicializar
    col_btn1, col_btn2 = st.sidebar.columns(2)
    
    with col_btn1:
        btn_procesar = st.button("🔄 Procesar Datos", type="primary", width="stretch", disabled=not todos_disponibles)
    
    with col_btn2:
        if st.button("🗑️ Inicializar", width="stretch", help="Limpia los datos cargados en memoria y vuelve al estado inicial"):
            for key in ['datos', 'validacion', 'datos_procesados']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    if btn_procesar:
        with st.spinner("Procesando archivos..."):
            try:
                # Cargar datos
                datos = cargar_datos(
                    archivo_rcf,
                    archivo_face,
                    archivo_anulaciones,
                    archivo_estados
                )
                
                # Validar archivos
                validacion = validar_archivos(datos)
                
                # Guardar en session_state
                st.session_state['datos'] = datos
                st.session_state['validacion'] = validacion
                st.session_state['datos_procesados'] = True
                
                st.sidebar.success("✅ Datos procesados correctamente")
                st.rerun()
                
            except Exception as e:
                st.sidebar.error(f"❌ Error al procesar: {str(e)}")
    
    # Contenido principal
    if 'datos_procesados' in st.session_state and st.session_state['datos_procesados']:
        mostrar_resumen_ejecutivo()
    else:
        mostrar_informacion_inicial()

def mostrar_informacion_inicial():
    """Muestra información cuando no hay datos cargados"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Funcionalidades")
        st.markdown("""
        - ✅ **Dashboard Ejecutivo**: Visualización de KPIs principales
        - 📄 **Facturas en Papel**: Análisis de cumplimiento normativo
        - ⏱️ **Anotación RCF**: Tiempos de inscripción y retenciones
        - ✅ **Validaciones**: Cumplimiento Orden HAP/1650/2015
        - 🔄 **Tramitación**: Análisis de estados y anulaciones
        - 📋 **Obligaciones**: Control de facturas pendientes
        - 📑 **Informe Final**: Generación automática del informe
        """)
    
    with col2:
        st.markdown("### 📋 Marco Legal")
        st.markdown("""
        - **Ley 25/2013**: Impulso factura electrónica
        - **Orden HAP/492/2014**: Requisitos funcionales RCF
        - **Orden HAP/1074/2014**: Regulación PGEFe
        - **Orden HAP/1650/2015**: Modificaciones y validaciones
        - **Circular 1/2015 IGAE**: Obligatoriedad
        """)
    
    st.markdown("---")
    
    # Información sobre archivos requeridos
    st.markdown("### 📁 Archivos Requeridos")
    
    st.markdown("""
    | Archivo | Descripción | Campos principales |
    |---------|-------------|-------------------|
    | **ftras-RCF.xlsx** | Facturas del RCF | ID_FACE, fecha_emision, importe, NIF, OC/OG/UT |
    | **Facturas FACe** | Registro FACe | registro, fecha_registro, nif_emisor, importe |
    | **Anulaciones** | Solicitudes anulación | registro, fecha_solicitud, comentario |
    | **Estados** | Histórico estados | registro, codigo_estado, fecha_cambio |
    """)
    
    st.info("💡 **Nota**: Las facturas en papel se identifican por tener el campo ID_FACE vacío")

def mostrar_resumen_ejecutivo():
    """Muestra resumen ejecutivo cuando hay datos cargados"""
    
    datos = st.session_state['datos']
    validacion = st.session_state['validacion']
    
    st.success("✅ Datos cargados y validados correctamente")
    
    # Métricas principales
    st.markdown("### 📊 Resumen Ejecutivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_facturas = len(datos['rcf'])
        st.metric(
            "Total Registros RCF",
            f"{total_facturas:,}",
            help="Total de registros cargados en el RCF (incluidos borrados)"
        )
    
    with col2:
        df_vivas_global = datos['rcf'][datos['rcf']['estado'].astype(str).str.upper() != 'BORRADA']
        total_vivas = len(df_vivas_global)
        st.metric(
            "Facturas Vivas",
            f"{total_vivas:,}",
            help="Facturas para análisis (excluyendo estado BORRADA)"
        )
        
    with col3:
        # Borradas
        total_borradas = total_facturas - total_vivas
        porcentaje_borradas = (total_borradas / total_facturas * 100) if total_facturas > 0 else 0
        st.metric(
            "Facturas Borradas",
            f"{total_borradas:,}",
            f"{porcentaje_borradas:.1f}%",
            delta_color="inverse"
        )
    
    with col4:
        anulaciones = len(datos['anulaciones'])
        st.metric(
            "Anulaciones (FACe)",
            f"{anulaciones:,}",
            help="Solicitudes de anulación registradas en el archivo de Anulaciones"
        )
    
    st.markdown("---")
    
    # Validaciones
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Estado de Validación")
        
        if validacion['errores']:
            st.error("**❌ Errores encontrados:**")
            for error in validacion['errores']:
                st.markdown(f"- {error}")
        
        if validacion['warnings']:
            st.warning("**⚠️ Advertencias:**")
            for warning in validacion['warnings']:
                st.markdown(f"- {warning}")
        
        if not validacion['errores'] and not validacion['warnings']:
            st.success("✅ Todos los archivos validados correctamente")
    
    with col2:
        st.markdown("### 📅 Periodo de Análisis")
        
        if 'fecha_emision' in datos['rcf'].columns:
            fecha_min = pd.to_datetime(datos['rcf']['fecha_emision']).min()
            fecha_max = pd.to_datetime(datos['rcf']['fecha_emision']).max()
            
            st.info(f"""
            **Fecha inicio:** {fecha_min.strftime('%d/%m/%Y')}  
            **Fecha fin:** {fecha_max.strftime('%d/%m/%Y')}  
            **Días:** {(fecha_max - fecha_min).days}
            """)
    
    st.markdown("---")
    
    # Navegación rápida
    st.markdown("### 🧭 Navegación Rápida")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Dashboard", width="stretch"):
            st.switch_page("pages/1_Dashboard.py")
    
    with col2:
        if st.button("📄 Facturas Papel", width="stretch"):
            st.switch_page("pages/2_Facturas_Papel.py")
    
    with col3:
        if st.button("⏱️ Anotación RCF", width="stretch"):
            st.switch_page("pages/3_Anotacion_RCF.py")
    
    with col4:
        if st.button("📑 Generar Informe", width="stretch"):
            st.switch_page("pages/7_Generar_Informe.py")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p>📊 Sistema de Auditoría RCF - Diputación de Sevilla</p>
        <p>Basado en la Guía IGAE para auditorías de Registros Contables de Facturas</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()