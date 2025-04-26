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
    # def test_runsipey(self):
    #     url = "https://www.halfbakedharvest.com/baked-frosted-chocolate-donuts/"
    #     print("RUNNING SPIDER")
    #     result = run_spider(url)

    #     print(result)
        
    def test_new_scraper(self):
        url = "https://www.allrecipes.com/recipe/158968/spinach-and-feta-turkey-burgers/"
        scraped_data = new_scraper(url)
        print("ingredients", process_instructions(scraped_data.instructions()))
        




        

if __name__ == "__main__":
    unittest.main()