import re
import requests
from newspaper import Article
from bs4 import BeautifulSoup
from urllib.parse import urlparse


def fetch_article(url, timeout=10):
	"""Fetch article using newspaper3k and grab some page metadata.

	Returns a dict with: url, domain, title, text, authors, publish_date, top_image, links
	"""
	# Try newspaper3k first (will fail on some sites with 403/blocks)
	article = Article(url)
	links = []
	soup = None
	try:
		article.download()
		article.parse()
	except Exception:
		# newspaper failed (site blocking, etc.) — fallback to requests + bs4
		try:
			headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"}
			resp = requests.get(url, timeout=timeout, headers=headers)
			resp.raise_for_status()
			soup = BeautifulSoup(resp.text, "html.parser")
			# try to get title
			title = soup.title.string.strip() if soup and soup.title and soup.title.string else ""
			# crude text extraction: join all <p> text
			paragraphs = [p.get_text(separator=" ").strip() for p in soup.find_all("p")]
			text = "\n\n".join([p for p in paragraphs if p])
			# find links
			links = [a.get("href") for a in soup.find_all("a", href=True)]
			# populate article-like fields so downstream code can use them
			article.title = title
			article.text = text
			article.authors = []
			article.publish_date = None
			article.top_image = None
		except Exception:
			# ultimate fallback: empty values
			article.title = ""
			article.text = ""
			article.authors = []
			article.publish_date = None
			article.top_image = None
			soup = None
	else:
		# If newspaper succeeded, also try to collect links via requests (non-fatal)
		try:
			headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"}
			resp = requests.get(url, timeout=timeout, headers=headers)
			resp.raise_for_status()
			soup = BeautifulSoup(resp.text, "html.parser")
			links = [a.get("href") for a in soup.find_all("a", href=True)]
		except Exception:
			# ignore link collection failures
			pass

	return {
		"url": url,
		"domain": urlparse(url).netloc,
		"title": article.title or "",
		"text": article.text or "",
		"authors": article.authors,
		"publish_date": article.publish_date,
		"top_image": article.top_image,
		"links": links,
	}


def _simple_metrics(text):
	words = re.findall(r"\w+", text)
	word_count = len(words)
	sentences = re.split(r"[.!?]+\s+", text.strip())
	sentence_count = max(1, len([s for s in sentences if s.strip()]))
	avg_sentence_len = word_count / sentence_count if sentence_count else word_count
	uppercase_words = sum(1 for w in words if w.isupper() and len(w) > 1)
	exclamations = text.count("!")
	long_word_ratio = sum(1 for w in words if len(w) > 7) / max(1, word_count)
	return {
		"word_count": word_count,
		"sentence_count": sentence_count,
		"avg_sentence_len": round(avg_sentence_len, 1),
		"uppercase_words": uppercase_words,
		"exclamations": exclamations,
		"long_word_ratio": round(long_word_ratio, 3),
	}


