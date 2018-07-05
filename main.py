#!/usr/bin/env python3

import aiohttp
from aiohttp.client_exceptions import ClientError
import asyncio
import bs4
from itertools import count
import logging
import markovify
import math
import numpy as np
import os
import requests
from requests.exceptions import RequestException
import sys
import traceback
from urllib.parse import urlencode, urljoin

log = logging.getLogger(__name__)

async def main():
    logging.basicConfig(level=logging.DEBUG)

    if not os.path.exists('corpus.txt'):
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
    with open('debug.txt', 'w', encoding='utf-8') as file:
        file.write(repr(corpus))
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
        result = await asyncio.gather(*[scrape_page(sess, pg) for pg in page_urls])
        result = [story for story in result if len(story) > 0]
        return result

async def scrape_page(sess, url):
    while True:
        try:
            html = await fetch(sess, url)
            bs = bs4.BeautifulSoup(html, 'html.parser')
            pattern = '.clearfix > p'
            paras = bs.select(pattern)
            texts = [transform(p.text) for p in paras if filter(p.text)]

            if len(texts) == 0:
                log.debug(f"Did not find text for {url}")
                await random_delay()
                continue
            else:
                return '\n\n'.join(texts)
        except (ClientError, asyncio.TimeoutError) as e:
            traceback.print_exc()
            if isinstance(e, asyncio.TimeoutError):
                log.debug(f"Request to {url} timed out")
                await random_delay()
            continue

def filter(text):
    text = text.lower().strip()
    if len(text) == 0 or text.startswith('[fvplayer') or text.startswith('credit'):
        return False
    return True

def transform(text):
    return text.strip().replace('\xa0', ' ') # \xa0 is the char code for a nbsp

async def random_delay():
    mean = 10
    log_mean = math.log(mean, 2)
    fuzz = np.random.standard_normal(size=1)[0]
    value = int(np.ceil(2 ** (log_mean + fuzz)))
    log.debug(f"Sleeping for {value}s...")
    await asyncio.sleep(value)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
