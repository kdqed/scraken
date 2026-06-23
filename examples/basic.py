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
