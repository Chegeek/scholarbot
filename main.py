#!/usr/bin/env python3

import aiohttp
import asyncio
import bs4
from urllib.parse import urljoin

async def main():
    corpus = await scrape()
    print(len(corpus))
    print(corpus[1])

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def scrape():
    # scrape corpus from apstudynotes

    url = 'https://www.apstudynotes.org/essays/'
    async with aiohttp.ClientSession() as sess:
        html = await fetch(sess, url)

        bs = bs4.BeautifulSoup(html, 'html.parser')
        pattern = '.entry .heading h3 a'
        anchors = bs.select(pattern)
        page_urls = [urljoin(url, a['href']) for a in anchors]

        return await asyncio.gather(*[scrape_page(sess, pg) for pg in page_urls])

async def scrape_page(sess, url):
    html = await fetch(sess, url)
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
