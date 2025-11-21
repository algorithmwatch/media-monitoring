import sqlite3
import os
from openai import OpenAI
from dotenv import load_dotenv, dotenv_values 
import json

load_dotenv() 

DB_PATH = "news_articles.db"
MODEL = "gpt-5-nano"


# ------------------------------------------------
# Initialize OpenAI client
# ------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ------------------------------------------------
# Ask ChatGPT for classification
# ------------------------------------------------
def analyze_article(title, description):
    instructions = "You are an AI content classifier. Your job is to return a JSON object."
    prompt = f"""

For the article below, determine:

1. Whether it fits ANY of these topics
- Use of automated systems or AI in the sectors of education, provision of healthcare (NOT medical research).
- Impact of social media algorithms.
- Use of automated management tools, for instance to control workers, employees or delivery workers.
- Construction of data centers, especially the conflicts related thereto.
- Reported biases in algorithms or AI systems.
- Actual, verified use of AI by armed forces.
- Use of automated systems in the government or in the justice sector.
- Personal testimonies of persons who were adversely affected by automated or AI systems.

2. Write a concise explanation of exactly 150 characters.

Return ONLY a JSON object with this structure:

{{
  "relevant": "YES" or "NO",
  "comment": "150-character explanation in English"
}}


Title: {title}
Description: {description}

"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        instructions=instructions
    )

    answer = response.output_text.strip()

    try:
        data = json.loads(answer)
    except json.JSONDecodeError:
        # fallback if model misbehaves
        data = {"relevant": "NO", "comment": ""}

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
        WHERE relevant IS NULL
    """)

    rows = cur.fetchall()
    print(f"Found {len(rows)} unclassified articles.")

    for article_id, title, description in rows:
        print(f"\nClassifying article {article_id}...")

        result = analyze_article(title, description)

        relevant = 1 if result.get("relevant", "").upper() == "YES" else 0
        comment = result.get("comment", "")

        cur.execute(
            "UPDATE articles SET relevant = ?, comment = ? WHERE id = ?",
            (relevant, comment, article_id)
        )
        conn.commit()

        print(f" -> relevant = {bool(relevant)}")
        if comment:
            print(f" -> comment: {comment}")

    conn.close()
    print("\nClassification complete!")


# ------------------------------------------------
# Entry point
# ------------------------------------------------
if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")
    classify_articles()
