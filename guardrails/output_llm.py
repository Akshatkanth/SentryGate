import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from guardrails.models import GuardrailResult

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Initialize ChatGroq model
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=GROQ_API_KEY
)

# Bind structured output
structured_llm = llm.with_structured_output(GuardrailResult)

# Define system prompt
system_prompt = """You are auditing a customer support bot's reply against this strict policy:
- The bot may approve refunds or store credit up to $20. Any reply that approves, promises, or confirms a refund/credit ABOVE $20 violates policy.
- The bot may not guarantee specific delivery/ship dates it wouldn't actually know (e.g. promising arrival by a specific day). General shipping info without a specific promised date is fine.
- The bot may not claim to lift, override, or remove an account suspension/ban/restriction.

Given the bot's reply text, if it violates any of the above policies, return blocked=True with category="unauthorized_promise" and a reason quoting or describing the violating part.
Otherwise, return blocked=False.
Do NOT flag replies that correctly stay within the $20 refund limit, correctly decline to guarantee ship dates, or correctly redirect account issues to human support.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{reply}")
])

# Create the chain
chain = prompt | structured_llm

def check_output_llm(reply: str) -> GuardrailResult:
    result = chain.invoke({"reply": reply})
    return result
