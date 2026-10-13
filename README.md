# Integral · Ingresos variables

**Una aplicación web local para analizar documentos financieros, construir un libro de ingresos y estimar ingresos futuros con notas personales.** Los cálculos funcionan sin Internet; Ollama agrega explicaciones opcionales.

> Proyecto educativo y de finanzas personales. No es un servicio bancario ni asesoría financiera. Antes de tomar decisiones, comprueba los datos importados y las categorías.

## 1. Qué puede hacer

- **Subir CSV, Excel, PDF, TXT e imágenes** de movimientos bancarios o ingresos. Extrae fechas, montos y descripciones cuando el formato lo permite. Para imágenes y PDF escaneados utiliza OCR mediante Tesseract.
- **Revisar cada propuesta de importación** y decidir qué guardar. Nada se incorpora de manera automática después de una lectura.
- **Registrar manualmente ingresos** y clasificarlos como recurrentes, variables, extraordinarios, gastos o movimientos excluidos.
- **Guardar notas personales** como «Este alumno solo tomó una clase» y, opcionalmente, consultarlas con Ollama para obtener sugerencias de interpretación.
- **Ver análisis del mes actual, últimos 3 meses, últimos 12 meses o historial completo**, por fuente y periodo.
- **Estimar escenarios conservador, esperado y optimista** y ofrecer una referencia de ahorro al introducir un presupuesto mensual.
- **Guardar localmente** los registros y documentos originales (estos últimos solo si marcas la opción) con protección mediante contraseña y cifrado.
- **Exportar el libro** a CSV para respaldarlo y trabajarlo en otro programa.

## 2. Instalación rápida (Windows)

