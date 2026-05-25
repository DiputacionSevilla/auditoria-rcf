# Especificación funcional y de generación del informe de auditoría del RCF  
## Tratamiento del ejercicio 2025 como año de transición en la anotación de facturas electrónicas procedentes de FACe

**Documento dirigido a:** IA/agente de desarrollo y análisis que mantiene la herramienta de auditoría del Registro Contable de Facturas (RCF) y genera cuadros, tablas y textos del informe a partir de extracciones de **FACe** y **SICAL/RCF**.  
**Ámbito:** Apartado 2 —Pruebas sobre anotación de facturas en el RCF— y Apartado 4 —Pruebas relacionadas con la tramitación de facturas— del informe de auditoría correspondiente al ejercicio 2025.  
**Estado del documento:** Especificación de requisitos funcionales, reglas de cálculo, estructura de tablas y plantillas de redacción.  
**Principio esencial:** El ejercicio 2025 no puede analizarse como un único periodo homogéneo, ya que durante el ejercicio se modificó el procedimiento de recepción y anotación de facturas electrónicas procedentes de FACe.

---

# 1. Objetivo de esta especificación

La herramienta de auditoría debe adaptar sus cálculos, tablas y textos automáticos del informe para reflejar que durante el ejercicio 2025 coexistieron dos procedimientos diferentes:

1. **Procedimiento anterior o régimen transitorio pendiente de corrección**, aplicado desde el 1 de enero de 2025 hasta la fecha efectiva de implantación del cambio en octubre de 2025.
   - SICAL descargaba la factura procedente de FACe.
   - Se asignaba inicialmente un identificador interno iniciado por la letra **S**.
   - Dicho identificador se comunicaba a FACe como identificador relacionado con el RCF.
   - Sin embargo, la entidad consideraba que la factura no quedaba definitivamente anotada en el RCF hasta que el área gestora actuaba sobre ella y se generaba un identificador iniciado por la letra **F**.
   - Esta operativa fue objeto de incidencia en la auditoría del ejercicio 2024.

2. **Procedimiento corregido**, aplicado desde la fecha efectiva de implantación del cambio en octubre de 2025 hasta el 31 de diciembre de 2025.
   - Las facturas electrónicas procedentes de FACe que superan las validaciones reglamentarias quedan anotadas directamente en el RCF con identificador iniciado por la letra **F**.
   - Las facturas que no superan las validaciones previstas en la fase de anotación se rechazan antes de su anotación, debiendo conservarse la trazabilidad de la causa del rechazo y de su comunicación a FACe.
   - Las unidades tramitadoras actúan posteriormente sobre facturas que ya están anotadas en el RCF.

La herramienta **no debe mezclar ambos regímenes en una única media anual no explicada**, pues los intervalos temporales analizados no tienen la misma naturaleza funcional ni auditora.

---

# 2. Contexto normativo y criterio auditor

## 2.1. Secuencia funcional que debe comprobarse

Conforme a la normativa reguladora del RCF y a la Guía para las auditorías de los Registros Contables de Facturas de la IGAE, la secuencia general que debe verificarse es la siguiente:

```text
Presentación de la factura electrónica en FACe
        ↓
FACe realiza sus validaciones y pone la factura a disposición del RCF
        ↓
El RCF recibe la factura y realiza las validaciones que le correspondan
        ↓
Si la factura supera las validaciones: anotación en el RCF y asignación de identificador
        ↓
Comunicación del identificador y estado correspondiente a FACe
        ↓
Puesta a disposición de la unidad tramitadora
        ↓
Aceptación, conformidad, devolución, rechazo posterior o restante tramitación
        ↓
Reconocimiento de la obligación y pago, cuando proceda
```

## 2.2. Distinción obligatoria entre anotación y tramitación

La herramienta deberá tratar como conceptos diferenciados:

| Concepto | Descripción | Apartado del informe |
|---|---|---|
| **Recepción/anotación en el RCF** | Proceso por el que una factura procedente de FACe, una vez superadas las validaciones aplicables, queda incorporada al RCF con identificador propio. | Apartado 2 |
| **Rechazo en fase de anotación** | Factura que no supera las validaciones aplicables y no llega a anotarse, debiendo constar motivo y trazabilidad. | Apartado 2 y apartado específico de causas de rechazo |
| **Tramitación posterior** | Actuaciones de la unidad tramitadora sobre una factura ya anotada: aceptación, conformidad, devolución, continuación del expediente, etc. | Apartado 4 |

## 2.3. Particularidad del procedimiento anterior

En el régimen anterior, la entidad mantenía una diferencia entre:

- identificador **S**, asignado tras la descarga desde FACe y comunicado a dicha plataforma; y
- identificador **F**, generado después de la intervención del área gestora y considerado internamente como registro definitivo.

Este régimen debe analizarse como una incidencia heredada del ejercicio 2024 que persistió durante una parte de 2025. La herramienta debe cuantificar sus efectos, pero no debe presentar los tiempos `S → F` como si fueran únicamente tiempos ordinarios de tramitación, pues durante ese periodo condicionaban la generación del registro considerado definitivo por la entidad.

---

# 3. Parámetros obligatorios de configuración

La aplicación deberá incorporar, como mínimo, los siguientes parámetros de configuración para el ejercicio 2025:

```yaml
ejercicio_auditado: 2025

fecha_inicio_ejercicio: "2025-01-01"
fecha_fin_ejercicio: "2025-12-31"

# Dato obligatorio que deberá introducirse o acreditarse documentalmente:
fecha_efectiva_cambio_procedimiento: null
# Ejemplo cuando se conozca: "2025-10-15"

prefijo_registro_previo: "S"
prefijo_registro_rcf_definitivo: "F"

plazo_aceptacion_areas_dias: 2
tipo_dias_plazo_aceptacion: "naturales_o_habiles_segun_bases"
# La IA no debe asumirlo: deberá configurarse conforme a la redacción exacta
# de las Bases de ejecución del presupuesto aplicables.

zona_horaria: "Europe/Madrid"
unidad_calculo_base: "segundos"
unidades_presentacion:
  - "minutos"
  - "dias"
```

## 3.1. Regla crítica sobre la fecha de cambio

La herramienta **no puede asumir automáticamente que el nuevo procedimiento se aplicó desde el 1 de octubre de 2025**. La fecha exacta debe ser:

- introducida por el auditor;
- obtenida de la evidencia técnica del cambio en producción; o
- deducida mediante análisis de registros, con advertencia expresa de que se trata de una fecha inferida pendiente de validación.

Si no se dispone de fecha acreditada, la herramienta deberá:

1. localizar el primer registro **F** directo sin estado previo **S**;
2. localizar el último registro tramitado mediante estado previo **S**;
3. mostrar posibles solapamientos o excepciones;
4. solicitar validación del auditor antes de cerrar tablas definitivas o texto conclusivo.

---

# 4. Fuentes de datos necesarias

## 4.1. Extracción de FACe

La herramienta debe admitir una extracción de FACe que permita identificar, como mínimo:

