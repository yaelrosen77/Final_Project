import tldextract

def get_app_name(url):
    extracted = tldextract.extract(url)
    app_name = extracted.domain
    if app_name:
        app_name = app_name.replace('-', ' ').capitalize().replace(' ', '')
    return app_name
