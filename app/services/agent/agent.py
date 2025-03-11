import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from typing import Annotated, Optional
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from enum import Enum


# from langgraph.checkpoint.postgres import PostgresSaver
# from psycopg_pool import ConnectionPool

class TipoOperacion(str, Enum):
    COMPRA = "Compra"
    ALQUILER = "Alquiler"
    ALQUILER_TEMPORAL = "Alquiler Temporal"

class TipoPropiedad(str, Enum):
    TERRENO = "Terreno"
    CASA = "Casa"
    DEPARTAMENTO = "Departamento"
    QUITNA = "Quinta"
    LOCAL = "Local"
    OFICINA = "Oficina"
    COCHERA = "Cochera"
    PH = "PH"
    FONDO_COMERCIO = "Fondo de Comercio"


class InteresCliente(BaseModel):
    nombre: str = Field(description="Nombre del cliente")
    mail: str = Field(description="Mail del cliente")
    tipo_propiedad: Optional[str] = Field(description="Tipo de porpiedad", default=None)
    tipo_operacion: Optional[TipoOperacion] = Field(description="Tipo de operacion de interes del cliente", default=None)
    zona: Optional[str] = Field(description="Zona, direccion, calle", default=None)
    disponibilidad_horaria: Optional[str] = Field(description="Horario en el que el cliente esta disponible para ser contactado", default=None)

class RespuestaAgente(BaseModel):
    respuesta_principal: str = Field(description="Mensaje que sera enviado al cliente, no incluir el numero de telefono en este mensaje (sera enviado como un link separado)")
    nombre_agente: Optional[str] = Field(description="Nombre del encargado de la propiedad", default=None)
    numero_agente: Optional[str] = Field(description="numero_agente para hablar con el encargado de la propiedad", default=None)

class State(TypedDict):
    user_id: Optional[str] = None
    name: Optional[str] = None
    messages: Annotated[list, add_messages]
    respuesta: Optional[RespuestaAgente] = None


@tool
def derivar_con_agente_encargado(nombre_propiedad: str):
    """
    Derivar a un agente de ventas encargado de la propiedad. Esta herramienta se utiliza para conectar al cliente con el agente encargado de UNA propiedad en específico.
    nombre_propiedad: nombre o direcion de la propiedad de interes.
    """

    # Llamar a la API de la inmobiliaria para obtener el agente encargado de la propiedad

    return {
        "nombre_agente": "Rogelio Bianchi",
        "numero_agente": "5493412594114",
    }


@tool
def generar_contacto_cliente(info: InteresCliente):
    """
    Guardar el contacto del cliente para ser contactado por un agente de ventas a la brevedad.

    nombre: Nombre del cliente
    mail: Mail del cliente
    tipo_propiedad: Tipo de propiedad (CASA, DEPARTAMENTO, LOCAL, OFICINA, COCHERA, PH, FONDO_COMERCIO)
    tipo_operacion: Tipo de operacion de interes del cliente (COMPRA, ALQUILER, ALQUILER_TEMPORAL)
    zona: Zona, direccion o calle
    disponibilidad_horaria: Horario en el que el cliente esta disponible para ser contactado
    """ 

    # Guardar contacto del cliente

    return "Se ha generado el contacto del cliente correctamente. En la brevedad un agente se contactara con el cliente."


