import os
import json
import logging
from contextlib import contextmanager
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

logger = logging.getLogger("agent-clinic.memory")


@contextmanager
def _get_db():
    import psycopg2
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL não configurado")
    conn = psycopg2.connect(url)
    try:
        yield conn
    finally:
        conn.close()


def save_messages(
    session_id: str,
    messages: List[BaseMessage],
    patient_id=None,
    metadata: Optional[dict] = None,
):
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                for msg in messages:
                    cur.execute(
                        """
                        INSERT INTO conversations (session_id, role, content, patient_id, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            session_id,
                            "assistant" if msg.type == "ai" else "user",
                            msg.content,
                            patient_id,
                            json.dumps(metadata or {}),
                        ),
                    )
            conn.commit()
    except Exception as e:
        logger.error(f"[persistence] save_messages error: {e}")


def save_summary(
    session_id: str,
    summary_data: dict,
    patient_id=None,
    feedback_score=None,
):
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO conversation_summaries
                        (session_id, summary, key_topics, sentiment, resolved, feedback_score, patient_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id) DO UPDATE SET
                        summary = EXCLUDED.summary,
                        key_topics = EXCLUDED.key_topics,
                        sentiment = EXCLUDED.sentiment,
                        resolved = EXCLUDED.resolved,
                        feedback_score = COALESCE(EXCLUDED.feedback_score, conversation_summaries.feedback_score)
                    """,
                    (
                        session_id,
                        summary_data.get("summary", ""),
                        summary_data.get("key_topics", []),
                        summary_data.get("sentiment", "neutro"),
                        summary_data.get("resolved", False),
                        feedback_score,
                        patient_id,
                    ),
                )
            conn.commit()
    except Exception as e:
        logger.error(f"[persistence] save_summary error: {e}")


def load_session_history(session_id: str) -> List[BaseMessage]:
    try:
        with _get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT role, content FROM conversations
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                    """,
                    (session_id,),
                )
                rows = cur.fetchall()
        return [
            AIMessage(content=r[1]) if r[0] == "assistant" else HumanMessage(content=r[1])
            for r in rows
        ]
    except Exception as e:
        logger.error(f"[persistence] load_session_history error: {e}")
        return []