| Campo lógico requerido | Descripción funcional |
|---|---|
| `id_face` | Identificador único de la factura en FACe/PGEFe o número de registro usado para el cruce. |
| `fecha_registro_face` | Fecha y hora de recepción o registro de la factura en FACe. |
| `fecha_registro_rcf_comunicada` | Fecha y hora en que el RCF comunica a FACe la recepción/registro, si existe en la extracción. |
| `codigo_rcf_comunicado` | Identificador del RCF comunicado a FACe, en su caso. |
| `estado_face` | Estado de la factura en FACe. |
| `fecha_estado_face` | Fecha del estado o del histórico de estados, si está disponible. |
| `motivo_rechazo_face` | Causa de rechazo comunicada a FACe, cuando proceda. |
| `nif_emisor` | Identificación del proveedor, para comprobaciones y rankings. |
| `numero_factura` | Número/serie de factura. |
| `importe_total` | Importe de la factura. |
| `oficina_contable` | Código de oficina contable. |
| `organo_gestor` | Código de órgano gestor. |
| `unidad_tramitadora` | Código de unidad tramitadora. |

La herramienta debe permitir cargar, cuando estén disponibles, los ficheros:

- **Facturas registradas en el RCF** suministrado por FACe.
- **Facturas retenidas en el PGEFe**.
- **Histórico de estados de facturas**.
- **Solicitudes de anulación**, en caso de analizarse dentro del alcance.

## 4.2. Extracción de SICAL/RCF

La extracción del sistema SICAL/RCF deberá proporcionar, como mínimo:

| Campo lógico requerido | Descripción funcional |
|---|---|
| `id_face_rcf` | Identificador que permite relacionar el registro de SICAL con la factura de FACe. |
| `codigo_s` | Código iniciado por S, si la factura pasó por el procedimiento anterior. |
| `fecha_codigo_s` | Fecha y hora de creación/asignación del código S. |
| `codigo_f` | Código iniciado por F correspondiente a la anotación definitiva o directa en RCF. |
| `fecha_codigo_f` | Fecha y hora de creación/asignación del código F. |
| `estado_rcf` | Estado actual o histórico de tramitación en SICAL/RCF. |
| `fecha_aceptacion_ut` | Fecha y hora de aceptación por la unidad tramitadora. |
| `fecha_conformidad` | Fecha y hora de conformidad, si se diferencia de la aceptación. |
| `fecha_rechazo` | Fecha y hora del rechazo, si procede. |
| `motivo_rechazo_rcf` | Motivo formal de rechazo. |
| `fecha_anulacion` | Fecha de anulación, en su caso. |
| `motivo_anulacion` | Motivo de anulación, en su caso. |
| `unidad_tramitadora` | Código de unidad tramitadora responsable. |
| `organo_gestor` | Código de órgano gestor. |
| `oficina_contable` | Código de oficina contable. |
| `nif_emisor` | Identificación del emisor. |
| `numero_factura` | Número/serie. |
| `importe_total` | Importe total. |
| `documento_disponible` | Indicador de disponibilidad del fichero original para prueba de custodia. |

## 4.3. Mapeo de campos

La herramienta no debe asumir nombres físicos de columnas concretos. Debe disponer de un módulo de mapeo configurable:

```yaml
mapeo_face:
  id_face: null
  fecha_registro_face: null
  fecha_registro_rcf_comunicada: null
  codigo_rcf_comunicado: null
  estado_face: null
  motivo_rechazo_face: null

mapeo_rcf:
  id_face_rcf: null
  codigo_s: null
  fecha_codigo_s: null
  codigo_f: null
  fecha_codigo_f: null
  fecha_aceptacion_ut: null
  fecha_conformidad: null
  fecha_rechazo: null
  motivo_rechazo_rcf: null
```

Antes de ejecutar los cálculos, la IA deberá validar:

- que las fechas tienen formato interpretable;
- que los identificadores de cruce no presentan duplicidades no justificadas;
- que el universo de FACe y el del RCF están referidos al mismo periodo;
- que se han identificado los registros de rechazo y de anulación;
- que la fecha efectiva del cambio ha sido introducida o validada.

---

# 5. Clasificación automática de facturas por régimen y resultado

Cada factura deberá clasificarse según el procedimiento que le resulte aplicable y su resultado de tramitación.

## 5.1. Regímenes del ejercicio 2025

```text
REGIMEN_ANTERIOR:
    fecha_registro_face < fecha_efectiva_cambio_procedimiento

REGIMEN_NUEVO:
    fecha_registro_face >= fecha_efectiva_cambio_procedimiento
```

### Precisión necesaria

Como una factura recibida antes del cambio podría haber sido tratada después de la implantación técnica, la herramienta deberá permitir adicionalmente clasificar por:

- fecha de recepción en FACe;
- fecha de primera incorporación en SICAL;
- procedimiento realmente aplicado, inferido de la existencia de código **S**.

La clasificación definitiva para tablas de funcionamiento deberá priorizar el **procedimiento realmente aplicado**:

```text
Si existe codigo_s:
    procedimiento_aplicado = "PROCEDIMIENTO_ANTERIOR_S_F"
Si no existe codigo_s y existe codigo_f:
    procedimiento_aplicado = "ANOTACION_DIRECTA_F"
Si no existe codigo_s y no existe codigo_f y existe rechazo motivado:
    procedimiento_aplicado = "RECHAZO_PREVIO_A_ANOTACION"
En otro caso:
    procedimiento_aplicado = "INCIDENCIA_A_ANALIZAR"
```

La herramienta deberá advertir de discrepancias como:

- facturas posteriores a la fecha del cambio que presentan código **S**;
- facturas anteriores al cambio que presentan anotación directa **F**;
- facturas sin código **S** ni **F** y sin motivo de rechazo;
- facturas con estado registrado en FACe pero no localizadas en SICAL;
- facturas rechazadas sin motivo identificable.

## 5.2. Estados de auditoría propuestos

Asignar a cada factura un campo `resultado_auditoria_rcf` con alguno de los siguientes valores:

| Valor | Interpretación |
|---|---|
| `ANOTADA_DIRECTA_F_CORRECTA` | Factura del nuevo régimen anotada directamente con F tras superar validaciones. |
| `TRAMITADA_REGIMEN_ANTERIOR_S_F` | Factura del régimen anterior que pasó por S y posteriormente F. |
| `REGIMEN_ANTERIOR_S_SIN_F` | Factura que quedó en S sin identificador F; requiere revisión individualizada. |
| `RECHAZADA_VALIDACION_TRAZABLE` | Factura rechazada antes de anotarse con motivo de validación documentado y comunicable/contrastable. |
| `RECHAZADA_SIN_CAUSA_SUFICIENTE` | Factura rechazada sin causa clara o sin trazabilidad bastante. |
| `POST_CAMBIO_CON_CODIGO_S` | Factura posterior al cambio que ha pasado por estado previo; posible incumplimiento de la medida correctora. |
| `FACE_SIN_CORRESPONDENCIA_RCF` | Factura presente en FACe sin registro o tratamiento acreditado en SICAL/RCF. |
| `RCF_SIN_CORRESPONDENCIA_FACE` | Registro RCF electrónico sin correspondencia con FACe. |
| `INCIDENCIA_MANUAL` | Cualquier caso no clasificable automáticamente. |

---

# 6. Reglas de cálculo temporal

