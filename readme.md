# Automated news monitoring

This program browses select news sources for articles about AI in all European countries as well as a few others, then asks an LLM to classify the articles based on their relevance.

## How to use

	make run

Runs all commands.

	python3 parse_newspapers.py

Scrapes articles about AI in many newspapers.

	python3 classify-articles.py

Classifies articles using gpt5-nano and finds relevant ones.

	python3 display_articles.py

Shows latest relevant articles.

## Todo

- Headless scraping.
- Remove old entries from DB.
- Allow for locally classifying articles.
- Build smaller classifyer based on data in DB.