from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
# from scrapy.http import FormRequest

from crawlers.items import UrlItem

# if you change the yearse update parse_month link extractor regex accordingly  
years = (2018, 2021)

class YnetSpiderSpider(CrawlSpider):
    source_name = 'ynet'
    name = 'ynet_spider_urls'
    allowed_domains = ['www.ynet.co.il']
    start_urls = ['https://www.ynet.co.il/home/0,7340,L-4269,00.html']

    urls_counter = 0

    # def start_requests(self):
    #     return [
    #         FormRequest('https://www.ynet.co.il/articles/0,7340,L-5882452,00.html', callback=self.parse_article),
    #         FormRequest('https://www.ynet.co.il/news/article/rkq5zrxfy', callback=self.parse_article),
    #         FormRequest('https://www.ynet.co.il/articles/0,7340,L-5994751,00.html', callback=self.parse_article),
    #         FormRequest('https://www.ynet.co.il/articles/0,7340,L-5390928,00.html', callback=self.parse_article)
    #         ]

    rules = (
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/home\/0,7340,L-4269,00.html'), follow=True),
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/home\/0,7340,L-4269-\d{2,4}-\d{2,4},00.html'), follow=True),
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/home\/0,7340,L-4269-\d{2,4}-\d{2,4}-(2018|2019|2020|2021){1}\d{2}-\d,00.html'), follow=True),
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/(([A-Za-z]+)\/)+article\/[a-zA-Z0-9]{8,10}'), callback='parse_article', follow=False),
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/articles\/0,7340,L-(?!3369891)([0-9]{7}),00\.html'), callback='parse_article', follow=False),
    )

    custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 0,
    }

    def parse_article(self, response):
        item = UrlItem()
        item['url'] = response.url

        if not response.xpath('/html/body/nav/div/div/div').get():
            yield item

