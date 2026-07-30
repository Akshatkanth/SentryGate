from guardrails.models import GuardrailResult

LEAKED_INFO_PHRASES = [
    "system prompt",
    "my instructions are",
    "i was instructed to",
    "as an ai model instructed to",
    "internal configuration"
]

def check_output_rules(reply: str) -> GuardrailResult:
    if not reply or not reply.strip():
        return GuardrailResult(blocked=True, category="malformed", reason="empty response")
    
    reply_lower = reply.lower()
    for phrase in LEAKED_INFO_PHRASES:
        if phrase in reply_lower:
            return GuardrailResult(blocked=True, category="leaked_info", reason=f"leaked info phrase detected: '{phrase}'")
            
    return GuardrailResult(blocked=False)
