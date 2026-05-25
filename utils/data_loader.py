"""
Módulo para carga y validación de datos
Versión mejorada con mapeo flexible de columnas
"""

import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple
from config.settings import CONFIGURACION

# Mapeo flexible de nombres de columnas
MAPEO_COLUMNAS = {
    'rcf': {
        'id_fra_rcf': ['id_fra_rcf', 'ID_FRA_RCF', 'ID_RCF', 'id_rcf', 'ID'],
        'entidad': ['entidad', 'ENTIDAD', 'Entidad'],
        'ID_FACE': ['ID_FACE', 'id_face', 'ID FACE', 'Nº Registro FACe', 'registro_face'],
        'fecha_emision': ['fecha_emision', 'fecha_expedicion', 'Fecha', 'fecha', 'Fecha Expedición', 'FECHA EXP. FRA.'],
        'fecha_registro_face': ['fecha_registro_face', 'FECHA REG. EN FACE', 'Fecha Reg. en FACe', 'fecha_reg_face'],
        'fecha_anotacion_rcf': ['fecha_anotacion_rcf', 'FECHA REGISTRO', 'Fecha registro', 'fecha_anotacion', 'Fecha Anotación', 'fecha_registro', 'F. DE GRABACIÓN DE LA OPER.'],
        'nif_emisor': ['nif_emisor', 'NIF', 'nif', 'CIF', 'cif', 'NIF Emisor', 'NIF/CIF'],
        'razon_social': ['razon_social', 'nombre', 'Razón Social', 'Nombre', 'proveedor', 'NOMBRE/RAZÓN SOCIAL'],
        'numero_factura': ['numero_factura', 'numero', 'Número', 'Nº Factura', 'num_factura', 'N_FRA'],
        'serie': ['serie', 'Serie', 'SERIE', 'S', 's', 'Serie Factura'],
        'importe_total': ['importe_total', 'importe', 'Importe', 'Total', 'total', 'Importe Total', 'I. TOTAL FACTURA'],
        'moneda': ['moneda', 'Moneda', 'divisa', 'UNIDAD MONETARIA', 'MONEDA'],
        'base_imponible': ['base_imponible', 'Base Imponible', 'bi', 'BI', 'BASE IMPONIBLE', 'IMP. BASE IMPONIBLE'],
        'ejercicio': ['ejercicio', 'Ejercicio', 'Año', 'año', 'EJERCICIO'],
        'tipo_persona': ['tipo_persona', 'Tipo', 'tipo', 'TIPO'],
        'estado': ['estado', 'Estado', 'status', 'ESTADO FACTURA'],
        'codigo_oc': ['codigo_oc', 'OC', 'oc', 'Oficina Contable', 'oficina_contable', 'CODIGO DIR3 OFICINA CONTABLE'],
        'codigo_og': ['codigo_og', 'OG', 'og', 'Órgano Gestor', 'organo_gestor', 'CODIGO DIR3 ÓRGANO GESTOR'],
        'codigo_ut': ['codigo_ut', 'UT', 'ut', 'Unidad Tramitadora', 'unidad_tramitadora', 'CODIGO DIR3 UNIDAD TRAMITADORA'],
        'motivo_rechazo': ['motivo_rechazo', 'MOTIVO RECHAZO', 'Motivo Rechazo', 'MOTIVO'],
        'area_unidad_servicio': ['area_unidad_servicio', 'ÁREA/UNIDAD/SERVICIO', 'AREA/UNIDAD/SERVICIO', 'Área/Unidad/Servicio', 'ÁREA', 'Area/Unidad/Servicio'],
        'fecha_aceptacion': ['fecha_aceptacion', 'FECHA ACEPTACION', 'Fecha Aceptacion', 'FECHA ACEPTACIÓN', 'Fecha Aceptación', 'F. ACEPTACION', 'FECHA DE ACEPTACION', 'Fecha de Aceptación'],
        # Campos para el análisis de transición 2025 (procedimiento S→F vs F directo)
        # fecha_codigo_s: fecha en que SICAL recibió/descargó la factura desde FACe
        #   = "FECHA RECEPCION FACE" en el Excel del RCF (equivale al hito S del procedimiento anterior)
        'fecha_codigo_s': [
            'fecha_codigo_s', 'FECHA RECEPCION FACE', 'FECHA RECEPCIÓN FACE',
            'Fecha Recepcion FACe', 'Fecha Recepción FACe',
            'FECHA_CODIGO_S', 'Fecha Código S', 'FECHA_S', 'fecha_s',
        ],
        # fecha_codigo_f / codigo_f: identificador y fecha de registro definitivo en el RCF
        #   = "ID_FRA_RCF" y "FECHA REGISTRO" en el Excel (ya mapeados como id_fra_rcf y fecha_anotacion_rcf)
        #   Se añaden aquí como alias explícitos para las funciones de cálculo temporal.
        'fecha_codigo_f': [
            'fecha_codigo_f', 'FECHA REGISTRO', 'Fecha registro', 'FECHA_CODIGO_F',
            'Fecha Código F', 'FECHA_F', 'fecha_f',
            'FECHA ACEPTACIÓN', 'Fecha Aceptación', 'FECHA ACEPTACION', 'Fecha Aceptacion',
            'F. DE GRABACIÓN DE LA OPER.',
        ],
        'codigo_f': [
            'codigo_f', 'ID_FRA_RCF', 'id_fra_rcf', 'ID_RCF', 'CODIGO_F',
            'Código F', 'ID_F', 'id_f',
        ],
        'fecha_aceptacion_ut': ['fecha_aceptacion_ut', 'FECHA_ACEPTACION_UT', 'Fecha Aceptación UT', 'fecha_aceptacion_unidad'],
        'fecha_conformidad': ['fecha_conformidad', 'FECHA_CONFORMIDAD', 'Fecha Conformidad', 'FECHA CONFORMIDAD'],
        'fecha_rechazo': ['fecha_rechazo', 'FECHA_RECHAZO', 'Fecha Rechazo', 'FECHA RECHAZO', 'fecha_rechazo_rcf'],
        'motivo_rechazo_rcf': ['motivo_rechazo_rcf', 'MOTIVO_RECHAZO_RCF', 'Motivo Rechazo RCF', 'MOTIVO RECHAZO RCF'],
    },
    'face': {
        'registro': ['registro', 'Registro', 'ID_FACE', 'id_face', 'Nº Registro'],
        'fecha_registro': ['fecha_registro', 'Fecha Registro', 'fecha', 'Fecha'],
        'nif_emisor': ['nif_emisor', 'NIF', 'nif', 'CIF', 'cif'],
        'nombre': ['nombre', 'Nombre', 'razon_social', 'Razón Social'],
        'numero': ['numero', 'Número', 'Nº Factura', 'numero_factura'],
        'serie': ['serie', 'Serie'],
        'importe': ['importe', 'Importe', 'Total', 'total', 'importe_total'],
        'moneda_original': ['moneda_original', 'moneda', 'Moneda', 'divisa'],
        'oc': ['oc', 'OC', 'Oficina Contable', 'codigo_oc'],
        'og': ['og', 'OG', 'Órgano Gestor', 'codigo_og'],
        'ut': ['ut', 'UT', 'Unidad Tramitadora', 'codigo_ut']
    },
    'anulaciones': {
        'registro': ['registro', 'Registro', 'ID_FACE', 'id_face', 'Nº Registro'],
        'fecha_solicitud_anulacion': ['fecha_solicitud_anulacion', 'Fecha Solicitud', 'fecha', 'Fecha', 'fecha solicitud anulacion'],
        'comentario': ['comentario', 'Comentario', 'observaciones', 'Observaciones', 'motivo']
    },
    'estados': {
        'registro': ['registro', 'Registro', 'ID_FACE', 'id_face', 'Nº Registro'],
        'codigo': ['codigo', 'Código', 'codigo_estado', 'Estado'],
        'insertado': ['insertado', 'Insertado', 'fecha', 'Fecha', 'fecha_cambio', 'insertado_h']
    }
}

