from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import dateutil.parser
from datetime import datetime

# from scrapy.http import FormRequest

from crawlers.items import UrlItem

start_date = datetime.strptime("10/2021", "%m/%Y")
end_date = datetime.strptime("08/2022", "%m/%Y")
# 2350 avg per month, 11 months, 26000

class YnetSpider(CrawlSpider):
    source_name = 'ynet'
    name = 'ynet_spider_urls'
    allowed_domains = ['www.ynet.co.il']
    start_urls = ['https://www.ynet.co.il/home/0,7340,L-8,00.html']
    # start_urls = ['https://www.ynet.co.il/home/0,7340,L-4269,00.html']


    urls_counter = 0
 
    # def start_requests(self):
    #     return [
    #         FormRequest('https://www.ynet.co.il/articles/0,7340,L-5882452,00.html', callback=self.parse_article),
    #         FormRequest('https://www.ynet.co.il/news/article/rkq5zrxfy', callback=self.parse_article),
    #         FormRequest('https://www.ynet.co.il/articles/0,7340,L-5994751,00.html', callback=self.parse_article),
    #         FormRequest('https://www.ynet.co.il/articles/0,7340,L-5390928,00.html', callback=self.parse_article)
    #         ]

    rules = (
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/home\/0,7340,L-8,00.html'), follow=True),
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/([A-Za-z-]+)$'), follow=True),
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/(([A-Za-z-]+)\/)+[0-9]{1,10}$'), follow=True),
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/(([A-Za-z-]+)\/)+([A-Za-z-]+)$'), follow=True),
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/(([A-Za-z-]+)\/)+article\/[a-zA-Z0-9]{8,10}$'), callback='parse_article', follow=True),
        Rule(LinkExtractor(allow=r'https:\/\/www\.ynet\.co\.il\/.*$'), follow=True),
    )

    custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 0,
        # 'CLOSESPIDER_ITEMCOUNT': 100,
    }

    def parse_article(self, response):
        item = UrlItem()
        item['url'] = response.url

        if not response.xpath('/html/body/nav/div/div/div').get():
            date_str = response.xpath('//meta[@property="article:published_time"]/@content').get().strip()
            # date_str = response.xpath('//time[contains(@class, "DateDisplay")]/@data-wcmdate').get().strip()
            date = dateutil.parser.isoparse(date_str).replace(tzinfo=None)
            
            # print(f'date.year {(start_date <= date <= end_date)}')

            if start_date <= date <= end_date:
                yield item

