import sqlite3
import os
from ollama import chat
from ollama import ChatResponse
from dotenv import load_dotenv, dotenv_values 
import json

load_dotenv() 

DB_PATH = "news_articles.db"

def analyze_article(title, description):
    instructions = "You are an AI content classifier. Your job is to return a JSON object."
    prompt = f"""
You are an AI content classifier. Your job is to return a JSON object.

For the article below, determine:

1. Whether it mentions ANY of these topics
- Concrete use of AI in the sectors of education or healthcare provision.
- Impact of social media algorithms.
- Use of automated management tools, for instance to control workers, employees or delivery workers.
- Resistance against data centers.
- Reported biases in algorithms or AI systems.
- Actual, verified use of AI by armed forces.
- Use of automated systems in the government or in the justice sector.
- Personal testimonies of persons who were adversely affected by automated or AI systems.

If an article mentions these topics, relevance is high, up to 100 if several topics are mentioned.

If the article is a commentary or does not bring new information, relevance is set to 0.

If the article is about an industry not listed above, relevance is set to 0.

2. Write a concise explanation of exactly 150 characters.

Return ONLY a JSON object with this structure:

{{
  "relevance": A number between 0 and 100,
  "comment": "150-character explanation in English"
}}


Title: {title}
Description: {description}

"""

    response: ChatResponse = chat(model='gemma3', messages=[
      {
        'role': 'user',
        'content': prompt,
      },
    ])

    answer = response.message.content.strip().replace("```json", "").replace("```", "")

    try:
        data = json.loads(answer)
    except json.JSONDecodeError:
        # fallback if model misbehaves
        data = {"relevance": "0", "comment": ""}

    return data

# ------------------------------------------------
# Main logic
# ------------------------------------------------
def classify_articles():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, description
        FROM articles
        WHERE relevance IS NULL
    """)

    rows = cur.fetchall()
    print(f"Found {len(rows)} unclassified articles.")

    for article_id, title, description in rows:
        print(f"\nClassifying article {article_id}...")

        result = analyze_article(title, description)

        relevance = int(result.get("relevance", ""))
        comment = result.get("comment", "")

        cur.execute(
            "UPDATE articles SET relevance = ?, comment = ? WHERE id = ?",
            (relevance, comment, article_id)
        )
        conn.commit()

        print(f" -> relevance = {relevance}")
        if comment:
            print(f" -> comment: {comment}")

    conn.close()
    print("\nClassification complete!")


# ------------------------------------------------
# Entry point
# ------------------------------------------------
if __name__ == "__main__":
    classify_articles()
