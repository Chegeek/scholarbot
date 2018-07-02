#!/usr/bin/env python3

import asyncio
import bs4
import requests
from urllib.parse import urljoin

async def main():
    corpus = scrape()
    print(len(corpus))
    print(corpus[1])

def scrape():
    # scrape corpus from apstudynotes

    url = 'http://web.archive.org/web/20160207232714/www.apstudynotes.org/essays'
    # For some reason aiohttp does not work with web.archive.org, use requests instead
    html = requests.get(url).text

    bs = bs4.BeautifulSoup(html, 'html.parser')
    pattern = '.entry .heading h3 a'
    anchors = bs.select(pattern)
    page_urls = [urljoin(url, a['href']) for a in anchors]

    return [scrape_page(pg) for pg in page_urls]

def scrape_page(url):
    html = requests.get(url).text
    bs = bs4.BeautifulSoup(html, 'html.parser')
    pattern = '.body p'
    paras = bs.select(pattern)
    texts = [p.text for p in paras]
    return '\n\n'.join(texts)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