Todos los intervalos deberán calcularse originalmente en segundos y presentarse en minutos o días con el criterio de redondeo configurable.

```python
segundos = fecha_final - fecha_inicial
minutos = segundos / 60
dias = segundos / 86400
```

No deben incluirse en medias registros con fechas ausentes, tiempos negativos o inconsistencias no resueltas. Dichos casos deberán recogerse en una tabla separada de incidencias de calidad de datos.

## 6.1. Indicadores del procedimiento anterior: facturas con código S

Para las facturas tratadas conforme al procedimiento anterior, calcular:

### Indicador A. Tiempo FACe–S: recepción técnica o descarga inicial

```text
tiempo_face_s = fecha_codigo_s - fecha_registro_face
```

**Interpretación:** tiempo transcurrido desde la recepción/registro de la factura en FACe hasta su descarga o incorporación inicial en SICAL mediante código **S**.

**Uso en informe:** prueba técnica de funcionamiento del interfaz FACe–SICAL/RCF. No debe presentarse aisladamente como tiempo de anotación definitiva reconocido internamente por la entidad.

### Indicador B. Tiempo S–F: permanencia en estado previo

```text
tiempo_s_f = fecha_codigo_f - fecha_codigo_s
```

**Interpretación:** tiempo durante el cual la factura permaneció en estado previo **S** hasta la generación del código **F** considerado definitivo por la entidad.

**Uso en informe:** cuantificación del impacto temporal de la incidencia detectada en 2024 y persistente durante parte de 2025.

### Indicador C. Tiempo FACe–F: tiempo total hasta el registro considerado definitivo

```text
tiempo_face_f_regimen_anterior = fecha_codigo_f - fecha_registro_face
```

**Interpretación:** tiempo total desde la presentación/recepción en FACe hasta la generación del código **F** en el procedimiento anterior.

**Uso en informe:** mostrar el efecto completo del procedimiento cuestionado durante el periodo anterior al cambio.

## 6.2. Indicadores del procedimiento nuevo: anotación directa F

Para las facturas tratadas conforme al nuevo procedimiento, calcular:

### Indicador D. Tiempo FACe–F directo: inscripción en el RCF

```text
tiempo_face_f_directo = fecha_codigo_f - fecha_registro_face
```

**Interpretación:** tiempo transcurrido entre la recepción o registro de la factura en FACe y su anotación directa en SICAL/RCF mediante código **F**.

**Uso en informe:** indicador de tiempo medio de inscripción en el RCF para el periodo posterior a la corrección.

### Indicador E. Tiempo F–aceptación/conformidad: tramitación posterior

```text
tiempo_f_aceptacion = fecha_aceptacion_ut - fecha_codigo_f
```

o, si la entidad emplea como hito la conformidad:

```text
tiempo_f_conformidad = fecha_conformidad - fecha_codigo_f
```

**Interpretación:** tiempo empleado por la unidad tramitadora en actuar sobre una factura que ya se encuentra anotada en el RCF.

**Uso en informe:** apartado 4. No debe denominarse tiempo de inscripción en el RCF.

## 6.3. Rechazos previos a la anotación en el nuevo procedimiento

Las facturas rechazadas por no superar validaciones previas o concurrentes a la anotación:

- deben incluirse en el análisis de número y causas de rechazos;
- no deben incluirse en la media de `tiempo_face_f_directo`, puesto que no existe anotación **F**;
- deben figurar en el denominador de facturas recibidas/procesadas desde FACe cuando se calculen ratios de rechazo;
- deben marcarse como incidencia si carecen de motivo reglamentario trazable.

Calcular, cuando existan fechas suficientes:

```text
tiempo_face_rechazo = fecha_rechazo - fecha_registro_face
```

Este indicador puede presentarse como análisis complementario de rapidez en la validación y rechazo, pero no debe confundirse con el tiempo de inscripción.

---

# 7. Prohibición de agregación no homogénea

La IA no deberá generar una única media anual bajo la etiqueta **“Tiempo medio de inscripción en el RCF durante 2025”** mezclando:

- facturas del procedimiento anterior medidas hasta código **S**;
- facturas del procedimiento anterior medidas hasta código **F**;
- facturas del nuevo procedimiento anotadas directamente con código **F**;
- rechazos previos sin anotación.

## 7.1. Salida anual permitida

Se podrá generar un resumen anual, pero deberá presentar métricas diferenciadas:

| Indicador anual segmentado | Población |
|---|---|
| Tiempo medio FACe–S, procedimiento anterior | Facturas con código S del periodo afectado |
| Tiempo medio S–F, procedimiento anterior | Facturas con S y F del periodo afectado |
| Tiempo medio FACe–F, procedimiento anterior | Facturas con S y F del periodo afectado |
| Tiempo medio FACe–F directo, procedimiento nuevo | Facturas con F directo posteriores a la corrección |
| Tiempo medio F–aceptación/conformidad, procedimiento nuevo | Facturas anotadas directamente y posteriormente tramitadas |
| Número y causas de rechazos antes de la anotación | Facturas rechazadas con trazabilidad suficiente |

Si se genera un total global del número de facturas recibidas, anotadas o rechazadas durante 2025, deberá hacerse sin agregar tiempos heterogéneos bajo un mismo indicador.

---

# 8. Apartado 2 del informe: pruebas sobre anotación de facturas en el RCF

## 8.1. Objetivo del apartado 2

El apartado 2 deberá verificar:

1. Que las facturas electrónicas presentadas en FACe y dirigidas al RCF de la entidad son descargadas y tratadas por SICAL.
2. Que no existen facturas retenidas en el PGEFe pendientes de descarga o tratamiento.
3. Que existe correspondencia entre los registros de FACe y los registros del RCF.
4. Que, en el nuevo procedimiento, las facturas que superan validaciones se anotan directamente con código **F**.
5. Que, tras la fecha efectiva del cambio, no se siguen generando códigos previos **S**, salvo incidencias individualmente justificadas.
6. Que las facturas rechazadas antes de su anotación lo han sido por no superar validaciones aplicables, constando su causa y trazabilidad.
7. Que se puede acceder a la factura electrónica original en los registros anotados, de acuerdo con la prueba de custodia.

## 8.2. Texto automático de introducción del apartado 2

La herramienta deberá generar un texto basado en el siguiente modelo, sustituyendo los campos parametrizables y adaptando los resultados:

