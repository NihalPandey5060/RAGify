from typing import Dict, List, Tuple
import re

from src import embedding, retrieval


def _tokenize(text: str) -> List[str]:
	return re.findall(r"[a-z0-9]+", text.lower())


def _sentence_split(text: str) -> List[str]:
	parts = re.split(r"(?<=[.!?])\s+", text.strip())
	return [p for p in parts if p]


def _score_sentence(sentence: str, query_tokens: set[str]) -> float:
	s_tokens = set(_tokenize(sentence))
	if not s_tokens:
		return 0.0
	overlap = len(s_tokens.intersection(query_tokens))
	return overlap / max(1, len(query_tokens))


def synthesize_answer(question: str, contexts: List[Tuple[str, float, Dict]], max_sentences: int = 4) -> str:
	"""
	Build a grounded extractive answer from retrieved chunks.
    
	This is intentionally simple and deterministic. It avoids API calls and
	keeps answers anchored to retrieved context.
	"""
	q_tokens = set(_tokenize(question))
	candidates: List[Tuple[float, str, Dict]] = []

	for chunk_text, similarity, meta in contexts:
		for sent in _sentence_split(chunk_text):
			score = _score_sentence(sent, q_tokens)
			# Similarity helps tie-break when lexical overlap is equal.
			final_score = 0.75 * score + 0.25 * max(0.0, similarity)
			if final_score > 0:
				candidates.append((final_score, sent.strip(), meta))

	if not candidates:
		return "I could not find grounded evidence in the indexed documents for this question."

	candidates.sort(key=lambda x: x[0], reverse=True)
	chosen = candidates[:max_sentences]
	answer_lines = []
	for _, sent, meta in chosen:
		answer_lines.append(f"- {sent} (source={meta.get('source')}, page={meta.get('page')})")

	# Your turn: improve this by adding a reranking stage before synthesis.
	return "\n".join(answer_lines)


def answer_question(
	question: str,
	top_k: int = 5,
	collection_name: str = "documents",
	persist_dir: str = "vector_store",
) -> Dict:
	"""Retrieve relevant chunks and return an extractive grounded answer."""
	q_embedding = embedding.get_embeddings([question])[0]
	contexts = retrieval.retrieve_similar_chunks(
		query_text=question,
		query_embedding=q_embedding,
		collection_name=collection_name,
		persist_dir=persist_dir,
		top_k=top_k,
	)

	answer = synthesize_answer(question, contexts)
	return {
		"question": question,
		"answer": answer,
		"contexts": contexts,
	}