def encontrar_columna(df: pd.DataFrame, nombre_estandar: str, tipo_archivo: str) -> str:
    """
    Encuentra el nombre real de una columna en el DataFrame
    buscando entre los posibles alias
    """
    if tipo_archivo not in MAPEO_COLUMNAS:
        return nombre_estandar
    
    posibles_nombres = MAPEO_COLUMNAS[tipo_archivo].get(nombre_estandar, [nombre_estandar])
    
    for nombre in posibles_nombres:
        if nombre in df.columns:
            return nombre
    
    # Si no se encuentra, devolver el nombre estándar
    return nombre_estandar

def normalizar_columnas(df: pd.DataFrame, tipo_archivo: str) -> pd.DataFrame:
    """
    Renombra las columnas del DataFrame a nombres estándar.
    Incluye limpieza de espacios extra y comparación case-insensitive.
    """
    df_normalizado = df.copy()
    mapeo = {}

    # Crear un diccionario de columnas normalizadas (sin espacios extra, lowercase)
    columnas_df_norm = {col.strip().lower(): col for col in df.columns}

    if tipo_archivo in MAPEO_COLUMNAS:
        for nombre_estandar, posibles_nombres in MAPEO_COLUMNAS[tipo_archivo].items():
            # Primero intentar coincidencia exacta
            for nombre_posible in posibles_nombres:
                if nombre_posible in df.columns:
                    mapeo[nombre_posible] = nombre_estandar
                    break
            else:
                # Si no hay coincidencia exacta, intentar con normalización
                for nombre_posible in posibles_nombres:
                    nombre_norm = nombre_posible.strip().lower()
                    if nombre_norm in columnas_df_norm:
                        col_original = columnas_df_norm[nombre_norm]
                        mapeo[col_original] = nombre_estandar
                        break

    if mapeo:
        df_normalizado = df_normalizado.rename(columns=mapeo)

    return df_normalizado

