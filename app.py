import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from flask import Flask, Response
import datetime
from dateutil import parser
import os

app = Flask(__name__)

def fetch_news_items(keyword):
    url = f'https://www.bing.com/news/search?q={keyword}&format=rss'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, features='xml')
    items = soup.findAll('item')

    news = []
    agora = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

    for item in items:
        pub_date_text = item.pubDate.text if item.pubDate else None
        if pub_date_text:
            pub_date = parser.parse(pub_date_text)
            if not pub_date.tzinfo:
                pub_date = pub_date.replace(tzinfo=datetime.timezone.utc)
            diff = agora - pub_date
            if diff.total_seconds() > 86400:
                continue
        title = item.title.text if item.title else None
        description = item.description.text if item.description else None
        link = item.link.text if item.link else None

        enclosure = item.find('enclosure')
        image = enclosure['url'] if enclosure and enclosure.has_attr('url') else None

        if title and description:
            news.append({
                'title': title,
                'image': image,
                'description': description,
                'link': link,
                'pub_date': pub_date_text or agora.isoformat()
            })
        if len(news) >= 10:
            break
    return news

@app.route('/feed/<keyword>')
def feed(keyword):
    news_items = fetch_news_items(keyword)
    fg = FeedGenerator()
    fg.title(f'Feed para {keyword}')
    fg.link(href=f'https://{os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost")}/feed/{keyword}', rel='self')
    fg.description(f'Últimas notícias sobre {keyword}')

    for data in news_items:
        fe = fg.add_entry()
        fe.title(data['title'])
        fe.link(href=data['link'])
        fe.description(data['description'])
        if data["image"]:
            fe.enclosure(url=data["image"], type="image/jpeg", length=0)
        fe.pubDate(data['pub_date'])

    rssfeed = fg.rss_str(pretty=True)
    return Response(rssfeed, mimetype='application/rss+xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
