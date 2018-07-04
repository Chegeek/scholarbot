#!/usr/bin/env python3

import aiohttp
from aiohttp.client_exceptions import ClientError
import asyncio
import bs4
from itertools import count
import logging
import markovify
import os
import requests
from requests.exceptions import RequestException
import sys
import traceback
from urllib.parse import urlencode, urljoin

log = logging.getLogger(__name__)

async def main():
    logging.basicConfig(level=logging.DEBUG)

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
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(url, timeout=timeout) as response:
        return await response.text()

async def scrape():
    # scrape corpus from apstudynotes

    if os.path.exists('pageurls.txt'):
        log.debug("Reading page_urls from pageurls.txt")
        with open('pageurls.txt', 'r', encoding='utf-8') as file:
            page_urls = file.read().strip().splitlines()
    else:
        log.debug("Collecting page_urls")
        page_urls = []

        async with aiohttp.ClientSession() as sess:
            baseurl = 'https://www.creepypasta.com/pastas-indexed-category/'
            for i in count(1, 1):
                params = {f'lcp_page{j}': i for j in range(1, 8)}
                url = f'{baseurl}?{urlencode(params)}'
                html = await fetch(sess, url)

                bs = bs4.BeautifulSoup(html, 'html.parser')
                pattern = '.lcp_catlist li a'
                anchors = bs.select(pattern)
                if len(anchors) == 0:
                    break

                page_urls.extend([urljoin(url, a['href']) for a in anchors])

        log.debug("Writing page_urls to pageurls.txt")
        with open('pageurls.txt', 'w', encoding='utf-8') as file:
            file.write('\n'.join(page_urls))

    log.debug(f"len(page_urls): {len(page_urls)}")
    async with aiohttp.ClientSession() as sess:
        return await asyncio.gather(*[scrape_page(sess, pg) for pg in page_urls])

async def scrape_page(sess, url):
    while True:
        try:
            html = await fetch(sess, url)
            bs = bs4.BeautifulSoup(html, 'html.parser')
            pattern = '.single-content p'
            paras = bs.select(pattern)
            texts = [p.text for p in paras]
            return '\n\n'.join(texts)
        except (ClientError, asyncio.TimeoutError):
            traceback.print_exc()
            continue

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
