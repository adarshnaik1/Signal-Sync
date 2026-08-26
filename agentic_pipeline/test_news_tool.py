#This file is only for purpose of testing news_tool independently. It is not part of the main pipeline and can be ignored for the overall project structure.

from tools.news_tool import fetch_company_news

news = fetch_company_news("Infosys")

print(news)