# Uber Facturas

Herramienta para descargar facturas de Uber de forma automatica. Compuesta por una extension de Chrome para extraer la cookie de sesion y un programa de escritorio para gestionar las descargas.

---

## Requisitos

- Windows 10 o superior
- Google Chrome
- Cuenta activa en [riders.uber.com](https://riders.uber.com)

---

## Instalacion

### 1. Extension de Chrome — Uber Cookie

La extension captura automaticamente la cookie de sesion mientras navegas en riders.uber.com.

1. Instalar la extension desde la Chrome Web Store:  
   [Uber Cookie — Chrome Web Store](https://chromewebstore.google.com/detail/uber-cookie/choecpneimnmjeeojbjfcfodnegnonkd)
2. Iniciar sesion en [riders.uber.com](https://riders.uber.com)
3. Navegar a la seccion **Tus viajes** (o cualquier pagina que cargue datos)
4. Hacer clic en el icono de la extension en la barra de Chrome
5. La cookie se captura automaticamente — hacer clic en **Copiar**

### 2. Programa de escritorio — Uber Facturas

**Opcion A — Ejecutable (recomendado)**

1. Descargar `UberFacturas.exe` desde la seccion [Releases](../../releases)
2. Ejecutar el archivo — no requiere instalacion ni dependencias

**Opcion B — Desde el codigo fuente**

1. Clonar o descargar este repositorio
2. Instalar dependencias:
   ```
   pip install requests customtkinter
   ```
3. Ejecutar:
   ```
   python index.py
   ```

---

## Uso

1. Abrir **Uber Facturas.exe** (o ejecutar `index.py`)
2. Pegar la cookie copiada desde la extension en el campo **Cookies**
3. Seleccionar el **Mes** y el **Año** de las facturas a descargar
4. Configurar el numero de **Hilos** (descargas en paralelo, recomendado: 5)
5. Elegir la **Carpeta** de destino donde se guardaran los archivos
6. Hacer clic en **Descargar Facturas**

El programa mostrara el progreso en tiempo real en el panel inferior.

---

## Compilar el ejecutable

Para generar el `.exe` desde el codigo fuente se recomienda usar **auto-py-to-exe**:

1. Instalar:
   ```
   pip install auto-py-to-exe
   ```
2. Abrir la interfaz:
   ```
   auto-py-to-exe
   ```
3. Configuracion recomendada:
   - Script: `index.py`
   - One File: activado
   - Window Based: activado (sin consola)
   - Icon: `icono.ico`
   - Additional Files: agregar `icono.ico` si se quiere incluir en el ejecutable

---

## Contenido del repositorio

| Archivo | Descripcion |
|---|---|
| `index.py` | Codigo fuente principal del programa |
| `icono.ico` | Icono de la aplicacion |
| `README.md` | Este archivo |

El ejecutable compilado (`UberFacturas.exe`) se encuentra en la seccion [Releases](../../releases).

---

## Notas

- La cookie tiene una duracion limitada. Si la descarga falla, volver a copiar la cookie desde la extension.
- No cerrar sesion en riders.uber.com mientras se ejecuta la descarga.
- El numero de hilos recomendado es entre 3 y 8. Valores muy altos pueden causar errores.

---

## Contribuciones y mejoras

Las sugerencias y mejoras son bienvenidas. Hay dos formas de contribuir:

- **Pull Request** — Se puede proponer codigo directamente en este repositorio. Toda mejora es revisada y requiere aprobacion antes de ser integrada.
- **Correo** — Para consultas, sugerencias o reportes: [bryanpinzon469@gmail.com](mailto:bryanpinzon469@gmail.com)

---

## Creditos

Desarrollado por **Cody Prime**
