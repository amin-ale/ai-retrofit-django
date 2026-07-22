from copilot.llm.embeddings import cosine_similarity


def top_matches(query_vector, stored, limit):
    scored = [
        (cosine_similarity(query_vector, row["vector"]), row)
        for row in stored
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:limit]
