# Guía de Desarrollo y Memoria Técnica - Auditoría RCF

Este documento detalla la arquitectura, lógica de negocio y criterios de auditoría implementados en la aplicación, sirviendo como manual de referencia para el desarrollo continuo.

## 1. Criterios de Auditoría (Ejercicio 2025)

La aplicación ha sido ajustada para el ciclo de auditoría 2025. Los parámetros globales se gestionan en `config/settings.py`.

- **Ejercicio auditado**: 2025 (Filtro global aplicado en la carga de datos).
- **Umbral de cumplimiento (Papel)**: 3.000€ de **Base Imponible** (anteriormente 5.000€ total).
- **Fecha de corte**: Facturas posteriores al 15/01/2015 para obligatoriedad general.

## 2. Lógica de Negocio y Procesamiento de Datos

### 2.1 Gestión de Facturas "BORRADA"
- **Regla General**: Las facturas con el estado `"BORRADA"` se excluyen de la mayoría de análisis (Dashboard, Papel, Tiempos, Morosidad) para no distorsionar las métricas de gestión activa y periodos medios de pago.
- **Excepción Crítica (Validaciones)**: En la página de **Validaciones de Contenido**, estas facturas **SÍ se incluyen**. Muchos incumplimientos de la Orden HAP son detectados por el sistema y el registro pasa automáticamente al estado "BORRADA", por lo que su exclusión impediría auditar estos errores históricos.

### 2.2 Detección de Personas Jurídicas (Robusta)
Dado que los datos de origen no siempre utilizan el código estándar 'J' para Personas Jurídicas, se ha implementado un sistema de detección por prefijo de NIF (`utils.data_loader.es_persona_juridica`):
- **PJ detectada si**: NIF empieza por A, B, C, D, E, F, G, H, J, U o V.
- **Fallback**: Si la columna `tipo_persona` existe y contiene 'J', se prioriza el dato del sistema.

### 2.3 Mapeo Flexible de Columnas (Normalización)
La aplicación maneja la inconsistencia de nombres de columnas en los Excels de entrada mediante `MAPEO_COLUMNAS` en `data_loader.py`. Esto permite que el sistema detecte automáticamente columnas como:
- **Base Imponible**: Soporta 'BI', 'IMP. BASE IMPONIBLE', 'base_imponible', etc.
- **Ejercicio**: Soporta 'Año', 'EJERCICIO', 'ejercicio'.
- **Motivo Rechazo**: Mapeado a `motivo_rechazo` para análisis de validaciones.

## 3. Pruebas de Auditoría (Secciones de la Guía IGAE)

### V.1 Facturas en Papel
Se identifican facturas sospechosas de incumplir la Ley 25/2013 si:
1. Son de tipo "Papel" (sin identificador FACe).
2. Pertenecen a una Persona Jurídica.
3. La Base Imponible supera los 3.000€.
4. Su estado no es "BORRADA" (análisis de cumplimiento actual).

### V.2 Tiempos de Anotación en RCF
Se calcula el tiempo de demora entre FACe y RCF:
- **Origen (FACe)**: `fecha_registro`.
- **Destino (RCF)**: `F. DE GRABACIÓN DE LA OPER.` (mapeada como `fecha_anotacion_rcf`).
- **Lógica**: Si el tiempo resultante es negativo, se asume error de datos en origen y se filtra de las métricas medias para evitar distorsiones.

### V.3 Validaciones de Contenido (Orden HAP/1650/2015)
El sistema no realiza un análisis técnico de los datos (redondeos, DNI, etc.), sino que reporta los errores oficiales ya detectados por el sistema RCF:
- **Criterio**: Se analizan los **primeros 8 caracteres** del campo `"MOTIVO RECHAZO"`.
- **Mapeo**: Se utiliza el archivo `validaciones.csv` como diccionario maestro (ej: `RCF06001` -> `6a`).
- **Inclusión**: Incluye facturas en estado "BORRADA" para capturar todos los fallos detectados por el sistema local.

## 4. Archivos de Soporte

- **`validaciones.csv`**: Archivo fundamental en la raíz del proyecto. Asocia códigos internos del RCF con los apartados de la Orden HAP (4c, 5f, 6a, etc.).
  - *Formato*: `CODIGO_RCF,APARTADO_HAP` (ej: `RCF06001,6a`).

## 5. Guía de Desarrollo Futuro

1. **Filtros por Estado**: Al añadir nuevas páginas, decidir si deben incluir o no las facturas "BORRADA" según el objetivo del análisis.
2. **Visualizaciones**: Usar `plotly.subplots` y asegurar la importación de `make_subplots` si se añaden gráficos complejos con ejes secundarios.
3. **Internacionalización**: Mantener los mensajes de error y etiquetas en español técnico contable.

---
*Documento actualizado el 30/01/2026 para reflejar el nuevo criterio de validaciones y gestión de estados.*
