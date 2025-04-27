import unittest
from app import *
from helpers import *
from flask import Flask, render_template, session, request, redirect, flash
from flask_session import Session
from new_scraper import *
from recipe_scrapers import scrape_me
import requests
from recipe_scrapers import scrape_me
from recipe_scrapers import scrape_html

class TestTests(unittest.TestCase):
        
    def test_new_scraper(self):
        try:
            url = "https://www.allrecipes.com/recipe/143052/sweet-and-spicy-turkey-sandwich/"
            scraped_data = new_scraper(url)
            print("ingredients", process_instructions(scraped_data.instructions()))
        except Exception as e:
            help(scraped_data)
            print(f"Error scraping {url}: {e}")
            self.fail(f"Scraping failed with error: {e}")
    
    def test_url(self):
        
     




        

if __name__ == "__main__":
    unittest.main()