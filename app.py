import requests
from feedgen.feed import FeedGenerator
from flask import Flask, Response
import os

app = Flask(__name__)

GNEWS_KEY = "d9f2349f23a0845fe466b2a959376e2f"  # Cole sua API Key do GNews.io aqui!

def fetch_gnews_items(keyword):
    # Busca notícias em português do Brasil, máximo 10 por consulta
    url = f'https://gnews.io/api/v4/search?q={keyword}&lang=pt&country=br&max=10&apikey={GNEWS_KEY}'
    response = requests.get(url)
    articles = response.json().get("articles", [])
    news = []
    for art in articles:
        # Garante que só entram notícias com imagem, título e descrição
        if art.get("title") and art.get("description") and art.get("image"):
            news.append({
                'title': art["title"],
                'description': art["description"],
                'link': art["url"],
                'image': art["image"],
                'pub_date': art["publishedAt"]
            })
    return news

@app.route('/feed/gnews/<keyword>')
def feed_gnews(keyword):
    news_items = fetch_gnews_items(keyword)
    fg = FeedGenerator()
    fg.title(f'GNews: {keyword}')
    fg.link(href=f'https://{os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost")}/feed/gnews/{keyword}', rel='self')
    fg.description(f'Últimas notícias do GNews sobre {keyword}')
    for data in news_items:
        fe = fg.add_entry()
        fe.title(data['title'])
        fe.link(href=data['link'])
        fe.description(data['description'])
        fe.enclosure(url=data['image'], type="image/jpeg", length=0)
        fe.pubDate(data['pub_date'])
    rssfeed = fg.rss_str(pretty=True)
    return Response(rssfeed, mimetype='application/rss+xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
