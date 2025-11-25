article_url = "https://www.kommersant.ru/doc/8227770query=%D0%98%D1%81%D0%BA%D1%83%D1%81%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B9%20%D0%B8%D0%BD%D1%82%D0%B5%D0%BB%D0%BB%D0%B5%D0%BA%D1%82"

article_url = article_url.split('?')[0]

#if not article_url.startswith("http"):
#    article_url = "http" + article_url

print(article_url)