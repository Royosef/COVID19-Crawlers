from os import name
from scrapy.http import FormRequest
from sortedcontainers import SortedDict
from scrapy.spiders import CrawlSpider

import dateutil.parser
import requests
import re
from crawlers.pipelines import MultiCSVItemPipeline
from crawlers.items import ArticleItem

URLS_PATH='urls.csv'

multi_words_phrases_path = "../multi-words-phrases.txt"

REMOVAL_STRINGS = [",", ":", "(", ")", ".", " \"", "\" ", " ,\"", "\", ",
                   " :\"", "\": ", "' ", " '", "?", "!", "<br />", "<br/>", "\n"]
QUOTATION = ["\"", "'"]

NEW_FORMAT = r'https:\/\/www\.ynet\.co\.il\/(([A-Za-z]+)\/)+article\/[a-zA-Z0-9]{8,10}'
OLD_FORMAT = r'https:\/\/www\.ynet\.co\.il\/articles\/0,7340,L-(?!3369891)([0-9]{7}),00\.html'


def get_multi_words_phrases():
    phrases = []

    with open(multi_words_phrases_path, 'r', encoding='Windows-1255', errors='ignore') as f:
        for line in f.readlines():
            phrase = line[:-1]

            for str1 in REMOVAL_STRINGS:
                phrase = phrase.replace(str1, " ")

            if not phrase.isspace() and phrase != '':
                phrases.append(phrase)

    return phrases


phrases = get_multi_words_phrases()
#print(f'phrases: {phrases}')


