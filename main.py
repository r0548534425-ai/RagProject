import os
import gradio as gr
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, SimpleDirectoryReader, Settings
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.cohere import Cohere
from llama_index.core.node_parser import SentenceSplitter
from dotenv import load_dotenv
load_dotenv()
# 1. הגדרת מפתחות - ודאי שהם נכונים
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# 2. הגדרת המודלים ב-Settings (מונע שגיאת OpenAI)
Settings.embed_model = CohereEmbedding(
    api_key=COHERE_API_KEY, 
    model_name="embed-multilingual-v3.0",
    input_type="search_document"
)
Settings.llm = Cohere(api_key=COHERE_API_KEY, model="command-r-08-2024")

# 3. חיבור ל-Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index("parking-index")

# 4. טעינת נתונים מהתיקייה
# ודאי שהנתיב ../parking_system אכן קיים ומכיל קבצים
reader = SimpleDirectoryReader(input_dir="../parking_system", recursive=True)
documents = reader.load_data()

# 5. הגדרת המחסן הוקטורי
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 6. יצירת האינדקס (כאן מוגדר ה-index שהיה חסר לך!)
index = VectorStoreIndex.from_documents(
    documents, 
    storage_context=storage_context
)

# 7. יצירת מנוע השיחה
from llama_index.core.memory import ChatMemoryBuffer

# אנחנו יוצרים זיכרון שישמור את ההקשר
memory = ChatMemoryBuffer.from_defaults(token_limit=1500)

chat_engine = index.as_chat_engine(
    chat_mode="context", 
    memory=memory,
    system_prompt="אתה עוזר חכם למערכת חניון. ענה תמיד בשפת השאלה."
)

# 8. פונקציית הצ'אט עבור Gradio
# --- 4. הגדרת ממשק Gradio ---

# פונקציית העזר שמחברת בין הממשק ל-Workflow
async def chat_with_workflow(user_question, history):
    wf = ParkingWorkflow(timeout=60)
    result = await wf.run(query=user_question)
    return str(result)

# כאן אנחנו מגדירים את המשתנה 'demo' שהיה חסר!
demo = gr.ChatInterface(
    fn=chat_with_workflow, 
    title="מערכת חניון חכמה - Agentic RAG",
    description="שאלו שאלות על תעריפים, נהלים והחלטות טכניות."
)

# --- 5. הפעלה ---
if __name__ == "__main__":
    print("Starting Gradio interface...")
    demo.launch(share=False, debug=True)