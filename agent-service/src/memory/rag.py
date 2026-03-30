import os
import uuid
import logging

logger = logging.getLogger("agent-clinic.memory")


def _get_embeddings():
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    )


class ClinicRAG:
    def __init__(self):
        self._embeddings = None

    def _embed(self):
        if self._embeddings is None:
            self._embeddings = _get_embeddings()
        return self._embeddings

    def retrieve(self, query: str, k: int = 4) -> str:
        try:
            from src.memory.persistence import _get_db
            embedding = self._embed().embed_query(query)
            with _get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT content FROM search_knowledge(%s::vector, %s, %s)",
                        (embedding, 0.72, k),
                    )
                    rows = cur.fetchall()
            if not rows:
                return ""
            return "\n---\n".join(r[0] for r in rows)
        except Exception as e:
            logger.error(f"[rag] retrieve error: {e}")
            return ""

    def index_summary(self, session_id: str, summary: str, title: str):
        try:
            from src.memory.persistence import _get_db
            embedding = self._embed().embed_query(summary)
            with _get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO knowledge_chunks (id, source_type, source_id, title, content, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s::vector)
                        ON CONFLICT (source_type, source_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding
                        """,
                        (
                            str(uuid.uuid4()),
                            "conversation_summary",
                            session_id,
                            title,
                            summary,
                            embedding,
                        ),
                    )
                conn.commit()
        except Exception as e:
            logger.error(f"[rag] index_summary error: {e}")
