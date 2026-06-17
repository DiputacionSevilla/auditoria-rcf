# Despliegue en Streamlit Cloud con datos por defecto (2025)

## Cambio técnico realizado en `app.py`

Se ha modificado la aplicación para que:

1. Busque automáticamente los 4 archivos Excel en la carpeta `datos/` al iniciar.
2. Los cargue sin intervención del usuario si existen.
3. Muestre en la barra lateral si se están usando datos por defecto o archivos subidos manualmente.
4. Permita al usuario subir otros archivos desde la barra lateral; si los sube, prevalecen sobre los por defecto.
5. Disponga de un botón **Inicializar** para limpiar la memoria y volver al estado inicial.

### Archivos esperados en `datos/`

| Clave | Archivo esperado |
|-------|------------------|
| RCF | `datos/1-ftras-RCF.xlsx` |
| FACe | `datos/2-Ftras FACe.xlsx` |
| Anulaciones | `datos/3-Anulacion de ftras.xlsx` |
| Estados | `datos/4-Cambio de estado de facturas.xlsx` |

> Si los archivos reales tienen otros nombres, se pueden adaptar fácilmente en `app.py` modificando el diccionario `RUTAS_DEFAULT`.

---

## Estrategia de despliegue elegida: repositorio privado + carpeta `datos/`

Los 4 archivos Excel de 2025 se suben al mismo repositorio privado de la aplicación, dentro de la carpeta `datos/`. Streamlit Cloud despliega directamente desde Git, por lo que los archivos estarán disponibles para la app en el momento del despliegue.

**Requisitos:**
- El repositorio debe ser **privado** porque contiene facturas de la Diputación de Sevilla.
- Cada archivo debe pesar menos de ~25 MB (límite recomendado de GitHub; el límite técnico es 100 MB por archivo).
- El `.gitignore` del proyecto bloquea `datos/` y `*.xlsx` por seguridad, por lo que hay que forzar la subida con `git add -f`.

### Pasos para subir los datos al repositorio privado

```bash
# 1. Asegurarse de que los 4 archivos están en la carpeta datos/
ls datos/
# 1-ftras-RCF.xlsx
# 2-Ftras FACe.xlsx
# 3-Anulacion de ftras.xlsx
# 4-Cambio de estado de facturas.xlsx

# 2. Forzar la subida porque .gitignore bloquea datos/ y *.xlsx
git add -f "datos/1-ftras-RCF.xlsx"
git add -f "datos/2-Ftras FACe.xlsx"
git add -f "datos/3-Anulacion de ftras.xlsx"
git add -f "datos/4-Cambio de estado de facturas.xlsx"

# 3. Confirmar y subir
git commit -m "Añade archivos de datos 2025 por defecto"
git push
```

### Ventajas

- Muy sencillo de configurar.
- Funciona inmediatamente con Streamlit Cloud sin credenciales adicionales.
- Los datos viajan y se versionan junto con el código.

### Inconvenientes

- Los Excel están en el repositorio. **Solo es viable si el repositorio es privado y la organización lo autoriza.**
- Si los archivos superan los 25 MB, es necesario usar Git LFS (ver Opción 3).
- Cada actualización de datos requiere un nuevo `commit` y `push`, lo que redeploya la aplicación.

---

## Alternativa para producción: almacenamiento privado + Streamlit Secrets

Si en el futuro se dispone de infraestructura en la nube, se recomienda no subir los Excel al repositorio. En su lugar:

- Los 4 archivos se guardan en un **bucket privado** (AWS S3, Azure Blob Storage, Google Cloud Storage, etc.) o en una URL privada interna de la Diputación.
- Se configuran en Streamlit Cloud (sección **Secrets**) las credenciales o tokens de acceso.
- Al arrancar, la app descarga los archivos a la carpeta `datos/` temporalmente y luego los procesa.

**Ventajas:**
- Datos sensibles fuera de GitHub.
- Se pueden actualizar los Excel sin redeployar la aplicación.
- Mayor cumplimiento con la protección de datos.

**Inconvenientes:**
- Requiere disponer de bucket/URL y credenciales.
- Añade complejidad inicial.

---

## Alternativa para archivos grandes: Git LFS

Si cada Excel supera los 25-100 MB, se puede usar Git Large File Storage:

```bash
git lfs track "datos/*.xlsx"
git add .gitattributes datos/
git commit -m "Añade datos 2025 con LFS"
git push
```

**Ventajas:**
- Maneja archivos grandes sin hinchar el historial de git.

**Inconvenientes:**
- Requiere activar Git LFS en el repositorio.
- Streamlit Cloud lo soporta, pero hay que verificar que la cuenta/plan lo permita.

---

## Pasos para desplegar en Streamlit Cloud

1. Subir el código y los datos a un repositorio Git privado (GitHub, GitLab o Bitbucket).
2. Conectar el repositorio en [share.streamlit.io](https://share.streamlit.io).
3. Asegurarse de que el archivo de entrada es `app.py`.
4. Si se usa la **alternativa de bucket privado**, configurar los secrets en el panel de Streamlit Cloud.
5. Desplegar la aplicación.

---

## Recomendación

Para el despliegue actual se ha elegido la estrategia de **repositorio privado + carpeta `datos/`** por simplicidad y porque los archivos actuales suman ~4 MB, muy por debajo de los límites de GitHub.

Dado que se trata de facturas de la Diputación de Sevilla, esta opción es adecuada **siempre que el repositorio sea privado**. Si en el futuro los archivos crecen o se requiere mayor seguridad, se recomienda migrar a la alternativa de **bucket privado + Streamlit Secrets**.
