import re
from guardrails.models import GuardrailResult

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
# Broad regex for US phone numbers matching formats like 555-123-4567, (555) 123-4567, 5551234567
PHONE_REGEX = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
# Match 13 to 19 digits potentially separated by spaces or dashes, isolated by boundaries
CC_REGEX = re.compile(r"(?<!\d)(?:\d[ \-]*){13,19}(?!\d)")

INJECTION_PHRASES = [
    "ignore previous instructions",
    "ignore the above",
    "disregard previous",
    "you are now",
    "act as if",
    "reveal your system prompt",
    "reveal your instructions",
    "print your prompt",
    "new instructions:",
    "system:",
    "developer mode"
]

def check_pii(message: str) -> GuardrailResult:
    if EMAIL_REGEX.search(message):
        return GuardrailResult(blocked=True, reason="email address detected", category="pii")
    
    if PHONE_REGEX.search(message):
        return GuardrailResult(blocked=True, reason="phone number detected", category="pii")
    
    # Check for credit card
    # Because CC_REGEX will also match a sequence of 13-19 digits with trailing spaces (since the inner group matches spaces),
    # it's best to verify the matched string has exactly 13-19 digits.
    for match in CC_REGEX.finditer(message):
        digits = re.sub(r"[^\d]", "", match.group())
        if 13 <= len(digits) <= 19:
            return GuardrailResult(blocked=True, reason="credit card number detected", category="pii")
            
    return GuardrailResult(blocked=False)

def check_injection(message: str) -> GuardrailResult:
    message_lower = message.lower()
    for phrase in INJECTION_PHRASES:
        if phrase in message_lower:
            return GuardrailResult(blocked=True, reason=f"injection phrase detected: '{phrase}'", category="injection")
    
    return GuardrailResult(blocked=False)

def check_input(message: str) -> GuardrailResult:
    pii_result = check_pii(message)
    if pii_result.blocked:
        return pii_result
        
    injection_result = check_injection(message)
    if injection_result.blocked:
        return injection_result
        
    return GuardrailResult(blocked=False)
