from langchain_community.retrievers import BM25Retriever

class Retriever:
    def __init__(self, documents):
        """
        Initialize BM25 retriever from documents.
        documents = list of Document objects
        """
        self.retriever = BM25Retriever.from_documents(documents)

    def reranking_retrieved_docs(self, new_documents):
        """
        Re-initialize the retriever with updated documents.
        Useful when you want to refresh indexing.
        """
        self.retriever = BM25Retriever.from_documents(new_documents)
        return self.retriever

    def invoke_retriever(self, query, k=5):
        """
        Retrieve top K documents for the input query.
        """
        return self.retriever.get_relevant_documents(query)[:k]


