from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
import os

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def read_pdf(pdf_path):
    """
    Reads a PDF file and processes its content.
    Args:       
        pdf_path (str): The path to the PDF file.
    Returns:
        list: A list of document pages.
    """
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    print(f"Total pages loaded: {len(pages)}")
    return pages

def create_chunks(pdf_path, chunk_size=500, chunk_overlap=50) -> list:
    """
    Splits the given pages into smaller chunks.
     Args:
        pdf_path (str): The path to the PDF file.
        chunk_size (int): The size of each chunk.
        chunk_overlap (int): The overlap between chunks.
    Returns:
        list: A list of document chunks.
    """
    pages = read_pdf(pdf_path)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = text_splitter.split_documents(pages)
    print(f"Total chunks created: {len(chunks)}")
    return chunks


def create_embeddings() -> OpenAIEmbeddings:
    """
    Creates embeddings for the given document chunks.
    Returns:
        OpenAIEmbeddings: The OpenAI embeddings.
    """    
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY)
    return embeddings

def create_vector_store(pdf_path) -> Chroma:
    """
    Creates a Chroma vector store from the given document chunks and embeddings.
    Args:
        chunks (list): List of document chunks.
        embeddings: The embeddings to be used for the vector store.
    Returns:
        Chroma: The Chroma vector store containing the embeddings.
    """
    chunks = create_chunks(pdf_path)
    embeddings = create_embeddings()
    db_chroma = Chroma.from_documents(chunks, embeddings, collection_name="pdf_collection")
    return db_chroma

def query_vector_store(pdf_path,query, top_k=5):
    """
    Queries the Chroma vector store for similar documents based on the given query.
    Args:
        query (str): The query string.
        top_k (int): The number of top similar documents to retrieve.
        pdf_path (str): The path to the PDF file.
    Returns:
        str: The concatenated content of the top similar documents.
    """
    embeddings = create_embeddings()
    db_chroma = create_vector_store(pdf_path)
    query_embedding = embeddings.embed_query(query)
    docs_chroma = db_chroma.similarity_search_by_vector(query_embedding, k=top_k)
    context_text = "\n\n".join([doc.page_content for doc in docs_chroma])
    return context_text


def chat_with_pdf(pdf_path, query, top_k=5):
    """
    Chats with the PDF by querying the vector store and generating a response.
    Args:
        pdf_path (str): The path to the PDF file.
        query (str): The query string.
        top_k (int): The number of top similar documents to retrieve.
    Returns:
        str: The generated response from the language model.
    """
    context_text = query_vector_store(pdf_path, query, top_k)

    llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY, temperature=0.7)
    prompt = f"Use the following context to answer the question:\n\nContext: {context_text}\n\nQuestion: {query}\n\nAnswer:"
    response = llm.invoke(prompt)
    return response.content

if __name__ == "__main__":
    pdf_path = "pdf/Rag_pdf.pdf"
    results = chat_with_pdf(pdf_path, "What is reality?", top_k=3)
    print("++++++++++++++Query Results:+++++++++++++")
    print(results)