> Los artículos 9.1 y 9.2 de la Ley 25/2013, de 27 de diciembre, establecen que toda factura electrónica remitida por el Punto General de Entrada de Facturas Electrónicas deberá ser puesta a disposición o remitida automáticamente al Registro Contable de Facturas correspondiente, el cual, una vez recibida y superadas las validaciones que resulten aplicables, procederá a su anotación, generando un código de identificación que deberá ser comunicado al Punto General de Entrada.
>
> Asimismo, el artículo 12.3 de la citada Ley exige que la auditoría anual verifique que no quedan retenidas facturas presentadas en el Punto General de Entrada en ninguna de las fases del proceso e incluya un análisis de los tiempos medios de inscripción en el RCF y del número y causas de las facturas rechazadas en la fase de anotación.
>
> En relación con esta prueba, debe señalarse que el ejercicio 2025 constituye un periodo de transición en el funcionamiento del procedimiento de recepción y anotación de facturas electrónicas procedentes de FACe en SICAL. En la auditoría del ejercicio 2024 se puso de manifiesto que el procedimiento implantado asignaba inicialmente, tras la descarga de la factura, un identificador iniciado por la letra S que era comunicado a FACe, mientras que la entidad no consideraba producida la anotación definitiva en el RCF hasta la posterior intervención del área gestora y la generación de un identificador iniciado por la letra F.
>
> Durante el ejercicio 2025 dicho procedimiento se mantuvo hasta **{fecha_efectiva_cambio_procedimiento}**. Desde esa fecha, las facturas procedentes de FACe que superan las validaciones reglamentarias quedan anotadas directamente en el RCF con identificador iniciado por la letra F, sin transitar por el anterior estado previo S. Las facturas que no superan las validaciones aplicables se rechazan antes de su anotación, debiendo quedar acreditadas la causa del rechazo y su comunicación o trazabilidad en el sistema.
>
> En consecuencia, las pruebas y los indicadores de este apartado se presentan separando los dos procedimientos sucesivamente vigentes durante el ejercicio.

## 8.3. Tabla 2.1 — Resultado del cruce FACe–RCF diferenciando procedimientos

La herramienta debe generar la siguiente tabla:

| Concepto | Procedimiento anterior S–F | Procedimiento nuevo: anotación directa F | Total ejercicio |
|---|---:|---:|---:|
| Facturas electrónicas recibidas desde FACe | `count_face_anterior` | `count_face_nuevo` | `count_face_total` |
| Facturas descargadas o localizadas en SICAL | `count_rcf_anterior` | `count_rcf_nuevo` | `count_rcf_total` |
| Facturas con identificador inicial S | `count_s_anterior` | `count_s_postcambio` | `count_s_total` |
| Facturas anotadas con identificador F | `count_f_anterior` | `count_f_directo_nuevo` | `count_f_total` |
| Facturas rechazadas por validaciones de la fase de anotación | `count_rechazo_anterior` | `count_rechazo_nuevo` | `count_rechazo_total` |
| Facturas retenidas en FACe pendientes de descarga | `count_retenidas_anterior` | `count_retenidas_nuevo` | `count_retenidas_total` |
| Diferencias no justificadas FACe–RCF | `count_diff_anterior` | `count_diff_nuevo` | `count_diff_total` |

### Validaciones automáticas asociadas

La tabla deberá lanzar alertas cuando:

```text
count_s_postcambio > 0
count_retenidas_total > 0
count_diff_total > 0
count_rechazo_sin_causa > 0
count_face_sin_rcf > 0
```

### Texto automático de resultados para esta tabla

#### Si no se detectan incidencias posteriores al cambio

> Del cruce efectuado entre la información proporcionada por FACe y los registros existentes en SICAL se desprende que, durante el periodo anterior a la modificación del procedimiento, las facturas continuaron siendo tratadas mediante la asignación inicial de identificadores S y la posterior generación de identificadores F cuando procedía.  
>
> Desde **{fecha_efectiva_cambio_procedimiento}**, las facturas electrónicas que superan las validaciones aplicables se encuentran anotadas directamente con identificador F, sin que se hayan detectado nuevos registros previos S. Asimismo, no se han identificado facturas retenidas en FACe pendientes de descarga ni diferencias no justificadas entre la información facilitada por FACe y la obrante en el RCF para el periodo posterior a la modificación.  
>
> Los resultados obtenidos permiten considerar implantada la medida correctora respecto del funcionamiento de la interfaz FACe–RCF, sin perjuicio del análisis de los rechazos producidos y de las actuaciones posteriores de las unidades tramitadoras.

#### Si se detectan códigos S posteriores al cambio

> No obstante la modificación comunicada, se han identificado **{count_s_postcambio}** facturas posteriores a la fecha efectiva del cambio que presentan identificador previo S. Estos registros deberán ser objeto de análisis individualizado para determinar si responden a incidencias excepcionales justificadas, a un periodo de implantación gradual o a la subsistencia parcial del procedimiento observado en la auditoría anterior.

## 8.4. Tabla 2.2 — Tiempos del procedimiento anterior

Generar únicamente para facturas que hayan sido tratadas mediante código **S**, agrupadas por mes de la fecha de recepción en FACe o por mes del hito que configure el auditor.

| Mes | Facturas con S | Facturas con S y F | Facturas S sin F | Tiempo medio FACe–S | Tiempo medio S–F | Tiempo medio FACe–F | Tiempo máximo FACe–F |
|---|---:|---:|---:|---:|---:|---:|---:|
| Enero | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| Febrero | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| ... | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| Octubre hasta cambio | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| **Total / Media periodo anterior** | `...` | `...` | `...` | `...` | `...` | `...` | `...` |

### Regla de redacción

La IA deberá denominar:

- `FACe–S`: **tiempo de descarga o incorporación técnica inicial desde FACe**.
- `S–F`: **tiempo de permanencia en el estado previo utilizado por el procedimiento anterior**.
- `FACe–F`: **tiempo total hasta la anotación considerada definitiva por la entidad durante el procedimiento anterior**.

No deberá denominar al tiempo `FACe–S` como tiempo definitivo de inscripción si se explica que la entidad solo consideraba definitiva la generación del código **F**.

### Texto automático de interpretación

> Para el periodo anterior a la modificación del procedimiento, se han calculado separadamente tres intervalos temporales. El tiempo FACe–S permite valorar la recepción técnica de las facturas desde el Punto General de Entrada; el tiempo S–F cuantifica la permanencia de las facturas en el estado previo cuya utilización fue observada en la auditoría del ejercicio anterior; y el tiempo FACe–F refleja el plazo total hasta la generación del registro considerado definitivo por la entidad.  
>
> Esta separación resulta necesaria porque el correcto funcionamiento de la descarga desde FACe no elimina el efecto de la demora posterior en el estado S, durante la cual la factura permanecía pendiente de la actuación del área gestora antes de recibir el registro F.

## 8.5. Tabla 2.3 — Tiempos de inscripción tras la implantación del procedimiento corregido

Generar únicamente para el periodo posterior a la fecha efectiva del cambio.

| Mes | Facturas recibidas FACe | Facturas anotadas directamente F | Facturas rechazadas antes de anotación | Facturas con S detectadas | Tiempo medio FACe–F directo | Tiempo máximo FACe–F directo |
|---|---:|---:|---:|---:|---:|---:|
| Octubre desde cambio | `...` | `...` | `...` | `...` | `...` | `...` |
| Noviembre | `...` | `...` | `...` | `...` | `...` | `...` |
| Diciembre | `...` | `...` | `...` | `...` | `...` | `...` |
| **Total / Media periodo corregido** | `...` | `...` | `...` | `...` | `...` | `...` |

### Texto automático de interpretación

> Desde la fecha de implantación del nuevo procedimiento, el tiempo de inscripción en el RCF se calcula directamente como la diferencia entre la fecha de recepción o registro de la factura en FACe y la fecha de generación del identificador F en SICAL/RCF. Al haberse eliminado para las facturas válidas el tránsito por el estado previo S, este indicador refleja de forma directa el tiempo empleado en la anotación de la factura en el registro contable.

