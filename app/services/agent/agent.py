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


# from langgraph.checkpoint.postgres import PostgresSaver
# from psycopg_pool import ConnectionPool

class RespuestaAgente(BaseModel):
    respuesta_principal: str = Field(description="Mensaje que sera enviado al cliente")
    nombre_agente: Optional[str] = Field(description="Nombre del encargado de la propiedad", default=None)
    numero_agente: Optional[str] = Field(description="numero_agente para hablar con el encargado de la propiedad", default=None)

class State(TypedDict):
    user_id: Optional[str] = None
    name: Optional[str] = None
    messages: Annotated[list, add_messages]
    respuesta: Optional[RespuestaAgente] = None


@tool
def derivar_con_agente(descripcion: str):
    """
    Derivar a un agente de ventas.
    Descripcion: Breve descripcion de la propiedad de interes.
    """

    nombre = "Rogelio Bianchi"
    numero_agente = "5493413918907"

    return f"Agente encargado de la propiedad: {nombre} Contacto: {numero_agente}\n"
    # return {
    #     "respuesta_principal": f"Agente encargado de la propiedad: {nombre} Contacto: {numero_agente}",
    #     "nombre_agente": nombre,
    #     "numero_agente": numero_agente,
    # }


TOOLS = [derivar_con_agente]
MODEL = ChatOpenAI(model="gpt-4o-mini")
checkpointer = MemorySaver()
PROMPT = "" \
"""
Eres un asiastente para una inmobiliaria. 
Te encargas de redireccionar a los clientes con los agentes de ventas relacionados a las propiedades.

Debes utilizar la herramienta 'derivar_con_agente' con una descripcion de la propiedad que busca el cliente.
Esta herramienta te devolver el numero_agente de wpp para contactar al agente de ventas. 

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

        return {"messages": bound_response , "respuesta": structured_response}



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
