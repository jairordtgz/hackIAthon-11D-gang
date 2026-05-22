import os
import json
import time
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
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

# =================================================================
# NUEVO: VARIABLE GLOBAL PARA EL DASHBOARD
# =================================================================
historial_decisiones = []

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
    
    Responde ÚNICAMENTE en formato JSON estricto.
    Para el campo "estado", debes usar EXACTAMENTE una de estas tres opciones, respetando mayúsculas: "Aprobado", "Rechazado" o "Pendiente".
    
    Estructura esperada:
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
    global historial_decisiones
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
                    
                    # --- NUEVO: GUARDAR EN EL HISTORIAL PARA EL DASHBOARD ---
                    hora_actual = datetime.now().strftime("%H:%M:%S")
                    registro = f"[{hora_actual}] <b>{nombre}</b> -> {ia_decision['estado']} <i>({ia_decision['justificacion']})</i>"
                    historial_decisiones.insert(0, registro) # Agregar al inicio de la lista
                    
                    # Evitar que la memoria se llene, guardamos solo los últimos 20
                    if len(historial_decisiones) > 20:
                        historial_decisiones.pop()
                    
            time.sleep(5) 
            
        except Exception as e:
            print(f"\n❌ Error en el ciclo: {e}")
            time.sleep(5)

# =================================================================
# --- DASHBOARD WEB PARA RENDER ---
# =================================================================
class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html; charset=utf-8')
        self.end_headers()
        
        # Plantilla HTML con CSS inyectado
        html_content = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Dashboard - Agente Médico IA</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; background-color: #f0f2f5; color: #333; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
                h1 { color: #1a365d; border-bottom: 2px solid #edf2f7; padding-bottom: 10px; }
                .status-badge { display: inline-block; padding: 5px 10px; border-radius: 15px; font-size: 0.85em; font-weight: bold; }
                .Aprobado { background-color: #c6f6d5; color: #22543d; }
                .Rechazado { background-color: #fed7d7; color: #822727; }
                ul { list-style-type: none; padding: 0; }
                li { background: #f8fafc; margin-bottom: 12px; padding: 15px; border-radius: 6px; border-left: 4px solid #cbd5e0; }
                .timestamp { color: #718096; font-size: 0.9em; margin-right: 10px; }
            </style>
            <meta http-equiv="refresh" content="10">
        </head>
        <body>
            <div class="container">
                <h1>🏥 Monitor del Agente Médico (Tiempo Real)</h1>
                <p>🟢 El sistema está activo y sincronizado con Notion. Actualización automática cada 10s.</p>
                
                <h2>Últimas Auditorías:</h2>
                <ul>
        """
        
        global historial_decisiones
        if not historial_decisiones:
            html_content += "<li>⏳ Esperando nuevas solicitudes... (Modifica un estado a 'Pendiente' en Notion)</li>"
        else:
            for item in historial_decisiones:
                # Darle color dinámico según la respuesta de la IA
                if "Aprobado" in item:
                    item = item.replace("Aprobado", "<span class='status-badge Aprobado'>APROBADO</span>")
                elif "Rechazado" in item:
                    item = item.replace("Rechazado", "<span class='status-badge Rechazado'>RECHAZADO</span>")
                
                html_content += f"<li>{item}</li>"

        html_content += """
                </ul>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html_content.encode('utf-8'))

def run_dashboard_server():
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    server.serve_forever()

if __name__ == "__main__":
    # Arrancar el dashboard web en un hilo secundario
    server_thread = threading.Thread(target=run_dashboard_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Arrancar tu agente principal
    main()