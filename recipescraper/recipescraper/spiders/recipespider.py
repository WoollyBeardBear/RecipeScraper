import scrapy


class RecipespiderSpider(scrapy.Spider):
    name = "recipespider"
    allowed_domains = ["www.halfbakedharvest.com"]
    start_urls = ["https://www.halfbakedharvest.com/honey-garlic-chicken/"]

    def parse(self, response):
        
        ingredients = response.css('a.wprm-recipe-ingredient-link::text').getall()
        amounts = response.css('span.wprm-recipe-ingredient-amount::text').getall()
        instructions = response.css('span::text').getall()
        instruct_list = []
        # list of ingredients with their amounts
        i_list = {}
        for i in range(0, len(ingredients)):
            try:
                i_list[ingredients[i]] = amounts[i]
            except:
                i_list[ingredients[i]] = 0
        
        for entry in instructions:
            if (entry[0] == 1 or entry[0] == 2 or entry[0] == 3 or entry[0] == 4 or entry[0] == 5 or entry[0] == 6 or entry[0] == 7) and len(entry) > 1:
                instruct_list.append(entry)

        yield [i_list, instruct_list]

