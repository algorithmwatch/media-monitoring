import sqlite3
import time, json
from seleniumbase import SB
from datetime import datetime

class NewsArticleScraper:
    def __init__(self, db_name='articles.db'):
        self.db_name = db_name
        self.setup_database()
        
    def setup_database(self):
        """Create SQLite database and articles table"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                description TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        
    def accept_cookies(self, sb):
        """Try common cookie acceptance patterns"""
        cookie_selectors = [
            "button:contains('Accept')",
            "button:contains('Accetto')",
            "button:contains('Souhlasím')",
            "button:contains('Prihvaćam')",
            "button:contains('Agree')",
            "button:contains('Consent')",
            "#didomi-notice-agree-button",
            "button[class*='accept']",
            "button[class*='consent']",
            "a:contains('Souhlasím')",
        ]
        
        for selector in cookie_selectors:
            try:
                if sb.is_element_visible(selector, timeout=5):
                    sb.click(selector)
                    print("✓ Cookies accepted")
                    time.sleep(1)
                    return True
            except Exception:
                continue
        
        print("⚠ No cookie banner found or already accepted")
        return False

    def scrape(self, sb, media):
        print(f"\n📰 Scraping {media["name"]}...")
        sb.open(media["url"])
        time.sleep(2)
        self.accept_cookies(sb)
        
        articles = []
        # Wait for articles to load
        sb.wait_for_element(media["el_to_wait_for"], timeout=10)
        
        # Use sb.find_elements directly (not on elem)
        article_elements = sb.find_elements(media["el_article"])
        
        if not article_elements:
            print("  No articles found")
            return articles
        
        for article in article_elements:

            link_elem = article.query_selector(media["el_link"])

            try:
                article_url = link_elem.get_attribute('href')
            except:
                article_url = ""
            
            try:
                title = article.query_selector(media["el_title"]).text
            except:
                title = ""
            
            try:
                description = article.query_selector(media["el_desc"]).text
            except:
                description = ""

            # Removes everything coming after a ? in the URL
            # Prevents duplicates especially for Le Monde
            article_url = article_url.split('?', 1)[-1]

            if not article_url.startswith("http"):
                article_url = media["base_url"] + article_url
            
            if article_url and title:
                articles.append({
                    'source': media["name"],
                    'url': article_url,
                    'title': title,
                    'description': description
                })
                        
        print(f"  Found {len(articles)} articles")

        self.save_to_database(articles)

        return articles
    
    def save_to_database(self, articles):
        """Save articles to SQLite database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        added = 0
        skipped = 0
        
        for article in articles:
            try:
                cursor.execute('''
                    INSERT INTO articles (source, url, title, description)
                    VALUES (?, ?, ?, ?)
                ''', (article['source'], article['url'], article['title'], article['description']))
                added += 1
            except sqlite3.IntegrityError:
                skipped += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n💾 Database: {added} added, {skipped} skipped (duplicates)")
        
    def scrape_all(self):
        """Scrape all configured news sources"""

        with open('sources.json') as json_data:
            news_sources = json.load(json_data)
            json_data.close()
        
        with SB(uc=True, headless=False) as sb:
            all_articles = []
            
            for media in news_sources: 
                try:
                    articles = self.scrape(sb, media)
                except Exception:
                    print(f"Could not scrape {media["name"]}")
                    continue
                all_articles.extend(articles)
                time.sleep(2)

# Example usage
if __name__ == "__main__":
    scraper = NewsArticleScraper('news_articles.db')
    scraper.scrape_all()
    
    # Query and display results
    conn = sqlite3.connect('news_articles.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles")
    count = cursor.fetchone()[0]
    print(f"\n📊 Total articles in database: {count}")
    
    cursor.execute("SELECT source, COUNT(*) FROM articles GROUP BY source")
    for source, cnt in cursor.fetchall():
        print(f"  {source}: {cnt} articles")
    
    conn.close()