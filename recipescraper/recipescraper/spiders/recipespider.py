import scrapy


class RecipeSpider(scrapy.Spider):
    name = "recipespider"
    allowed_domains = ["www.halfbakedharvest.com"]

    def __init__(self, recipe_url, *args, **kwargs):
        super(RecipeSpider, self).__init__(*args, **kwargs)
        self.start_urls = [recipe_url]

    def parse(self, response):
        print("Spider parsing response:", response.url)
        recipe_container = response.css('div.wprm-recipe-container')

        # Extracting ingredients
        ingredients_data = {}
        for item in recipe_container.css('li.wprm-recipe-ingredient'):
            ingredient = item.css('a.wprm-recipe-ingredient-link::text').get()
            amount = item.css('span.wprm-recipe-ingredient-amount::text').get()
            unit = item.css('span.wprm-recipe-ingredient-unit::text').get()
            print(f"Getting {ingredient}")
            if ingredient:
                full_amount = f"{amount} {unit}" if amount and unit else amount if amount else unit if unit else " "
                ingredients_data[ingredient] = full_amount

        
        instructions = response.css('div.wprm-recipe-instruction-text span::text').getall()

        # list of instructions
        instruct_list = []
            
        i = 1
        for entry in instructions:
            entry = entry.lstrip(f"{i}. ")
            instruct_list.append(entry)
            i += 1
        yield { 
            "title": response.css('h2.wprm-recipe-name::text').get(),
            "ingredients": ingredients_data,
            "instructions": instruct_list,
            "source_url": response.url
            }


        

