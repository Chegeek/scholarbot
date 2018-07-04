#!/usr/bin/env python3

import aiohttp
from aiohttp.client_exceptions import ClientError
import asyncio
import bs4
import logging
import markovify
import os
import requests
from requests.exceptions import RequestException
import traceback
from urllib.parse import urljoin

log = logging.getLogger(__name__)

async def main():
    logging.basicConfig(level=logging.DEBUG)

    if not os.path.isfile('corpus.txt'):
        await make_corpus()

    with open('corpus.txt', 'r', encoding='utf-8') as file:
        corpustxt = file.read()

    text_model = markovify.Text(corpustxt)
    with open('sentences.txt', 'w', encoding='utf-8') as sents:
        for i in range(100):
            print(text_model.make_sentence(), file=sents)

    with open('short_sentences.txt', 'w', encoding='utf-8') as short_sents:
        for i in range(100):
            print(text_model.make_short_sentence(140), file=short_sents)

async def make_corpus():
    corpus = await scrape()
    corpustxt = '\n\n\n'.join(corpus)
    with open('corpus.txt', 'w', encoding='utf-8') as file:
        file.write(corpustxt)

async def fetch(session, url):
    log.debug(f"GET {url}")
    async with session.get(url) as response:
        return await response.text()

async def scrape():
    # scrape corpus from apstudynotes

    url = 'http://www.creepypasta.org/creepypasta'
    async with aiohttp.ClientSession() as sess:
        html = await fetch(sess, url)

        bs = bs4.BeautifulSoup(html, 'html.parser')
        pattern = '.creepypasta-list a'
        anchors = bs.select(pattern)
        page_urls = [urljoin(url, a['href']) for a in anchors]

        return await asyncio.gather(*[scrape_page(sess, pg) for pg in page_urls])

async def scrape_page(sess, url):
    while True:
        try:
            html = await fetch(sess, url)
            bs = bs4.BeautifulSoup(html, 'html.parser')
            pattern = '.entry-content p'
            paras = bs.select(pattern)
            texts = [p.text for p in paras]
            return '\n\n'.join(texts)
        except ClientError:
            continue

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
