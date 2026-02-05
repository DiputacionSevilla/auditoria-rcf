"""
Configuración global de la aplicación
"""

# Configuración general
CONFIGURACION = {
    'nombre_entidad': 'Diputación de Sevilla',
    'ejercicio_auditado': '2025',
    'fecha_inicio_obligatoriedad': '2025-01-01',
    'fecha_inicio_validaciones': '2025-01-01',
    'importe_minimo_obligatorio': 3000,
    'meses_alerta_morosidad': 3,
}

# Colores corporativos
COLORES = {
    'primario': '#0066CC',
    'secundario': '#FF6B35',
    'exito': '#28A745',
    'advertencia': '#FFC107',
    'error': '#DC3545',
    'info': '#17A2B8',
    'fondo': '#F8F9FA',
    'card': '#FFFFFF',
    'texto': '#212529',
    'border': '#DEE2E6'
}

# Colores para gráficos
COLORES_GRAFICOS = {
    'papel': '#FF6B6B',
    'electronicas': '#4ECDC4',
    # Estados específicos del RCF (mapeo directo por etiqueta)
    'pagada': '#2ECC71',          # Verde
    'contabilizada': '#3498DB',   # Azul
    'ordenada': '#9B59B6',        # Púrpura
    'inicial': '#95A5A6',         # Gris
    'pdte de aceptar': '#F1C40F', # Amarillo
    'rechazada': '#E74C3C',       # Rojo
    'anulada': '#34495E',         # Gris oscuro
    # Compatibilidad y variaciones (singular/plural)
    'anuladas': '#34495E',
    'rechazadas': '#E74C3C',
    'pagadas': '#2ECC71',
    'conformadas': '#8360C3',
    'conformada': '#8360C3',
    'pendientes': '#F39C12',
    'pendiente': '#F39C12',
}

# Estados de facturas
ESTADOS_FACTURAS = {
    '1200': 'Registrada',
    '1300': 'Registrada en RCF',
    '1400': 'Verificada en RCF',
    '2100': 'Recibida en destino',
    '2300': 'Conformada',
    '2400': 'Contabilizada obligación',
    '2500': 'Pagada',
    '2600': 'Rechazada',
    '3100': 'Anulada'
}

# Validaciones HAP/1650/2015
VALIDACIONES_HAP = {
    '4c': 'No duplicidad de facturas',
    '5f': 'NIF emisor ≠ NIF cesionario',
    '6a': 'Importes líneas correctos (2 decimales)',
    '6b': 'Importes factura correctos (2 decimales)',
    '6c': 'Código moneda válido (ISO 4217)',
    '6d': 'Impuestos retenidos >= 0',
    '6e': 'Total bruto = bruto - descuentos + cargos',
    '6f': 'Total factura = bruto + repercutidos - retenidos'
}

# Columnas esperadas en archivos
COLUMNAS_ESPERADAS = {
    'rcf': [
        'id_fra_rcf', 'entidad', 'ID_FACE', 'fecha_emision', 'fecha_anotacion_rcf',
        'nif_emisor', 'razon_social', 'numero_factura', 'serie',
        'importe_total', 'moneda', 'tipo_persona', 'estado',
        'codigo_oc', 'codigo_og', 'codigo_ut'
    ],
    'face': [
        'registro', 'fecha_registro', 'nif_emisor', 'nombre',
        'numero', 'serie', 'importe', 'moneda_original',
        'oc', 'og', 'ut'
    ],
    'anulaciones': [
        'registro', 'fecha_solicitud_anulacion', 'comentario'
    ],
    'estados': [
        'registro', 'codigo', 'insertado'
    ]
}

# Configuración de informes
CONFIGURACION_INFORME = {
    'titulo': 'INFORME DE AUDITORÍA DEL REGISTRO CONTABLE DE FACTURAS',
    'subtitulo': 'Según Artículo 12 de la Ley 25/2013',
    'autor': 'Intervención General',
    'footer': 'Diputación de Sevilla - Intervención General',
}