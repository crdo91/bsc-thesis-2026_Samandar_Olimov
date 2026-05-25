"""
Prompt builder with 4 strategies:
- naive: just list profile
- constrained: rules and format
- cot: chain-of-thought
- persona: role-play expert advisor
"""

STRATEGIES = ["naive", "constrained", "cot", "persona"]


def _profile_block(profile: dict) -> str:
    interests = ", ".join(profile.get("interests", [])) or "not specified"
    free_text = profile.get("free_text") or "none"
    return (
        f"- Relation: {profile['relation']}\n"
        f"- Gender: {profile['gender']}\n"
        f"- Age: {profile['age_group']}\n"
        f"- Occasion: {profile['occasion']}\n"
        f"- Budget: {profile['budget']}\n"
        f"- Interests: {interests}\n"
        f"- Extra notes: {free_text}"
    )


def build_naive_prompt(profile: dict) -> str:
    return f"""Suggest a gift for this person:
{_profile_block(profile)}"""


def build_constrained_prompt(profile: dict) -> str:
    return f"""Suggest exactly 3 gift ideas for this person.

Profile:
{_profile_block(profile)}

Rules:
- Stay within the budget.
- Do NOT suggest flowers, chocolates, or generic gift cards.
- Each idea must be a specific product type (not "a book", but "a hardcover edition of a fantasy novel").
- For each idea, write: Name, Why it fits (1 sentence), Approximate price in USD.
"""


def build_cot_prompt(profile: dict) -> str:
    return f"""You are helping someone choose a gift. Think step by step.

Profile:
{_profile_block(profile)}

Step 1: What does this person likely enjoy?
Step 2: What types of gifts match those interests AND the budget?
Step 3: Filter out cliches (flowers, chocolates, generic cards).
Step 4: Pick 3 specific ideas.

Finally, write the 3 ideas in this format:
Name | Why it fits | Approximate price in USD
"""


def build_persona_prompt(profile: dict) -> str:
    return f"""You are Elena, an expert personal gift advisor with 20 years of experience.
You are famous for finding original, thoughtful, and budget-friendly gifts. You hate cliches.

A customer asks you for advice. Here is the gift receiver profile:
{_profile_block(profile)}

Give your 3 best recommendations. For each idea, write:
- Name of the gift
- One sentence why it fits this specific person
- Approximate price in USD
"""


BUILDERS = {
    "naive": build_naive_prompt,
    "constrained": build_constrained_prompt,
    "cot": build_cot_prompt,
    "persona": build_persona_prompt,
}


def build_prompt(strategy: str, profile: dict) -> str:
    if strategy not in BUILDERS:
        raise ValueError(f"Unknown strategy: {strategy}. Use one of {STRATEGIES}.")
    return BUILDERS[strategy](profile)
