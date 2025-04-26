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