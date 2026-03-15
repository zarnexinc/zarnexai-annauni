from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma(
    persist_directory="vector_db",
    embedding_function=embedding
)

retriever = db.as_retriever(search_kwargs={"k":3})


def retrieve_context(query: str):

    docs = retriever.get_relevant_documents(query)

    context = "\n".join([doc.page_content for doc in docs])

    return context