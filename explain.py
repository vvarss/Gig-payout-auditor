"""
explain.py  --  Step 3 of the pipeline: flags -> plain-language explanation + message.

Two modes:
  * Built-in template : free, always works, English only.
  * Claude            : nicer wording, English or Tamil. Needs API credit.
If Claude fails for ANY reason (no credit, no internet), we fall back to the template,
so the app never breaks during a demo.
"""
MODEL = "claude-haiku-5-5"
MARKER = "---MESSAGE---"


def template_explanation(flags):
    if not flags:
        return "No inconsistencies found in these trips."
    lines = ["Here is what looks inconsistent (largest rupee impact first):", ""]
    for i, f in enumerate(flags, 1):
        lines.append(f"{i}. {f['file']}: {f['detail']}")
    lines += ["", "These are questions to ask, not proof of an error. Pay can legitimately "
              "vary (peak hours, pickup distance, incentives)."]
    return "\n".join(lines)


def template_message(flags):
    if not flags:
        return ""
    lines = ["Hello Support Team,", "",
             "While reviewing my trip earnings, I noticed a few items I could not "
             "reconcile. Could you please explain or correct them?", ""]
    for f in flags:
        lines.append(f"- {f['file']}: {f['detail']}")
    lines += ["", "Please share the calculation for these trips. Thank you."]
    return "\n".join(lines)


def claude_explanation(flags, language="English"):
    """Ask Claude to explain the flags. Returns (explanation, message) or None on failure."""
    try:
        import anthropic          # imported here so the app works without a key

        client = anthropic.Anthropic()
        flag_text = "\n".join(
            f"- {f['file']} [{f['check']}] ~{f['rupees']} rupees: {f['detail']}" for f in flags
        )
        prompt = f"""A delivery rider's trip earnings were checked by a program. These items
looked inconsistent:

{flag_text}

Write in {language}, in simple words a non-technical person understands:
1. A short explanation, most rupee impact first. Say "looks inconsistent" or
   "worth asking about". NEVER say the rider was cheated or that the platform made an
   error; pay can vary for legitimate reasons.
2. Then a line containing exactly {MARKER}
3. Then a polite, short message the rider can send to support asking for clarification.
Only use the facts above. Do not invent numbers."""
        msg = client.messages.create(
            model=MODEL, max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text
        if MARKER in text:
            expl, message = text.split(MARKER, 1)
            return expl.strip(), message.strip()
        return text.strip(), template_message(flags)
    except Exception:
        return None


def explain(flags, language="English", use_claude=False):
    """Returns (explanation, message, source) where source is 'claude' or 'template'."""
    if use_claude and flags:
        result = claude_explanation(flags, language)
        if result:
            return result[0], result[1], "claude"
    return template_explanation(flags), template_message(flags), "template"
