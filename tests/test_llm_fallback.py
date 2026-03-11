import asyncio

from app.llm import TemplateLLMClient


def test_template_llm_generates_text() -> None:
    client = TemplateLLMClient()
    text = asyncio.run(client.generate_monologue({"mood": "eerie", "density": 0.2, "generation": 3}))
    assert "mood=eerie" in text
    assert len(text) > 30
