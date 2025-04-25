import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from recipescraper.recipescraper.spiders.recipespider import RecipeSpider
import psycopg2
import os
import time
import re
import json
from functools import wraps
from flask import Flask, render_template, session, request, redirect, flash
from flask_session import Session
from psycopg2.extras import DictCursor
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from scrapy.utils.project import get_project_settings
import threading

DATABASE_URL = os.environ.get("DATABASE_URL")

def login_required(f):
    """" 
    Decorates routes that need a log in.     
    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# Global runner and reactor state
crawler_thread_started = False
from scrapy.settings import Settings


runner = CrawlerRunner(Settings({
    'ITEM_PIPELINES': {
        __name__ + '.ItemCollectorPipeline': 1
    }
}))


def start_crawler_reactor():
    """Starts the Twisted reactor in a background thread if not already running."""
    if not reactor.running:
        threading.Thread(target=reactor.run, kwargs={'installSignalHandlers': False}, daemon=True).start()


class ItemCollectorPipeline:
    results = []  # Class-level list to store results

    def process_item(self, item, spider):
        print("PIPELINE GOT ITEM:", item)
        ItemCollectorPipeline.results.append(item)
        return item



def run_spider(url):
    """Runs the Scrapy spider using the global runner and reactor."""
    start_crawler_reactor()
    ItemCollectorPipeline.results = []  # Reset
    deferred = runner.crawl(RecipeSpider, recipe_url=url)
    print(f"Running spider for URL: {url}")
    print(f"{deferred}")
    deferred.addCallback(process_spider_output)
    deferred.addErrback(handle_scraping_error)

def start_crawler():
    process.start() 

def get_db():
    conn = psycopg2.connect(DATABASE_URL)  
    return conn

def scrape_and_store(url):
    print(f"Starting scrape for: {url}")
    run_spider(url)

def get_scraped_items():
    return ItemCollectorPipeline.results

def process_spider_output(_):
    results = get_scraped_items()
    if results:
        print(f"Scraped data: {results}")
        store_recipe(results[0])
    else:
        print("No recipe data scraped.")

def handle_scraping_error(failure):
    print(f"Scraping failed: {failure.getErrorMessage()}")


def store_recipe(recipe_data):
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        title_slug = slugify(recipe_data[0].get('title', 'untitled'))
        cursor.execute('''
            INSERT INTO recipes (url, title, slug, ingredients, instructions, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (recipe_data[0].get('source_url'), recipe_data[0].get('title'), title_slug, json.dumps(recipe_data[0].get('ingredients')), json.dumps(recipe_data[0].get('instructions')), session.get("user_id")))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error in store_recipe: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_recipe_from_storage(recipe_slug):
    conn = None
    cursor = None
    recipe_data = None
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute('''SELECT title, ingredients, instructions, url FROM recipes WHERE slug = %s''', (recipe_slug,))
        result = cursor.fetchone()
        if result:
            return {
                'title': result[0],
                'ingredients': json.loads(result[1]),
                'instructions': json.loads(result[2]),
                'url': result[3]
            }
    except psycopg2.Error as e:
        print(f"Database error in fetch_recipe_from_storage: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return recipe_data


def slugify(title):
    """Converts a title into a URL-safe slug."""
    title = title.lower().strip()
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[-\s]+', '-', title)
    return title