def analyze_article(title, text, metadata=None):
	"""Improved heuristic credibility check.

	Only the credibility logic lives here; fetching remains unchanged.
	Returns an explainable dict with score (0-100), verdict and reasons.
	"""
	if metadata is None:
		metadata = {}

	metrics = _simple_metrics(text)
	lowered = (text or "").lower()

	# Small curated domain allow/block lists (expandable)
	trusted_domains = {
		"reuters.com", "bbc.co.uk", "bbc.com", "apnews.com", "nytimes.com",
		"theguardian.com", "washingtonpost.com", "npr.org", "wsj.com", "cnn.com"
	}
	low_quality_domains = {"example.com", "fakenews.test", "clickbait.example"}

	reasons = []
	score = 50

	# 1) Metadata signals
	authors = metadata.get("authors") or []
	if authors:
		score += 12
		reasons.append(f"Has author(s): {', '.join(authors[:3])}")
	if metadata.get("publish_date"):
		score += 10
		reasons.append("Has publish date")

	# 2) Domain reputation
	domain = (metadata.get("domain") or "").lower()
	if domain:
		if any(d in domain for d in trusted_domains):
			score += 20
			reasons.append(f"Trusted source domain: {domain}")
		elif any(d in domain for d in low_quality_domains):
			score -= 25
			reasons.append(f"Low-quality domain: {domain}")

	# 3) Article length and structure
	wc = metrics["word_count"]
	if wc >= 800:
		score += 12
		reasons.append("Long, in-depth article")
	elif wc >= 300:
		score += 6
		reasons.append("Moderate length")
	elif wc < 120:
		score -= 20
		reasons.append("Very short article — likely incomplete or opinion")

	# 4) Sourcing and citations
	source_phrases = ["according to", "reported", "said", "told", "sources say", "study", "research", "according to a study", "a report by"]
	source_hits = sum(1 for p in source_phrases if p in lowered)
	if source_hits:
		bonus = min(18, source_hits * 6)
		score += bonus
		reasons.append(f"Sourcing language present ({source_hits} signals)")

	# 5) External references (links)
	links = metadata.get("links") or []
	external_links = [l for l in links if l and l.startswith("http")]
	if len(external_links) >= 3:
		score += 6
		reasons.append(f"Several external links ({len(external_links)})")
	# reward links to trusted domains
	trusted_link_hits = sum(1 for l in external_links if any(td in l for td in trusted_domains))
	if trusted_link_hits:
		score += min(12, trusted_link_hits * 6)
		reasons.append(f"Links to trusted sources ({trusted_link_hits})")

	# 6) Clickbait / sensational indicators
	clickbait_terms = ["shocking", "you won't believe", "unbelievable", "must read", "won't believe", "viral", "breaking"]
	clickbait_count = sum(1 for t in clickbait_terms if t in lowered)
	if clickbait_count:
		deduction = min(30, clickbait_count * 8)
		score -= deduction
		reasons.append(f"Clickbait language detected ({clickbait_count})")

	# 7) Formatting / tone problems
	if metrics["exclamations"] > 0:
		dec = min(10, metrics["exclamations"] * 3)
		score -= dec
		reasons.append(f"Exclamation marks ({metrics['exclamations']})")
	if metrics["uppercase_words"] > 3:
		score -= min(12, metrics["uppercase_words"])
		reasons.append(f"Many ALL-CAPS words ({metrics['uppercase_words']})")

	# 8) Factuality cues: presence of numbers/dates/percentages increases factual tone
	numbers = len(re.findall(r"\b\d{1,4}\b", text))
	if numbers >= 3:
		score += 4
		reasons.append(f"Numeric evidence present ({numbers} numbers detected)")

	# 9) Opinion markers (reduce trust)
	opinion_markers = ["i think", "in my opinion", "we believe", "our view"]
	opin = sum(1 for o in opinion_markers if o in lowered)
	if opin:
		score -= 6 * opin
		reasons.append("Opinionated language detected")

	# 10) Readability extremes
	if metrics["avg_sentence_len"] > 30:
		score -= 6
		reasons.append("Very long sentences — poor readability")

	# Final normalization
	score = int(max(0, min(100, round(score))))

	if score >= 75:
		verdict = "Likely Reliable"
	elif score >= 45:
		verdict = "Questionable"
	else:
		verdict = "Unreliable"

	# Short human-readable explanation (top signals)
	short_reasons = reasons[:5] if reasons else ["No clear signals detected"]

	return {
		"title": title,
		"trust_score": score,
		"verdict": verdict,
		"metrics": metrics,
		"metadata": {
			"authors": metadata.get("authors"),
			"publish_date": metadata.get("publish_date"),
			"domain": metadata.get("domain"),
			"top_image": metadata.get("top_image"),
			"links_count": len(metadata.get("links", [])),
		},
		"reasons": short_reasons,
		"all_reasons": reasons,
	}
    