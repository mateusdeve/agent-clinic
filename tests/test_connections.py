# tests/test_connections.py
import os
from dotenv import load_dotenv

load_dotenv()

print("PUBLIC:", os.getenv("LANGFUSE_PUBLIC_KEY"))
print("SECRET:", os.getenv("LANGFUSE_SECRET_KEY")[:10] + "...")
print("HOST:", os.getenv("LANGFUSE_HOST"))


def test_langfuse():
    from langfuse import Langfuse

    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST"),
    )

    trace = langfuse.trace(
        name="teste-inicial",
        user_id="dev-local",
        metadata={"env": "local", "source": "agent-clinic"},
        tags=["agent-clinic", "teste-inicial"],
    )

    span = trace.span(name="primeiro-span", input="oi")
    span.end(output="funcionou!")

    langfuse.flush()
    print("✅ Langfuse OK!")


def test_llm():
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    )

    response = llm.invoke("Responda apenas: conexão ok!")
    print(f"✅ LLM OK: {response.content}")


if __name__ == "__main__":
    test_langfuse()
    test_llm()