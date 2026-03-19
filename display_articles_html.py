import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, render_template_string, g
import os

app = Flask(__name__)
DB_PATH = "news_articles.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_display_title(article):
    if article['lang'] in ('fr', 'en', 'de'):
        return article['title']
    return article['title_en'] or article['title']

def country_to_flag_html(country_code):
    """Return an <img> tag using flagcdn.com for reliable cross-browser display."""
    if not country_code:
        return '<span class="flag-fallback">?</span>'
    code = country_code.strip().lower()
    return (
        f'<img class="flag-img" '
        f'src="https://flagcdn.com/24x18/{code}.png" '
        f'srcset="https://flagcdn.com/48x36/{code}.png 2x" '
        f'alt="{country_code.upper()}" '
        f'title="{country_code.upper()}">'
    )

def relevance_to_color(relevance):
    """Interpolate from light gray (0) to orange (100)."""
    r = max(0, min(100, relevance or 0)) / 100.0
    # Gray: (220, 220, 220) → Orange: (255, 140, 0)
    red   = int(220 + (255 - 220) * r)
    green = int(220 + (140 - 220) * r)
    blue  = int(220 + (  0 - 220) * r)
    # Text: dark for light bg, light for dark bg
    luminance = 0.299 * red + 0.587 * green + 0.114 * blue
    text_color = "#1a1a1a" if luminance > 140 else "#f5f5f5"
    source_color = "#555555" if luminance > 140 else "#cccccc"
    return f"rgb({red},{green},{blue})", text_color, source_color

@app.route("/")
def index():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM articles WHERE DATE(scraped_at) = CURRENT_DATE ORDER BY scraped_at DESC"
    ).fetchall()

    # Group by cluster_id — keep highest relevance as primary
    cluster_map = defaultdict(list)
    no_cluster = []
    for row in rows:
        d = dict(row)
        d['display_title'] = get_display_title(d)
        d['flag'] = country_to_flag_html(d.get('country'))
        bg, tc, sc = relevance_to_color(d.get('relevance', 0))
        d['bg_color'] = bg
        d['text_color'] = tc
        d['source_color'] = sc
        if d.get('cluster_id') != -1:
            cluster_map[d['cluster_id']].append(d)
        else:
            no_cluster.append(d)

    # For each cluster pick the best article
    processed = list(no_cluster)
    for cid, articles in cluster_map.items():
        articles.sort(key=lambda a: a.get('relevance') or 0, reverse=True)
        primary = articles[0]
        primary['cluster_siblings'] = articles[1:]
        processed.append(primary)

    # Group by date
    by_day = defaultdict(list)
    for art in processed:
        try:
            day = datetime.strptime(art['scraped_at'][:10], "%Y-%m-%d").strftime("%A, %B %-d %Y")
        except Exception:
            day = art['scraped_at'][:10]
        by_day[day].append(art)

    # Sort days descending
    def day_sort_key(day_str):
        try:
            return datetime.strptime(day_str, "%A, %B %d %Y")
        except Exception:
            return datetime.min

    sorted_days = sorted(by_day.keys(), key=day_sort_key, reverse=True)

    # Sort articles within each day by relevance desc
    for day in sorted_days:
        by_day[day].sort(key=lambda a: a.get('relevance') or 0, reverse=True)

    return render_template_string(TEMPLATE, by_day=by_day, sorted_days=sorted_days)


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>News Feed</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f0f2f5;
    color: #1a1a1a;
    padding: 24px 16px;
  }

  .day-section {
    max-width: 1000px;
    margin: 0 auto 36px auto;
  }

  .day-title {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #888;
    padding: 0 0 8px 4px;
    border-bottom: 1px solid #ddd;
    margin-bottom: 8px;
  }

  .article-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 6px;
    margin-bottom: 4px;
    width: 100%;
    position: relative;
    transition: filter 0.15s;
  }

  .article-row:hover { filter: brightness(0.96); }

  .flag {
    font-size: 1.35rem;
    flex-shrink: 0;
    line-height: 1;
    width: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .flag-img {
    display: block;
    width: 24px;
    height: 18px;
    object-fit: contain;
    border-radius: 2px;
  }

  .flag-fallback {
    font-size: 0.75rem;
    color: #999;
  }

  .article-meta {
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: baseline;
    gap: 10px;
    flex-wrap: wrap;
  }

  .source {
    font-size: 0.75rem;
    font-weight: 500;
    flex-shrink: 0;
    white-space: nowrap;
  }

  .article-title a {
    font-size: 0.9rem;
    font-weight: 600;
    text-decoration: none;
    word-break: break-word;
  }

  .article-title a:hover { text-decoration: underline; }

  .relevance {
    font-size: 0.72rem;
    font-weight: 700;
    opacity: 0.75;
    flex-shrink: 0;
    margin-left: auto;
    white-space: nowrap;
  }

  .toggle-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    padding: 0 0 0 10px;
    flex-shrink: 0;
    opacity: 0.6;
    transition: opacity 0.15s, transform 0.2s;
    line-height: 1;
  }

  .toggle-btn:hover { opacity: 1; }
  .toggle-btn.open { transform: rotate(180deg); }

  .siblings {
    max-width: 1000px;
    margin: 0 auto;
    display: none;
    padding-left: 20px;
    margin-bottom: 4px;
  }

  .siblings.visible { display: block; }

  .sibling-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 7px 14px;
    border-radius: 6px;
    margin-bottom: 3px;
    opacity: 0.88;
  }
