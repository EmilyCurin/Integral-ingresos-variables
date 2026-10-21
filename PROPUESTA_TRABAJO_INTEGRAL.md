# Propuesta de trabajo — Integral · Ingresos Variables

**Emily Curin | Entregas: miércoles 21 y miércoles 28 de octubre de 2026**

## Primera entrega — 21 de octubre
**Clasificación con IA e interfaz más intuitiva**

- Permitir **subir el archivo y escribir notas en el mismo paso**, para que la IA utilice ese contexto al clasificar automáticamente los ingresos y gastos en la vista previa.
- Sustituir Ollama por una **API de IA en la nube**; mantener reglas locales si la API falla. Las clasificaciones deben reflejarse en la tabla antes de la aprobación.
- Corregir la lectura de PDF con fechas y saldos en formatos diferentes, evitando el descarte silencioso de movimientos.
- Simplificar el flujo: **documento + notas → clasificación → revisión mínima → confirmación**.
- Reclutar **tres personas con ingresos variables** y preparar un cuestionario breve para las pruebas de la segunda entrega.

**Entregable:** versión funcional mejorada, casos de prueba del importador y plan de validación con tres usuarios.

## Segunda entrega — 28 de octubre
**Publicación, pruebas y documentación**

- Preparar el despliegue web, preferentemente **Vercel para el frontend** y un servicio compatible para FastAPI, con almacenamiento persistente y autenticación segura si se procesarán datos personales.
- Sustituir el acceso con contraseña anterior por **Google/Firebase Authentication** en la versión pública, con datos separados por usuario. No exponer una base compartida sin autenticación.
- Ejecutar **tres pruebas end-to-end**: importar documentos, aplicar notas con IA y consultar resultados guardados.
- Completar **tres sesiones con usuarios reales** antes de la entrega; registrar hallazgos, resultados del cuestionario y correcciones prioritarias en `docs/feedback/`.
- Actualizar el README con instrucciones de construcción, diagramas fieles al código y URL de la aplicación; entregar un artículo técnico con aprendizajes.

**Entregable:** versión publicada o demo segura, tres pruebas E2E, evidencia de tres evaluaciones de usuarios, README con diagramas y artículo técnico.

> **Alcance:** el uso local sin contraseña es aceptable para desarrollo; el despliegue público con datos reales requiere autenticación y aislamiento por usuario antes de habilitar la carga y almacenamiento.
