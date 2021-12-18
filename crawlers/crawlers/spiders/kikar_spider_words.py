from os import name
from scrapy.http import FormRequest
from sortedcontainers import SortedDict
from scrapy.spiders import XMLFeedSpider
from datetime import datetime

from lxml import html
from crawlers.pipelines import MultiCSVItemPipeline
from crawlers.items import ArticleItem

multi_words_phrases_path = "../multi-words-phrases.txt"

REMOVAL_STRINGS = [",", ":", "(", ")", ".", " \"", "\" ", " ,\"", "\", ",
                   " :\"", "\": ", "' ", " '", "?", "!", "<br />", "<br/>", "\n"]
QUOTATION = ["\"", "'"]


def get_multi_words_phrases():
    phrases = []

    with open(multi_words_phrases_path, 'r') as f:
        for line in f.readlines():
            phrase = line[:-1]

            for str1 in REMOVAL_STRINGS:
                phrase = phrase.replace(str1, " ")

            if not phrase.isspace() and phrase != '':
                phrases.append(phrase)

    return phrases


phrases = get_multi_words_phrases()


class KikarSpider(XMLFeedSpider):
    source_name = 'kikar'
    name = 'kikar_spider_words'
    allowed_domains = ['www.kikar.co.il']
    itertag = 'Result'

    urls_counter = 0

    def start_requests(self):
        # return [FormRequest('https://www.kikar.co.il/wapapi.php?op=GetItem&app=1&dsk=1&id=387973')]
        for article_url in open('urls-test.csv', 'r'):
            article_url = article_url.strip()
            id = article_url.split('/')[-1].split('.')[0]
            url = f'https://www.kikar.co.il/wapapi.php?op=GetItem&app=1&dsk=1&id={id}'

            yield FormRequest(url)

    custom_settings = {
        'CLOSESPIDER_PAGECOUNT': 1,
        'ITEM_PIPELINES': {
            MultiCSVItemPipeline: 300,
        }
    }

    def parse_node(self, response, selector):
        item = ArticleItem()
        self.urls_counter += 1
        item['id'] = str(self.urls_counter)

        kikar_article_id = response.url.split('=')[-1]
        item['url'] = f'https://www.kikar.co.il/{kikar_article_id}.html'
        item['source'] = self.source_name

        item['author'] = selector.xpath(
            './Item/Author/text()').get().replace('\n', ' ')

        timestamp = selector.xpath(
            './Item/ItemDateRaw/text()').get().replace('\n', ' ')
        date = datetime.fromtimestamp(int(timestamp))

        item['year'] = str(date.year)
        item['month'] = str(date.month)
        item['day'] = str(date.day)

        title = selector.xpath('./Item/Title/text()').get()
        subtitle = selector.xpath('./Item/SubTitle/text()').get()

        content_html = selector.xpath('./Item/ItemText/text()').get()
        content = ' '.join(html.fromstring(
            content_html).xpath('//text()'))

        comments = self.get_comments(selector)
        joined_comments = ' '.join(comments).strip()
        item['comments_count'] = selector.xpath(
            './Item/CommentCount/text()').get()

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

    def get_comments(self, item):
        xml_comments = item.xpath('./Item/ItemComments/Comment')
        comments = []

        for comment in xml_comments:
            title = comment.xpath('Title/text()').get() or ''
            text = comment.xpath('Text/text()').get() or ''

            comments.append(f'{title} {text}')

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
