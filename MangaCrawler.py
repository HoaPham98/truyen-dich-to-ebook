from fileinput import filename
from xml.etree.ElementTree import tostring, tostringlist
from requests import request
from requests_cache import CachedSession
from lxml import etree
import os
from typing import List
import shutil
import re

class SpyFamilyCrawler:

    class ChapterItem:
        def __init__(self, title: str, path: str, url: str, index: int):
            self.title = title
            self.path = path
            self.url = url
            self.int = int

    session: CachedSession = CachedSession('spy_x_family')
    save_path: str = 'SpyXFamily'
    base_url: str = 'https://w3.spy-x-family.online/'

    def crawl(self):
        if os.path.isdir(self.save_path):
            shutil.rmtree(self.save_path)
        os.mkdir(self.save_path)
        html_text = self.session.get(self.base_url).text
        tree = etree.HTML(html_text)
        chapters: List[SpyFamilyCrawler.ChapterItem] = []
        chapter_nodes = tree.xpath('//li[@class="su-post "]/a')
        for node in chapter_nodes:
            url: str = node.xpath('./@href')[0]
            title: str = node.xpath('./text()')[0]
            new_url = url.replace('-part-', '-')
            matches = re.finditer('chapter-\d{1,3}(-\d{1,3})?', new_url, re.IGNORECASE)
            path: str = ''
            for matchNum, match in enumerate(matches, start=1):
                print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))
                path = match.group()
            path = path.split('chapter-')[-1]
            pathes = path.split('-')
            pathes[0] = '{:04d}'.format(int(pathes[0]))
            path = '-'.join(pathes)
            chapter_item = SpyFamilyCrawler.ChapterItem(title=title, path=path, url=url, index=int(pathes[0]))
            chapters.append(chapter_item)
        for chapter in chapters:
            self._crawlChapter(chapter=chapter)


    def _crawlChapter(self, chapter: ChapterItem):
        html_text = self.session.get(chapter.url).text
        tree = etree.HTML(html_text)
        folder_path = '{}/chapter-{}'.format(self.save_path, chapter.path)
        os.mkdir(folder_path)
        img_urls = tree.xpath('//img[@class="aligncenter"]/@src')
        for (num, url) in enumerate(img_urls):
            f = open('{}/{:03d}.jpg'.format(folder_path, num), 'wb')
            f.write(self.session.get(url=url, headers={
                "accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "accept-language": "en-GB,en;q=0.9,vi-VN;q=0.8,vi;q=0.7,en-US;q=0.6",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"macOS\"",
                "sec-fetch-dest": "image",
                "sec-fetch-mode": "no-cors",
                "sec-fetch-site": "cross-site",
                "Referer": "https://w3.spy-x-family.online/",
                "Referrer-Policy": "strict-origin-when-cross-origin"
            }).content)
            f.close()


SpyFamilyCrawler().crawl()
