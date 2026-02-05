import sqlite3

def fetch_latest_relevant_articles(db_path="news_articles.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # enables dict-like access
    cursor = conn.cursor()

    query = """
        SELECT source, url, comment, relevance
        FROM articles
        WHERE DATE(scraped_at) = CURRENT_DATE
        AND relevance IS NOT NULL
        ORDER BY relevance ASC
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    conn.close()
    return rows


if __name__ == "__main__":
    articles = fetch_latest_relevant_articles()

    for article in articles:
        print(f"Source:  {article['source']}")
        print(f"URL:     {article['url']}")
        print(f"Comment: {article['comment']}")
        print(f"Relevance: {article['relevance']}")
        print("-" * 80)
