from dotenv import load_dotenv
load_dotenv()
import os

# .env:
#   ANTHROPIC_API_KEY=sk-ant-...
#   CLAUDE_MODEL=claude-haiku-4-5-20251001     (optional; this is the default)
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")


class Brain:
    def __init__(self, model: str = None, temp: float = 0, tokens: int = 2048):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is missing. Add it to your .env file.")
        self.model = model or CLAUDE_MODEL
        self.temperature = temp
        self.max_tokens = tokens
        self.timeout = 60
        self.llm = self._create_model()

    def _create_model(self):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            timeout=self.timeout,
            max_retries=3,  # retries automatically on overloaded (529) / rate-limit (429) errors
            api_key=self.api_key,
        )