@st.cache_data
def cargar_datos(archivo_rcf, archivo_face, archivo_anulaciones, archivo_estados) -> Dict:
    """
    Carga todos los archivos Excel y retorna un diccionario con los DataFrames
    """
    try:
        # Cargar archivos
        df_rcf = pd.read_excel(archivo_rcf)
        df_face = pd.read_excel(archivo_face)
        df_anulaciones = pd.read_excel(archivo_anulaciones)
        df_estados = pd.read_excel(archivo_estados)
        
        # Limpiar nombres de columnas (quitar espacios)
        df_rcf.columns = df_rcf.columns.str.strip()
        df_face.columns = df_face.columns.str.strip()
        df_anulaciones.columns = df_anulaciones.columns.str.strip()
        df_estados.columns = df_estados.columns.str.strip()
        
        # Normalizar nombres de columnas
        df_rcf = normalizar_columnas(df_rcf, 'rcf')
        df_face = normalizar_columnas(df_face, 'face')
        df_anulaciones = normalizar_columnas(df_anulaciones, 'anulaciones')
        df_estados = normalizar_columnas(df_estados, 'estados')
        
        # Garantizar que fecha_codigo_f y fecha_codigo_s tengan columna aunque no se mapearon por nombre.
        # fecha_codigo_f = FECHA REGISTRO = fecha_anotacion_rcf (coincide con FECHA ACEPTACIÓN en estos datos)
        # fecha_codigo_s = FECHA RECEPCION FACE (si no está, se usará fecha_registro_face como fallback)
        if 'fecha_codigo_f' not in df_rcf.columns and 'fecha_anotacion_rcf' in df_rcf.columns:
            df_rcf['fecha_codigo_f'] = df_rcf['fecha_anotacion_rcf']
        if 'fecha_codigo_f' not in df_rcf.columns and 'fecha_aceptacion' in df_rcf.columns:
            df_rcf['fecha_codigo_f'] = df_rcf['fecha_aceptacion']
        if 'fecha_codigo_s' not in df_rcf.columns and 'fecha_registro_face' in df_rcf.columns:
            df_rcf['fecha_codigo_s'] = df_rcf['fecha_registro_face']

        # Convertir fechas
        df_rcf = convertir_fechas(df_rcf, [
            'fecha_emision', 'fecha_anotacion_rcf', 'fecha_registro_face', 'fecha_aceptacion',
            'fecha_codigo_s', 'fecha_codigo_f', 'fecha_aceptacion_ut', 'fecha_conformidad',
            'fecha_rechazo',
        ])
        df_face = convertir_fechas(df_face, ['fecha_registro'])
        df_anulaciones = convertir_fechas(df_anulaciones, ['fecha_solicitud_anulacion'])
        df_estados = convertir_fechas(df_estados, ['insertado'])
        
        # Procesar facturas en papel vs electrónicas
        if 'ID_FACE' in df_rcf.columns:
            # Asegurar que ID_FACE se trate como cadena para consistencia y limpiar espacios
            df_rcf['ID_FACE'] = df_rcf['ID_FACE'].fillna('').astype(str).str.strip()
            # Es papel si está vacío o es 'nan' (resultado de fillna de un nulo real que luego se convirtió a string)
            df_rcf['es_papel'] = (df_rcf['ID_FACE'] == '') | (df_rcf['ID_FACE'].str.lower() == 'nan')
        else:
            df_rcf['es_papel'] = True  # Asumir papel si no hay columna ID_FACE
            df_rcf['ID_FACE'] = ''

        # EXCLUIR FACTURAS BORRADAS (Global desactivado - se hará por página)
        if 'estado' in df_rcf.columns:
            borradas = len(df_rcf[df_rcf['estado'].astype(str).str.upper() == 'BORRADA'])
            if borradas > 0:
                st.sidebar.info(f"🗑️ Se han detectado {borradas} facturas 'BORRADA' en el RCF (se usarán solo en Validaciones)")
        
        # Convertir tipos numéricos
        if 'importe_total' in df_rcf.columns:
            df_rcf['importe_total'] = pd.to_numeric(df_rcf['importe_total'], errors='coerce')
        
        if 'base_imponible' in df_rcf.columns:
            df_rcf['base_imponible'] = pd.to_numeric(df_rcf['base_imponible'], errors='coerce')
        else:
            # Si no existe, usamos importe_total como fallback para evitar errores, 
            # pero lo ideal es que esté la columna.
            if 'importe_total' in df_rcf.columns:
                df_rcf['base_imponible'] = df_rcf['importe_total']
        
        if 'importe' in df_face.columns:
            df_face['importe'] = pd.to_numeric(df_face['importe'], errors='coerce')
        
        if 'id_fra_rcf' not in df_rcf.columns:
            df_rcf['id_fra_rcf'] = range(1, len(df_rcf) + 1)
        
        # FILTRAR POR EJERCICIO AUDITADO (Global) - Basado en Fecha de Registro en RCF
        import toml
        try:
            config_toml = toml.load(str(Path(__file__).parent.parent / ".streamlit" / "config.toml"))
            ejercicio_auditado = config_toml.get('auditoria', {}).get('ejercicio_auditado')
        except:
            ejercicio_auditado = CONFIGURACION.get('ejercicio_auditado')
            
        if ejercicio_auditado:
            # Mantener una copia de IDs de FACe antes de filtrar por año para el cálculo de retenidas
            # Esto evita que facturas sin fecha (como las 'BORRADA') aparezcan como retenidas si ya están en RCF
            ids_face_en_rcf_total = set(df_rcf[df_rcf['ID_FACE'].notna()]['ID_FACE'].astype(str))
            
            # Priorizamos filtrar por la columna 'ejercicio' (Año) si existe,
            # ya que suele estar más completa que las fechas individuales.
            if 'ejercicio' in df_rcf.columns:
                df_rcf['ejercicio'] = pd.to_numeric(df_rcf['ejercicio'], errors='coerce')
                # Incluir el año auditado y el anterior (según feedback del usuario)
                anios_permitidos = [float(ejercicio_auditado), float(ejercicio_auditado) - 1]
                df_rcf = df_rcf[df_rcf['ejercicio'].isin(anios_permitidos)].copy()
            elif 'fecha_anotacion_rcf' in df_rcf.columns:
                # Si filtramos por fecha, incluimos las de 2025 (incluyendo aquellas de 2024 registradas en 2025)
                # pero mantenemos la prioridad de la columna 'ejercicio' si está disponible
                df_rcf = df_rcf[df_rcf['fecha_anotacion_rcf'].dt.year == int(ejercicio_auditado)].copy()
            elif 'fecha_emision' in df_rcf.columns:
                df_rcf = df_rcf[df_rcf['fecha_emision'].dt.year == int(ejercicio_auditado)].copy()
                
            # Filtrar FACe por año de registro
            if 'fecha_registro' in df_face.columns:
                df_face = df_face[df_face['fecha_registro'].dt.year == int(ejercicio_auditado)].copy()
                
            # Filtrar Anulaciones por año de solicitud
            if 'fecha_solicitud_anulacion' in df_anulaciones.columns:
                df_anulaciones = df_anulaciones[df_anulaciones['fecha_solicitud_anulacion'].dt.year == int(ejercicio_auditado)].copy()
                
            # Filtrar Estados por año de inserción (si aplica) o por registros vinculados al RCF actual
            if 'insertado' in df_estados.columns:
                df_estados = df_estados[df_estados['insertado'].dt.year == int(ejercicio_auditado)].copy()
        else:
            ids_face_en_rcf_total = set(df_rcf[df_rcf['ID_FACE'].notna()]['ID_FACE'].astype(str))
        
        # Identificar facturas de FACe anuladas antes de llegar al RCF:
        # condición: tienen solicitud de anulación Y no aparecen en ningún ejercicio del RCF
        ids_anuladas_face = (
            set(df_anulaciones['registro'].astype(str))
            if 'registro' in df_anulaciones.columns
            else set()
        )
        if 'registro' in df_face.columns:
            face_ids = df_face['registro'].astype(str)
            mask_anulada = (
                ~face_ids.isin(ids_face_en_rcf_total) &
                face_ids.isin(ids_anuladas_face)
            )
            df_face_anuladas_antes_rcf = df_face[mask_anulada].copy()
        else:
            df_face_anuladas_antes_rcf = pd.DataFrame()

        return {
            'rcf': df_rcf,
            'face': df_face,
            'anulaciones': df_anulaciones,
            'estados': df_estados,
            'ids_face_en_rcf_total': ids_face_en_rcf_total,
            'face_anuladas_antes_rcf': df_face_anuladas_antes_rcf
        }
        
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.error(f"Detalles del error: {type(e).__name__}")
        raise e

