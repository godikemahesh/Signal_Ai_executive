"""
Signal — Ask Signal NLQ Prompt Template
Instructs the LLM to synthesize natural language answers from retrieved signals/entities.
"""

ASK_SIGNAL_SYSTEM_INSTRUCTION = """You are Signal, an AI Executive Assistant.
Answer the user's natural language question about their digital life based ONLY on the provided context (signals and entities).

Be direct, calm, concise, and helpful. Start directly with the answer. Avoid fluff or verbose meta-explanations.

Respond in JSON format:
{
  "answer": "Human-readable markdown response",
  "intent": "Extracted user intent classification"
}
"""


def build_ask_signal_prompt(query: str, context_signals_text: str, context_entities_text: str) -> str:
    return f"""User Query: "{query}"

Retrieved Relevant Entities:
{context_entities_text}

Retrieved Relevant Signals:
{context_signals_text}

Answer the query clearly based on the context above.
"""
