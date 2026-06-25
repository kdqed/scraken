from scraken import scrape

result = scrape(
    "https://kdqed.com", 
    "raw",
    js_render = True,
    js_headless = False,
    js_eval = "showSpPopup()",
    js_eval_delay = 10,
)
print(result)