def convertir_fechas(df: pd.DataFrame, columnas: List[str]) -> pd.DataFrame:
    """
    Convierte columnas a formato fecha.
    Usa formato europeo (día primero: DD/MM/YYYY) por defecto.
    """
    for col in columnas:
        if col in df.columns:
            try:
                # Usar dayfirst=True para formato europeo DD/MM/YYYY
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')
            except:
                pass
    return df

def validar_archivos(datos: Dict) -> Dict:
    """
    Valida que los archivos tengan datos y columnas mínimas
    """
    errores = []
    warnings = []
    
    # Validar que los DataFrames no estén vacíos
    if len(datos['rcf']) == 0:
        errores.append("El archivo RCF está vacío")
    
    if len(datos['face']) == 0:
        warnings.append("El archivo FACe está vacío")
    
    # Validar columnas críticas
    columnas_criticas_rcf = ['importe_total', 'fecha_emision']
    for col in columnas_criticas_rcf:
        if col not in datos['rcf'].columns:
            warnings.append(f"RCF: Falta la columna '{col}'")
    
    # Validar fechas
    if 'fecha_emision' in datos['rcf'].columns:
        nulas = datos['rcf']['fecha_emision'].isna().sum()
        if nulas > 0:
            warnings.append(f"RCF: {nulas} facturas sin fecha de emisión")
    
    return {
        'valido': len(errores) == 0,
        'errores': errores,
        'warnings': warnings
    }

@st.cache_data
def filtrar_por_periodo(df: pd.DataFrame, fecha_col: str, fecha_inicio=None, fecha_fin=None) -> pd.DataFrame:
    """
    Filtra un DataFrame por periodo de fechas
    """
    df_filtrado = df.copy()
    
    if fecha_col not in df.columns:
        return df_filtrado
    
    if fecha_inicio:
        df_filtrado = df_filtrado[df_filtrado[fecha_col] >= pd.to_datetime(fecha_inicio)]
    
    if fecha_fin:
        df_filtrado = df_filtrado[df_filtrado[fecha_col] <= pd.to_datetime(fecha_fin)]
    
    return df_filtrado

@st.cache_data
def calcular_estadisticas_basicas(df: pd.DataFrame) -> Dict:
    """
    Calcula estadísticas básicas de un DataFrame
    """
    stats = {
        'total_registros': len(df),
        'columnas': list(df.columns),
        'tipos': df.dtypes.to_dict(),
        'nulos': df.isna().sum().to_dict(),
    }
    
    # Si hay columna de importe
    if 'importe_total' in df.columns:
        stats['importe_total'] = df['importe_total'].sum()
        stats['importe_medio'] = df['importe_total'].mean()
        stats['importe_max'] = df['importe_total'].max()
        stats['importe_min'] = df['importe_total'].min()
    
    return stats

