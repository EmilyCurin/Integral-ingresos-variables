# Integral · Ingresos Variables
## Informe de avances y mejoras solicitadas

**Fecha:** 27 de octubre de 2026  
**Alcance:** mejoras de experiencia de usuario, clasificación financiera y planificación personal.

### Objetivo de los cambios

Se solicitó que Integral dejara de ser únicamente una herramienta para extraer movimientos de un estado de cuenta y ofreciera una experiencia más completa: interpretar los registros con ayuda de IA y de las observaciones de la persona, facilitar la revisión de las transacciones y construir un plan de gastos y ahorro a partir de los datos analizados.

### Cambios solicitados e implementados

**1. Colores diferenciados en la clasificación de transacciones.**  
Se modificaron los selectores de categoría para que sea más fácil reconocer visualmente cada tipo de movimiento, tanto en la revisión de importación como en el libro de ingresos. Las categorías utilizan colores distintos: **gastos (amarillo)**, **préstamos/deudas (rojo)**, **ingresos recurrentes (verde)**, **ingresos variables (azul)**, **extraordinarios (morado)**, **transferencias propias (gris azulado)**, **reembolsos (turquesa)** y **pendientes (naranja claro)**. Esto ayuda a identificar errores antes de aceptar la clasificación propuesta.

**2. Dictado de observaciones mediante voz.**  
Se añadió un botón para **dictar notas personales** al momento de subir un documento. El texto reconocido se incorpora al mismo campo donde se pueden escribir aclaraciones: pagos extraordinarios, transferencias entre cuentas propias, gastos puntuales o clientes recurrentes. También hay dictado disponible para las consultas de la sección de IA. La función utiliza el reconocimiento de voz del navegador, por lo que depende de su compatibilidad y del permiso de micrófono; no equivale a un sistema de transcripción propio del backend.

**3. Notas integradas directamente en la importación.**  
El documento y las observaciones se procesan en un mismo flujo. La persona puede subir un PDF, imagen, Excel, CSV o TXT, escribir o dictar sus generalidades, permitir el uso de IA en la nube y recibir **categorías sugeridas en la tabla de revisión previa**. Es posible corregirlas o volver a clasificar antes de confirmar la importación. Se conserva una alternativa de reglas locales si la IA no está disponible.

**4. Eliminación de «Texto reconocido (muestra)».**  
Se quitó esa sección de la interfaz porque mostraba extractos parciales del PDF sin ayudar directamente a decidir qué era ingreso o gasto. El flujo se centra ahora en la **tabla de movimientos detectados, sus categorías y la confirmación**.

**5. Menos movimientos «sin determinar».**  
Se ajustó el criterio de clasificación para evitar que demasiadas transacciones queden pendientes: los **débitos** se proponen como *gastos*; los **créditos pequeños de origen no identificado** pueden proponerse como *ingresos variables*, con confianza baja y sujetos a revisión. Los movimientos que podrían ser transferencias propias necesitan evidencia adicional. **Los créditos de Q2,000 o más cuyo origen no esté claro permanecen pendientes para una comprobación puntual**: un monto alto no demuestra por sí solo que sea un ingreso fijo. Esto hace más útil el análisis sin inventar ingresos recurrentes.

**6. Preguntas breves sobre los principales gastos.**  
Se incorporó un cuestionario basado en **hasta tres categorías con mayor gasto identificado**. Para cada una, Integral pregunta si el gasto fue necesario, podría reducirse o fue excepcional. Por ejemplo, si destaca la comida fuera de casa o el entretenimiento, la persona puede explicar si esos gastos responden a una necesidad o si existe margen para reducirlos. La intención es evitar cuestionarios extensos y centrarse en los rubros de mayor impacto.

**7. Plan orientativo de ahorro y gasto.**  
A partir de los ingresos clasificados, gastos detectados, respuestas al cuestionario y **gastos fijos mensuales opcionales**, se agregó un cálculo que muestra **ingreso habitual aproximado, meta de ahorro, presupuesto máximo de gasto y gasto promedio observado**. El objetivo es recomendar cuánto reservar y cuánto puede gastarse, considerando si ciertos rubros son reducibles. Este cálculo es orientativo y puede requerir ajustes si existen deudas u obligaciones que no figuran en los documentos.

**8. Resultados organizados en tres pestañas.**  
Se añadieron las secciones **Gastos**, **Ingresos** y **Plan**:

- **Gastos:** muestra una agrupación aproximada por tipo de consumo, según las descripciones bancarias.
- **Ingresos:** reúne los importes clasificados y confirmados como recurrentes, variables o extraordinarios.
- **Plan:** presenta las preguntas personalizadas y el cálculo de ahorro y gasto recomendado.

Esta estructura facilita pasar del análisis del documento a conclusiones útiles, sin revisar toda la información en una sola pantalla.

**9. Exportación del libro de ingresos.**  
Se identificó y mantuvo una opción para **exportar el libro a CSV**. Aunque los datos del almacenamiento se protejan mediante cifrado, el archivo exportado se entrega **en formato legible** para poder consultarlo o trabajarlo fuera de Integral. Por ello, se recomienda guardarlo en un lugar privado y no compartirlo accidentalmente. Esta es una función disponible, más que una mejora creada específicamente en esta última ronda.

### Funcionamiento local y acceso

La instalación descargable se ejecuta iniciando **`INICIAR_WINDOWS.bat`**, que pone en marcha el servidor local. Después, la persona debe abrir **`http://localhost:8765`** en su navegador. El archivo de inicio y la dirección local cumplen funciones distintas: el primero ejecuta la aplicación y la segunda permite utilizar su interfaz.

Durante las pruebas, el inicio de sesión con Firebase funcionó desde `localhost` después de configurar las credenciales administrativas. `localhost` y `127.0.0.1` pueden recibir un trato distinto en la autenticación por dominio. **Esto no significa que cualquier persona pueda entrar desde Internet:** la instalación local solo funciona mientras el servidor esté ejecutándose en esa computadora. La publicación en Vercel requiere, por separado, configurar el dominio autorizado, el backend, las credenciales privadas y el almacenamiento persistente.

### Resultado general

Los cambios solicitados quedaron **incorporados al código de la versión actualizada de Integral**: interfaz de categorías con colores, notas por voz, clasificación contextual, eliminación del texto de muestra, reducción de categorías pendientes, preguntas sobre los tres gastos más importantes, recomendaciones de ahorro y gasto y pestañas de resultados.

La versión entregada reportó **21 pruebas automatizadas superadas**. Aun así, es importante distinguir entre funcionalidades implementadas y comprobación completa en condiciones reales: el reconocimiento de voz depende del navegador, la clasificación de IA requiere una configuración válida de Gemini y el despliegue público debe probarse de forma independiente. Las recomendaciones financieras y la agrupación de gastos siguen siendo estimaciones sujetas a revisión.

**Conclusión:** Integral avanzó de la lectura básica de estados de cuenta hacia un proceso de **documento → notas → clasificación → revisión → análisis de gastos e ingresos → plan personal**, con menos trabajo manual para quien lo utiliza.
