"""Domain knowledge packs. One entry point for app/graph.py:

    from app.domains import domain_context
    system += domain_context(question)      # "" when the question is not covered by a pack

Packs:  affiliates.py | transactions.py | affiliate_transactions.py (needs both topics)
To add a new topic (providers, games, coupons ...): copy affiliates.py to a new file with its own
GUIDE / EXAMPLES / TRIGGER, then register it in PACKS below.
Set the environment variable DOMAIN_KNOWLEDGE=off to switch all of this off.
"""
import os

from app.domains import affiliate_transactions, affiliates, transactions
from app.domains.common import format_examples, pick_examples

PACKS = {"affiliates": affiliates, "transactions": transactions}


def detect_domains(question: str) -> list[str]:
    return [name for name, pack in PACKS.items() if pack.TRIGGER.search(question or "")]


def domain_context(question: str) -> str:
    if os.getenv("DOMAIN_KNOWLEDGE", "on").lower() == "off":
        return ""
    found = detect_domains(question)
    if not found:
        return ""

    guides = [PACKS[name].GUIDE for name in found]
    pool = [ex for name in found for ex in PACKS[name].EXAMPLES]

    cross = "affiliates" in found and "transactions" in found
    if cross:  # question needs both topics: add the cross rules and prefer the cross examples
        guides.append(affiliate_transactions.GUIDE)
        pool = [dict(ex, bonus=4) for ex in affiliate_transactions.EXAMPLES] + pool

    shots = format_examples(pick_examples(question, pool, k=4 if cross else 3))
    return (
        "\n\n".join(guides)
        + "\n\nVerified examples (follow their structure, adapt filters/limits/period to the user's question):\n"
        + shots
    )