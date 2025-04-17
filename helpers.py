import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from recipescraper.recipescraper.spiders.recipespider import RecipeSpider
import sqlite3 as sql
import time
import re
import json
from functools import wraps
from flask import Flask, render_template, session, request, redirect, flash
from flask_session import Session



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

class ItemCollectorPipeline:
    results = []  # Class-level list to store results

    def process_item(self, item, spider):
        print("PIPELINE GOT ITEM:", item)
        ItemCollectorPipeline.results.append(item)
        return item

def run_spider(url):
    settings = Settings()
    print(f"NOW RUNNING SPIDER FOR URL: {url}")
    crawler_process = CrawlerProcess(settings)
    ItemCollectorPipeline.results = []  # Reset results for each run

    settings.set('ITEM_PIPELINES', {__name__ + '.ItemCollectorPipeline': 1})
    crawler_process.crawl(RecipeSpider, recipe_url=url)
    crawler_process.start()  # This blocks until the crawl is finished
    crawler_process.stop()
    print("SPIDER FINISHED")
    return ItemCollectorPipeline.results

def store_recipe(recipe_data):
    conn = sql.connect('users.db')  # Connect to the recipes database
    cursor = conn.cursor()
    title_slug = slugify(recipe_data[0].get('title', 'untitled'))
    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS recipes (
    #         slug TEXT UNIQUE,
    #         url TEXT PRIMARY KEY,
    #         title TEXT,
    #         ingredients TEXT, --Store as JSON String
    #         instructions TEXT, --Store as JSON String
    #         user_id INTEGER,
    #         FOREIGN KEY (user_id) REFERENCES users(user_id)
    # )
    # ''')
    cursor.execute('''
    INSERT OR REPLACE INTO recipes (url, title, slug, ingredients, instructions, user_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (recipe_data[0].get('source_url'), recipe_data[0].get('title'), title_slug, json.dumps(recipe_data[0].get('ingredients')), json.dumps(recipe_data[0].get('instructions')), session.get("user_id")))
    conn.commit()
    conn.close()


def fetch_recipe_from_storage(recipe_slug):
    conn = sql.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT title, ingredients, instructions, url FROM recipes WHERE slug = ?''', (recipe_slug,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'title': result[0],
            'ingredients': json.loads(result[1]),
            'instructions': json.loads(result[2]),
            'url': result[3]
        }
    return None


def slugify(title):
    """Converts a title into a URL-safe slug."""
    title = title.lower().strip()
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[-\s]+', '-', title)
    return title