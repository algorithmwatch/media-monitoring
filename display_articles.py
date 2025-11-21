import sqlite3

def fetch_latest_relevant_articles(db_path="news_articles.db"):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # enables dict-like access
    cursor = conn.cursor()

    query = """
        SELECT q.* FROM (
        SELECT source, url, comment, scraped_at
        FROM articles
        WHERE relevant = 1
        ORDER BY scraped_at DESC
        LIMIT 50) q
        ORDER BY q.scraped_at ASC
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
        print("-" * 80)
