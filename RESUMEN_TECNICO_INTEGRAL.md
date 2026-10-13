# Integral — Resumen técnico rápido

**Proyecto:** aplicación web local para analizar documentos financieros y estimar ingresos variables.  
**Estado:** prototipo funcional con importación, revisión, libro de ingresos y predicciones; la automatización mediante IA todavía necesita ajustes.

## 1. ¿Qué se logró?

- Se creó un **frontend web** con secciones de resumen, importación, libro de ingresos y notas con IA.
- Se implementó la lectura de **PDF, Excel, CSV, TXT e imágenes** (estas últimas requieren Tesseract OCR).
- Se añadió un importador más flexible: busca fechas, importes y columnas como **débito/crédito**, aunque no se llamen exactamente «Fecha» y «Monto».
- Se incorporó una **base de datos SQLite local** con contraseña y cifrado de registros/documentos sensibles.
- Se agregaron categorías para separar ingresos recurrentes, variables, extraordinarios, préstamos, reembolsos, transferencias propias, gastos y pendientes.
- Se programaron análisis por periodo, promedios y **estimaciones conservadora, esperada y optimista**; también una sugerencia básica de ahorro si se registra un presupuesto.
- Se añadieron pruebas automatizadas y archivos para iniciar la aplicación desde Windows.

**Prueba de extracción:** con el estado de cuenta de septiembre se consiguió identificar movimientos y reconciliar los totales de **Q18,127.50 en créditos** y **Q24,457.83 en débitos**. Esto no significa que todos los créditos sean ingresos reales.

## 2. ¿Cómo está construido?

| Archivo o recurso | Función |
|---|---|
| `app/main.py` | API y conexión entre frontend, archivos, base de datos y análisis. |
| `app/importer.py` | Lectura y extracción de movimientos de documentos. |
| `app/classifier.py` | Reglas de clasificación e intento de clasificación mediante Ollama. |
| `app/ai.py` | Comunicación con Ollama para interpretar notas y generar texto. |
| `app/core.py` | Cálculos y predicciones, sin depender de IA. |
| `app/storage.py` | Base de datos, acceso y cifrado. |
| `static/index.html`, `app.js`, `style.css` | Pantallas, interacción del usuario y apariencia. |
| `tests/` | Pruebas automáticas. |
| `INICIAR_WINDOWS.bat` | Inicia la aplicación desde Windows. |

## 3. Librerías y herramientas de Python

| Librería o recurso | ¿Para qué sirve? |
|---|---|
| **FastAPI** | Construye el backend y las rutas de la aplicación. |
| **Uvicorn** | Ejecuta el servidor web local. |
| **python-multipart** | Recibe archivos subidos desde el navegador. |
| **PyMuPDF** | Extrae texto y datos de archivos PDF. |
| **openpyxl** | Lee hojas de cálculo Excel (`.xlsx`). |
| **Pillow + pytesseract** | Prepara imágenes y utiliza Tesseract para reconocer texto (OCR); Tesseract se instala aparte. |
| **requests** | Envía solicitudes HTTP a Ollama. |
| **sqlite3** (incluido con Python) | Guarda registros en una base de datos local. |
| **cryptography** | Cifra información sensible con Fernet. |
| **itsdangerous** | Dependencia declarada para funcionalidades de seguridad; el acceso principal del proyecto usa otras rutinas. |
| **statistics, decimal, datetime, csv, re** (Python estándar) | Estadísticas, montos exactos, fechas, lectura CSV y búsqueda de patrones. |
| **pytest + httpx** | Pruebas del código y de la API. |

## 4. ¿Dónde se utiliza inteligencia artificial?

**Ollama (local, opcional):**

1. Lee notas como «este depósito fue extraordinario».
2. Propone categorías para los movimientos encontrados.
3. Genera interpretaciones escritas para ayudar a comprender los registros.

**Lo que NO hace la IA:** las sumas, promedios y proyecciones matemáticas son realizados por `app/core.py` con reglas de Python. Las predicciones son **estimaciones estadísticas sencillas**, no un modelo de IA entrenado con datos financieros.

## 5. Limitación pendiente: clasificación automática

**Problema observado:** Ollama ofrece sugerencias útiles, pero en tu uso **no está actualizando correctamente las categorías de la tabla**. En el código de la última versión existe una ruta de clasificación por lotes que intenta aplicar propuestas a la vista previa, pero **no se ha confirmado que ese flujo funcione de principio a fin en tu equipo**.

**Objetivo pendiente:** subir un PDF, escribir generalidades una sola vez, dejar que Integral clasifique los movimientos en la tabla y **aprobar todo o corregir solo excepciones**, sin copiar recomendaciones una por una.

También queda por mejorar el reconocimiento de formatos bancarios variados y evitar que una descripción ambigua se trate como prueba de que una transferencia es un ingreso o un movimiento propio.

## 6. Próximo paso prioritario

**Conectar y verificar la clasificación de Ollama con la tabla de importación**, mostrando categoría, nivel de confianza y justificación por movimiento. Solo después de la aprobación del usuario se guardarán los cambios en el libro de ingresos.

**En una frase:** Integral ya puede **leer, organizar, almacenar y estimar**; su principal mejora pendiente es pasar de una IA que **explica y propone** a una IA que **preclasifica automáticamente para revisión**.
