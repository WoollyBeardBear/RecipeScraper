import scrapy


class RecipeSpider(scrapy.Spider):
    name = "recipespider"
    allowed_domains = ["www.halfbakedharvest.com"]

    def __init__(self, recipe_url, *args, **kwargs):
        super(RecipeSpider, self).__init__(*args, **kwargs)
        self.start_urls = [recipe_url]

    def parse(self, response):
        print("running spider")
        ingredients = response.css('a.wprm-recipe-ingredient-link::text').getall()
        amounts = response.css('span.wprm-recipe-ingredient-amount::text').getall()
        units = response.css('span.wprm-recipe-ingredient-unit::text').getall()
        instructions = response.css('div.wprm-recipe-instruction-text span::text').getall()

        # list of instructions
        instruct_list = []
        ingredient_dict = {}

        # list of ingredients with their amounts
        
        for i in range(0, len(ingredients)):
            ingredient = ingredients[i]
            amount = (amounts[i] + " " + units[i]) if i < len(amounts) else None
            ingredient_dict[ingredient] = amount
            
        
        for entry in instructions:
            instruct_list.append(entry)
        yield { 
            "title": response.css('h2.wprm-recipe-name::text').get(),
            "ingredients": ingredient_dict,
            "instructions": instruct_list,
            "source_url": response.url
            }


        