</style>
</head>
<body>

{% for day in sorted_days %}
<div class="day-section">
  <div class="day-title">{{ day }}</div>

  {% for art in by_day[day] %}
  {% set has_siblings = art.cluster_siblings is defined and art.cluster_siblings|length > 0 %}
  {% set row_id = "row-" ~ loop.index ~ "-" ~ day|replace(" ", "") %}

  <div class="article-row"
       style="background:{{ art.bg_color }}; color:{{ art.text_color }};">
    <span class="flag">{{ art.flag | safe }}</span>
    <div class="article-meta">
      <span class="source" style="color:{{ art.source_color }};">{{ art.source }}</span>
      <span class="article-title">
        <a href="{{ art.url }}" target="_blank" rel="noopener"
           style="color:{{ art.text_color }};">{{ art.display_title }}</a>
      </span>
    </div>
    <span class="relevance">{{ art.relevance }}</span>
    {% if has_siblings %}
    <button class="toggle-btn"
            style="color:{{ art.text_color }};"
            onclick="toggleSiblings('{{ row_id }}', this)"
            title="Show {{ art.cluster_siblings|length }} more article(s) in this cluster">▼</button>
    {% endif %}
  </div>

  {% if has_siblings %}
  <div class="siblings" id="{{ row_id }}">
    {% for sib in art.cluster_siblings %}
    <div class="sibling-row"
         style="background:{{ sib.bg_color }}; color:{{ sib.text_color }};">
      <span class="flag">{{ sib.flag | safe }}</span>
      <div class="article-meta">
        <span class="source" style="color:{{ sib.source_color }};">{{ sib.source }}</span>
        <span class="article-title">
          <a href="{{ sib.url }}" target="_blank" rel="noopener"
             style="color:{{ sib.text_color }};">{{ sib.display_title }}</a>
        </span>
      </div>
      <span class="relevance">{{ sib.relevance }}</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% endfor %}
</div>
{% endfor %}

{% if not sorted_days %}
<div style="max-width:1000px;margin:60px auto;text-align:center;color:#999;">
  No articles found in the past 5 days.
</div>
{% endif %}

<script>
function toggleSiblings(id, btn) {
  const el = document.getElementById(id);
  const open = el.classList.toggle('visible');
  btn.classList.toggle('open', open);
}
</script>
</body>
</html>"""

if __name__ == "__main__":
    print("Starting server on http://localhost:5000")
    print(f"Using database: {DB_PATH}")
    print("Set DB_PATH env var to point to your SQLite file.")
    app.run(debug=True, port=5000)
