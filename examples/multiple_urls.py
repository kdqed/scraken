from scraken import scrape

urls = ['https://kdqed.com', 'https://example.com']

results = scrape(urls, {'title': ("title", ">text")})
for result in results:
    print(result)
