import os
import uuid
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

# Se la tua versione di LangGraph non ha 'langgraph.node',
# non importare da lì. Prova con 'langgraph.core.node',
# o definisci da solo una classe Node minima (come qui sotto).

try:
    from langgraph.core.node import Node
except ImportError:
    # Se non esiste, definiamo una classe Node minima:
    class Node:
        def __init__(self, name="CustomNode"):
            self.name = name

        def run(self, state: dict) -> dict:
            """Metodo da sovrascrivere nei nodi custom."""
            return state

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

import spotipy
from spotipy.oauth2 import SpotifyOAuth

##############################################
# LOG INIZIALE
##############################################
print("DEBUG: CURRENT DIRECTORY:", os.getcwd())
print("DEBUG: SPOTIFY_CLIENT_ID =", os.getenv("SPOTIFY_CLIENT_ID"))
print("DEBUG: SPOTIFY_CLIENT_SECRET =", os.getenv("SPOTIFY_CLIENT_SECRET"))
print("DEBUG: SPOTIFY_REDIRECT_URI =", os.getenv("SPOTIFY_REDIRECT_URI"))

##############################################
# TOOL 1: get_structured_time
##############################################
@tool
def get_structured_time(query: str = "") -> dict:
    """
    Ritorna l'orario locale in formato dict: {hour, minute, second}.
    Argomento opzionale: 'query' (string) non usato.
    """
    import datetime
    now = datetime.datetime.now()
    return {
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second
    }

##############################################
# TOOL 2: list_spotify_devices
##############################################
@tool
def list_spotify_devices(query: Optional[str] = None) -> list:
    """
    Recupera i dispositivi Spotify come una lista di dict [{name, id, type}].
    Argomento opzionale: 'query' (string) non usato.
    """
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    cache_file = ".cache-langgraph"
    print("DEBUG: list_spotify_devices using cache_file ->", os.path.abspath(cache_file))

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-modify-playback-state user-read-playback-state",
        cache_path=cache_file
    )
    try:
        import spotipy
        sp = spotipy.Spotify(auth_manager=auth_manager)
        devices_info = sp.devices()["devices"]
        print(f"DEBUG: Trovati {len(devices_info)} dispositivi in list_spotify_devices:")
        for dev in devices_info:
            print("   -", dev)

        result = []
        for d in devices_info:
            result.append({
                "name": d["name"],
                "id": d["id"],
                "type": d["type"]
            })
        print("DEBUG: result ->", result)
        return result

    except Exception as e:
        print("DEBUG: Eccezione nel recupero device:", e)
        return []

##############################################
# TOOL 3: play_spotify_on_device
##############################################
@tool
def play_spotify_on_device(query: str) -> str:
    """
    Riproduce un brano su Spotify, dato:
    {
      "track_name": "...",
      "device_name": "..."
    }
    """
    import json

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    cache_file = ".cache-langgraph"
    print("DEBUG: play_spotify_on_device cache_file ->", os.path.abspath(cache_file))

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="user-modify-playback-state user-read-playback-state",
        cache_path=cache_file
    )

    try:
        import spotipy
        data = json.loads(query)
        track_name = data.get("track_name")
        device_name = data.get("device_name")
        if not track_name or not device_name:
            return "Devi specificare sia track_name che device_name."

        sp = spotipy.Spotify(auth_manager=auth_manager)
        results = sp.search(q=track_name, type="track", limit=1)
        items = results["tracks"]["items"]
        if not items:
            return f"Nessuna traccia trovata per '{track_name}'"
        track_uri = items[0]["uri"]

        devices_info = sp.devices()["devices"]
        print("DEBUG: dispositivi in play_spotify_on_device:")
        for dev in devices_info:
            print("   -", dev)

        device_id = None
        for d in devices_info:
            if d["name"].lower() == device_name.lower():
                device_id = d["id"]
                break
        if not device_id:
            return f"Non trovo nessun device con nome '{device_name}'"

        sp.start_playback(device_id=device_id, uris=[track_uri])
        return f"Sto riproducendo '{track_name}' sul dispositivo '{device_name}'"

    except Exception as e:
        return f"Errore nella riproduzione: {e}"

