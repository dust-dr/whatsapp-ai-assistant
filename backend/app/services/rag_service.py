# The RAG Service does two things:
#
# 1. INDEX — takes text, splits it into chunks,
#    converts to numbers, stores in ChromaDB
#
# 2. SEARCH — takes a question, converts to numbers,
#    finds the most similar chunks in ChromaDB,
#    returns the matching text
#
# Each business has their own ISOLATED collection.
# Business A can never see Business B's knowledge.

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings
import httpx
import json


class RAGService:

    def __init__(self):
        # Connect to ChromaDB running on localhost:8001
        self.client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port
        )

        # Text splitter breaks large documents into small chunks
        # chunk_size=500 means each chunk is max 500 characters
        # chunk_overlap=50 means chunks share 50 characters with
        # their neighbour — this prevents losing context at the
        # boundary between two chunks
        #
        # Example without overlap:
        # Chunk 1: "Samsung A54 price is GHS 3,200. Available in"
        # Chunk 2: "blue and black. Camera is 50MP..."
        # ← "Available in" got cut off, meaning is lost
        #
        # Example with overlap:
        # Chunk 1: "Samsung A54 price is GHS 3,200. Available in"
        # Chunk 2: "Available in blue and black. Camera is 50MP..."
        # ← context is preserved
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " "]
        )

    def _get_collection(self, business_id: str):
        """
        Gets or creates a ChromaDB collection for a business.
        
        Each business gets their own collection named:
        "business_<their_id>"
        
        This ensures complete data isolation between businesses.
        Business A's products never mix with Business B's products.
        """
        return self.client.get_or_create_collection(
            name=f"business_{business_id}",
            metadata={"hnsw:space": "cosine"}
            # cosine similarity is best for text — it measures
            # the ANGLE between vectors not the distance
            # this makes it better at finding similar meaning
        )

    async def _embed(self, text: str) -> list:
        """
        Converts text into a list of numbers (embedding/vector).
        
        We use Groq's API with a small embedding approach.
        Actually we'll use a simple HTTP call to get embeddings.
        
        For now we use ChromaDB's built-in embedding function
        which uses a local model automatically.
        """
        # We return None here to let ChromaDB use its
        # built-in embedding model automatically.
        # This is simpler and works well for MVP.
        return None

    def index_document(
        self,
        business_id: str,
        document_text: str,
        doc_id: str,
        doc_type: str = "general"
    ) -> int:
        """
        Takes a document, splits it into chunks,
        and stores everything in ChromaDB.
        
        Returns the number of chunks created.
        
        Parameters:
        - business_id: which business this belongs to
        - document_text: the full text to index
        - doc_id: a unique name for this document
                  e.g. "products", "faqs", "policies"
        - doc_type: category label for filtering later
        """

        collection = self._get_collection(business_id)

        # Split the document into chunks
        chunks = self.text_splitter.split_text(document_text)

        if not chunks:
            return 0

        # Create a unique ID for each chunk
        # Format: "products_chunk_0", "products_chunk_1", etc.
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

        # Metadata helps us filter and understand results later
        metadatas = [
            {
                "doc_id": doc_id,
                "doc_type": doc_type,
                "chunk_index": i,
                "business_id": business_id
            }
            for i in range(len(chunks))
        ]

        # If doc already exists, delete old chunks first
        # This allows re-uploading/updating knowledge
        try:
            existing = collection.get(
                where={"doc_id": doc_id}
            )
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass

        # Add all chunks to ChromaDB
        # We don't pass embeddings — ChromaDB generates them
        # automatically using its built-in model
        collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

        return len(chunks)

    def search(
        self,
        business_id: str,
        query: str,
        top_k: int = 4
    ) -> list[str]:
        """
        Searches for the most relevant chunks for a query.
        
        Parameters:
        - business_id: only search THIS business's knowledge
        - query: the customer's question
        - top_k: how many chunks to return (4 is usually enough)
        
        Returns a list of text chunks most relevant to the query.
        """

        collection = self._get_collection(business_id)

        # Check if collection has any documents
        if collection.count() == 0:
            return []

        results = collection.query(
            query_texts=[query],  # ChromaDB embeds this automatically
            n_results=min(top_k, collection.count())
        )

        # results["documents"] is a list of lists
        # [0] gets the first (and only) query's results
        if results["documents"] and results["documents"][0]:
            return results["documents"][0]

        return []

    def delete_business_knowledge(self, business_id: str):
        """
        Deletes ALL knowledge for a business.
        Used when a business deletes their account.
        """
        try:
            self.client.delete_collection(f"business_{business_id}")
        except Exception:
            pass

    def get_knowledge_stats(self, business_id: str) -> dict:
        """
        Returns stats about how much knowledge a business has stored.
        Useful for the dashboard.
        """
        try:
            collection = self._get_collection(business_id)
            return {
                "total_chunks": collection.count(),
                "has_knowledge": collection.count() > 0
            }
        except Exception:
            return {"total_chunks": 0, "has_knowledge": False}


# Create a single instance to reuse across the app
rag_service = RAGService()
