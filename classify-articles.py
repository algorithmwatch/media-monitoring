import sqlite3
import os
from ollama import chat
from ollama import ChatResponse
from dotenv import load_dotenv, dotenv_values 
import json

load_dotenv() 

DB_PATH = "news_articles.db"

def analyze_article(title, description):
    instructions = "You are an AI content classifier. Your job is to return an integer."
    prompt = f"""
For the article below, determine:

1. Whether it mentions ANY of these topics
- Use of AI in education.
- Use of AI in healthcare, but NOT to detect cancers.
- Impact of social media algorithms.
- Use of automated management tools, for instance to control workers, employees or delivery workers.
- Resistance against data centers.
- Reported biases in algorithms or AI systems.
- Actual, verified use of AI by armed forces.
- Use of AI in the government or in the justice sector.
- Personal testimonies of persons who were adversely affected by automated or AI systems.

If an article mentions these topics, relevance is high, up to 100 if several topics are mentioned.

If the article is a commentary or does not bring new information, relevance is set to 0.

If the article is about an industry not listed above, relevance is set to 0.

Return ONLY an integer between 0 and 100 with the relevance.

Title: {title}
Description: {description}

"""

    response: ChatResponse = chat(model='gemma3', messages=[
      {
        'role': 'user',
        'content': prompt,
      },
    ])

    answer = response.message.content.strip()
    try:
        relevance = int(answer)
    except Exception:
        # fallback if model misbehaves
        relevance = None

    return relevance

def translate(text):
    instructions = "You are a translator to English."
    prompt = f"""
Translate the following to English: {text}

Return ONLY the translation.

"""

    response: ChatResponse = chat(model='gemma3', messages=[
      {
        'role': 'user',
        'content': prompt,
      },
    ])

    translated = response.message.content.strip()

    return translated

# ------------------------------------------------
# Main logic
# ------------------------------------------------
def classify_articles():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, description, lang
        FROM articles
        WHERE relevance IS NULL
        AND DATE(scraped_at) = CURRENT_DATE
    """)

    rows = cur.fetchall()
    # print(f"Found {len(rows)} unclassified articles.")

    for article_id, title, description, lang in rows:
        # print(f"\nClassifying article {article_id}...")

        relevance = analyze_article(title, description)
        
        if lang != "en":
            title_en = translate(title)
            desc_en = translate(description)
        else:
            title_en = title
            desc_en = description

        cur.execute(
            "UPDATE articles SET relevance = ?, title_en = ?, desc_en = ? WHERE id = ?",
            (relevance, title_en, desc_en, article_id)
        )
        conn.commit()

        # print(f" -> relevance = {relevance}")
        # if title_en:
        #   print(f" -> title: {title_en}")

    conn.close()
    # print("\nClassification complete!")


# ------------------------------------------------
# Entry point
# ------------------------------------------------
if __name__ == "__main__":
    classify_articles()