def es_persona_juridica(nif: str) -> bool:
    """
    Identifica si un NIF corresponde a una Persona Jurídica en España
    Prefijos de PJ: A, B, C, D, E, F, G, H, J, P, Q, R, S, U, V, N, W
    """
    if pd.isna(nif) or not str(nif):
        return False
    
    # Limpiar y obtener primer carácter
    s_nif = str(nif).strip().upper()
    if not s_nif:
        return False
        
    first_char = s_nif[0]
    
    # Si empieza por letra y no es NIE (X, Y, Z), se considera PJ en este contexto de auditoría
    # (Siguiendo la lógica de la Guía IGAE y los tipos de NIF comunes)
    return first_char.isalpha() and first_char not in ['X', 'Y', 'Z']

def excluir_facturas_borradas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Excluye las facturas con estado BORRADA del DataFrame.
    Según la guía IGAE, las facturas borradas no deben tenerse en cuenta
    en los análisis de auditoría.
    """
    if 'estado' in df.columns:
        return df[df['estado'].astype(str).str.upper() != 'BORRADA'].copy()
    return df.copy()


def agregar_columna_entidad(df: pd.DataFrame, posicion: int = 0) -> pd.DataFrame:
    """
    Agrega la columna 'Entidad' como primera columna en el DataFrame.
    Útil para las tablas de presentación de facturas.
    """
    df_con_entidad = df.copy()
    entidad = CONFIGURACION.get('nombre_entidad', 'Sin especificar')

    # Insertar columna de entidad en la posición indicada
    df_con_entidad.insert(posicion, 'Entidad', entidad)

    return df_con_entidad


def obtener_facturas_papel_sospechosas(df_rcf: pd.DataFrame) -> pd.DataFrame:
    """
    Identifica facturas en papel que podrían incumplir la normativa
    Según Ley 25/2013 y Circular 1/2015 IGAE

    NOTA: Se excluyen facturas BORRADAS según criterios de auditoría
    """
    # Criterios desde configuración
    ejercicio_auditado = CONFIGURACION['ejercicio_auditado']
    importe_minimo = CONFIGURACION['importe_minimo_obligatorio']
    fecha_obligatoriedad = pd.to_datetime(CONFIGURACION['fecha_inicio_obligatoriedad'])

    # Verificar columnas necesarias
    columnas_necesarias = ['es_papel', 'fecha_emision', 'base_imponible']
    if not all(col in df_rcf.columns for col in columnas_necesarias):
        return pd.DataFrame()

    # PRIMERO: Excluir facturas BORRADAS (no deben tenerse en cuenta)
    df_trabajo = excluir_facturas_borradas(df_rcf)

    # Filtrar
    condicion = (
        (df_trabajo['es_papel'] == True) &
        (df_trabajo['fecha_emision'] > fecha_obligatoriedad) # Mantener por seguridad normativa general
    )

    if 'fecha_anotacion_rcf' in df_trabajo.columns:
        condicion &= (df_trabajo['fecha_anotacion_rcf'].dt.year == int(ejercicio_auditado))
    elif 'ejercicio' in df_trabajo.columns:
        # Convertir a numérico y comparar (maneja floats como 2025.0)
        df_trabajo['ejercicio'] = pd.to_numeric(df_trabajo['ejercicio'], errors='coerce')
        condicion &= (df_trabajo['ejercicio'] == float(ejercicio_auditado))
    else:
        condicion &= (df_trabajo['fecha_emision'].dt.year == int(ejercicio_auditado))

    # Filtrar por importe (Base Imponible)
    condicion &= (df_trabajo['base_imponible'] > importe_minimo)

    df_sospechoso = df_trabajo[condicion].copy()

    # Filtrar por tipo de persona (Personas Jurídicas)
    if 'tipo_persona' in df_sospechoso.columns:
        tiene_j = (df_sospechoso['tipo_persona'] == 'J').any()
        if tiene_j:
            df_sospechoso = df_sospechoso[df_sospechoso['tipo_persona'] == 'J']
        else:
            # Fallback: Identificar por prefijo de NIF si no hay 'J's
            df_sospechoso = df_sospechoso[df_sospechoso['nif_emisor'].apply(es_persona_juridica)]
    else:
        # Si no hay columna de tipo, aplicamos por NIF
        if 'nif_emisor' in df_sospechoso.columns:
            df_sospechoso = df_sospechoso[df_sospechoso['nif_emisor'].apply(es_persona_juridica)]

    # Filtrar por estado: excluir RECHAZADA y ANULADA (además de BORRADA ya excluida)
    if 'estado' in df_sospechoso.columns:
        df_sospechoso = df_sospechoso[~df_sospechoso['estado'].astype(str).str.upper().isin(['RECHAZADA', 'ANULADA'])]

    return df_sospechoso

def calcular_tiempos_anotacion(df_rcf: pd.DataFrame, df_face: pd.DataFrame = None) -> pd.DataFrame:
    """
    Calcula los tiempos de inscripción en el RCF.

    - Facturas FACe:  tiempo = fecha_aceptacion - fecha_registro_face
                      (desde registro en FACe hasta aceptación)
    - Facturas papel: tiempo = fecha_aceptacion - fecha_anotacion_rcf
                      (desde fecha de registro en RCF hasta aceptación)

    Requiere la columna 'fecha_aceptacion' en el RCF.
    Devuelve columna 'tipo_origen' = 'FACe' | 'Papel' y
    'fecha_inicio' con la fecha usada como origen del cómputo.
    """
    if 'fecha_aceptacion' not in df_rcf.columns:
        return pd.DataFrame()

    segmentos = []

    # --- Facturas FACe (electrónicas) ---
    df_face_inv = df_rcf[df_rcf['es_papel'] == False].copy()

    tiene_col_face = (
        'fecha_registro_face' in df_face_inv.columns
        and df_face_inv['fecha_registro_face'].notna().any()
    )

    if tiene_col_face:
        df_seg = df_face_inv.dropna(subset=['fecha_aceptacion', 'fecha_registro_face']).copy()
        df_seg['fecha_inicio'] = df_seg['fecha_registro_face']
    elif df_face is not None and 'registro' in df_face.columns and 'ID_FACE' in df_face_inv.columns:
        # Fallback: obtener fecha de registro desde el archivo FACe
        df_seg = df_face_inv.merge(
            df_face[['registro', 'fecha_registro']],
            left_on='ID_FACE',
            right_on='registro',
            how='left'
        ).rename(columns={'fecha_registro': 'fecha_registro_face'})
        df_seg = df_seg.dropna(subset=['fecha_aceptacion', 'fecha_registro_face']).copy()
        df_seg['fecha_inicio'] = df_seg['fecha_registro_face']
    else:
        df_seg = pd.DataFrame()

    if not df_seg.empty:
        df_seg['tipo_origen'] = 'FACe'
        segmentos.append(df_seg)

    # --- Facturas papel ---
    if 'fecha_anotacion_rcf' in df_rcf.columns:
        df_papel = df_rcf[df_rcf['es_papel'] == True].copy()
        df_papel = df_papel.dropna(subset=['fecha_aceptacion', 'fecha_anotacion_rcf']).copy()
        if not df_papel.empty:
            df_papel['fecha_inicio'] = df_papel['fecha_anotacion_rcf']
            df_papel['tipo_origen'] = 'Papel'
            segmentos.append(df_papel)

    if not segmentos:
        return pd.DataFrame()

    df_resultado = pd.concat(segmentos, ignore_index=True)

    # tiempo = fecha_aceptacion - fecha_inicio (en minutos)
    df_resultado['tiempo_anotacion_min'] = (
        df_resultado['fecha_aceptacion'] - df_resultado['fecha_inicio']
    ).dt.total_seconds() / 60

    return df_resultado

def identificar_facturas_retenidas(df_face: pd.DataFrame, df_rcf: pd.DataFrame, ids_precalculados=None) -> pd.DataFrame:
    """
    Identifica facturas que están en FACe pero no en RCF (retenidas)
    """
    if 'registro' not in df_face.columns:
        return pd.DataFrame()
    
    # Obtener IDs de facturas en RCF
    if ids_precalculados is not None:
        ids_rcf = ids_precalculados
    else:
        if 'ID_FACE' not in df_rcf.columns:
            return pd.DataFrame()
        ids_rcf = set(df_rcf[df_rcf['ID_FACE'].apply(lambda x: str(x).strip() not in ['', 'nan', 'NaN', 'None'])]['ID_FACE'].astype(str))
    
    # Facturas en FACe que no están en RCF
    df_retenidas = df_face[~df_face['registro'].astype(str).isin(ids_rcf)].copy()
    
    return df_retenidas

def obtener_ranking_por_campo(df: pd.DataFrame, campo_agrupar: str, 
                               campo_sumar: str = 'importe_total', 
                               top_n: int = 10) -> pd.DataFrame:
    """
    Obtiene un ranking por un campo específico
    """
    if campo_agrupar not in df.columns or campo_sumar not in df.columns:
        return pd.DataFrame()
    
    # Necesitamos una columna para contar
    columna_contar = 'id_fra_rcf' if 'id_fra_rcf' in df.columns else df.columns[0]
    
    ranking = df.groupby(campo_agrupar).agg({
        columna_contar: 'count',
        campo_sumar: 'sum'
    }).rename(columns={
        columna_contar: 'num_facturas',
        campo_sumar: 'importe_total'
    }).sort_values('importe_total', ascending=False).head(top_n)
    
    return ranking

def clasificar_procedimiento(df_rcf: pd.DataFrame, fecha_cambio=None) -> pd.DataFrame:
    """
    Clasifica cada factura electrónica por el procedimiento realmente aplicado
    durante el año de transición 2025.

    La clasificación es EXCLUSIVAMENTE por fecha, sin requerir un campo codigo_s:
      - fecha_codigo_s ("FECHA RECEPCION FACE") < fecha_cambio → PROCEDIMIENTO_ANTERIOR_S_F
      - fecha_codigo_s >= fecha_cambio → ANOTACION_DIRECTA_F
      - factura rechazada (fecha_rechazo presente) → RECHAZO_PREVIO_A_ANOTACION
      - sin fechas suficientes → INCIDENCIA_A_ANALIZAR

    Campos añadidos al DataFrame:
      procedimiento_aplicado: PROCEDIMIENTO_ANTERIOR_S_F | ANOTACION_DIRECTA_F |
                               RECHAZO_PREVIO_A_ANOTACION | INCIDENCIA_A_ANALIZAR
      resultado_auditoria_rcf: valor detallado (ver spec sección 5.2)
    """
    from config.settings import CONFIGURACION_TRANSICION_2025

    df = df_rcf.copy()

    if fecha_cambio is None:
        fecha_cambio_cfg = CONFIGURACION_TRANSICION_2025.get('fecha_efectiva_cambio_procedimiento')
        fecha_cambio = pd.to_datetime(fecha_cambio_cfg) if fecha_cambio_cfg else None

    tiene_fecha_s = 'fecha_codigo_s' in df.columns
    tiene_fecha_f = 'fecha_codigo_f' in df.columns
    tiene_rechazo = 'fecha_rechazo' in df.columns

    # Columna de referencia para clasificar: "FECHA RECEPCION FACE" o fallback a fecha_anotacion_rcf
    col_fecha_ref = 'fecha_codigo_s' if tiene_fecha_s else ('fecha_anotacion_rcf' if 'fecha_anotacion_rcf' in df.columns else None)

    def _procedimiento(row):
        fecha_ref = row.get(col_fecha_ref) if col_fecha_ref else None
        tiene_rechazo_fila = pd.notna(row.get('fecha_rechazo')) if tiene_rechazo else False

        if tiene_rechazo_fila:
            return 'RECHAZO_PREVIO_A_ANOTACION'

        if fecha_cambio is not None and pd.notna(fecha_ref):
            if fecha_ref < fecha_cambio:
                return 'PROCEDIMIENTO_ANTERIOR_S_F'
            return 'ANOTACION_DIRECTA_F'

        # Sin fecha de referencia: si tiene fecha_codigo_f, asumir F directo; si no, incidencia
        if tiene_fecha_f and pd.notna(row.get('fecha_codigo_f')):
            return 'ANOTACION_DIRECTA_F'
        return 'INCIDENCIA_A_ANALIZAR'

    def _resultado(row):
        proc = row['procedimiento_aplicado']
        motivo = str(row.get('motivo_rechazo_rcf', '')).strip() if pd.notna(row.get('motivo_rechazo_rcf', None)) else ''
        fecha_ref = row.get(col_fecha_ref) if col_fecha_ref else None
        tiene_f_definitivo = tiene_fecha_f and pd.notna(row.get('fecha_codigo_f'))

        if proc == 'PROCEDIMIENTO_ANTERIOR_S_F':
            # Facturas recibidas antes del cambio pero que podrían no tener F aún
            if not tiene_f_definitivo:
                return 'REGIMEN_ANTERIOR_S_SIN_F'
            return 'TRAMITADA_REGIMEN_ANTERIOR_S_F'

        if proc == 'ANOTACION_DIRECTA_F':
            # Verificar si alguna es posterior al cambio pero con fecha_codigo_s < cambio
            # (no aplica aquí porque la clasificación ya usa la fecha directamente)
            return 'ANOTADA_DIRECTA_F_CORRECTA'

        if proc == 'RECHAZO_PREVIO_A_ANOTACION':
            if motivo:
                return 'RECHAZADA_VALIDACION_TRAZABLE'
            return 'RECHAZADA_SIN_CAUSA_SUFICIENTE'

        return 'INCIDENCIA_MANUAL'

    mask_electronica = df['es_papel'] == False if 'es_papel' in df.columns else pd.Series(True, index=df.index)

    df['procedimiento_aplicado'] = 'NO_APLICA'
    df['resultado_auditoria_rcf'] = 'NO_APLICA'

    if mask_electronica.any():
        df_elec = df[mask_electronica].copy()
        df_elec['procedimiento_aplicado'] = df_elec.apply(_procedimiento, axis=1)
        df_elec['resultado_auditoria_rcf'] = df_elec.apply(_resultado, axis=1)
        df.loc[mask_electronica, 'procedimiento_aplicado'] = df_elec['procedimiento_aplicado'].values
        df.loc[mask_electronica, 'resultado_auditoria_rcf'] = df_elec['resultado_auditoria_rcf'].values

    return df


def calcular_indicadores_procedimiento_anterior(df_rcf: pd.DataFrame) -> pd.DataFrame:
    """
    Para facturas con procedimiento_aplicado == PROCEDIMIENTO_ANTERIOR_S_F,
    calcula los indicadores temporales (en minutos):

      tiempo_s_f    — FECHA RECEPCION FACE → FECHA REGISTRO
                      Tiempo de permanencia en estado previo (el indicador auditor clave).
      tiempo_face_f — fecha FACe → FECHA REGISTRO
                      Tiempo total hasta el registro definitivo (calculable si existe fecha FACe).
      tiempo_face_s — fecha FACe → FECHA RECEPCION FACE
                      Tiempo de descarga técnica desde FACe (calculable si existe fecha FACe).

    Fuentes de columnas en los datos reales:
      fecha_codigo_s = "FECHA RECEPCION FACE"  (hito S del procedimiento anterior)
      fecha_codigo_f = "FECHA REGISTRO" ≈ "FECHA ACEPTACIÓN"  (hito F / registro definitivo)
      fecha_registro_face = fecha de registro en FACe (del fichero FACe o columna propia del RCF)

    Registros con fechas ausentes o tiempos negativos se marcan incidencia_temporal=True
    y se excluyen de las medias, pero se conservan para revisión individualizada.
    """
    if 'procedimiento_aplicado' not in df_rcf.columns:
        return pd.DataFrame()

    df = df_rcf[df_rcf['procedimiento_aplicado'] == 'PROCEDIMIENTO_ANTERIOR_S_F'].copy()
    if df.empty:
        return pd.DataFrame()

    # Indicador principal: FECHA RECEPCION FACE → FECHA REGISTRO
    tiene_s = 'fecha_codigo_s' in df.columns
    tiene_f = 'fecha_codigo_f' in df.columns
    tiene_face = 'fecha_registro_face' in df.columns

    if tiene_s and tiene_f:
        df['tiempo_s_f'] = (df['fecha_codigo_f'] - df['fecha_codigo_s']).dt.total_seconds() / 60
    else:
        df['tiempo_s_f'] = pd.NA

    if tiene_face and tiene_f:
        df['tiempo_face_f'] = (df['fecha_codigo_f'] - df['fecha_registro_face']).dt.total_seconds() / 60
    else:
        df['tiempo_face_f'] = pd.NA

    if tiene_face and tiene_s:
        df['tiempo_face_s'] = (df['fecha_codigo_s'] - df['fecha_registro_face']).dt.total_seconds() / 60
    else:
        df['tiempo_face_s'] = pd.NA

    df['incidencia_temporal'] = (
        (df['tiempo_s_f'].isna() | (df['tiempo_s_f'] < 0)) &
        (df['tiempo_face_f'].isna() | (df['tiempo_face_f'] < 0))
    )

    return df


def calcular_indicadores_procedimiento_nuevo(df_rcf: pd.DataFrame) -> pd.DataFrame:
    """
    Para facturas con procedimiento_aplicado == ANOTACION_DIRECTA_F,
    calcula el indicador temporal (en minutos):

      tiempo_face_f_directo — fecha FACe → FECHA REGISTRO (anotación directa en el RCF)

    Fuentes:
      fecha_codigo_s = "FECHA RECEPCION FACE" (en el nuevo procedimiento ≈ fecha FACe)
      fecha_codigo_f = "FECHA REGISTRO" (= fecha de anotación directa F)
      fecha_registro_face = fecha de registro en FACe (del fichero FACe, si disponible)

    Para el nuevo procedimiento, "FECHA RECEPCION FACE" y "FECHA REGISTRO" coinciden o
    están muy próximas, por lo que el indicador refleja directamente el tiempo de inscripción.
    """
    if 'procedimiento_aplicado' not in df_rcf.columns:
        return pd.DataFrame()

    df = df_rcf[df_rcf['procedimiento_aplicado'] == 'ANOTACION_DIRECTA_F'].copy()
    if df.empty:
        return pd.DataFrame()

    # Preferencia de fecha inicial: fecha_registro_face (FACe), fallback fecha_codigo_s
    if 'fecha_registro_face' in df.columns and df['fecha_registro_face'].notna().any():
        col_inicio = 'fecha_registro_face'
    elif 'fecha_codigo_s' in df.columns:
        col_inicio = 'fecha_codigo_s'
    else:
        df['tiempo_face_f_directo'] = pd.NA
        df['incidencia_temporal'] = True
        return df

    col_fin = 'fecha_codigo_f' if 'fecha_codigo_f' in df.columns else None
    if col_fin is None:
        df['tiempo_face_f_directo'] = pd.NA
        df['incidencia_temporal'] = True
        return df

    df['tiempo_face_f_directo'] = (
        df[col_fin] - df[col_inicio]
    ).dt.total_seconds() / 60

    df['incidencia_temporal'] = (
        df['tiempo_face_f_directo'].isna() | (df['tiempo_face_f_directo'] < 0)
    )

    return df


def calcular_indicadores_tramitacion_posterior(df_rcf: pd.DataFrame) -> pd.DataFrame:
    """
    Para facturas con procedimiento_aplicado == ANOTACION_DIRECTA_F que ya tienen
    fecha de aceptación o conformidad, calcula el indicador de tramitación posterior
    (en minutos):

      tiempo_f_aceptacion — código F → fecha aceptación/conformidad

    Este indicador pertenece al Apartado 4 del informe (tramitación posterior),
    NO debe denominarse tiempo de inscripción en el RCF.
    """
    cols_requeridas = {'fecha_codigo_f', 'procedimiento_aplicado'}
    if not cols_requeridas.issubset(df_rcf.columns):
        return pd.DataFrame()

    df = df_rcf[df_rcf['procedimiento_aplicado'] == 'ANOTACION_DIRECTA_F'].copy()
    if df.empty:
        return pd.DataFrame()

    # Usar fecha_aceptacion_ut si existe; si no, fecha_aceptacion como fallback
    if 'fecha_aceptacion_ut' in df.columns and df['fecha_aceptacion_ut'].notna().any():
        df['fecha_tramitacion'] = df['fecha_aceptacion_ut']
    elif 'fecha_aceptacion' in df.columns:
        df['fecha_tramitacion'] = df['fecha_aceptacion']
    else:
        return pd.DataFrame()

    # También registrar conformidad si existe (indicador alternativo)
    if 'fecha_conformidad' in df.columns:
        df['tiempo_f_conformidad'] = (
            df['fecha_conformidad'] - df['fecha_codigo_f']
        ).dt.total_seconds() / 60

    df['tiempo_f_aceptacion'] = (
        df['fecha_tramitacion'] - df['fecha_codigo_f']
    ).dt.total_seconds() / 60

    df['incidencia_temporal'] = (
        df['tiempo_f_aceptacion'].isna() | (df['tiempo_f_aceptacion'] < 0)
    )

    return df


def exportar_a_excel(df: pd.DataFrame, nombre_archivo: str):
    """
    Exporta un DataFrame a Excel y retorna los bytes para descarga
    """
    import io
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    
    return output.getvalue()