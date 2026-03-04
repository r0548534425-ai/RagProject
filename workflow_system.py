import os
import json
import asyncio
import gradio as gr
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, SimpleDirectoryReader, Settings
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.cohere import Cohere
from llama_index.core.workflow import Workflow, step, StartEvent, StopEvent, Event, Context
from llama_index.core.base.llms.types import ChatMessage
from dotenv import load_dotenv

# 1. טעינת משתנים
load_dotenv() 

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not COHERE_API_KEY:
    raise ValueError("שגיאה: המפתח COHERE_API_KEY לא נמצא בקובץ ה-.env")

# 2. הגדרות מודלים
Settings.embed_model = CohereEmbedding(api_key=COHERE_API_KEY, model_name="embed-multilingual-v3.0")
Settings.llm = Cohere(api_key=COHERE_API_KEY, model="command-r-08-2024")

# 3. חיבור ל-Pinecone ואינדקס
pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index("parking-index")
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
query_engine = index.as_query_engine(streaming=False)

# 4. הגדרת אירועים
class ValidatedQueryEvent(Event):
    query: str

class RouterEvent(Event):
    query: str
    source: str

class RetrievalEvent(Event):
    context: str
    query: str

# 5. בניית ה-Workflow
class SmartParkingWorkflow(Workflow):
    
    @step
    async def validate_input(self, ev: StartEvent) -> ValidatedQueryEvent | StopEvent:
        query = ev.get("query")
        if not query or len(query.strip()) < 2:
            return StopEvent(result="השאלה קצרה מדי, אנא פרט יותר.")
        return ValidatedQueryEvent(query=query)

    @step
    async def router_step(self, ev: ValidatedQueryEvent) -> RouterEvent:
        # הנחיות חזקות יותר לניתוב
        messages = [
            ChatMessage(role="system", content="""תפקידך להחליט מאיפה לשלוף מידע:
            - בחר 'JSON' רק עבור: תעריפי חניה, מחירים, שעות פעילות, או רשימת רכיבי מערכת.
            - בחר 'Pinecone' עבור: נהלי בטיחות, הסברים על תקלות, תיאור תהליכים, וכל שאלה שדורשת הסבר.
            ענה במילה אחת בלבד: 'JSON' או 'Pinecone'."""),
            ChatMessage(role="user", content=f"השאלה היא: {ev.query}")
        ]
        response = Settings.llm.chat(messages)
        choice = str(response).strip().upper()
        
        # הדפסת ההחלטה של המודל לטרמינל לצרכי בקרה
        print(f">>> [ROUTER] המודל החליט על: {choice}")
        
        source = "JSON" if "JSON" in choice else "Pinecone"
        return RouterEvent(query=ev.query, source=source)

    @step
    async def retrieve_data(self, ev: RouterEvent) -> RetrievalEvent:
        if ev.source == "JSON":
            print(f">>> [FETCH] שולף נתונים קשיחים מ-JSON")
            with open("parking_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return RetrievalEvent(context=json.dumps(data, ensure_ascii=False), query=ev.query)
        else:
            print(f">>> [FETCH] מבצע חיפוש סמנטי ב-Pinecone")
            res = query_engine.query(ev.query)
            return RetrievalEvent(context=str(res), query=ev.query)

    @step
    async def generate_and_validate(self, ev: RetrievalEvent) -> StopEvent:
        messages = [
            ChatMessage(role="system", content="אתה עוזר חכם למערכת חניון. ענה ישירות ומקצועי על בסיס המידע המצורף בלבד."),
            ChatMessage(role="user", content=f"מידע: {ev.context}\nשאלה: {ev.query}")
        ]
        response = Settings.llm.chat(messages)
        return StopEvent(result=str(response))

# 6. ממשק Gradio
async def chat_interface(message, history):
    wf = SmartParkingWorkflow(timeout=30)
    result = await wf.run(query=message)
    return str(result)

demo = gr.ChatInterface(fn=chat_interface, title="מערכת ניהול חניון - Agentic RAG")

if __name__ == "__main__":
    print("Starting system...")
    demo.launch()