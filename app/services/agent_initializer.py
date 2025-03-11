import requests
from langchain_core.messages import HumanMessage
from datetime import datetime

from app.services.agent.agent import create_agent

def agent_initializer(phone_number: str, user_input: str):


    app = create_agent()
        

    initial_state = {
        'phone_number': phone_number,
        "messages": [HumanMessage(content=user_input)]
    }

    fecha_actual = datetime.now().strftime('%Y%m%d')
    thread_id = f"{phone_number} | {fecha_actual}"
    config = {"configurable": {"thread_id": thread_id, "recursion_limit": 10}}


    print("\n ==================== Inicio Mensaje =================================================")
    print(f"\nUsuario: {user_input}\n")

    # Invocar el grafo
    response = app.invoke(initial_state, config)
    
    # Obtener el último mensaje (respuesta de IA)
    ia_response = response["messages"][-1].content
    respuesta = response['respuesta']
    respuesta_principal = respuesta.respuesta_principal
    nombre_agente = respuesta.nombre_agente
    numero_agente = respuesta.numero_agente


    print(f"\nAgente: {respuesta}")
    print("\n ==================== Fin mensaje ====================================================")

    return respuesta_principal, nombre_agente, numero_agente, ia_response