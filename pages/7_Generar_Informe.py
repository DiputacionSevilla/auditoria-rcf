"""
Generador de Informe Final - Consolidación de todos los análisis
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import COLORES, CONFIGURACION, CONFIGURACION_INFORME
from utils.report_generator import generar_informe_word, generar_informe_pdf

st.set_page_config(
    page_title="Generar Informe - Auditoría RCF",
    page_icon="📑",
    layout="wide"
)

def main():
    st.title("📑 Generador de Informe de Auditoría")
    st.markdown("Consolidación y generación del informe final según la Guía IGAE")
    
    # Verificar datos
    if 'datos' not in st.session_state:
        st.warning("⚠️ No hay datos cargados. Por favor, carga los archivos en la página principal.")
        if st.button("Ir a página principal"):
            st.switch_page("app.py")
        return
    
    datos = st.session_state['datos']
    
    # Verificar análisis realizados
    if 'analisis' not in st.session_state:
        st.session_state['analisis'] = {}
    
    analisis = st.session_state['analisis']
    
    st.markdown("---")
    
    # === ESTADO DE LOS ANÁLISIS ===
    st.markdown("### 📊 Estado de los Análisis")
    st.info("Verifica que todos los análisis se hayan completado antes de generar el informe")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### ✅ Análisis Completados")
        
        secciones = {
            'facturas_papel': '📄 Facturas en Papel',
            'anotacion': '⏱️ Anotación en RCF',
            'validaciones': '✅ Validaciones',
            'tramitacion': '🔄 Tramitación',
            'obligaciones': '📋 Obligaciones'
        }
        
        completados = 0
        for key, nombre in secciones.items():
            if key in analisis:
                st.success(f"✅ {nombre}")
                completados += 1
            else:
                st.warning(f"⏳ {nombre}")
        
        st.metric("Progreso", f"{completados}/5", f"{completados*20}%")
    
    with col2:
        st.markdown("#### 📈 Estadísticas Generales")
        
        total_facturas = len(datos['rcf'])
        facturas_electronicas = len(datos['rcf'][datos['rcf']['es_papel'] == False])
        facturas_papel = len(datos['rcf'][datos['rcf']['es_papel'] == True])
        
        st.metric("Total Facturas", f"{total_facturas:,}")
        st.metric("Electrónicas", f"{facturas_electronicas:,}")
        st.metric("En Papel", f"{facturas_papel:,}")
    
    with col3:
        st.markdown("#### 🔍 Hallazgos Principales")
        
        if 'facturas_papel' in analisis:
            sospechosas = analisis['facturas_papel'].get('total_sospechosas', 0)
            st.metric("Facturas Papel Sospechosas", f"{sospechosas:,}")
        
        if 'anotacion' in analisis:
            retenidas = analisis['anotacion'].get('facturas_retenidas', 0)
            st.metric("Facturas Retenidas", f"{retenidas:,}")
            n_s_post = analisis['anotacion'].get('n_s_postcambio', 0)
            if n_s_post > 0:
                st.metric("S post-cambio (alerta)", f"{n_s_post:,}", delta=str(n_s_post), delta_color="inverse")
        
        if 'obligaciones' in analisis:
            pendientes_3m = analisis['obligaciones'].get('facturas_3_meses', 0)
            st.metric("Pendientes >3 Meses", f"{pendientes_3m:,}")
    
    st.markdown("---")
    
    # === CONFIGURACIÓN DEL INFORME ===
    st.markdown("### ⚙️ Configuración del Informe")
    
    col1, col2 = st.columns(2)
    
    with col1:
        formato_informe = st.selectbox(
            "Formato del Informe",
            ["Word (DOCX) - Completo", "PDF - Ejecutivo"],
            help="Word incluye análisis completo, PDF es versión ejecutiva resumida"
        )
    
    with col2:
        incluir_graficos = st.checkbox(
            "Incluir gráficos",
            value=True,
            help="Incluir visualizaciones en el informe"
        )
    
    # Opciones avanzadas
    with st.expander("🔧 Opciones Avanzadas"):
        st.markdown("#### Secciones a Incluir")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            incluir_resumen = st.checkbox("Resumen Ejecutivo", value=True)
            incluir_papel = st.checkbox("Facturas en Papel", value=True)
            incluir_anotacion = st.checkbox("Anotación RCF", value=True)
        
        with col2:
            incluir_validaciones = st.checkbox("Validaciones", value=True)
            incluir_tramitacion = st.checkbox("Tramitación", value=True)
            incluir_obligaciones = st.checkbox("Obligaciones", value=True)
        
        with col3:
            incluir_conclusiones = st.checkbox("Conclusiones", value=True)
            incluir_recomendaciones = st.checkbox("Recomendaciones", value=True)
            incluir_anexos = st.checkbox("Anexos", value=False)
        
        st.markdown("---")
        
        st.markdown("#### Información del Auditor")
        
        col1, col2 = st.columns(2)
        
        with col1:
            autor = st.text_input(
                "Autor del Informe",
                value=CONFIGURACION_INFORME['autor'],
                help="Nombre del responsable de la auditoría"
            )
        
        with col2:
            cargo = st.text_input(
                "Cargo",
                value="Interventor/a",
                help="Cargo del responsable"
            )
    
    st.markdown("---")
    
    # === VISTA PREVIA ===
    st.markdown("### 👀 Vista Previa del Contenido")
    
    with st.expander("📄 Estructura del Informe"):
        st.markdown("""
        ### INFORME DE AUDITORÍA DEL REGISTRO CONTABLE DE FACTURAS
        
        #### 1. RESUMEN EJECUTIVO
        - Cifras principales
        - Principales hallazgos
        - Conclusiones generales
        
        #### 2. INTRODUCCIÓN
        - Marco normativo
        - Objetivos de la auditoría
        - Alcance y metodología
        - Archivos analizados
        
        #### 3. FACTURAS EN PAPEL (Sección V.1)
        - Análisis de cumplimiento normativo
        - Evolución temporal
        - Top 10 facturas por importe
        - Rankings de proveedores y unidades
        - Identificación de incumplimientos
        
        #### 4. ANOTACIÓN EN RCF (Sección V.2)
        - Facturas retenidas en FACe
        - Tiempos de anotación
        - Estadísticas mensuales
        - Facturas con mayor demora
        - Rankings por unidad
        
        #### 5. VALIDACIONES DE CONTENIDO (Sección V.3)
        - Aplicación Orden HAP/1650/2015
        - Resumen de las 8 validaciones
        - Incumplimientos detectados
        - Análisis de causas de rechazo
        
        #### 6. TRAMITACIÓN DE FACTURAS (Sección V.4)
        - Solicitudes de anulación
        - Evolución de estados
        - Tiempos medios por estado
        - Reconocimiento de obligación
        - Análisis de pagos
        
        #### 7. OBLIGACIONES DE CONTROL (Sección V.5)
        - Facturas pendientes >3 meses
        - Análisis de morosidad
        - Rankings de unidades
        - Verificación de controles
        
        #### 8. CONCLUSIONES Y RECOMENDACIONES
        - Síntesis de hallazgos
        - Valoración de cumplimiento
        - Áreas de mejora identificadas
        - Recomendaciones priorizadas
        
        #### 9. ANEXOS (opcional)
        - Tablas detalladas
        - Listados completos
        - Referencias normativas
        """)
    
    st.markdown("---")

    # === CUADRO RESUMEN EJECUTIVO AÑO DE TRANSICIÓN 2025 ===
    st.markdown("### 📋 Cuadro Resumen Ejecutivo — Año de Transición 2025")
    st.info("Este cuadro refleja los dos procedimientos coexistentes durante 2025 y permite evaluar la eficacia de la medida correctora.")

    if 'anotacion' in analisis and 'tramitacion' in analisis:
        anot = analisis['anotacion']
        tram = analisis['tramitacion']
        fecha_cambio_res = anot.get('fecha_cambio_procedimiento', 'No configurada')

        def _fmtv(val, es_tiempo=False):
            if val is None:
                return '—'
            try:
                v = float(val)
                if es_tiempo:
                    return f'{v/1440:.1f} d' if v >= 1440 else f'{v:.0f} min'
                return f'{int(v):,}'
            except Exception:
                return str(val)

        filas_res = [
            ('Facturas electrónicas recibidas FACe',
             _fmtv(anot.get('n_facturas_s', 0)),
             _fmtv(anot.get('n_facturas_f_directo', 0)),
             'Universo analizado'),
            ('Facturas con estado previo S',
             _fmtv(anot.get('n_facturas_s', 0)),
             _fmtv(anot.get('n_s_postcambio', 0)),
             'Tras el cambio el valor esperado es 0'),
            ('Facturas con anotación F',
             _fmtv(anot.get('n_facturas_s_con_f', 0)),
             _fmtv(anot.get('n_facturas_f_directo', 0)),
             'En nuevo régimen debe ser anotación directa'),
            ('Rechazos en fase de validación',
             '—',
             _fmtv(anot.get('n_rechazadas_nuevo', 0)),
             'Revisar causas y trazabilidad'),
            ('Tiempo técnico FACe–S',
             _fmtv(anot.get('tiempo_medio_face_s_min'), es_tiempo=True),
             'No aplica',
             'Solo procedimiento anterior'),
            ('Tiempo permanencia S–F',
             _fmtv(anot.get('tiempo_medio_s_f_min'), es_tiempo=True),
             'No aplica',
             'Impacto de incidencia anterior'),
            ('Tiempo inscripción FACe–F directo',
             _fmtv(anot.get('tiempo_medio_face_f_anterior_min'), es_tiempo=True),
             _fmtv(anot.get('tiempo_medio_face_f_nuevo_min'), es_tiempo=True),
             'Indicador del nuevo procedimiento'),
            ('Tiempo posterior F–aceptación/conformidad',
             '—',
             _fmtv(tram.get('tiempo_medio_f_aceptacion_min'), es_tiempo=True),
             'Tramitación posterior (Apartado 4)'),
            ('Facturas FACe retenidas',
             _fmtv(anot.get('facturas_retenidas', 0)),
             '0',
             'Debe ser 0'),
            ('Incidencias sin justificar',
             _fmtv(anot.get('n_fechas_negativas', 0)),
             _fmtv(anot.get('n_s_postcambio', 0)),
             'Requieren actuación auditora'),
        ]

        th_res = 'background:#1f4e79;color:white;padding:7px 10px;border:1px solid #555;text-align:center;white-space:nowrap;font-size:13px;'
        th_lbl = 'background:#1f4e79;color:white;padding:7px 14px;border:1px solid #555;text-align:left;min-width:280px;font-size:13px;'
        td_res = 'padding:6px 10px;border:1px solid #ccc;text-align:center;font-size:13px;'
        td_lbl = 'padding:6px 14px;border:1px solid #ccc;text-align:left;font-size:13px;'
        td_val = 'padding:6px 10px;border:1px solid #ccc;text-align:left;font-size:12px;color:#555;'

        thead_res = (
            f'<thead><tr>'
            f'<th style="{th_lbl}">Bloque de análisis</th>'
            f'<th style="{th_res}">Procedimiento anterior<br><small>hasta {fecha_cambio_res}</small></th>'
            f'<th style="{th_res}">Procedimiento nuevo<br><small>desde {fecha_cambio_res}</small></th>'
            f'<th style="{th_res}">Valoración</th>'
            f'</tr></thead>'
        )
        rows_res = ''
        for i, (lbl, v_ant, v_nvo, obs) in enumerate(filas_res):
            bg = 'background:#f5f9ff;' if i % 2 == 0 else ''
            rows_res += (
                f'<tr>'
                f'<td style="{td_lbl}{bg}">{lbl}</td>'
                f'<td style="{td_res}{bg}">{v_ant}</td>'
                f'<td style="{td_res}{bg}">{v_nvo}</td>'
                f'<td style="{td_val}{bg}">{obs}</td>'
                f'</tr>'
            )

        st.markdown(
            f'<table style="border-collapse:collapse;font-size:13px;width:100%;">'
            f'{thead_res}<tbody>{rows_res}</tbody></table>',
            unsafe_allow_html=True
        )

        # Valoración semáforo
        n_s_post_val = anot.get('n_s_postcambio', 0)
        n_sin_causa = anot.get('n_rechazadas_sin_causa', 0)
        n_ret = anot.get('facturas_retenidas', 0)
        if n_s_post_val == 0 and n_sin_causa == 0 and n_ret == 0:
            st.success(f"✅ La medida correctora implantada el {fecha_cambio_res} puede considerarse eficaz: no se detectan códigos S posteriores al cambio, facturas retenidas ni rechazos sin causa acreditada.")
        else:
            partes = []
            if n_s_post_val > 0:
                partes.append(f"{n_s_post_val} facturas con código S posteriores al cambio")
            if n_sin_causa > 0:
                partes.append(f"{n_sin_causa} rechazos sin causa acreditada")
            if n_ret > 0:
                partes.append(f"{n_ret} facturas retenidas en FACe")
            st.error(f"⚠️ No se puede afirmar la plena eficacia de la medida correctora. Incidencias detectadas: {'; '.join(partes)}.")
    else:
        st.warning("Completa los análisis de **Anotación RCF** (página 3) y **Tramitación** (página 5) para ver el cuadro resumen.")

    st.markdown("---")

    # === GENERACIÓN DEL INFORME ===
    st.markdown("### 🚀 Generar Informe")
    
    if completados < 5:
        st.warning(f"""
        ⚠️ **Atención**: Solo se han completado {completados} de 5 análisis.
        
        Se recomienda navegar por todas las secciones antes de generar el informe para 
        asegurar que todos los datos estén disponibles.
        
        **Secciones pendientes:**
        """)
        
        for key, nombre in secciones.items():
            if key not in analisis:
                st.markdown(f"- {nombre}")
        
        st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Generar Informe Word", type="primary", width="stretch"):
            if formato_informe.startswith("Word"):
                with st.spinner("Generando informe Word... Esto puede tardar unos segundos."):
                    try:
                        # Generar informe
                        informe_bytes = generar_informe_word(datos, analisis)
                        
                        # Botón de descarga
                        fecha_str = datetime.now().strftime("%Y%m%d")
                        nombre_archivo = f"Informe_Auditoria_RCF_{fecha_str}.docx"
                        
                        st.success("✅ Informe Word generado correctamente")
                        
                        st.download_button(
                            label="📥 Descargar Informe Word",
                            data=informe_bytes,
                            file_name=nombre_archivo,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error al generar el informe: {str(e)}")
                        st.exception(e)
    
    with col2:
        if st.button("📕 Generar Informe PDF", type="primary", width="stretch"):
            if formato_informe.startswith("PDF") or True:  # Permitir generar PDF siempre
                with st.spinner("Generando informe PDF... Esto puede tardar unos segundos."):
                    try:
                        # Generar informe
                        informe_bytes = generar_informe_pdf(datos, analisis)
                        
                        # Botón de descarga
                        fecha_str = datetime.now().strftime("%Y%m%d")
                        nombre_archivo = f"Informe_Auditoria_RCF_Ejecutivo_{fecha_str}.pdf"
                        
                        st.success("✅ Informe PDF generado correctamente")
                        
                        st.download_button(
                            label="📥 Descargar Informe PDF",
                            data=informe_bytes,
                            file_name=nombre_archivo,
                            mime="application/pdf"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error al generar el informe: {str(e)}")
                        st.exception(e)
    
    with col3:
        if st.button("📊 Generar Ambos Formatos", width="stretch"):
            with st.spinner("Generando ambos informes..."):
                try:
                    fecha_str = datetime.now().strftime("%Y%m%d")
                    
                    # Generar Word
                    informe_word = generar_informe_word(datos, analisis)
                    nombre_word = f"Informe_Auditoria_RCF_{fecha_str}.docx"
                    
                    # Generar PDF
                    informe_pdf = generar_informe_pdf(datos, analisis)
                    nombre_pdf = f"Informe_Auditoria_RCF_Ejecutivo_{fecha_str}.pdf"
                    
                    st.success("✅ Ambos informes generados correctamente")
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.download_button(
                            label="📥 Descargar Word",
                            data=informe_word,
                            file_name=nombre_word,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    
                    with col_b:
                        st.download_button(
                            label="📥 Descargar PDF",
                            data=informe_pdf,
                            file_name=nombre_pdf,
                            mime="application/pdf"
                        )
                    
                except Exception as e:
                    st.error(f"❌ Error al generar los informes: {str(e)}")
                    st.exception(e)
    
    st.markdown("---")
    
    # === INFORMACIÓN ADICIONAL ===
    st.markdown("### ℹ️ Información del Informe")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📋 Contenido Incluido")
        st.markdown("""
        **Informe Word (Completo):**
        - Todas las secciones de análisis
        - Tablas detalladas con datos
        - Referencias normativas
        - Conclusiones y recomendaciones
        - ~30-50 páginas
        
        **Informe PDF (Ejecutivo):**
        - Resumen ejecutivo
        - Principales hallazgos
        - Tablas resumen
        - Conclusiones principales
        - ~10-15 páginas
        """)
    
    with col2:
        st.markdown("#### 🎯 Recomendaciones de Uso")
        st.markdown("""
        **Antes de generar:**
        1. ✅ Carga los 4 archivos Excel
        2. ✅ Navega por todas las secciones
        3. ✅ Revisa los análisis
        4. ✅ Verifica las alertas
        
        **Después de generar:**
        - Revisa el informe generado
        - Ajusta conclusiones si es necesario
        - Complementa con observaciones adicionales
        - Añade anexos manuales si procede
        """)
    
    st.markdown("---")
    
    # === EXPORTACIÓN DE DATOS COMPLEMENTARIOS ===
    st.markdown("### 📦 Exportación de Datos Complementarios")
    st.info("Exporta todos los datos de análisis en formato Excel para anexos o análisis adicional")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Exportar Datos RCF Completos", width="stretch"):
            from utils.data_loader import exportar_a_excel
            excel_bytes = exportar_a_excel(datos['rcf'], "RCF_Completo")
            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name="datos_rcf_completo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("📥 Exportar Resumen Análisis", width="stretch"):
            # Crear DataFrame resumen
            resumen_data = {
                'Sección': [],
                'Métrica': [],
                'Valor': []
            }
            
            for seccion, datos_seccion in analisis.items():
                for metrica, valor in datos_seccion.items():
                    if isinstance(valor, (int, float)):
                        resumen_data['Sección'].append(seccion)
                        resumen_data['Métrica'].append(metrica)
                        resumen_data['Valor'].append(valor)
            
            df_resumen = pd.DataFrame(resumen_data)
            
            from utils.data_loader import exportar_a_excel
            excel_bytes = exportar_a_excel(df_resumen, "Resumen_Analisis")
            st.download_button(
                label="Descargar Excel",
                data=excel_bytes,
                file_name="resumen_analisis.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col3:
        if st.button("📥 Exportar Todo (ZIP)", width="stretch"):
            st.info("Funcionalidad próximamente: Exportará todos los análisis en un archivo ZIP")
    
    st.markdown("---")
    
    # === PIE DE PÁGINA ===
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px; margin-top: 40px;'>
        <p><strong>📊 Sistema de Auditoría RCF - Diputación de Sevilla</strong></p>
        <p>Basado en la Guía IGAE para auditorías de Registros Contables de Facturas</p>
        <p style='font-size: 0.9em;'>Ley 25/2013 | Orden HAP/492/2014 | Orden HAP/1650/2015</p>
        <hr style='width: 50%; margin: 20px auto;'>
        <p style='font-size: 0.8em;'>Generado el {}</p>
    </div>
    """.format(datetime.now().strftime('%d/%m/%Y %H:%M:%S')), unsafe_allow_html=True)

if __name__ == "__main__":
    main()