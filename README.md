# 📊 Sistema de Auditoría de Facturas Electrónicas RCF

Aplicación web desarrollada con Streamlit para realizar auditorías del Registro Contable de Facturas (RCF) según la **Guía IGAE** para auditorías de sistemas en el ámbito de la Administración Pública.

## 🎯 Características

### ✅ Análisis Completos
- **Facturas en Papel**: Cumplimiento obligatoriedad factura electrónica (Ley 25/2013)
- **Anotación en RCF**: Tiempos de inscripción y facturas retenidas
- **Validaciones**: Orden HAP/1650/2015 (8 validaciones obligatorias)
- **Tramitación**: Anulaciones, estados y reconocimiento de obligación
- **Obligaciones**: Control de morosidad y facturas >3 meses

### 📊 Dashboard Interactivo
- KPIs principales en tiempo real
- Gráficos interactivos con Plotly
- Filtros dinámicos por fecha y unidad
- Exportación a Excel de cualquier tabla

### 📑 Generación de Informes
- **Informe Word completo** (~30-50 páginas)
- **Informe PDF ejecutivo** (~10-15 páginas)
- Estructura según Guía IGAE
- Conclusiones y recomendaciones

## 🚀 Instalación

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación Rápida

**Windows:**
```batch
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### Instalación Manual
```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar aplicación
streamlit run app.py
```

## 📁 Archivos Requeridos

La aplicación necesita 4 archivos Excel:

1. **ftras-RCF.xlsx**: Facturas del RCF
2. **Facturas_FACe.xlsx**: Facturas de la plataforma FACe
3. **Anulaciones.xlsx**: Solicitudes de anulación
4. **Cambios_Estado.xlsx**: Histórico de estados

## 🖥️ Uso

1. **Iniciar la aplicación:**
```bash
   streamlit run app.py
```

2. **Acceder en el navegador:**
```
   http://localhost:8501
```

3. **Cargar archivos:**
   - Usa el sidebar para subir los 4 archivos Excel
   - Haz clic en "Procesar Datos"

4. **Navegar por las secciones:**
   - Dashboard: Vista general
   - Facturas Papel: Análisis cumplimiento
   - Anotación RCF: Tiempos de inscripción
   - Validaciones: Orden HAP/1650/2015
   - Tramitación: Estados y anulaciones
   - Obligaciones: Control morosidad
   - Generar Informe: Crear informe final

5. **Exportar resultados:**
   - Cada tabla tiene botón de exportación
   - Genera informes Word/PDF completos

## 📋 Estructura del Proyecto
```
auditoria_rcf/
├── app.py                          # Aplicación principal
├── requirements.txt                # Dependencias
├── README.md                       # Documentación
├── setup.sh / setup.bat           # Scripts instalación
├── config/
│   └── settings.py                 # Configuración
├── utils/
│   ├── data_loader.py             # Carga de datos
│   ├── validaciones.py            # Validaciones HAP
│   └── report_generator.py        # Generador informes
└── pages/
    ├── 1_📊_Dashboard.py
    ├── 2_📄_Facturas_Papel.py
    ├── 3_⏱️_Anotacion_RCF.py
    ├── 4_✅_Validaciones.py
    ├── 5_🔄_Tramitacion.py
    ├── 6_📋_Obligaciones.py
    └── 7_📑_Generar_Informe.py
```

## ⚙️ Configuración

Edita `config/settings.py` para personalizar:

- Nombre de la entidad
- Ejercicio auditado
- Umbrales de alertas
- Colores corporativos
- Textos del informe

## 📖 Marco Legal

- **Ley 25/2013**: Impulso de la factura electrónica
- **Orden HAP/492/2014**: Requisitos funcionales RCF
- **Orden HAP/1074/2014**: Regulación PGEFe
- **Orden HAP/1650/2015**: Modificaciones y validaciones
- **Circular 1/2015 IGAE**: Obligatoriedad

## 🔧 Solución de Problemas

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error al cargar archivos
- Verifica nombres de columnas
- Comprueba formato de fechas (DD/MM/YYYY)
- Asegúrate que son archivos .xlsx válidos

### La aplicación va lenta
- Reduce el rango de fechas con filtros
- Limita el número de registros
- Limpia caché: Menú → Clear cache

## 📊 Tecnologías Utilizadas

- **Streamlit**: Framework web interactivo
- **Pandas**: Análisis y manipulación de datos
- **Plotly**: Visualizaciones interactivas
- **Python-docx**: Generación de documentos Word
- **ReportLab**: Generación de PDFs
- **Openpyxl**: Procesamiento de archivos Excel

## 👥 Autor

Desarrollado para la **Diputación de Sevilla**  
Basado en la Guía IGAE para auditorías de RCF

## 📄 Licencia

Uso interno - Diputación de Sevilla

## 🆘 Soporte

Para problemas o consultas:
- Revisa la documentación en `README.md`
- Consulta los comentarios en el código
- Contacta con el departamento de IT

---

**Versión**: 1.0.0  
**Fecha**: Enero 2026