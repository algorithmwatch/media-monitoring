import sqlite3
from datetime import date
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np

# --- CONFIG ---
DB_PATH = "news_articles.db"

# DBSCAN parameters (tune these!)
EPS = 0.5          # similarity threshold (lower = stricter)
MIN_SAMPLES = 2    # minimum articles to form a cluster


def main():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()


    # Fetch today's articles
    cursor.execute("""
        SELECT rowid, title_en, desc_en
        FROM articles
        WHERE DATE(scraped_at) = CURRENT_DATE
    """)
    
    rows = cursor.fetchall()

    if not rows:
        print("No articles found for today.")
        return

    row_ids = []
    texts = []

    for row in rows:
        row_id, title, desc = row
        combined_text = f"{title or ''} {desc or ''}"
        
        row_ids.append(row_id)
        texts.append(combined_text)

    # --- Vectorize text ---
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_df=0.8,
        min_df=1
    )
    X = vectorizer.fit_transform(texts)

    # --- Run DBSCAN clustering ---
    clustering = DBSCAN(
        eps=EPS,
        min_samples=MIN_SAMPLES,
        metric='cosine'
    )

    labels = clustering.fit_predict(X)

    # --- Update DB with cluster IDs ---
    for row_id, cluster_id in zip(row_ids, labels):
        cursor.execute("""
            UPDATE articles
            SET cluster_id = ?
            WHERE rowid = ?
        """, (int(cluster_id), row_id))

    conn.commit()
    conn.close()

    print("Clustering complete.")
    print(f"Clusters found: {len(set(labels)) - (1 if -1 in labels else 0)}")
    print(f"Noise points: {list(labels).count(-1)}")


if __name__ == "__main__":
    main()