class YnetSpider(CrawlSpider):
    source_name = 'ynet'
    name = 'ynet_spider_words'
    allowed_domains = ['www.ynet.co.il']

    urls_counter = 0

    def start_requests(self):
        # return [FormRequest('https://www.ynet.co.il/dating/pride/article/BysRdg0000P', callback=self.parse_article)]
        for url in open(URLS_PATH, 'r'):
            url = url.strip()
            # url = 'https://www.ynet.co.il/news/article/BJyc6EkTO'

            if re.search(NEW_FORMAT, url):
                yield FormRequest(url, callback=self.parse_new_format_article)

            if re.search(OLD_FORMAT, url):
                yield FormRequest(url, callback=self.parse_old_format_article)

    custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 0,
        'ITEM_PIPELINES': {
            MultiCSVItemPipeline: 300,
        }
    }

    def parse_new_format_article(self, response):
        item = ArticleItem()
        self.urls_counter += 1
        item['id'] = str(self.urls_counter)

        item['url'] = response.url
        item['source'] = self.source_name
        item['author'] = response.xpath(
            '//div[contains(@class, "authors")]//text()').get().strip()

        date_str = response.xpath(
            '//span[contains(@class, "DateDisplay")]/@data-wcmdate').get().strip()
        date = dateutil.parser.isoparse(date_str)

        item['year'] = str(date.year)
        item['month'] = str(date.month)
        item['day'] = str(date.day)

        title = response.xpath(
            '//h1[contains(@class, "mainTitle")]/text()').get().strip()
        subtitle = response.xpath(
            '//h2[@class="subTitle"]//text()').get().strip()
        content = ' '.join(response.xpath(
            '//div[@id="ArticleBodyComponent"]//div[contains(@class, "text_editor_paragraph")]//text()').extract()).strip()
        

        comments = self.get_new_format_comments(response.url)
        joined_comments = ' '.join(comments).strip()
        item['comments_count'] = str(len(comments))

        self._set_dicts(item, title, subtitle, content, joined_comments)

        yield item

    def parse_old_format_article(self, response):
        item = ArticleItem()
        self.urls_counter += 1
        item['id'] = str(self.urls_counter)
        item['url'] = response.url
        item['source'] = self.source_name

        item['author'] = response.xpath(
            '//span[contains(@class, "art_header_footer_author")]/span//text()').get().strip()

        date_str = response.xpath(
            '//span[contains(@class, "art_header_footer_author")]/text()').get().strip()
        date = date_str.split()[-3].split('.')
        item['year'] = str(date[2])
        item['month'] = str(date[1])
        item['day'] = str(date[0])

        title = response.xpath(
            '//h1[@class="art_header_title"]/text()').get().strip()
        subtitle = response.xpath(
            '//h2[@class="art_header_sub_title"]//text()').get().strip()
        content = ' '.join(response.xpath(
            '//div[@class="art_body art_body_width_3"]//p/text() | //div[@class="art_body art_body_width_3"]//span/text()').extract()).strip()
        
        comments = self.get_old_format_comments(response.url)
        joined_comments = ' '.join(comments).strip()
        item['comments_count'] = str(len(comments))

        self._set_dicts(item, title, subtitle, content, joined_comments)

        yield item

    def _set_dicts(self, item, title, subtitle, content, comments):
        titles_dict = self.count_words_to_dict(title)
        subtitle_dict = self.count_words_to_dict(subtitle)
        content_dict = self.count_words_to_dict(content)
        comments_dict = self.count_words_to_dict(comments)

        item['title_words_count'] = len(titles_dict)
        item['title_words_dict'] = titles_dict

        item['subtitle_words_count'] = len(subtitle_dict)
        item['subtitle_words_dict'] = subtitle_dict

        item['content_words_count'] = len(content_dict)
        item['content_words_dict'] = content_dict

        item['comments_words_count'] = len(comments_dict)
        item['comments_words_dict'] = comments_dict

        pass

    def get_clean_words(self, content):
        clean_content = str(content)
        if content.isspace() or clean_content == '':
            return []

        if clean_content[0] in QUOTATION:
            clean_content = clean_content[1:]

        if clean_content[-1] in QUOTATION:
            clean_content = clean_content[0:-1]

        for str1 in REMOVAL_STRINGS:
            clean_content = clean_content.replace(str1, " ")

        return list(filter(lambda w: w not in ["-"], clean_content.split()))

    def merge_counter_dicts(self, counter_dict1, counter_dict2):
        counter_dict = counter_dict1.copy()
        for word in counter_dict2:
            if word not in counter_dict:
                counter_dict[word] = 0
            counter_dict[word] += 1

        return counter_dict

    def count_words_to_dict(self, text):
        if not isinstance(text, str):
            raise TypeError(
                f'text must be of type `str`, but got `{type(text)}`')

        counter_dict = SortedDict()
        words = self.get_clean_words(text)

        for word in words:
            if word not in counter_dict:
                counter_dict[word] = 0
            counter_dict[word] += 1

        for phrase in phrases:
            count_phrase = text.count(phrase)

            if count_phrase > 0:
                counter_dict[phrase] = count_phrase

        return counter_dict

    def get_new_format_comments(self, url):
        article_id = url.split('/')[-1]
        comments_json_url = f'https://www.ynet.co.il/iphone/json/api/talkbacks/list/{article_id}/end_to_start/1'
        comments_json = requests.get(url=comments_json_url).json()
        comments = []

        if 'rss' in comments_json and 'channel' in comments_json['rss'] and 'item' in comments_json['rss']['channel']:
            comments = [' '.join([x['title'], x['text']])
                        for x in comments_json['rss']['channel']['item']]

        return comments

    def get_old_format_comments(self, url):
        article_id = url.split('-')[-1].split(',')[0]
        comments_json_url = f'https://www.ynet.co.il/Ext/Comp/ArticleLayout/Proc/ShowTalkBacksAjax/v2/0,12990,L-{article_id}-desc-68-0-0,00.html'
        comments_json = requests.get(url=comments_json_url).json()
        comments = []

        if 'rows' in comments_json:
            comments = [' '.join([x['title'], x['text']])
                        for x in comments_json['rows']]

        return comments


if __name__ == '__main__':
    print('phrases')
    text = 'וכך נותר לנו הספר כמקור עיוני מרכזי, מלבד נאומיו וראיונותיו בתקשורת, לגבי התנהלותו בעתיד. בעיקר, כאשר דרך הטיפול שלו בקורונה יכולה לתת בסיס השוואתי להתנהלות של קודמו נתניהו. אולי הדבר גם יאפשר לבנט להשתחרר מן הצל הענק שמטיל עליו ראש הממשלה הקודם.'
    print('ראש הממשלה' in phrases)
    counter_dict = SortedDict()

    for phrase in phrases:
        count_phrase = text.count(phrase)

        if count_phrase > 0:
            counter_dict[phrase] = count_phrase

    print(counter_dict)
