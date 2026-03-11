import os
import gradio as gr
from llama_index.core import VectorStoreIndex, StorageContext, SimpleDirectoryReader, Settings
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.cohere import Cohere
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.node_parser import SentenceSplitter
from pinecone import Pinecone
from dotenv import load_dotenv
from workflow_system import SmartParkingWorkflow

load_dotenv()

# מפתחות
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# הגדרות מודלים
Settings.embed_model = CohereEmbedding(api_key=COHERE_API_KEY, model_name="embed-multilingual-v3.0", input_type="search_document")
Settings.llm = Cohere(api_key=COHERE_API_KEY, model="command-r-08-2024")

# Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index("parking-index")

# טעינת מסמכים עם Chunking
reader = SimpleDirectoryReader(input_dir="../parking_system", recursive=True)
documents = reader.load_data()

splitter = SentenceSplitter()
nodes = splitter.split(documents)

# אינדקס
vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(nodes, storage_context=storage_context)

# מנוע צ'אט עם זיכרון
memory = ChatMemoryBuffer.from_defaults(token_limit=1500)
chat_engine = index.as_chat_engine(chat_mode="context", memory=memory, system_prompt="אתה עוזר חכם למערכת חניון. ענה תמיד בשפת השאלה.")

# פונקציה ל-Gradio
async def chat_with_workflow(user_question, history):
    wf = SmartParkingWorkflow(timeout=60)
    result = await wf.run(query=user_question)
    return str(result)

demo = gr.ChatInterface(fn=chat_with_workflow, title="מערכת חניון חכמה - Agentic RAG", description="שאלו שאלות על תעריפים, נהלים והחלטות טכניות.")

if __name__ == "__main__":
    print("Starting Gradio interface...")
    demo.launch(share=False, debug=True)