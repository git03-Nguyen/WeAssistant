"""Intent classification service with LLM-based detection."""

from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from typing import Dict, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config.settings import get_settings
from app.models.intent import IntentType


@dataclass(frozen=True)
class IntentResult:
    """Intent classification result."""

    intent: IntentType
    confidence: float
    metadata: Optional[Dict[str, str]] = field(default_factory=dict)


class IntentClassifierService:
    """LLM-based intent classification."""

    def __init__(self):
        self.settings = get_settings()
        self._classification_cache: Dict[str, IntentResult] = {}

    @cached_property
    def llm(self) -> ChatOpenAI:
        """Cached LLM instance for classification."""
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is required for intent classification")
        return ChatOpenAI(
            model=self.settings.openai_classifier_model,
            api_key=SecretStr(self.settings.openai_api_key),
            temperature=0,  # Deterministic results
        )

    @lru_cache(maxsize=1)
    def _get_classification_prompt(self) -> ChatPromptTemplate:
        """Get cached classification prompt."""
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Classify user intent for WeMasterTrade (WMT) prop-trading platform:

TRIVIAL: greetings, thanks, goodbye
- "hi", "thank you", "bye"

FAQ: questions about trading, WMT services, education  
- "what is forex", "how to trade", "explain risk consistency rules"

CONSULTANT: requesting package recommendations
- "which package is best for me", "recommend a plan", "what do you offer"

OTHER: topics unrelated to WMT/trading
- "weather today", "cooking recipes", "movie recommendations"

Respond JSON only:
{"intent":"TRIVIAL|FAQ|CONSULTANT|OTHER","confidence":0.9,"subtype":"greeting|thanks|goodbye|null"}""",
                ),
                ("human", "{message}"),
            ]
        )

    @lru_cache(maxsize=1)
    def _get_output_parser(self) -> JsonOutputParser:
        """Get cached JSON output parser."""
        return JsonOutputParser()

    async def classify_intent(self, message: str) -> IntentResult:
        """Classify user intent using LLM with caching."""
        if not message.strip():
            return IntentResult(
                intent=IntentType.TRIVIAL,
                confidence=0.95,
                metadata={"type": "greeting"},
            )

        message_clean = message.strip()

        # Check cache first
        if message_clean in self._classification_cache:
            return self._classification_cache[message_clean]

        try:
            # Use LLM for classification
            prompt = self._get_classification_prompt()
            parser = self._get_output_parser()

            chain = prompt | self.llm | parser

            result = await chain.ainvoke({"message": message_clean})

            # Parse LLM response
            intent_str = result.get("intent", "FAQ").upper()
            confidence = float(result.get("confidence", 0.8))
            subtype = result.get("subtype")

            # Ensure valid intent
            try:
                intent = IntentType(intent_str)
            except ValueError:
                intent = IntentType.FAQ
                confidence = 0.6

            # Build metadata
            metadata = {}
            if intent == IntentType.TRIVIAL and subtype:
                metadata["type"] = subtype

            intent_result = IntentResult(
                intent=intent, confidence=confidence, metadata=metadata
            )  # Cache the result
            self._classification_cache[message_clean] = intent_result

            return intent_result

        except Exception as e:
            print(f"Warning: LLM classification failed: {e}")
            # Fallback to FAQ when LLM fails
            return IntentResult(intent=IntentType.FAQ, confidence=0.5)

    def clear_cache(self):
        """Clear classification cache."""
        self._classification_cache.clear()
