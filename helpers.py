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
from recipe_scrapers import scrape_me
import requests
from recipe_scrapers import scrape_html

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




def get_db():
    conn = psycopg2.connect(DATABASE_URL)  
    return conn

def process_instructions(instructions):
    ''' Clean and put instructions into a list '''
    instructions = instructions.split("\n")
    instructions = [line.strip() for line in instructions]
    return instructions

def store_recipe(recipe_data):
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        title_slug = slugify(recipe_data.title())
        cursor.execute('''
            INSERT INTO recipes (url, title, slug, ingredients, instructions, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (recipe_data.canonical_url(), recipe_data.title(), title_slug, json.dumps(recipe_data.ingredients()), json.dumps(process_instructions(recipe_data.instructions())), session.get("user_id")))
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

