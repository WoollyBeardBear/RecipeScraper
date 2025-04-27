from recipe_scrapers import scrape_me
import requests
from recipe_scrapers import scrape_html
 

def new_scraper(url):
    '''A new scraper using the reciper_scrapers library'''
    html = requests.get(url).text # retrieves the recipe webpage HTML
    scraper = scrape_html(html, org_url=url)
    return scraper
        