TOOLS = [generar_contacto_cliente, derivar_con_agente_encargado]
MODEL = ChatOpenAI(model="gpt-4o-mini")
checkpointer = MemorySaver()
PROMPT = "" \
"""
Contexto:
Eres un asistente inmobiliario que ayuda a los clientes a obtener información o a conectarse con el agente encargado de una propiedad en específico. Dependiendo de la información que te proporcione el cliente, deberás:

Si el cliente menciona una propiedad puntual y concreta:
Utiliza la herramienta derivar_con_agente_encargado pasando el nombre o direccion de la propiedad para conectarlo directamente con el agente responsable.

Si el cliente desea recibir información o dejar sus datos para que se lo contacten:
Recaba el nombre, una descripción del interés en alguna propiedad (puede ser general o con algunos detalles) y otros comentarios adicionales, y utiliza la herramienta generar_lead_cliente para crear un lead que permita que un agente se ponga en contacto lo antes posible.

Ejemplo de interacción:

Cliente: “Queria saber mas informacion sobre el departamento de <calle><altura>.”
Agente: (Se llama a derivar_con_agente_encargado con la descripción proporcionada.)

Cliente: “Quisiera recibir más información sobre de departamentos a la venta en zona centro.”
Agente: “Perfecto, por favor indícame tu nombre, detalles de lo que buscas y cualquier comentario adicional.”
(Se llama a generar_contacto_cliente con los datos del cliente.)
Agente: "En la brevedad se comuinicara un agente. Si te interesa puedes visitar nuestra pagina para ver nuestras opciones proyectou.com.ar"

"""


def create_agent():


    def call_model(state: State):
        # Create the prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", PROMPT),
            ("placeholder", "{messages}")
        ])
        
        # Prepare the messages from the state
        messages = state["messages"]

        # Format the prompt with the messages
        formatted_prompt = prompt_template.invoke({"messages": messages})
        
        structured_response = structured_model.invoke(formatted_prompt)
            
        bound_response = bound_model.invoke(formatted_prompt)

        return {"messages": bound_response, "respuesta": structured_response}



    #  ==== Conditional Edges ====
    def should_continue(state: State):
        """Return the next node to execute."""

        last_message = state["messages"][-1]

        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return END
        
        # Otherwise if there is, we continue
        return "action"
    

    # ==== Compile Workflow ====
    tools = TOOLS
    tool_node = ToolNode(tools)
    model = MODEL
    bound_model = model.bind_tools(tools)
    structured_model = bound_model.with_structured_output(RespuestaAgente)
    workflow = StateGraph(State)


    # Define Nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("action", tool_node)

    # Define Edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(     # Conditional Edge
        "agent",                            # Desde este nodo
        should_continue,                    # Nodo controlador
        ["action", END],                    # Posibles nodos a continuar
    )
    workflow.add_edge("action", "agent")
    workflow.add_edge("agent", END)    

    return workflow.compile(checkpointer=checkpointer)




# config = {"configurable": {"thread_id": 2, "recursion_limit": 10}}


# def chat_loop(app):    
#     # ==== Chat Loop ====
#     try:
#         while True:
#             try:
#                 user_input = input("\nHuman: ")
                
#                 if user_input.lower() in ['salir', 'exit', 'q']:
#                     print("Saliendo del chat...")
#                     break
                
#                 # Validar entrada
#                 if not user_input.strip():
#                     print("Por favor, escribe un mensaje.")
#                     continue

#                 initial_state = {
#                     'user_id': None,
#                     'name': None,
#                     'phone_number': None,
#                     "messages": [HumanMessage(content=user_input)]
#                 }

#                 events = app.stream(
#                     {"messages": [HumanMessage(content=user_input)]},
#                     # initial_state,
#                     config,
#                     stream_mode="values",
#                 )

#                 # Procesar eventos
#                 for event in events:
#                     # Print the standard response message
#                     event["messages"][-1].pretty_print()

#             except Exception as e:
#                 print(f"Error en la conversación: {e}")
#                 continue

#     except KeyboardInterrupt:
#         print("\nChat interrumpido por el usuario.")



# app = create_agent()

# # chat_loop(app)

# user_input = "Quiero saber sobre la propiedad de caferata 366"
# result = app.invoke({"messages": [HumanMessage(content=user_input)]},
#                     # initial_state,
#                     config,
#                     stream_mode="values",)
# # print(result)
# print(f"Mensaje: {result["respuesta"].respuesta_principal}")
# print(f"Nombre Agente: {result["respuesta"].nombre_agente}")
# print(f"numero_agente: {result["respuesta"].numero_agente}")
