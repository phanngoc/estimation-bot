from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAI
from PyPDF2 import PdfReader

# Or set the OpenAI key in the environment directly
import os
from dotenv import load_dotenv

load_dotenv("../.env")

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

documents = [
    "This is a document about the authors of the book.",
    "The authors of the book are John Doe and Jane Smith.",
]

chain = load_qa_chain(llm=OpenAI(api_key=os.getenv("OPENAI_API_KEY")), chain_type="map_reduce")
query = ["Who are the autors?"]

chain.run(input_documents=documents, question=query)