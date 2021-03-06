#!/usr/bin/env python3

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
        make_corpus()

    with open('corpus.txt', 'r', encoding='utf-8') as file:
        corpustxt = file.read()

    text_model = markovify.Text(corpustxt)
    with open('sentences.txt', 'w', encoding='utf-8') as sents:
        for i in range(100):
            print(text_model.make_sentence(), file=sents)

    with open('short_sentences.txt', 'w', encoding='utf-8') as short_sents:
        for i in range(100):
            print(text_model.make_short_sentence(140), file=short_sents)

def make_corpus():
    corpus = scrape()
    assert(len(corpus) == 141)
    corpustxt = '\n\n\n'.join(corpus)
    with open('corpus.txt', 'w', encoding='utf-8') as file:
        file.write(corpustxt)

def scrape():
    # scrape corpus from apstudynotes

    url = 'http://web.archive.org/web/20160207232714/www.apstudynotes.org/essays' # earliest snapshot from 2016
    # For some reason aiohttp does not work with web.archive.org, use requests instead
    html = requests.get(url).text

    bs = bs4.BeautifulSoup(html, 'html.parser')
    pattern = '.entry .heading h3 a'
    anchors = bs.select(pattern)
    page_urls = [urljoin(url, a['href']) for a in anchors]

    return [scrape_page(pg) for pg in page_urls]

def scrape_page(url):
    try:
        html = requests.get(url).text
        bs = bs4.BeautifulSoup(html, 'html.parser')
        pattern = '.body p'
        paras = bs.select(pattern)
        texts = [p.text for p in paras]
        return '\n\n'.join(texts)
    except RequestException:
        traceback.print_exc()
        return scrape_page(url)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
