#!/usr/bin/env python3

import aiohttp
from aiohttp.client_exceptions import ClientError
import asyncio
import bs4
from itertools import count
import json
import logging
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
    
    if not os.path.exists('corpus.json'):
        log.debug("corpus.json does not exist")
        urls_to_scrape = await get_page_urls()
    else:
        log.debug("Loading data from corpus.json")
        dic = read_corpus_json()
        urls_to_scrape = urls_with_missing_data(dic)
        log.debug("There are %s urls with missing data", len(urls_to_scrape))

    dic.update(await scrape(urls_to_scrape))
    write_corpus_json(dic)

    if len(urls_with_missing_data(dic)) > 0:
        log.debug("There are still %s urls with missing data, exiting", len(urls_with_missing_data(dic)))
        sys.exit(0)

    write_corpus_txt(dic)

async def get_page_urls():
    if os.path.exists('pageurls.txt'):
        log.debug("Reading page urls from pageurls.txt")
        with open('pageurls.txt', 'r', encoding='utf-8') as file:
            page_urls = file.read().strip().splitlines()
    else:
        log.debug("Collecting page urls from the creepypasta website")
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

        log.debug("Writing page urls to pageurls.txt")
        with open('pageurls.txt', 'w', encoding='utf-8') as file:
            file.write('\n'.join(page_urls))

    log.debug("len(page_urls): %s", len(page_urls))
    return page_urls

def read_corpus_json():
    assert os.path.exists('corpus.json')

    with open('corpus.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def write_corpus_json(dic):
    with open('corpus.json', 'w', encoding='utf-8') as file:
        return json.dump(dic, file, indent=4, sort_keys=True)

def write_corpus_txt(dic):
    # Sort by key, then extract the values
    pairs = dic.items().sorted(key=lambda t: t[0])
    _, values = zip(*pairs)
    corpustxt = '\n\n\n'.join(values)

    with open('corpus.txt', 'w', encoding='utf-8') as file:
        file.write(corpustxt)

def urls_with_missing_data(dic):
    return [url for url, story in dic.items() if len(story) == 0]

async def fetch(session, url):
    log.debug("GET %s", url)
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.get(url, timeout=timeout) as response:
        # response.raise_for_status()
        return await response.text()

async def scrape(page_urls):
    conn = aiohttp.TCPConnector(limit_per_host=10)
    async with aiohttp.ClientSession(connector=conn) as sess:
        lst = await asyncio.gather(*[scrape_page(sess, pg) for pg in page_urls])
        dic = {url: story for url, story in zip(page_urls, lst)}
        return dic

async def scrape_page(sess, url):
    while True:
        try:
            html = await fetch(sess, url)
            bs = bs4.BeautifulSoup(html, 'html.parser')
            pattern = '.clearfix > p'
            paras = bs.select(pattern)
            texts = [transform(p.text) for p in paras if filter(p.text)]
            return '\n\n'.join(texts)
        except (ClientError, asyncio.TimeoutError):
            traceback.print_exc()
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
    log.debug("Sleeping for %ss...", value)
    await asyncio.sleep(value)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
