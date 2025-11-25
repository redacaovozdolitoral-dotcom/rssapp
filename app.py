import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from flask import Flask, Response
import datetime
from dateutil import parser
import os

app = Flask(__name__)

def fetch_news_links(keyword):
    url = f'https://www.bing.com/news/search?q={keyword}&format=rss'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, features='xml')
    items = soup.findAll('item')

    links = []
    agora = datetime.datetime.utcnow()

    for item in items:
        pub_date_text = item.pubDate.text if item.pubDate else None
        if pub_date_text:
            pub_date = parser.parse(pub_date_text).replace(tzinfo=None)
            diff = agora - pub_date
            if diff.total_seconds() > 86400:  # mais que 24h? Ignora
                continue
        link = item.link.text if item.link else None
        if link:
            links.append(link)
        if len(links) >= 10:
            break
    return links

def extract_article_data(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.content, 'html.parser')

    h1 = soup.find('h1')
    if not h1 or not h1.text.strip():
        return None

    img = soup.find('img')
    if not img or not img.get('src'):
        return None

    p = soup.find('p')
    if not p or not p.text.strip():
        return None

    return {
        'title': h1.text.strip(),
        'image': img['src'],
        'paragraph': p.text.strip(),
        'link': url
    }

@app.route('/feed/<keyword>')
def feed(keyword):
    links = fetch_news_links(keyword)
    fg = FeedGenerator()
    fg.title(f'Feed para {keyword}')
    fg.link(href=f'https://{os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost")}/feed/{keyword}', rel='self')
    fg.description(f'Últimas notícias sobre {keyword}')

    added_titles = set()
    now = datetime.datetime.utcnow()

    for link in links:
        try:
            data = extract_article_data(link)
            if not data:
                continue

            if data['title'] in added_titles:
                continue

            fe = fg.add_entry()
            fe.title(data['title'])
            fe.link(href=data['link'])
            fe.description(f'<img src="{data["image"]}" alt="Imagem" /><p>{data["paragraph"]}</p>')
            fe.pubDate(now)

            added_titles.add(data['title'])
        except Exception as e:
            print(f'Erro processando {link}:', e)
            continue

    rssfeed = fg.rss_str(pretty=True)
    return Response(rssfeed, mimetype='application/rss+xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
