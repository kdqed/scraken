import asyncio
from contextlib import nullcontext
import html
import random
import time
from urllib.parse import urljoin

from html_to_markdown import convert as md_convert
import niquests
from niquests.adapters import AsyncHTTPAdapter
from selectolax.lexbor import LexborHTMLParser

try:
    from playwright.async_api import async_playwright
except:
    async_playwright = None


class AttributeNotFound(Exception):
    pass

class ElementNotFound(Exception):
    pass

class InvalidListExtractArgs(Exception):
    pass

class NoListExtractArgs(Exception):
    pass

class NoBrowserAvailable(Exception):
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
        js_render = False,
        js_delay = 0,
        js_eval = '',
        js_eval_delay = 0,
        js_headless = True,
        js_wait_until = 'load',
        proxies = None,
        session = None,
        timeout = 60,
        sleep = 0,
        ):
        self.extract = extract
        self.cookies = cookies
        self.headers = headers
        self.js_render = js_render
        self.js_delay = js_delay
        self.js_eval = js_eval
        self.js_eval_delay = js_eval_delay
        self.js_headless = js_headless
        self.js_wait_until = js_wait_until
        self.proxies = proxies
        self.session = session
        self.timeout = timeout
        self.sleep = sleep

    async def start_browser(self):
        if async_playwright:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.js_headless)
        else:
            raise NoBrowserAvailable("Install scraken[pw] to render JS")

    
    async def scrape(self, target, semaphore=None):
        content = target
        final_url = '__content_string__'
        if target.startswith("http://") or target.startswith("https://"):
            if self.js_render:
                async with semaphore or nullcontext():
                    context = await self._browser.new_context()
                    page = await context.new_page()
                    await page.goto(
                        target, 
                        timeout = self.timeout*1000, 
                        wait_until = self.js_wait_until,
                    )
                    if self.js_delay:
                        time.sleep(self.js_delay)
                    if self.js_eval:
                        await page.evaluate(self.js_eval)
                        if self.js_eval_delay:
                            time.sleep(self.js_eval_delay)
                    content = await page.content()
                    final_url = page.url

                    await page.close()
                    await context.close()
            else:
                
                fetch = niquests.aget
                if self.session:
                    fetch = self.session.get

                proxies = None
                if self.proxies:
                    proxy_url = random.choice(self.proxies)
                    proxies = {"http": proxy_url, "https": proxy_url}

                fetch_opts = dict(
                    cookies = self.cookies,
                    headers = self.headers,
                    proxies = proxies,
                    timeout = self.timeout,
                )

                async with semaphore or nullcontext():
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

    async def close_browser(self):
        if hasattr(self, '_browser'):
            await self._browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()


async def scrape_async(
    target,
    extract,
    concurrency = 1,
    cookies = None,
    headers = None,
    js_render = False,
    js_delay = 0,
    js_eval = '',
    js_eval_delay = 0,
    js_headless = True,
    js_wait_until = 'load',
    proxies = None,
    sleep = 0,
    timeout = 60,
    ):

    scraper_opts = dict(
        cookies = cookies,
        headers = headers,
        js_render = js_render,
        js_delay = js_delay,
        js_eval = js_eval,
        js_eval_delay = js_eval_delay,
        js_headless = js_headless,
        js_wait_until = js_wait_until,
        proxies = proxies,
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
        if js_render:
            scraper = AsyncScraper(extract, session=session, **scraper_opts)
            await scaper.start_browser()
            tasks = [scraper.scrape(t, semaphore) for t in target]
            result = await asyncio.gather(*tasks)
            await scraper.close_browser()
            return result           
        else:
            async with niquests.AsyncSession(multiplexed=False) as session:
                session.mount("http://", adapter)
                session.mount("https://", adapter)
                scraper = AsyncScraper(extract, session=session, **scraper_opts)
                tasks = [scraper.scrape(t, semaphore) for t in target]
                return await asyncio.gather(*tasks)
        
    else:    
        scraper = AsyncScraper(extract, **scraper_opts)
        if js_render:
            await scraper.start_browser()
        result = await scraper.scrape(target)
        if js_render:
            await scraper.close_browser()
        return result


def scrape(*args, **kwargs):
    return asyncio.run(scrape_async(*args, **kwargs))
