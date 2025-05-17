from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingManager:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Inicializa el gestor de embeddings."""
        print(f"\nCargando modelo de embeddings: {model_name}")
        self.model = SentenceTransformer(model_name)
        print("Modelo de embeddings cargado")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos."""
        if not texts:
            print("No hay textos para generar embeddings")
            return []
        
        filtered_texts = []
        for text in texts:
            if text and len(text.strip()) >= 3:
                filtered_texts.append(text)
            else:
                # Para textos muy cortos, usar un placeholder
                filtered_texts.append("placeholder_text")
                
        try:
            print(f"\nGenerando embeddings para {len(filtered_texts)} textos")
            embeddings = self.model.encode(filtered_texts, convert_to_tensor=False)
            
            # Asegurar que los resultados son listas, no ndarrays
            result_embeddings = []
            for emb in embeddings:
                if isinstance(emb, np.ndarray):
                    result_embeddings.append(emb.tolist())
                else:
                    result_embeddings.append(emb)
                    
            print("Embeddings generados exitosamente")
            return result_embeddings
        except Exception as e:
            print(f"Error al generar embeddings: {e}")
            # Fallback: devolver vectores de ceros
            vector_dim = 384  # Dimensión típica de all-MiniLM-L6-v2
            return [[0.0] * vector_dim for _ in range(len(texts))]

    def embed_query(self, query: str) -> List[float]:
        """Genera embedding para una consulta."""
        print(f"\nGenerando embedding para consulta: {query}")
        try:
            embedding = self.model.encode([query], convert_to_tensor=False)[0]
            # Asegurar que el resultado es una lista, no un ndarray
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            print("Embedding de consulta generado")
            return embedding
        except Exception as e:
            print(f"Error al generar embedding para consulta: {e}")
            # Fallback: devolver un vector de ceros si hay algún error
            vector_dim = 384  # Dimensión típica de all-MiniLM-L6-v2
            return [0.0] * vector_dim
        
    async def embed_text(self, text: str) -> List[float]:
        """Genera embedding para un texto individual de forma asíncrona."""
        # Optimizar para textos vacíos o muy cortos
        if not text or len(text) < 3:
            # Devolver un vector de ceros como fallback para textos muy cortos
            vector_dim = 384  # Dimensión típica de all-MiniLM-L6-v2
            return [0.0] * vector_dim
            
        try:
            # Usar embed_query para aprovechar el logging y conversión a lista
            return self.embed_query(text)
        except Exception as e:
            print(f"Error al generar embedding para texto: {e}")
            # Fallback en caso de error
            vector_dim = 384  # Dimensión típica de all-MiniLM-L6-v2
            return [0.0] * vector_dim

    def get_embedding_model(self):
        """Retorna el modelo de embeddings para uso directo."""
        return self.model 