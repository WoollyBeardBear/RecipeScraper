import scrapy


class RecipespiderSpider(scrapy.Spider):
    name = "recipespider"
    allowed_domains = ["www.halfbakedharvest.com"]
    start_urls = ["https://www.halfbakedharvest.com/honey-garlic-chicken/"]

    def parse(self, response):
        
        ingredients = respone.css('ul')
