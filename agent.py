import os
import json
import time
from dotenv import load_dotenv
from notion_client import Client

from google import genai
from google.genai import types

# 1. Cargar variables de entorno
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([NOTION_TOKEN, DATABASE_ID, GEMINI_API_KEY]):
    print("❌ ERROR: Faltan variables de entorno en el .env")
    exit()

# 2. Configurar APIs
notion = Client(auth=NOTION_TOKEN)
ai_client = genai.Client()

def get_pending_requests():
    """Busca en Notion las solicitudes que están en estado 'Pendiente'."""
    try:
        query = notion.data_sources.query(
            data_source_id=DATABASE_ID,
            filter={
                "property": "Estado",
                "status": {
                    "equals": "Pendiente"
                }
            }
        )
        return query.get("results", [])
    except Exception as e:
        print(f"❌ Error leyendo la tabla: {e}")
        return []

def analyze_request(informe_medico, poliza):
    """Envía la información a la IA para determinar la pre-autorización."""
    prompt = f"""
    Eres un agente experto en pre-autorizaciones de seguros médicos. 
    Tu tarea es analizar el informe médico y compararlo con la póliza del paciente.
    
    INFORME MÉDICO:
    {informe_medico}
    
    PÓLIZA DEL PACIENTE:
    {poliza}
    
    Evalúa:
    1. ¿El procedimiento está cubierto?
    2. ¿Cumple con los requisitos de carencia?
    
    Responde ÚNICAMENTE en formato JSON estricto con la siguiente estructura:
    {{
        "estado": "Aprobado", 
        "justificacion": "Explicación breve de la decisión."
    }}
    """
    
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    return json.loads(response.text)

def update_notion_status(page_id, nuevo_estado, justificacion):
    """Actualiza la fila en Notion con la decisión de la IA."""
    notion.pages.update(
        page_id=page_id,
        properties={
            "Estado": {
                "status": {"name": nuevo_estado}
            },
            "Respuesta IA": {
                "rich_text": [{"text": {"content": justificacion}}]
            }
        }
    )

def main():
    print("🚀 Iniciando el Agente Médico...")
    print("Escuchando tu tabla en Notion (Presiona Ctrl+C para detener).\n")
    
    while True:
        try:
            pendientes = get_pending_requests()
            
            if not pendientes:
                print(".", end="", flush=True) 
            else:
                print("\n\n🔔 ¡Nueva solicitud detectada!")
                
                for page in pendientes:
                    page_id = page["id"]
                    
                    # AQUÍ ESTÁ EL ARREGLO: "Póliza del Paciente" tal cual está en tu Notion
                    informe_list = page["properties"].get("Informe Médico", {}).get("rich_text", [])
                    poliza_list = page["properties"].get("Póliza del Paciente", {}).get("rich_text", [])
                    nombre_list = page["properties"].get("ID Solicitud", {}).get("title", [])
                    
                    informe = "".join([t.get("plain_text", "") for t in informe_list])
                    poliza = "".join([t.get("plain_text", "") for t in poliza_list])
                    nombre = "".join([t.get("plain_text", "") for t in nombre_list]) or "Paciente X"
                    
                    if not informe or not poliza:
                        print(f"⚠️ Faltan datos médicos de {nombre}. Llena la celda en Notion. Saltando...")
                        continue
                    
                    print(f"⚙️ Analizando caso de: {nombre}...")
                    
                    ia_decision = analyze_request(informe, poliza)
                    
                    update_notion_status(page_id, ia_decision["estado"], ia_decision["justificacion"])
                    print(f"✅ Pre-autorización resuelta: {ia_decision['estado']}")
                    
            time.sleep(5) 
            
        except Exception as e:
            print(f"\n❌ Error en el ciclo: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