## 8.6. Tabla 2.4 — Facturas rechazadas antes de anotación y causas

Para el periodo posterior al cambio, generar tabla por causa de rechazo:

| Código/causa de rechazo | Descripción normalizada | Número de facturas | Porcentaje sobre rechazadas | Porcentaje sobre recibidas FACe | Importe total | Trazabilidad correcta |
|---|---|---:|---:|---:|---:|---|
| `...` | `...` | `...` | `...` | `...` | `...` | `Sí/No` |
| **Total** |  | `...` | `100 %` | `...` | `...` |  |

### Reglas de auditoría

La herramienta deberá diferenciar:

| Tipo de rechazo | Tratamiento |
|---|---|
| Rechazo por validación reglamentaria, con causa y comunicación acreditadas | Correctamente tratado como rechazo previo a anotación. |
| Rechazo sin causa reglamentaria identificable | Incidencia. |
| Comunicación informal al proveedor sin rechazo registrado | Incidencia de trazabilidad. |
| Rechazo posterior a una factura ya anotada F | Tramitación posterior; no confundir con rechazo en fase de anotación. |

## 8.7. Tabla 2.5 — Incidencias de correspondencia FACe–RCF y calidad de datos

| Tipo de incidencia | Número de registros | Importe afectado | Requiere revisión individual | Observación automática |
|---|---:|---:|---|---|
| Facturas FACe sin correspondencia en RCF | `...` | `...` | Sí | Posible retención o falta de incorporación. |
| Registros RCF sin correspondencia en FACe | `...` | `...` | Sí | Revisar origen y método de presentación. |
| Registros posteriores al cambio con código S | `...` | `...` | Sí | Posible subsistencia del procedimiento anterior. |
| Rechazos sin causa acreditada | `...` | `...` | Sí | Incumplimiento de trazabilidad. |
| Fechas negativas o inconsistentes | `...` | `...` | Sí | No incluir en medias hasta resolver. |
| Duplicidades en identificador de cruce | `...` | `...` | Sí | Revisar integridad del cruce. |

## 8.8. Conclusión automática del apartado 2

La IA deberá generar la conclusión según las evidencias calculadas, sin afirmar la subsanación si no se cumplen los controles.

### Modelo cuando la medida correctora ha sido verificada

> De las actuaciones realizadas se concluye que durante el ejercicio 2025 han coexistido dos procedimientos diferenciados para la recepción y anotación de facturas electrónicas procedentes de FACe. Hasta **{fecha_efectiva_cambio_procedimiento}** continuó aplicándose el procedimiento observado en la auditoría del ejercicio anterior, en virtud del cual las facturas descargadas desde FACe recibían inicialmente un identificador S y permanecían pendientes de la generación del registro F considerado definitivo por la entidad hasta la actuación del área gestora. Durante dicho periodo se mantuvo, por tanto, la incidencia previamente comunicada, cuyos efectos se cuantifican en las tablas anteriores.
>
> Desde **{fecha_efectiva_cambio_procedimiento}**, las facturas electrónicas que superan las validaciones reglamentarias quedan anotadas directamente en el RCF con identificador F, sin transitar por el anterior estado previo. Las comprobaciones realizadas sobre el periodo posterior a la implantación del cambio no han identificado nuevos códigos S para facturas válidas, facturas retenidas en FACe ni diferencias no justificadas entre FACe y el RCF.  
>
> En consecuencia, la incidencia detectada en la auditoría anterior puede considerarse **subsanada durante el ejercicio**, con efectos persistentes respecto de las facturas tramitadas conforme al procedimiento anterior hasta la fecha efectiva del cambio y con necesidad de seguimiento de la correcta aplicación del nuevo procedimiento en ejercicios posteriores.

### Modelo cuando existen incidencias posteriores al cambio

> La modificación del procedimiento comunicada por la entidad constituye una medida adecuada para corregir la deficiencia observada en la auditoría anterior. No obstante, las pruebas realizadas han detectado **{descripcion_incidencias_postcambio}**, por lo que no resulta posible considerar plenamente acreditada su implantación efectiva para la totalidad del periodo posterior al cambio. Deberán analizarse individualmente los registros afectados y adoptarse, en su caso, las medidas necesarias para garantizar que toda factura válida procedente de FACe queda anotada directamente en el RCF y que todo rechazo previo a su anotación responde a validaciones reglamentarias debidamente trazadas.

---

# 9. Apartado 4 del informe: pruebas relacionadas con la tramitación de facturas

## 9.1. Objetivo del apartado 4

El apartado 4 deberá analizar los tiempos de actuación de las unidades tramitadoras y los efectos de la modificación del procedimiento sobre la interpretación de dichos tiempos.

La herramienta deberá diferenciar:

| Periodo | Qué significa el tiempo analizado |
|---|---|
| Procedimiento anterior | El tiempo `S → F` refleja la permanencia de una factura en el estado previo hasta la generación del registro considerado definitivo por la entidad. No es únicamente demora de tramitación ordinaria. |
| Procedimiento nuevo | El tiempo `F → aceptación/conformidad` refleja tramitación posterior sobre una factura ya anotada en el RCF. |

## 9.2. Texto automático de introducción del apartado 4

> Los apartados 3 y 4 del artículo 9 de la Ley 25/2013 regulan las actuaciones posteriores a la anotación de las facturas en el Registro Contable de Facturas. Una vez anotada la factura, corresponde su remisión o puesta a disposición del órgano competente para su tramitación, debiendo quedar constancia en el propio RCF de la aceptación, rechazo, conformidad, devolución y restantes estados relevantes.
>
> Las Bases de ejecución del presupuesto aplicables al ejercicio establecen que las facturas recibidas a través de FACe deberán ser atendidas por el área gestora en el plazo máximo de **{plazo_aceptacion_areas_dias} días {tipo_dias_plazo_aceptacion_validado}** desde **{hito_inicio_plazo_bases}**.
>
> No obstante, al haberse modificado durante el ejercicio 2025 el procedimiento de anotación inicial en el RCF, el análisis de tiempos de tramitación debe efectuarse distinguiendo dos periodos. Durante el procedimiento anterior, la actuación de la unidad tramitadora condicionaba la generación del identificador F considerado definitivo por la entidad. Tras la implantación del nuevo procedimiento, las facturas válidas quedan anotadas directamente con código F, de modo que la posterior actuación del área gestora constituye una fase de tramitación diferenciada y posterior a la inscripción en el RCF.

**Regla:** La herramienta no deberá completar `tipo_dias_plazo_aceptacion_validado` ni `hito_inicio_plazo_bases` sin que el auditor haya validado el texto literal de las Bases de ejecución aplicables.

---

# 10. Tablas del apartado 4 para el procedimiento anterior

## 10.1. Tabla 4.1 — Tiempo de permanencia en estado previo S hasta código F

| Mes | Facturas con S | Facturas que obtienen F | Facturas S sin F al cierre de extracción | Tiempo medio S–F | Mediana S–F | Tiempo máximo S–F | Facturas fuera del plazo configurado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Enero | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| Febrero | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| ... | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| Octubre hasta cambio | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| **Total / Media periodo** | `...` | `...` | `...` | `...` | `...` | `...` | `...` |

