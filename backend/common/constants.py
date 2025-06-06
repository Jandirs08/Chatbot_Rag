# TEXT_MODEL_NAME = "text-bison@001"
# CHAT_MODEL_NAME = "chat-bison@001"

ANONYMIZED_FIELDS = ['US_BANK_NUMBER', 'US_DRIVER_LICENSE', 'US_ITIN', 'US_PASSPORT', 'US_SSN']
NLP_CONFIG = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "es", "model_name": "es_core_news_sm"}
    ]
}
PERSONAL_CHAT_PROMPT_REACT = "SHELDON_REACT_PROMPT"
PERSONAL_CHAT_PROMPT = "SHELDON_REACT_PROMPT"

# Message roles
USER_ROLE = "user"
ASSISTANT_ROLE = "assistant"
