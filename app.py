#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify
import json
from bs4 import BeautifulSoup
import requests
from datetime import date
import feedparser


# Article Klasse die die zu scrapenden Daten speichert
class Article:
    def __init__(self, headline, link, text_body, source, source_name, author, topic, crawl_date, creation_date):
        self.headline = headline
        self.link = link
        self.text_body = text_body
        self.source = source
        self.source_name = source_name
        self.author = author
        self.topic = topic
        self.crawl_date = crawl_date
        self.creation_date = creation_date

    # Helfer Methode die es später ermöglicht einen JSON String zu erstellen
    # siehe return von 'def get_articles()'
    def serialize(self):
        return {
            'headline': self.headline,
            'textBody': self.text_body,
            'source': self.source,
            'source_name': self.source_name,
            'author': self.author,
            'topic': self.topic,
            'link': self.link,
            'crawl_date': self.crawl_date,
            'creation_date': self.creation_date,
        }


# Sucht sich die eine Liste mit allen Artikel links zusammen
# fetch from RSS feed
def get_news_links(url):
    rss = requests.get(url).content
    doc = feedparser.parse(rss)
    link_data = []

    if "naszdziennik.pl/" in url:
        for entry in doc['entries']:
            link_data.append({ 'link': entry['link'] })
            
    elif "blaetter.de/" in url:
        print(doc)
        for entry in doc['entries']:
            print(entry)
            # sämtliche Übersichtsseiten herausfiltern
            non_articles_url_contains = [ "/dossiers/", '/kurzgefasst', '/chronik-des-monats' ]
            link = entry['link']
            if not any(x in link for x in non_articles_url_contains):
                link_data.append({'link': link, 'creation_date': entry['published']})

    return link_data


# Extrahiert alle notwendigen informationen von einem einzigen Artikel
def scrape(link, _creation_date = ''):

    soup = BeautifulSoup(requests.get(link).content, 'html.parser')
    [s.extract() for s in soup('script')]  # entfernt alle script tags

    source_url = ''
    source_name = ''
    headline = ''
    topic = ''
    author = ''
    text_body = ''
    creation_date = ''

    if "naszdziennik.pl/" in link:
        
        source_url = "https://naszdziennik.pl/"
        source_name = "Nasz Dziennik"

        # HEADLINE
        headline = soup.find('h1').string

        # TOPIC
        if soup.find(id='nav').find('a', class_='current'):
            topic = soup.find(id='nav').find('a', class_='current').string

        # AUTHOR
        if soup.find(id='article-author'):
            author = soup.find(id='article-author').string

        # TEXT_BODY
        subtitle = soup.find(id='article-subtitle').get_text()
        body = soup.find(id='article-content').get_text()
        text_body = subtitle + '\n' + body

        # CREATION_DATE
        if soup.find(id='article-date'):
            creation_date = soup.find(id='article-date').string
            creation_date = ' '.join(creation_date.split())
        
    elif "blaetter.de/" in link:
        source_url = "https://blaetter.de/"
        source_name = "Blätter für deutsche und internationale Politik"
        
        # HEADLINE
        headline = soup.find('h1', class_='heading--article').find('span').string

        # TOPIC
        if soup.findAll('div', class_='articleinfo'):
            for a in soup.findAll('div', class_='articleinfo'):
                if 'author--article' not in a.attrs['class']:
                    for t in a.findAll('a'):
                        topic += t.string + ' '

        # AUTHOR
        if soup.find('div', class_='author--article'):
            author = soup.find('div', class_='author--article').find('a').string

        # TEXT_BODY
        text_body = soup.find('div', class_='field--type-text-with-summary').getText()

        # CREATION_DATE
        creation_date = _creation_date

    return Article(headline, link, text_body, source_url, source_name, author, topic, date.today(), creation_date)


# ************************* Flask web app *************************  #


app = Flask(__name__)


# Hier wird der Pfad(route) angegeben der den scraper arbeiten lässt.
# In dem Fall ist die URL "localhost:5000/pikio"
@app.route('/blaetter')
def get_articles_blaetter():
    link_data = get_news_links('https://www.blaetter.de/rss.xml')
    articles = []
    for link in link_data:
        print(link['link'])
        articles.append(scrape(link['link'], link['creation_date']))
    return jsonify([e.serialize() for e in articles])


@app.route('/naszdziennik')
def get_articles_nd():
    link_data = get_news_links('https://naszdziennik.pl/articles/rss.xml')
    articles = []
    for link in link_data:
        articles.append(scrape(link['link']))
    return jsonify([e.serialize() for e in articles])


@app.route('/')
def index():
    return "<h1>Hier passiert nichts.</h1>"


# Web Application wird gestartet
if __name__ == '__main__':
    app.run()
