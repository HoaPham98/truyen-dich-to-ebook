from fileinput import filename
from xml.etree.ElementTree import tostring, tostringlist
import requests_cache
from lxml import etree
from markdownify import markdownify as md
import os
import MarkdownPP
from typing import List
import shutil
import pandoc
import yaml

url = 'https://truyendich.com/co-hai-con-meo-ngoi-ben-cua-so'

class ChapterItem:
    def __init__(self, title: str, file_name: str):
        self.title = title
        self.file_name = file_name

class Novel:
    title: str = ''
    slug: str = ''
    author: str = ''
    abstract: str = ''
    chapters: List[ChapterItem] = []

class NovelCrawler:
    session = requests_cache.CachedSession('novel_cache')
    save_path: str = ''
    markdown_name: str = 'Novel'

    def getNovel(self, url: str):
        html_text = self.session.get(url).text
        tree = etree.HTML(html_text)
        novel = Novel()
        chapters: List[ChapterItem] = []
        name_node = tree.xpath('//h1[@class="hl-name-book"]/a')[0]
        name = name_node.xpath('./@title')[0]
        slug = ''.join(name_node.xpath('./@href')).split('/').pop()
        self.save_path = '{0}'.format(slug)
        if os.path.isdir(self.save_path):
            shutil.rmtree(self.save_path)
        os.mkdir(self.save_path)
        novel.title = name
        novel.slug = slug
        novel.author = ', '.join(tree.xpath('//a[@class="name-author ellipsis-1"]/@title'))
        abstract_nodes = tree.xpath('//div[@itemprop="description"]/p/text()')
        novel.abstract = '\n\n'.join(abstract_nodes).strip()
        chapter_nodes = tree.xpath('//ul[@class="list-chapter"]/li')
        for idx, node in enumerate(chapter_nodes):
            a_node = node.xpath('./a')[0]
            chapter = ''.join(a_node.xpath('./span/text()')).strip()
            name = ''.join(a_node.xpath('./text()')).strip()
            title = ''.join([chapter, name])
            chapter_url = a_node.xpath('./@href')[0]
            self._getChapter(idx + 1, chapter_url)
            chapter_item = ChapterItem(title=title, file_name='chapter-{0}.md'.format(idx + 1))
            chapters.append(chapter_item)
        novel.chapters = chapters
        input_name = os.path.join(self.save_path, '{0}.mdpp'.format(self.markdown_name))
        output_name = os.path.join(self.save_path, '{0}.md'.format(self.markdown_name))
        with open(input_name, 'w', encoding='utf-8') as template:
            # template.write('> Dedication\n\n')
            template.writelines(['% {0}'.format(novel.title),'\n', '% {0}'.format(novel.author), '\n\n'])
            # template.write('# {0}\n\n'.format(novel.title))
            # template.write('!TOC\n\n')
            for chapter in chapters:
                template.write('## {0}\n\n'.format(chapter.title))
                template.write('!INCLUDE "{0}/{1}", 1\n\n'.format(self.save_path, chapter.file_name))
            template.close()
        input = open(input_name, 'r')
        output = open(output_name, 'w')
        MarkdownPP.MarkdownPP(input=input, output=output, modules=list(MarkdownPP.modules))
        input.close()
        output.close()

        output = open(output_name, 'r')
        doc = pandoc.read(file=output)
        pandoc.write(doc=doc, file='{0}.epub'.format(slug), format='epub', options=['--css=style.css'])
        output.close()

    def _getChapter(self, number: int, url: str):
        file_name = 'chapter-{0}.md'.format(number)
        html_text = self.session.get(url).text
        tree = etree.HTML(html_text)
        content_node = tree.xpath('//div[@id="read-content"]')[0]
        chapter_html = etree.tostring(content_node)
        file = os.path.join(self.save_path, file_name)
        with open(file, "w", encoding='utf-8') as text_file:
            markdown_text = md(chapter_html)
            markdown_text = markdown_text.replace(' - ', ' \- ')
            text_file.write(markdown_text)

    def _createMetadata(self, novel: Novel):
        metadata = {
            'title': novel.title,
            'author': novel.author.split(', '),
            'abstract': novel.abstract
        }
        path = os.path.join(self.save_path, 'metadata.yaml')
        with open(path, 'w', encoding='utf-8') as meta:
            yaml_str = str(yaml.dump(data=metadata, encoding='utf-8'))
            meta.writelines(['---', yaml_str,'...'])
            meta.close()

crawler = NovelCrawler()
crawler.getNovel(url)