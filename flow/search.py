from rapidfuzz import fuzz

from .runbook import Runbook


def fuzzy_search(runbooks: list[Runbook], query: str, limit: int = 50) -> list[Runbook]:
    if not query.strip():
        return runbooks[:limit]

    q = query.lower()
    scored: list[tuple[Runbook, float]] = []

    for rb in runbooks:
        name_score = fuzz.partial_ratio(q, rb.name.lower())
        desc_score = fuzz.partial_ratio(q, rb.desc.lower()) * 0.7 if rb.desc else 0
        tag_score = max(
            (fuzz.partial_ratio(q, t.lower()) for t in rb.tags), default=0
        ) * 0.85
        score = max(name_score, desc_score, tag_score)
        if score >= 45:
            scored.append((rb, score))

    scored.sort(key=lambda x: -x[1])
    return [rb for rb, _ in scored[:limit]]
