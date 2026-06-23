from scraken import scrape

reflected_headers = scrape(
    "https://httpbin.org/headers",
    "raw", # to return raw response without any extraction
    headers = {"user-agent": "My Custom User Agent"},
)

print(reflected_headers)
