import os
from datetime import datetime
from dotenv import load_dotenv

# Carica le variabili d'ambiente (.env)
load_dotenv()

# Nuovi import dai pacchetti aggiornati
from langchain_openai import ChatOpenAI
from langchain_community.agents import initialize_agent, AgentType, Tool
from langchain_community.utilities import SerpAPIWrapper
from langchain_community.memory import ConversationBufferMemory


def get_current_time() -> str:
    """Ritorna l'orario locale in formato HH:MM:SS."""
    return datetime.now().strftime("%H:%M:%S")

def create_agent():
    # Inizializza LLM
    llm = ChatOpenAI(
        temperature=0.5,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Tool per l'ora corrente
    time_tool = Tool(
        name="CurrentTime",
        func=get_current_time,
        description="Use this tool to get the current time."
    )

    # Tool per ricerche sul web (SerpAPI)
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    if not serpapi_key:
        raise ValueError("SERPAPI_API_KEY mancante nel file .env!")

    search = SerpAPIWrapper(serpapi_api_key=serpapi_key)

    search_tool = Tool(
        name="Search",
        func=search.run,
        description="Use this tool to search the internet. Input should be a plain text query."
    )

    # Lista dei tools
    tools = [time_tool, search_tool]

    # Memoria di conversazione
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    # Inizializza l’agente (Chat Conversazionale + Tools)
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory
    )

    return agent