## 10.2. Tabla 4.2 — Procedimiento anterior por unidad tramitadora

| Código UT | Denominación UT | Facturas con S | Facturas con S y F | Facturas S sin F | Tiempo medio S–F | Tiempo máximo S–F | Facturas fuera de plazo | Porcentaje fuera de plazo |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| **Total** |  | `...` | `...` | `...` | `...` | `...` | `...` | `...` |

## 10.3. Tabla 4.3 — Detalle de facturas del procedimiento anterior que requieren revisión

La herramienta deberá permitir exportar el detalle completo, al menos para:

- facturas `S` sin posterior código `F`;
- facturas con mayor tiempo `S → F`;
- facturas que excedan el plazo configurado;
- facturas en las que consten incidencias o rechazo sin trazabilidad bastante;
- facturas en las que el estado en FACe no resulte coherente con el estado en SICAL.

| Id FACe | Número factura | NIF emisor | Importe | Unidad tramitadora | Fecha FACe | Código S | Fecha S | Código F | Fecha F | Tiempo S–F | Estado final | Motivo revisión |
|---|---|---|---:|---|---|---|---|---|---|---:|---|---|
| `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` |

## 10.4. Texto automático de valoración del procedimiento anterior

> Durante el periodo comprendido entre el 1 de enero de 2025 y **{fecha_efectiva_cambio_procedimiento}**, la actuación de las unidades tramitadoras sobre las facturas descargadas desde FACe determinaba la posterior generación del identificador F considerado definitivo por la entidad. Por ello, el tiempo transcurrido entre los identificadores S y F no representa exclusivamente un plazo ordinario de tramitación, sino también la permanencia de la factura en la situación previa cuestionada en la auditoría correspondiente al ejercicio anterior.
>
> En dicho periodo se han identificado **{facturas_s_total}** facturas con identificador S, de las cuales **{facturas_s_f_total}** obtuvieron posteriormente identificador F y **{facturas_s_sin_f_total}** no disponían de código F a la fecha de extracción. El tiempo medio de permanencia en estado previo fue de **{tiempo_medio_s_f}**, habiéndose identificado **{facturas_fuera_plazo_anterior}** facturas que superan el plazo configurado de referencia.  
>
> Las facturas sin código F posterior y las que presentan tiempos especialmente elevados deberán ser objeto de revisión individualizada, con el fin de determinar su estado final, la existencia de rechazos o anulaciones, la posible sustitución de la factura y la adecuada trazabilidad de las comunicaciones realizadas al proveedor.

---

# 11. Tablas del apartado 4 para el procedimiento nuevo

## 11.1. Tabla 4.4 — Tramitación posterior de facturas ya anotadas directamente con F

| Mes | Facturas anotadas directamente F | Facturas aceptadas/conformadas | Facturas pendientes de actuación a fecha de extracción | Tiempo medio F–aceptación/conformidad | Mediana | Tiempo máximo | Facturas fuera del plazo configurado |
|---|---:|---:|---:|---:|---:|---:|---:|
| Octubre desde cambio | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| Noviembre | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| Diciembre | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| **Total / Media periodo corregido** | `...` | `...` | `...` | `...` | `...` | `...` | `...` |

## 11.2. Tabla 4.5 — Tramitación posterior por unidad tramitadora

