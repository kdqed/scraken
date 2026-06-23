import json

from scraken import scrape

hn_result = scrape(
    'https://news.ycombinator.com',
    {
        "posts": (".titleline>a", ">list", {
            "title": ("", ">text"),
            "link": ("", "href"),
        })
    },
)

urls = [r['link'] for r in hn_result['posts']]

result = scrape(
    urls,
    {
        "url": ("", ">final_url"),
        "title": ("title", ">text"),
        "description": ("meta[name=description]", "content", None),
        "favicon": ("link[rel='shortcut icon']", "href", None),
        "h1": ("h1", ">text", None),
    },
    concurrency = 30,
)

print(json.dumps(result, indent=2))
