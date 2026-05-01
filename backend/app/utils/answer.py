import re
from typing import List, Tuple


def tokenize(text: str) -> List[str]:
    """Tokenize text into words."""
    return re.findall(r"[a-z0-9]+", text.lower())


def sentence_split(text: str) -> List[str]:
    """Split text into sentences."""
    sentences = re.split(r"[.!?]", text)
    return [s.strip() for s in sentences if s.strip()]


def score_sentence(sentence: str, query: str) -> float:
    """Score sentence by token overlap with query."""
    query_tokens = set(tokenize(query))
    sentence_tokens = set(tokenize(sentence))
    
    if not query_tokens or not sentence_tokens:
        return 0.0
    
    overlap = len(query_tokens & sentence_tokens)
    return overlap / max(len(query_tokens), len(sentence_tokens))


def synthesize_answer(query: str, retrieved_chunks: List[Tuple[str, float, dict]]) -> str:
    """Generate answer from retrieved chunks."""
    if not retrieved_chunks:
        return "No relevant information found."
    
    sentences = []
    for chunk_text, similarity, metadata in retrieved_chunks:
        chunk_sentences = sentence_split(chunk_text)
        for sent in chunk_sentences:
            if sent:
                score = score_sentence(sent, query)
                blended_score = 0.6 * score + 0.4 * similarity
                sentences.append((sent, blended_score, metadata))
    
    if not sentences:
        return "No relevant information found."
    
    sentences.sort(key=lambda x: x[1], reverse=True)
    top_sentences = sentences[:5]
    
    answer_lines = []
    for sent, score, metadata in top_sentences:
        page = metadata.get("page", "unknown")
        answer_lines.append(f"- {sent} (page={page})")
    
    return "\n".join(answer_lines)
