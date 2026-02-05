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
        'fecha_anotacion_rcf': ['Fecha registro', 'fecha_anotacion_rcf', 'fecha_anotacion', 'Fecha Anotación', 'fecha_registro', 'FECHA REGISTRO', 'F. DE GRABACIÓN DE LA OPER.'],
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
        'motivo_rechazo': ['motivo_rechazo', 'MOTIVO RECHAZO', 'Motivo Rechazo', 'MOTIVO']
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
    Renombra las columnas del DataFrame a nombres estándar
    """
    df_normalizado = df.copy()
    mapeo = {}
    
    if tipo_archivo in MAPEO_COLUMNAS:
        for nombre_estandar, posibles_nombres in MAPEO_COLUMNAS[tipo_archivo].items():
            for nombre_posible in posibles_nombres:
                if nombre_posible in df.columns:
                    mapeo[nombre_posible] = nombre_estandar
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
        
        # Convertir fechas
        df_rcf = convertir_fechas(df_rcf, ['fecha_emision', 'fecha_anotacion_rcf'])
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
        
        return {
            'rcf': df_rcf,
            'face': df_face,
            'anulaciones': df_anulaciones,
            'estados': df_estados,
            'ids_face_en_rcf_total': ids_face_en_rcf_total
        }
        
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.error(f"Detalles del error: {type(e).__name__}")
        raise e

def convertir_fechas(df: pd.DataFrame, columnas: List[str]) -> pd.DataFrame:
    """
    Convierte columnas a formato fecha
    """
    for col in columnas:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
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

def calcular_tiempos_anotacion(df_rcf: pd.DataFrame, df_face: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula los tiempos de anotación en RCF desde FACe
    """
    # Verificar columnas necesarias
    if 'ID_FACE' not in df_rcf.columns or 'registro' not in df_face.columns:
        return pd.DataFrame()
    
    # Merge de facturas electrónicas
    # Renombramos fecha_registro a fecha_registro_face para evitar confusión
    df_merge = df_rcf[df_rcf['es_papel'] == False].merge(
        df_face[['registro', 'fecha_registro']],
        left_on='ID_FACE',
        right_on='registro',
        how='left'
    ).rename(columns={'fecha_registro': 'fecha_registro_face'})
    
    # Verificar que existan las columnas de fecha
    if 'fecha_anotacion_rcf' not in df_merge.columns or 'fecha_registro_face' not in df_merge.columns:
        return pd.DataFrame()
    
    # Limpieza: Si fecha_anotacion_rcf es nula, no podemos calcular
    df_merge = df_merge.dropna(subset=['fecha_anotacion_rcf', 'fecha_registro_face']).copy()
    
    # Calcular diferencia en minutos (Anotación - Registro en FACe)
    # Si sale negativo, es que la fecha de anotación es anterior (error de datos)
    df_merge['tiempo_anotacion_min'] = (
        df_merge['fecha_anotacion_rcf'] - df_merge['fecha_registro_face']
    ).dt.total_seconds() / 60
    
    # Filtrar outliers o errores absurdos (tiempos negativos) para métricas limpias
    # Pero los mantenemos si el usuario quiere auditar errores de sistema
    
    return df_merge

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

def exportar_a_excel(df: pd.DataFrame, nombre_archivo: str):
    """
    Exporta un DataFrame a Excel y retorna los bytes para descarga
    """
    import io
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    
    return output.getvalue()