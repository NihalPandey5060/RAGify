from typing import List, Dict
from pypdf import PdfReader
import os
import json

def load_pdf_pages(path: str) -> List[str]:
	"""Return list of page texts for the given PDF path."""
	reader = PdfReader(path)
	pages = []
	for p in reader.pages:
		text = p.extract_text() or ""
		pages.append(text)
	return pages


def chunk_texts(pages: List[str], source: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
	"""
	Simple character-based chunker with overlap.
	Returns list of dicts: {"id":..., "text":..., "meta":{...}}
	"""
	chunks = []
	chunk_id = 0
	for page_idx, page in enumerate(pages, start=1):
		if not page.strip():
			continue
		start = 0
		length = len(page)
		while start < length:
			end = min(start + chunk_size, length)
			chunk_text = page[start:end]
			meta = {"source": os.path.basename(source), "page": page_idx}
			chunks.append({"id": f"{os.path.basename(source)}_p{page_idx}_c{chunk_id}", "text": chunk_text, "meta": meta})
			chunk_id += 1
			if end == length:
				break
			start = end - overlap
	return chunks


def ingest_pdf(path: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
	"""Load PDF, chunk pages, and return chunk dicts. Does NOT embed or index.

	This function intentionally returns plain chunks so you can inspect
	results before wiring embeddings and the vector store.
	"""
	pages = load_pdf_pages(path)
	chunks = chunk_texts(pages, source=path, chunk_size=chunk_size, overlap=overlap)
	return chunks


def write_chunks_jsonl(chunks: List[Dict], out_path: str):
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	with open(out_path, "w", encoding="utf-8") as f:
		for c in chunks:
			f.write(json.dumps(c, ensure_ascii=False) + "\n")

