import feedparser
from newspaper import Article
from feedgen.feed import FeedGenerator
from flask import Flask, Response
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

def scrape_news_from_google():
    keyword = "litoral+norte+de+sao+paulo"
    rss_url = f'https://news.google.com/rss/search?q={keyword}&hl=pt-BR&gl=BR&ceid=BR:pt-419'
    parsed_feed = feedparser.parse(rss_url)
    news_list = []
    now = datetime.now(timezone.utc)
    for entry in parsed_feed.entries:
        pub_date = entry.get('published_parsed')
        if pub_date:
            entry_time = datetime(*pub_date[:6], tzinfo=timezone.utc)
            if (now - entry_time).total_seconds() > 86400:
                continue  # só notícias das últimas 24h
        url = entry.get('link')
        try:
            article = Article(url, language='pt')
            article.download()
            article.parse()
            title = article.title or entry.get('title')
            lead = article.text[:300] + "..." if article.text else entry.get('summary')
            image = article.top_image if article.top_image else None
            news_list.append({
                'title': title,
                'description': lead,
                'link': url,
                'image': image,
                'pub_date': entry.get('published')
            })
            if len(news_list) >= 10:
                break
        except Exception as e:
            continue  # ignora erros de scraping
    return news_list

@app.route('/feed/google_scrape/litoral+norte+de+sao+paulo')
def custom_feed():
    news_items = scrape_news_from_google()
    fg = FeedGenerator()
    fg.title('Google News Scrape: litoral norte de são paulo')
    fg.link(href='https://rssapp-8wwg.onrender.com/feed/google_scrape/litoral+norte+de+sao+paulo', rel='self')
    fg.description('Notícias filtradas e raspadas do Google sobre litoral norte de São Paulo (últimas 24h)')
    for data in news_items:
        fe = fg.add_entry()
        fe.title(data['title'])
        fe.link(href=data['link'])
        fe.guid(data['link'])
        fe.description(data['description'])
        if data["image"]:
            fe.enclosure(url=data["image"], type="image/jpeg", length=0)
        fe.pubDate(data['pub_date'])
    rssfeed = fg.rss_str(pretty=True)
    return Response(rssfeed, mimetype='application/rss+xml')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
