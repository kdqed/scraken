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
