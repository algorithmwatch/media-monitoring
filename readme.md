# Automated news monitoring

This program browses select news sources for articles about AI in all European countries as well as a few others, then asks an LLM to classify the articles based on their relevance.

## How to use

	make run

Runs all commands.

	python3 parse_newspapers.py

Scrapes articles about AI in many newspapers.

	python3 classify-articles.py

Classifies articles using gemma3 and finds relevant ones.

	python3 cluster.py

Clusters articles to group duplicates

	python3 display_articles_html.py

Shows latest relevant articles.