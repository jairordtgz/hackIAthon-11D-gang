# 🏥 Agente de Pre-Autorización Quirúrgica en Tiempo Real (IA)

## 📝 Descripción del Proyecto
Esta solución fue desarrollada para el **Reto 1 del HackIAthon de Viamática**. El objetivo principal es optimizar el proceso de auditoría médica para la aprobación de cirugías, reduciendo un trámite burocrático que tradicionalmente toma horas o días a un flujo automatizado de **menos de 10 segundos**.

El sistema actúa como un backend robusto en Python que conecta una base de datos operativa hospitalaria (**Notion**) con un motor de procesamiento de lenguaje natural avanzado (**Gemini 2.5 Flash**). El agente analiza críticamente los informes médicos frente a las condiciones y periodos de carencia de las pólizas de seguros, emitiendo un dictamen estructurado y auditable de forma instantánea.

---

## ✨ Características Principales
- **Monitoreo Reactivo (Polling Activo):** Escucha constante de la base de datos de Notion buscando nuevos registros en estado `Pendiente` mediante un ciclo de control optimizado.
- **Análisis Contextual de Cobertura y Carencia:** Evaluación cruzada automatizada de variables complejas (procedimientos solicitados vs. exclusiones de la póliza y tiempos de afiliación).
- **Garantía de Respuestas Estructuradas:** Uso de esquemas JSON estrictos a nivel de API para asegurar el determinismo en las respuestas de la IA, eliminando la ambigüedad del lenguaje libre.
- **Auditoría Transparente:** Generación automática de justificaciones médicas detalladas dentro de la plataforma Notion para facilitar revisiones humanas o auditorías posteriores.

---

## 📋 Guía de Replicación para Evaluadores (Jueces)
Dado que las bases de datos y credenciales son entornos privados, hemos preparado una plantilla exacta para que el jurado pueda probar el flujo completo en su propio entorno:

1. **Duplicar la Base de Datos:** Ingresa a [Nuestra Plantilla de Notion](https://eminent-caboc-ec6.notion.site/367704fd10938034ae9de4e2b8f66608?v=367704fd109380eebbbe000c4cc71941&source=copy_link) y haz clic en el botón **"Duplicar"** (esquina superior derecha) para copiar la estructura a tu espacio de trabajo.
2. **Crear la Integración de Notion:** Ve a [Notion Developers](https://www.notion.so/my-integrations) y crea una nueva integración interna para obtener el `Internal Integration Secret` (Tu Token).
3. **Conectar la Base de Datos:** En tu página de Notion recién duplicada, haz clic en los tres puntos `...` (arriba a la derecha), selecciona **"Añadir conexión"** y busca el nombre de la integración que acabas de crear.
4. **Extraer el ID de la Tabla:** Copia los **32 caracteres alfanuméricos** que se encuentran en la URL de tu base de datos duplicada (justo después del nombre de tu espacio y antes del `?v=`).

---

## 🚀 Instalación y Configuración Local

### Prerrequisitos
- Python 3.10 o superior.
- Credenciales de API (Notion y Google AI Studio).

### 1. Clonar el repositorio e instalar dependencias
```bash
git clone [https://github.com/jairordtgz/hackIAthon-11D-gang.git](https://github.com/jairordtgz/hackIAthon-11D-gang.git)
cd hackIAthon-11D-gang
python3 -m venv venv
source venv/bin/activate  # En Windows usa: venv\Scripts\activate
pip install -r requirements.txt

## env
NOTION_TOKEN=""
NOTION_DATABASE_ID=""
GEMINI_API_KEY=""