from bs4 import BeautifulSoup
import requests
from collections import defaultdict
import urllib.parse
import sys
import spacy
import json

def parse_url(url) -> str:
    return str(urllib.parse.urlparse(url).geturl())

def get_base(url):
    parsed = urllib.parse.urlparse(url)
    return f'{parsed.scheme}://{parsed.netloc}'

def get_noun_phrases(doc):
    for chunk in doc.noun_chunks:
        phrase = chunk.text

        if ' and ' in phrase:
            subphrases = phrase.split(' and ')
            for subphrase in subphrases:
                yield subphrase
        else:
            yield phrase

def skip(child):

    if child == None:
        return True
    elif child == '':
        return True
    elif child.endswith('.pdf'):
        return True
    elif '#' in child:
        return True
    else:
        return False

def normalize_url(child, parent):

    if not child.startswith('http://') and not child.startswith('https://'): # subpage
        child = urllib.parse.urljoin(parent, child)
        
    return parse_url(child)

start = parse_url(sys.argv[1])

nlp = spacy.load("en_core_web_sm")

keywords = defaultdict(list)

visited = set()
queue = [start]

while queue:

    parent = queue.pop(0)
    visited.add(parent)

    print('\n', parent, sep='')

    try:
        response = requests.get(parent)
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception:
        continue

    paragraphs = soup.find_all('p')
    page_text = '. '.join([str.lower(p.text) for p in paragraphs])

    page_doc = nlp(page_text)

    for i, phrase in enumerate(get_noun_phrases(page_doc)):
        if phrase not in keywords[parent]:
            keywords[parent].append(phrase)

    print(f'\t{len(keywords[parent])} keywords')

    links = soup.find_all('a')

    children = []
    for link in links:
        child = link.get('href')

        if skip(child):
            continue

        normalized_child = normalize_url(child, parent)
        if get_base(normalized_child) == get_base(parent):
            children.append(normalized_child)

    print(f'\t{len(children)} children')
    for child in children:
        if child not in visited and child not in queue:
            queue.append(child)

    print(f'\t{len(visited)} visited')
    print(f'\t{len(queue)} queued')

print('Writing to keywords.json')
with open('keywords.json', 'w') as file:
    json.dump(keywords, file)