| Código UT | Denominación UT | Facturas anotadas F | Facturas aceptadas/conformadas | Pendientes | Tiempo medio posterior | Tiempo máximo | Fuera de plazo | Porcentaje fuera de plazo |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` |
| **Total** |  | `...` | `...` | `...` | `...` | `...` | `...` | `...` |

## 11.3. Tabla 4.6 — Detalle de facturas del procedimiento nuevo con tramitación demorada

| Id FACe | Código F | Número factura | NIF emisor | Importe | Unidad tramitadora | Fecha anotación F | Fecha aceptación/conformidad | Tiempo posterior | Estado actual | Motivo revisión |
|---|---|---|---|---:|---|---|---|---:|---|---|
| `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` | `...` |

## 11.4. Texto automático de valoración del procedimiento nuevo

> Desde **{fecha_efectiva_cambio_procedimiento}**, las facturas electrónicas procedentes de FACe que superan las validaciones aplicables quedan anotadas directamente en el RCF con identificador F. Por tanto, las actuaciones posteriores de las unidades tramitadoras ya no condicionan la inscripción inicial de la factura, sino que constituyen trámites posteriores sobre facturas previamente registradas.
>
> En este periodo se han anotado directamente **{facturas_f_directas_total}** facturas, de las cuales **{facturas_aceptadas_total}** han sido aceptadas o conformadas por las correspondientes unidades tramitadoras a la fecha de extracción. El tiempo medio de tramitación posterior ha sido de **{tiempo_medio_f_aceptacion}**, identificándose **{facturas_fuera_plazo_nuevo}** facturas que superan el plazo de referencia configurado.  
>
> En consecuencia, las demoras detectadas en este segundo periodo, en su caso, deben valorarse como retrasos de tramitación posterior y no como demoras en la anotación inicial en el RCF, sin perjuicio de su posible incidencia sobre el reconocimiento de la obligación, el pago y la adecuada gestión de las facturas.

---

# 12. Conclusión automática del apartado 4

## 12.1. Modelo de conclusión cuando se confirma la corrección estructural

> El cambio implantado durante el mes de octubre de 2025 modifica sustancialmente la interpretación de los tiempos analizados. Durante el primer periodo del ejercicio, el retraso de las unidades tramitadoras en actuar sobre las facturas descargadas desde FACe incidía en la generación del registro F considerado definitivo por la entidad, prolongando la permanencia de las facturas en el estado previo S observado en la auditoría del ejercicio anterior.
>
> Desde la implantación del nuevo procedimiento, las facturas válidas procedentes de FACe quedan anotadas directamente en el RCF mediante código F, de modo que las actuaciones posteriores de las unidades tramitadoras ya no condicionan su inscripción inicial. En este segundo periodo, las posibles demoras tienen la naturaleza de retrasos en la tramitación posterior de facturas ya anotadas.
>
> La información estadística se presenta separada por periodos al no resultar homogéneos los intervalos medidos. La modificación introducida permite considerar corregida la deficiencia estructural relacionada con la existencia del estado previo S, sin perjuicio del seguimiento de las demoras que puedan persistir en la actuación posterior de las unidades tramitadoras.

## 12.2. Modelo de conclusión cuando no se confirma plenamente la corrección

> Aunque la entidad ha modificado el procedimiento de anotación de facturas electrónicas procedentes de FACe, las pruebas efectuadas han detectado incidencias posteriores a la fecha comunicada de implantación, consistentes en **{descripcion_incidencias}**. En consecuencia, deberá completarse el análisis individualizado de los registros afectados antes de concluir sobre la plena eficacia de la medida correctora.
>
> En todo caso, debe mantenerse la separación entre los tiempos correspondientes al procedimiento anterior —en los que la actuación del área incidía en la generación del registro F considerado definitivo— y los tiempos posteriores a la anotación directa de las facturas, que deben analizarse exclusivamente como tramitación posterior.

---

# 13. Cuadro resumen ejecutivo obligatorio

La herramienta deberá generar un cuadro resumen que permita comprender inmediatamente el año de transición:

| Bloque de análisis | Procedimiento anterior hasta cambio | Procedimiento nuevo desde cambio | Valoración |
|---|---:|---:|---|
| Facturas electrónicas recibidas FACe | `...` | `...` | Universo analizado |
| Facturas con estado previo S | `...` | `...` | Tras el cambio el valor esperado es 0 |
| Facturas con anotación F | `...` | `...` | En nuevo régimen debe ser anotación directa |
| Rechazos en fase de validación | `...` | `...` | Revisar causas y trazabilidad |
| Tiempo técnico FACe–S | `...` | No aplica | Solo procedimiento anterior |
| Tiempo permanencia S–F | `...` | No aplica | Impacto de incidencia anterior |
| Tiempo inscripción FACe–F directo | No homogéneo / mostrar solo como total hasta F | `...` | Indicador del nuevo procedimiento |
| Tiempo posterior F–aceptación/conformidad | No comparable como tal | `...` | Tramitación posterior |
| Facturas FACe retenidas | `...` | `...` | Debe ser 0 |
| Incidencias sin justificar | `...` | `...` | Requieren actuación auditora |

---

# 14. Gráficos recomendados

La herramienta deberá ofrecer los siguientes gráficos, siempre separando regímenes:

## 14.1. Gráficos del apartado 2

1. **Evolución mensual del número de facturas con código S y código F**
   - Series: `facturas_codigo_s`, `facturas_codigo_f_directo`.
   - Marcar visualmente la fecha de cambio de procedimiento.
   - Objetivo: evidenciar la desaparición del estado S.

2. **Tiempo medio mensual FACe–S y FACe–F durante el procedimiento anterior**
   - Solo hasta la fecha de cambio.
   - Objetivo: mostrar diferencia entre descarga inicial y registro F considerado definitivo.

3. **Tiempo medio mensual FACe–F directo tras el cambio**
   - Solo desde la fecha de cambio.
   - Objetivo: evaluar el nuevo tiempo de inscripción.

4. **Número de rechazos por causa tras el cambio**
   - Gráfico de barras por causa normalizada.
   - Objetivo: controlar rechazos en fase de validación.

## 14.2. Gráficos del apartado 4

1. **Tiempo medio S–F por unidad tramitadora en el procedimiento anterior**
   - Objetivo: identificar unidades con mayor incidencia en la permanencia del estado previo.

2. **Porcentaje de facturas S–F fuera del plazo de referencia por unidad tramitadora**
   - Solo procedimiento anterior.

3. **Tiempo medio F–aceptación/conformidad por unidad tramitadora en el procedimiento nuevo**
   - Solo tras la corrección.

4. **Porcentaje de facturas ya anotadas F cuya tramitación posterior supera plazo**
   - Solo nuevo procedimiento.

## 14.3. Regla visual obligatoria

Nunca debe dibujarse una única serie anual de “tiempo de anotación” sin marcar el cambio procedimental y sin separar la definición del indicador antes y después del cambio.

---

# 15. Controles automáticos y alertas de auditoría

La herramienta deberá generar alertas clasificadas por gravedad:

## 15.1. Alertas críticas

| Código | Condición | Mensaje |
|---|---|---|
| `ALERTA_RCF_001` | Existe factura posterior al cambio con código S | Se detectan registros previos S tras la implantación del procedimiento corregido. Revisar subsistencia del circuito anterior. |
| `ALERTA_RCF_002` | Factura FACe no aparece en SICAL/RCF ni consta rechazo | Posible factura retenida o no tratada por el RCF. |
| `ALERTA_RCF_003` | Rechazo sin causa o sin trazabilidad | No resulta acreditada la causa de rechazo en fase de anotación. |
| `ALERTA_RCF_004` | FACe refleja registro RCF pero SICAL no contiene anotación o actuación equivalente | Posible discordancia entre el estado comunicado a FACe y la realidad interna. |

## 15.2. Alertas relevantes

| Código | Condición | Mensaje |
|---|---|---|
| `ALERTA_RCF_101` | Factura S sin F del periodo anterior | Revisar estado final de factura tramitada bajo procedimiento anterior. |
| `ALERTA_RCF_102` | Tiempo S–F superior al plazo configurado | Factura permaneció en estado previo más allá del plazo de referencia. |
| `ALERTA_RCF_103` | Tiempo F–aceptación posterior al cambio superior al plazo configurado | Retraso de tramitación de factura ya anotada en RCF. |
| `ALERTA_RCF_104` | Fechas negativas o secuencia cronológica imposible | Registro excluido temporalmente de medias hasta aclaración. |

## 15.3. Alertas informativas

| Código | Condición | Mensaje |
|---|---|---|
| `INFO_RCF_201` | Factura anterior al cambio con F directo | Verificar si se trató de prueba previa o excepción justificada. |
| `INFO_RCF_202` | Cambio de procedimiento inferido de datos, no acreditado | Solicitar evidencia de la fecha efectiva de puesta en producción. |

---

# 16. Reglas para la generación de texto por la IA

La IA generadora del informe deberá cumplir las siguientes reglas:

1. **No inventar datos.** Todos los valores numéricos deben proceder de cálculos sobre las extracciones cargadas.
2. **No asumir la fecha exacta de cambio.** Debe emplear el parámetro validado por el auditor.
3. **No afirmar que la incidencia está subsanada** si se detectan códigos S posteriores al cambio, discrepancias FACe–RCF o rechazos sin trazabilidad suficiente.
4. **No confundir rechazo por validación previa con tramitación posterior.**
5. **No mezclar medias de periodos con definiciones distintas.**
6. **Mantener la trazabilidad del cálculo:** toda cifra presentada en el informe debe permitir exportar el detalle de facturas que la compone.
7. **Mostrar población y exclusiones:** cada tabla de tiempos deberá indicar número de facturas incluidas, excluidas por falta de fecha e incidencias detectadas.
8. **Redactar en términos de evidencia:** utilizar expresiones como “se ha constatado”, “del cruce realizado se desprende” o “se han identificado”, exclusivamente cuando exista dato que lo sustente.
9. **Diferenciar medida correctora e incidencia histórica:** la corrección puede estar implantada desde octubre, pero los efectos del procedimiento anterior forman parte del resultado de auditoría de 2025.
10. **Evitar conclusiones jurídicas automáticas irreversibles:** cuando existan dudas de clasificación, proponer revisión por el auditor.

---

# 17. Requisitos de exportación y evidencia

Cada tabla agregada mostrada en el informe deberá permitir exportar una hoja o fichero detalle con las facturas que la sustentan.

## 17.1. Exportables mínimos

| Informe agregado | Exportación detalle obligatoria |
|---|---|
| Cruce FACe–RCF | Todas las facturas cruzadas con indicador de coincidencia y clasificación |
| Facturas con S posteriores al cambio | Detalle individual completo |
| Facturas S sin F | Detalle individual completo |
| Facturas rechazadas | Factura, causa, fecha, estado FACe, estado RCF y trazabilidad |
| Tiempos FACe–S | Detalle con fechas inicial/final y tiempo calculado |
| Tiempos S–F | Detalle con fechas inicial/final y tiempo calculado |
| Tiempos FACe–F directo | Detalle con fechas inicial/final y tiempo calculado |
| Tiempos F–aceptación/conformidad | Detalle con unidad tramitadora y estado posterior |
| Facturas fuera de plazo | Detalle individual con criterio de plazo aplicado |
| Incidencias de calidad de datos | Registro, anomalía y motivo de exclusión |

## 17.2. Campos de auditoría en cada detalle

Cada exportación deberá incorporar:

```text
id_factura_face
codigo_s
codigo_f
procedimiento_aplicado
resultado_auditoria_rcf
fecha_registro_face
fecha_codigo_s
fecha_codigo_f
fecha_aceptacion_o_conformidad
fecha_rechazo
motivo_rechazo
unidad_tramitadora
importe_total
tiempo_face_s
tiempo_s_f
tiempo_face_f
tiempo_f_tramitacion
fuera_plazo
codigo_alerta
observacion_auditor
```

---

# 18. Criterios de aceptación de la implementación

La modificación de la herramienta se considerará correctamente realizada cuando cumpla todos los criterios siguientes:

## 18.1. Carga y clasificación

- [ ] Permite introducir la fecha efectiva de cambio del procedimiento.
- [ ] Clasifica facturas según procedimiento realmente aplicado.
- [ ] Distingue facturas `S → F`, anotaciones directas `F`, rechazos previos e incidencias.
- [ ] Detecta códigos `S` posteriores al cambio.

## 18.2. Cálculos

- [ ] Calcula `FACe → S`, `S → F`, `FACe → F` para el procedimiento anterior.
- [ ] Calcula `FACe → F directo` para el procedimiento nuevo.
- [ ] Calcula `F → aceptación/conformidad` para la tramitación posterior.
- [ ] Calcula rechazos por causa y ratios respecto del total recibido.
- [ ] Excluye de medias los registros con fechas inválidas, informando de la exclusión.

## 18.3. Tablas y gráficos

- [ ] Genera tablas separadas para ambos procedimientos.
- [ ] No produce una media anual única de tiempos heterogéneos.
- [ ] Genera cuadros por unidad tramitadora.
- [ ] Genera listado individualizado de facturas críticas.
- [ ] Marca visualmente la fecha de cambio en los gráficos temporales.

## 18.4. Texto del informe

- [ ] Genera los apartados 2 y 4 con redacción coherente con el carácter transitorio de 2025.
- [ ] Denomina correctamente cada intervalo temporal.
- [ ] Solo concluye que la medida ha sido eficaz si los datos lo acreditan.
- [ ] Señala los efectos persistentes del procedimiento anterior durante parte del ejercicio.
- [ ] Distingue entre anotación inicial, rechazo en validación y tramitación posterior.

## 18.5. Evidencia y reproducibilidad

- [ ] Cada tabla agregada puede exportarse a detalle.
- [ ] Cada valor puede trazarse hasta facturas concretas.
- [ ] Se conserva el criterio de cálculo empleado y la fecha de extracción.
- [ ] Las alertas quedan vinculadas a registros concretos.
- [ ] El auditor puede añadir observaciones manuales y decidir la conclusión final.

---

# 19. Resultado esperado del módulo de informe

Al finalizar el procesamiento, la herramienta deberá producir:

1. **Apartado 2 completo del informe**, con:
   - explicación de la transición;
   - cruce FACe–RCF;
   - análisis de facturas retenidas;
   - tiempos del procedimiento anterior;
   - tiempos del procedimiento corregido;
   - análisis de rechazos previos a la anotación;
   - conclusión condicionada por los resultados.

2. **Apartado 4 completo del informe**, con:
   - análisis de permanencia `S → F` durante el procedimiento anterior;
   - análisis por unidades tramitadoras;
   - análisis de tramitación posterior `F → aceptación/conformidad` tras el cambio;
   - facturas fuera de plazo;
   - conclusión diferenciada por periodos.

3. **Anexos de evidencia**, con:
   - detalle de cruces;
   - detalle de incidencias;
   - detalle de rechazos;
   - detalle de tiempos por factura;
   - parámetros utilizados en la ejecución;
   - fecha efectiva de cambio y evidencia que la sustenta.

4. **Cuadro ejecutivo del ejercicio 2025**, que refleje:
   - que la incidencia de 2024 persistió durante parte de 2025;
   - que se implantó una modificación correctora en octubre de 2025;
   - que la eficacia de la modificación se evalúa únicamente sobre las facturas posteriores al cambio;
   - y que los retrasos de tramitación posteriores al cambio no deben confundirse con tiempos de inscripción en el RCF.

---

# 20. Fuentes documentales que sustentan esta especificación

La implementación deberá contrastarse con la documentación de auditoría y normativa disponible, especialmente:

1. **Guía para las auditorías de los Registros Contables de Facturas previstas en el artículo 12 de la Ley 25/2013 — Guía de Auditoría versión 2, IGAE.**
   - Apartado V.2: pruebas sobre anotación de facturas en el RCF.
   - Apartado V.2.1.2: informe estadístico de tiempos medios de inscripción.
   - Apartado V.3: validaciones del contenido de las facturas.
   - Apartado V.4: pruebas relacionadas con la tramitación.

2. **Informe provisional de auditoría del RCF de la entidad correspondiente al ejercicio 2025.**
   - Apartado 2: funcionamiento observado en la descarga de facturas desde FACe, códigos S/F y tiempos de inscripción/descarga.
   - Apartado 4: tiempos asociados a la actuación de las unidades tramitadoras y cumplimiento de plazos.

3. **Antecedente de auditoría del ejercicio 2024.**
   - Incidencia relativa a la comunicación a FACe de la recepción/registro de la factura mientras internamente permanecía en un estado previo antes de la generación del código F.

4. **Evidencia técnica del cambio implantado en octubre de 2025.**
   - Fecha de puesta en producción.
   - Cambio funcional o técnico aplicado.
   - Registros de prueba o logs que acrediten la anotación directa con código F.
   - Confirmación de tratamiento de rechazos por validaciones.

---

# 21. Instrucción final para el agente de IA/desarrollo

Implementa la adaptación de la herramienta de auditoría conforme a esta especificación. Antes de generar resultados definitivos:

1. Solicita o configura la fecha exacta de entrada en funcionamiento del nuevo procedimiento.
2. Mapea los campos reales de las extracciones FACe y SICAL/RCF a los campos lógicos definidos.
3. Ejecuta las validaciones de calidad y correspondencia.
4. Clasifica cada factura por procedimiento y resultado.
5. Calcula indicadores temporales sin mezclar poblaciones heterogéneas.
6. Genera las tablas y gráficos diferenciados.
7. Genera los textos de los apartados 2 y 4 únicamente con los resultados obtenidos.
8. Exporta los detalles que soportan cada conclusión.
9. No concluyas que la incidencia está subsanada si existen facturas posteriores al cambio con código S, rechazos sin causa acreditada o divergencias no resueltas entre FACe y SICAL/RCF.
