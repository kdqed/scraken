from scraken import scrape

result = scrape(
    "https://api.ipify.org", 
    "raw",
    proxies = [
        'your-proxy-1',
        'your-proxy-2',
        'your-proxy-3',
    ]
)
print(result)
