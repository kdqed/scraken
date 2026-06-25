# Scraken: Just scrape() everything

Scraken is a refreshing, declarative take on how a scraping library in Python should work for humans and AI agents alike. It focuses on maximizing efficiency and minimizing the syntax (code tokens) required to pull off common scraping tasks. Scrape raw HTML, JS rendered pages, structured data using CSS selectors, or as markdown content. All within a function call. It's free and open source (MIT Licensed).

Everything works with the `scrape` function, a quick example:

```python
from scraken import scrape

my_homepage = scrape(
    "https://kdqed.com", 
    {
        # "field": (css_selector, attribute)
        "title": ("title", ">text"),
        "favicon": ("link[rel='shortcut icon']", "href", None),
        # a third value is an optional fallback, otherwise it would raise an error
        
        "description": ("meta[name=description]", "content"),
        "h1": ("h1", ">text"),
        "posts": ("a.post", ">list", {
            "title": (".title", ">text"),
            "link": ("", "href"),
        })
    }
)

print(my_homepage)
```

- In the example above, the first parameter was the URL to scrape, followed by a dict that specifies how to extract data from the page using CSS selectors. 
- Each key corresponds to a field to be scraped, and the value is 2 or 3-length tuple of params. 
- The first param is the CSS selector, the second is the attribute to get from that element. An optional third param specifies a fallback value, or a nested extract dict if the specified attribute is `>list`.
- Attributes may be any attributes on the HTML tag, or special attributes ">text" (Unescaped text in the element), ">html" (outer HTML), ">inner_html" (inner HTML), ">final_url" (final URL of the page), or ">list". 
- The ">list" attribute selects all matching elements for further processing with the specified nested extract dict.
- For the attributes 'action', 'href', 'src', and 'srcset', if they are not full URLs, they are automatically resolved to full URLs using the base URL of the page.
- The The function returns a dict containing the specified keys with their scraped data values. 

**The above snippet outputs the following:**

```
{'title': 'Karthik Devan (@kdqed)', 'favicon': 'https://kdqed.com/assets/brand/favicon.ico', 'description': 'Personal Website', 'h1': 'Karthik Devan (@kdqed)', 'posts': [{'title': 'Lima: The Edge Of My World', 'link': 'https://kdqed.com/lima-edge-of-my-world'}...
```

## Scrape Multiple URLs:

Pass a list of URLs instead of just one:

```python
from scraken import scrape

urls = ['https://kdqed.com', 'https://example.com']

results = scrape(urls, {'title': ("title", ">text")})
for result in results:
    print(result)
```

**OUTPUT:**

```
{'title': 'Karthik Devan (@kdqed)'}
{'title': 'Example Domain'}
```

## Concurrency And Delay

Use `concurrency` to specify number of concurrent requests (default is 1). Use `sleep` to wait a specified number of seconds after each network request (default is 0).

```python
from scraken import scrape

urls = ['https://kdqed.com', 'https://example.com']

results = scrape(
    urls, 
    {'title': ("title", ">text")},
    concurrency = 2,
    sleep = 1
)

for result in results:
    print(result)
```

## Custom Headers

Use `headers` with a dict of headers you want to send in the requests:

```python
from scraken import scrape

reflected_headers = scrape(
    "https://httpbin.org/headers",
    "raw", # to return raw response without any extraction
    headers = {"user-agent": "My Custom User Agent"},
)

print(reflected_headers)
```

**OUTPUT:**

```
{
  "headers": {
    "Accept": "*/*", 
    "Accept-Encoding": "gzip, deflate", 
    "Host": "httpbin.org", 
    "User-Agent": "My Custom User Agent", 
    "X-Amzn-Trace-Id": "Root=1-6a3a6145-3b99736e72f482875f843af6"
  }
}
```

## Scrape As Markdown

Just pass "markdown" as the second parameter:

```python
from scraken import scrape

md_content = scrape("https://example.com", "markdown")
print(md_content)
```

**OUTPUT:**

```
---
meta-viewport: width=device-width, initial-scale=1
title: Example Domain
---

# Example Domain

This domain is for use in documentation examples without needing permission. Avoid use in operations.

[Learn more](https://iana.org/domains/example)
```

## Features Coming Soon

- JSON scraping with JSONPath
- Scraping structured data
- Determine CSS selectors using sample data (for development)

