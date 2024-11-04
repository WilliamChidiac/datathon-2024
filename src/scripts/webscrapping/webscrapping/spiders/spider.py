import scrapy
import html2text

class SpiderSpider(scrapy.Spider):
    name = "spider"
    allowed_domains = ["apple.com"]
    start_urls = ["https://apple.com"]

    def __init__(self):
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.body_width = 0
        
    def parse(self, response):
        # Extract data from the page
        page_data = response.css('body').get()
        text_context = self.converter.handle(page_data)
        yield {'markdown_content': text_context}

        # Follow links to inner pages
        for href in response.css('a::attr(href)').getall():
            if href.startswith('/'):
                href = response.urljoin(href)
            yield scrapy.Request(href, callback=self.parse)

