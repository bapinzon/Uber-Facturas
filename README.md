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

1. Ir a la Chrome Web Store e instalar la extension:  
   [Uber Cookie — Chrome Web Store](https://chromewebstore.google.com/detail/uber-cookie/choecpneimnmjeeojbjfcfodnegnonkd)

2. Iniciar sesion en [riders.uber.com](https://riders.uber.com)

3. Navegar a la seccion **Tus viajes** (o cualquier pagina que cargue datos)

4. Hacer clic en el icono de la extension en la barra de Chrome

5. La cookie se captura automaticamente — hacer clic en **Copiar**

### 2. Programa de escritorio — Uber Facturas

1. Descargar el archivo `UberFacturas.exe` desde la seccion [Releases](../../releases)

2. Ejecutar el archivo (no requiere instalacion)

---

## Uso

1. Abrir **Uber Facturas.exe**

2. Pegar la cookie copiada desde la extension en el campo **Cookies**

3. Seleccionar el **Mes** y el **Año** de las facturas a descargar

4. Configurar el numero de **Hilos** (descargas en paralelo, recomendado: 5)

5. Elegir la **Carpeta** de destino donde se guardaran los archivos

6. Hacer clic en **Descargar Facturas**

El programa mostrara el progreso en tiempo real en el panel inferior.

---

## Notas

- La cookie tiene una duracion limitada. Si la descarga falla, volver a copiar la cookie desde la extension.
- No cerrar sesion en riders.uber.com mientras se ejecuta la descarga.
- El numero de hilos recomendado es entre 3 y 8. Valores muy altos pueden causar errores.

---

## Creditos

Desarrollado por **Cody Prime**
