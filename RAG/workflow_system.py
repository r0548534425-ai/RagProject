import os
import json
import asyncio
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
from pinecone import Pinecone
import gradio as gr

from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.workflow import Workflow, step, StartEvent, StopEvent, Event
from llama_index.core.base.llms.types import ChatMessage
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.cohere import Cohere
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core.program import LLMTextCompletionProgram

# טעינת משתני סביבה
load_dotenv()

# הגדרות מודלים
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

Settings.embed_model = CohereEmbedding(api_key=COHERE_API_KEY, model_name="embed-multilingual-v3.0")
Settings.llm = Cohere(api_key=COHERE_API_KEY, model="command-r-08-2024")

# --- חלק א': חילוץ נתונים אוטומטי מהתיקיות שבתמונה ---

class ExtractedInfo(BaseModel):
    technical_decisions: List[str]
    business_rules: List[str]
    system_warnings: List[str]


def initialize_data_extraction():
    print(">>> [PRE-PROCESS] סורק תיקיות ומחלץ מידע עם Metadata...")
    
    input_dirs = ["./.cursor", "./.claudecode"]
    valid_dirs = [d for d in input_dirs if os.path.exists(d)]
    
    if not valid_dirs:
        print("אזהרה: תיקיות המקור לא נמצאו.")
        return

    # קורא קבצים ושומר את המקור של כל מסמך
    reader = SimpleDirectoryReader(input_dirs=valid_dirs, recursive=True)
    documents = reader.load_data()
    
    extracted_items = {
        "technical_decisions": [],
        "business_rules": [],
        "system_warnings": []
    }

    # עיבוד כל מסמך בנפרד כדי לשמור על המקור (Metadata)
    for doc in documents:
        file_name = doc.metadata.get("file_name", "unknown")
        
        prompt_template = f"""
        נתח את הטקסט הבא מקובץ ההגדרות '{file_name}'.
        חלץ הנחיות ספציפיות עבור הקטגוריות הבאות:
        1. technical_decisions (החלטות טכנולוגיות)
        2. business_rules (חוקים ומגבלות סוכן)
        3. system_warnings (אזהרות בטיחות)
        
        החזר רשימה של אובייקטים הכוללים את תוכן ההנחיה ואת שם הקובץ כמקור.
        הטקסט:
        {doc.text}
        """

        # שימוש ב-LLM לחילוץ מובנה
        program = LLMTextCompletionProgram.from_defaults(
            output_cls=ExtractedInfo,
            prompt_template_str=prompt_template,
            llm=Settings.llm
        )
        
        res = program()
        
        # הוספת המקור לכל פריט שחולץ
        for item in res.technical_decisions:
            extracted_items["technical_decisions"].append({"content": item, "source": file_name})
        for item in res.business_rules:
            extracted_items["business_rules"].append({"content": item, "source": file_name})
        for item in res.system_warnings:
            extracted_items["system_warnings"].append({"content": item, "source": file_name})

    data_to_save = {
        "project_metadata": {
            "last_updated": "2026-03-11",
            "files_scanned": [doc.metadata.get("file_name") for doc in documents]
        },
        "items": extracted_items
    }
    
    with open("parking_data.json", "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    print(f">>> [PRE-PROCESS] חולצו {len(documents)} קבצים ל-parking_data.json עם Metadata!")

# --- חיבור ל-Pinecone ---
pc = Pinecone(api_key=PINECONE_API_KEY)
# ודאי ששם האינדקס תואם למה שמוגדר אצלך ב-Console
pinecone_index = pc.Index("parking-index") 
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
query_engine = index.as_query_engine(streaming=False)

# --- הגדרת אירועי Workflow ---
class ValidatedQueryEvent(Event):
    query: str

class RouterEvent(Event):
    query: str
    source: str 

class JsonQueryEvent(Event):
    query: str
    category: str

class RetrievalEvent(Event):
    context: str
    query: str

# --- Agentic Workflow ---
class AgentDocsWorkflow(Workflow):

    @step
    async def validate_input(self, ev: StartEvent) -> ValidatedQueryEvent | StopEvent:
        query = ev.get("query")
        if not query or len(query.strip()) < 2:
            return StopEvent(result="השאלה קצרה מדי, אנא פרט יותר.")
        return ValidatedQueryEvent(query=query)

   
    @step
    async def router_step(self, ev: ValidatedQueryEvent) -> RouterEvent:
        messages = [
            ChatMessage(role="system", content="""תפקידך לסווג את שאילתת המשתמש לאחד משני מקורות מידע לפי המאפיינים הבאים:

1. בחר 'JSON' כאשר השאלה מחפשת מידע מסוג "אמת יחידה" (Single Source of Truth):
   - רשימות סופיות (מהן הדרכים, אילו כלים, מי האנשים).
   - חוקים ומגבלות (מותר/אסור, תנאים, אזהרות, הנחיות עבודה).
   - נתונים כמותיים (מחירים, תאריכים, גרסאות).
   - החלטות שהתקבלו (מה נבחר, מה השתנה).

2. בחר 'PINECONE' כאשר השאלה מחפשת מידע מסוג "הקשר רחב" (Semantic Context):
   - הסברים תיאורטיים (איך זה עובד, מה המשמעות של...).
   - נימוקים וסיבות (למה בחרנו, מה היתרון של...).
   - תיאורי תהליכים ארוכים או רקע היסטורי של הפרויקט.

כלל מכריע: אם התשובה צפויה להיות רשימה או שורת חוק קצרה - בחר JSON.
ענה במילה אחת בלבד: JSON או PINECONE."""),
            ChatMessage(role="user", content=ev.query)
        ]
        response = Settings.llm.chat(messages)
        choice = str(response.message.content).strip().upper()
        source = "JSON" if "JSON" in choice else "PINECONE"
        print(f">>> [ROUTER] סיווג לוגי: {source}")
        return RouterEvent(query=ev.query, source=source)
       
      
    @step
    async def retrieve_pinecone(self, ev: RouterEvent) -> RetrievalEvent | None:
        if ev.source != "PINECONE": return None
        print(">>> [FETCH] מבצע חיפוש סמנטי ב-Pinecone...")
        res = query_engine.query(ev.query)
        return RetrievalEvent(context=str(res), query=ev.query)

    @step
    async def generate_json_query(self, ev: RouterEvent) -> JsonQueryEvent | None:
        if ev.source != "JSON": return None
        schema_keys = "['technical_decisions', 'business_rules', 'system_warnings']"
        messages = [
            ChatMessage(role="system", content=f"בחר את המפתח המתאים ביותר מהרשימה {schema_keys}. ענה במילה אחת בלבד באנגלית."),
            ChatMessage(role="user", content=ev.query)
        ]
        res = Settings.llm.chat(messages)
        category = str(res.message.content).strip().lower()
        # ניקוי תווים
        category = "".join(filter(str.isalnum, category.split()[0]))
        return JsonQueryEvent(query=ev.query, category=category)

    @step
    async def retrieve_json(self, ev: JsonQueryEvent) -> RetrievalEvent:
        print(f">>> [FETCH] שולף קטגוריית '{ev.category}' מה-JSON...")
        try:
            with open("parking_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                extracted_data = data.get("items", {}).get(ev.category, "לא נמצא מידע ספציפי.")
                context = json.dumps(extracted_data, ensure_ascii=False)
        except:
            context = "שגיאה בגישה לנתוני ה-JSON."
        return RetrievalEvent(context=context, query=ev.query)

    @step
    async def generate_and_validate(self, ev: RetrievalEvent) -> StopEvent:
        print(">>> [GENERATE] מנסח תשובה סופית...")
        messages = [
            ChatMessage(role="system", content="אתה עוזר AI מקצועי המבוסס על תיעוד טכני. ענה בצורה ברורה וישירה."),
            ChatMessage(role="user", content=f"הקשר: {ev.context}\nשאלה: {ev.query}")
        ]
        response = Settings.llm.chat(messages)
        return StopEvent(result=str(response.message.content))

# --- ממשק Gradio ---
async def chat_interface(message, history):
    wf = AgentDocsWorkflow(timeout=60)
    result = await wf.run(query=message)
    return str(result)

if __name__ == "__main__":
    # הפעלת חילוץ הנתונים מהתיקיות בתמונה
    initialize_data_extraction()
    
    # הפעלת הממשק
    demo = gr.ChatInterface(
        fn=chat_interface, 
        title="🤖 Agentic Code Docs RAG"
        
    )
    demo.launch(share=False, debug=True)