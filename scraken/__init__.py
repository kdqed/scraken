import asyncio
import html
import time
from urllib.parse import urljoin

from html_to_markdown import convert as md_convert
import niquests
from niquests.adapters import AsyncHTTPAdapter
from selectolax.lexbor import LexborHTMLParser


class AttributeNotFound(Exception):
    pass

class ElementNotFound(Exception):
    pass

class InvalidListExtractArgs(Exception):
    pass

class NoListExtractArgs(Exception):
    pass


def _extract_by_css_selectors(content, extract_args, final_url, base_url=None):
    parser = content # default for LexborNode objects
    if type(content) is str:
        parser = LexborHTMLParser(content)
        base_url = final_url
        base_element = parser.css_first('base[href]')
        if final_url == '__content_string__':
            base_url = None
        elif base_element:
            raw_base_href = base_element.attributes.get("href", "").strip()
            base_url = urljoin(final_url, base_url)
    
    result = {}
    for key in extract_args:
        params = extract_args[key]
        selector = params[0]
        attribute = params[1]
        if attribute == ">list":
            if len(params) >= 3 and type(params[2]) is dict:
                result[key] = []
                for node in parser.css(selector):
                    result[key].append(_extract_by_css_selectors(
                        node,
                        params[2],
                        final_url,
                        base_url
                    ))
            elif len(params) >= 3:
                raise InvalidListExtractArgs(
                    f'{params[2]} is not a dict, for selector: {selector} in url: {final_url}'
                )
            else:
                raise NoListExtractArgs(
                    f'No list extarat args provided for selector: {selector} in url: {final_url}'
                )
        else:
            node = parser # default for selector==''
            if selector != '':
                node = parser.css_first(selector)
            if node:
                if attribute == ">final_url":
                    result[key] = final_url
                elif attribute == ">html":
                    result[key] = node.html
                elif attribute == ">inner_html":
                    result[key] = node.inner_html
                elif attribute == ">text":
                    result[key] = html.unescape(node.text())
                else:
                    if attribute in node.attributes:
                        if base_url and attribute in ['action', 'href', 'src', 'srcset']:
                            result[key] = urljoin(base_url, node.attributes[attribute])
                        else:
                            result[key] = node.attributes[attribute]
                    elif len(params) >= 3:
                        result[key] = params[2]
                    else:
                        raise AttributeNotFound(
                            f"attribute: {attribute} for selector: {selector} not found in url: {final_url}"
                        )
            else:
                if len(params) >= 3:
                    result[key] = params[2]
                else:
                    raise ElementNotFound(
                        f"selector: {selector} not found in url: {final_url}"
                    )
    return result

class AsyncScraper:

    def __init__(
        self,
        extract,
        cookies = None,
        headers = None,
        session = None,
        timeout = 60,
        sleep = 0,
        ):
        self.extract = extract
        self.cookies = cookies
        self.headers = headers
        self.session = session
        self.timeout = timeout
        self.sleep = sleep

    
    async def scrape(self, target, semaphore=None):
        content = target
        final_url = '__content_string__'
        if target.startswith("http://") or target.startswith("https://"):
            fetch = niquests.aget
            if self.session:
                fetch = self.session.get

            fetch_opts = dict(
                headers = self.headers,
                timeout = self.timeout,
                cookies = self.cookies,
            )

            if semaphore:
                async with semaphore:
                    response = await fetch(target, **fetch_opts)
            else:
                response = await fetch(target, **fetch_opts)
                
            content = response.text
            final_url = response.url

        if self.sleep:
            time.sleep(self.sleep)
        
        if self.extract == 'raw':
            return content
        elif self.extract == 'markdown':
            return md_convert(content).content
        elif type(self.extract) is dict:
            return _extract_by_css_selectors(content, self.extract, final_url)


async def scrape_async(
    target,
    extract,
    cookies = None,
    headers = None,
    timeout = 60,
    concurrency = 1,
    sleep = 0,
    ):

    scraper_opts = dict(
        cookies = cookies,
        headers = headers,
        timeout = timeout,
        sleep = sleep,
    )


    if type(target) is list:
        concurrency = len(target) if len(target) < concurrency else concurrency
        adapter = AsyncHTTPAdapter(
            pool_connections = concurrency,  
            pool_maxsize = concurrency + 20,
            max_retries = 3
        )
        semaphore = asyncio.Semaphore(concurrency)
        async with niquests.AsyncSession(multiplexed=False) as session:
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            scraper = AsyncScraper(extract, session=session, **scraper_opts)
            tasks = [scraper.scrape(t, semaphore) for t in target]
            return await asyncio.gather(*tasks)
    else:
        scraper = AsyncScraper(extract, **scraper_opts)
        return await scraper.scrape(target)


def scrape(*args, **kwargs):
    return asyncio.run(scrape_async(*args, **kwargs))
