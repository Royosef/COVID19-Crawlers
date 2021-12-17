from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
# from scrapy.http import FormRequest

from crawlers.items import UrlItem

# if you change the yearse update parse_month link extractor regex accordingly
years = (18, 21)


class KikarSpider(CrawlSpider):
    source_name = 'kikar'
    name = 'kikar_spider_urls'
    allowed_domains = ['www.kikar.co.il']
    start_urls = ['https://www.kikar.co.il/']

    urls_counter = 0

    rules = (
        Rule(LinkExtractor(
            allow=r'https:\/\/www\.kikar\.co\.il\/\d{6}\.html'), callback='parse_article', follow=True),
        Rule(LinkExtractor(
            allow=r'https:\/\/www\.kikar\.co\.il\/(?!(\d{6}\.html)).*'), follow=True),
    )

    custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 0,
    }

    def parse_article(self, response):
        item = UrlItem()
        item['url'] = response.url

        try:
            full_date_string = response.xpath(
                '//div[@class="art-date-author"]/div[@class="article_buttons_field"][not(./a)]').get()
            year = int(full_date_string.split()[5].strip().split('.')[2])

            if years[0] <= year <= years[1]: 
                yield item
        except Exception as exc:
            print(exc)
            pass