**Necesitas Python 3.11 o 3.12** instalado desde [python.org](https://www.python.org/downloads/) con la casilla *Add Python to PATH* y conexión a Internet **solo para instalar dependencias la primera vez**.

1. Descarga este repositorio como ZIP desde GitHub (Code → Download ZIP) y descomprímelo, o clónalo:
   ```powershell
   git clone https://github.com/EmilyCurin/Integral-ingresos-variables.git
   cd Integral-ingresos-variables
   ```
2. Haz doble clic en **`INICIAR_WINDOWS.bat`**. En su primer inicio prepara el entorno de Python e instala las bibliotecas necesarias. No cierres la consola mientras uses la app.
3. Abre **http://127.0.0.1:8765** si tu navegador no se abrió automáticamente.
4. Configura una contraseña de al menos 10 caracteres. Úsala para entrar las siguientes veces.
5. Abre **Importar**, registra un ingreso a mano o prueba el archivo `examples/ingresos_ejemplo.csv`. Confirma y clasifica los ingresos como *recurrente*, *variable* o *extraordinario*. Los registros *pendientes* no se cuentan como ingresos.

Para iniciar otra vez, usa el mismo `.bat`. Si la ventana se cierra por algún error, ábrela desde PowerShell para ver el mensaje. Si el puerto 8765 ya está ocupado, cierra la sesión anterior.

**Mac/Linux:** ejecuta `bash INICIAR_MAC_LINUX.sh` y abre http://127.0.0.1:8765. En Linux puede ser necesario instalar `python3-venv` con el gestor de paquetes del sistema.

## 3. Leer imágenes y estados de cuenta

**CSV y Excel** son los formatos más confiables para el prototipo. La primera fila debe incluir **Fecha** y **Monto** (también reconoce variantes en inglés y español), opcionalmente **Descripción** y **Fuente**. Las fechas recomendadas son `2026-09-05` o `05/09/2026`; los montos deben ser positivos para ingresos y negativos para gastos. Si un CSV tiene un separador diferente de coma, conviértelo a CSV con comas desde Excel antes de importarlo.

**PDF con texto seleccionable, fotografías y capturas:** la extracción de una transferencia o estado de cuenta puede ser imperfecta, porque los bancos usan diseños distintos y una fila puede contener saldo, débito y crédito. El importador conservador solo propone líneas con fecha y un monto reconocible; omite las ambiguas. **Comprueba los importes, los signos y las fechas en la vista previa**. Si no reconoce un archivo, registra esos movimientos manualmente o convierte el estado de cuenta a CSV.

Para OCR en Windows, instala **Tesseract OCR**, comprueba que esté en PATH (o configura `TESSERACT_CMD` en el sistema, por ejemplo `C:\Program Files\Tesseract-OCR\tesseract.exe`). El programa intenta usar español e inglés, y recurre a inglés cuando falta el paquete de español. **No se incluye Tesseract dentro del ZIP**. Sin él, CSV, Excel, PDF con texto y registro manual siguen funcionando.

## 4. Cómo funcionan las predicciones

Se cuentan como ingresos las categorías **recurrente**, **variable** y **extraordinario**. Transferencias propias, préstamos, reembolsos, gastos, excluidos y pendientes no suman.

- **Ingreso total:** suma de las entradas clasificadas como ingresos en el periodo consultado.
- **Promedio observado:** ingreso total dividido entre los meses que tienen ingresos registrados.
- **Esperado próximo mes:** mediana de los ingresos mensuales *no extraordinarios* en los meses con movimientos.
- **Conservador y optimista:** esperado menos/más una desviación estándar histórica de esos mismos ingresos, con mínimo cero.
- **Ahorro orientativo:** si ingresas un presupuesto mensual, se sugiere guardar el 50% del excedente entre el escenario conservador y ese presupuesto, si es positivo.

**Limitaciones importantes:** no se imputan meses vacíos; un historial parcial puede sesgar los cálculos. Estos escenarios son heurísticos, no un pronóstico validado estadísticamente ni una garantía. El dinero de una venta excepcional cuenta en el total histórico, pero **no en la mediana de ingreso habitual** cuando se clasifica como extraordinario. Las **notas por sí solas no modifican automáticamente cifras**: la persona confirma las categorías en el libro de ingresos.

## 5. IA con Ollama (opcional)

La app está diseñada para trabajar incluso sin Ollama; así puedes registrar, importar, consultar y estimar ingresos sin IA. La pestaña **Notas e IA** permite enviar una nota y hasta 40 descripciones/montos de movimientos al **servidor Ollama configurado** para recibir sugerencias. **Estas sugerencias no alteran ningún registro automáticamente.**

Si ya tienes Ollama instalado, en una terminal independiente:

```powershell
ollama pull gemma3:4b
ollama serve
```

Si `ollama serve` indica que el puerto está ocupado, probablemente Ollama ya esté ejecutándose: no necesitas abrir otro servidor. Modelo y dirección por defecto: `gemma3:4b` y `http://127.0.0.1:11434`. Para cambiarlos puedes definir las variables `OLLAMA_MODEL` y `OLLAMA_URL` **antes de iniciar** la aplicación. El uso de otro modelo compatible puede requerir descargarlo primero. La aplicación **no llama a servicios de IA en la nube** y no requiere claves de API ni tarjeta de crédito.

## 6. Seguridad, privacidad y base de datos

- **SQLite local**: los datos se almacenan en `data/vault.db`. No hace falta Firebase ni crear cuentas externas.
- **Contraseña**: el sistema almacena su verificador con `scrypt`; la contraseña no se guarda en texto claro. Los documentos originales guardados y los campos sensibles de movimientos y notas se cifran con Fernet utilizando una clave derivada de la contraseña. Fechas, categorías, metadatos y nombres de archivos **no están cifrados**.
- **Acceso**: la aplicación escucha exclusivamente en `127.0.0.1` (tu propia computadora). La sesión usa una cookie opaca y la clave descifrada solo permanece en memoria del proceso mientras la sesión está activa. La sesión expira después de 8 horas y se pierde al cerrar el servidor.
- **Respaldo**: guarda una copia privada de `data/` en un lugar seguro y conserva tu contraseña. No hay función de recuperación de contraseña. La pérdida de la clave impide leer lo cifrado.
- **GitHub**: `.gitignore` excluye `data/`, bases de datos, entornos virtuales y `.env`. **Nunca subas estados de cuenta reales ni la carpeta `data/`** a un repositorio público.
- **Advertencias**: es un prototipo local **monousuario**, no una plataforma multiusuario ni una auditoría formal de seguridad. No publiques el servidor en Internet, no cambies el bind de `127.0.0.1` a `0.0.0.0` y evita equipos compartidos sin protección del sistema operativo. Las exportaciones CSV descargadas quedan fuera del cifrado y deben guardarse de forma segura.

## 7. Estructura y desarrollo

```text
Integral-ingresos-variables/
├── INICIAR_WINDOWS.bat            # Arranque con doble clic
├── INICIAR_MAC_LINUX.sh
├── requirements.txt
├── app/
│   ├── main.py                    # API e inicio web
│   ├── importer.py                # CSV, Excel, PDF, OCR
│   ├── storage.py                 # SQLite + cifrado
│   ├── core.py                    # Cálculos y predicción
│   └── ai.py                      # Ollama opcional
├── static/                        # Frontend HTML, CSS, JS
├── examples/                      # Ejemplo ficticio
├── tests/                         # Pruebas automatizadas
└── data/                          # Bóveda local (no subir)
```

**Para ejecutar pruebas** (con el entorno instalado):

```powershell
.venv\Scripts\python.exe -m pytest -q
```

**Para iniciar desde la terminal**, alternativamente:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765
```

La arquitectura separa **cálculos determinísticos** (Python) de **interpretación textual opcional** (Ollama). Esto no exige dos modelos ni una arquitectura Split Brain. Las sugerencias del modelo nunca son la fuente oficial de los totales.

## 8. Prueba guiada en tres minutos

1. Ejecuta `INICIAR_WINDOWS.bat`, crea la contraseña y entra a **Importar**.
2. Carga `examples/ingresos_ejemplo.csv`, revisa las filas y cambia su categoría de `pendiente` a `recurrente` o `extraordinario` según corresponda; confirma.
3. En **Resumen**, selecciona **Todo el historial**. Verás totales, gráfico, fuentes y escenarios. En **Libro de ingresos** podrás corregir los registros.
4. Agrega una nota como «El proyecto de septiembre no se repetirá». Si tienes Ollama activo, consúltale qué movimientos conviene revisar. Cambia manualmente su clasificación si corresponde.
5. Ingresa un presupuesto para ver una referencia de ahorro. Exporta un CSV si quieres conservar una copia.

### Posibles mejoras futuras

Reconocimiento especializado para formatos de bancos, revisión de duplicados con identificadores de operación, gestión de monedas y tipos de cambio, análisis de meses sin movimientos, reglas recurrentes por cliente y un pronóstico respaldado por más historia. Estas mejoras **no son necesarias para ejecutar esta versión**.

---

**Stack:** Python + FastAPI + SQLite + Fernet + HTML/CSS/JavaScript, PyMuPDF, OpenPyXL, Tesseract (OCR externo) y Ollama opcional. Software local; no se realizan compras ni suscripciones.

### Importación flexible (actualización)

El importador intenta identificar las columnas por su contenido, incluso cuando la hoja incluye títulos o filas preliminares, y admite formatos con columnas separadas de **crédito y débito**. En PDF bancarios digitales reconoce ciertas tablas usando la posición de sus columnas (no se limita a buscar una fecha y un monto por línea). Las descripciones de clases, tutorías e inscripciones se sugieren como posibles ingresos; los depósitos sin origen verificable y las transferencias de cuentas no identificadas permanecen **pendientes**. Puedes corregir la categoría de cada propuesta antes de guardarla.

**Importante:** no se garantiza la lectura universal de cualquier estado de cuenta, escritura manual o diseño de Excel. Los PDF escaneados y las imágenes requieren OCR; la extracción puede equivocarse y siempre debe revisarse. Un crédito bancario no equivale automáticamente a un ingreso real. No se utilizan documentos personales reales como fixtures en este repositorio.

Para probar el lector flexible ejecuta `python -m pytest -q`. Se incluye un estado de cuenta **sintético** de ejemplo en `tests/fixtures/`.