##############################################
# Montiamo i tool
##############################################
tools = [get_structured_time, list_spotify_devices, play_spotify_on_device]
llm = ChatOpenAI(
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
).bind_tools(tools)

system_msg = SystemMessage(content=(
    "Se list_spotify_devices ritorna dispositivi, converti i dati in un messaggio. "
    "Se è vuota, di' 'Non ci sono dispositivi'. "
    "Non ignorare i dati del tool."
))

##############################################
# ToolNode classico
##############################################
tool_node = ToolNode(tools)

##############################################
# NODO CUSTOM: Intercettazione di list_spotify_devices
##############################################
class ListDevicesNode(Node):
    """Nodo custom che intercetta l'output di list_spotify_devices e lo trasforma in un AIMessage."""
    def __init__(self, name="ListDevicesNode"):
        super().__init__(name)

    def run(self, state: dict) -> dict:
        """Intercetta l'ultimo ToolMessage di name='list_spotify_devices' e crea un AIMessage con i device."""
        from langchain_core.messages import AIMessage, ToolMessage

        new_msgs = []
        for msg in state["messages"]:
            if isinstance(msg, ToolMessage) and msg.name == "list_spotify_devices":
                # 'msg.content' è la stringa di repr(list_of_dict).
                import ast
                try:
                    devices_list = ast.literal_eval(msg.content)
                except:
                    devices_list = []

                if not devices_list:
                    text = "Non ci sono dispositivi Spotify disponibili."
                else:
                    lines = ["Ecco i dispositivi:"]
                    for d in devices_list:
                        lines.append(f"- {d['name']} ({d['type']}), ID: {d['id']}")
                    text = "\n".join(lines)

                new_msgs.append(AIMessage(content=text))
            else:
                new_msgs.append(msg)

        state["messages"] = new_msgs
        return state

##############################################
# NODO AGENTE: chiama il LLM
##############################################
class AgentNode(Node):
    """Nodo agente che chiama il modello LLM."""
    def __init__(self, llm: ChatOpenAI, system_msg: SystemMessage, name="AgentNode"):
        super().__init__(name)
        self.llm = llm
        self.system_msg = system_msg

    def run(self, state: dict) -> dict:
        messages = [self.system_msg] + state["messages"]
        response = self.llm.invoke(messages)
        print("DEBUG: tool_calls:", response.tool_calls)
        return {"messages": [response]}

agent_node = AgentNode(llm, system_msg)

##############################################
# Controllo tool_calls
##############################################
def check_tool_calls(state):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return END

##############################################
# MONTIAMO IL GRAFO
##############################################
workflow = StateGraph(MessagesState)  # Passiamo MessagesState come schema di stato
workflow.add_node("agent", agent_node.run)
workflow.add_node("tools", tool_node)
workflow.add_node("list_node", ListDevicesNode().run)

# Flusso:
# START -> agent
# agent -> (condizionale tool_calls) -> tools
# tools -> list_node (conversione ToolMessage -> AIMessage)
# list_node -> agent (per eventuali step successivi)
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", check_tool_calls, ["tools", END])
workflow.add_edge("tools", "list_node")
workflow.add_edge("list_node", "agent")

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

##############################################
# Test run (facoltativo)
##############################################
def test_run():
    """Esempio di test run per chiedere i dispositivi."""
    from langchain_core.messages import HumanMessage

    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}

    msg = HumanMessage(content="Quali dispositivi Spotify ho?")
    final_state = app.invoke({"messages": [msg]}, config=cfg)
    print("RISPOSTA:", final_state["messages"][-1].content)

if __name__ == "__main__":
    test_run()
