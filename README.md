# scholarbot

Are you a high school student hoping to impress college admissions offices? Have no fear, ScholarBot is here! Simply run the program and it will say fancy things like

```
Trials were held closely by the unyielding razor of reality.
With esteemed programs like Stanford Technology Ventures and the smell of India, that raw, intimate stench of human flesh.
```

which are sure to get you into the college of your dreams.

## Running

Requirements: Python 3 (latest), Git

```
<clone the repo>
pip install -U requirements.txt
python ./main.py
```

---

## Explanation

The code uses a [Markov chain](https://en.wikipedia.org/wiki/Markov_chain) to generate random samples of the text. The implementation of the chain is provided by https://github.com/jsvine/markovify

The corpus used for the model is 141 essays sourced from http://web.archive.org/web/20160207232714/www.apstudynotes.org/essays. Please note, running this program may be a legal gray area since these essays are normally under a paywall; I was able to obtain them by scraping an old version of apstudynotes.org that did not remove the paywalled text from the HTML.
