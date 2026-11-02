from bs4 import BeautifulSoup
import requests

def getHTML(url):
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.text

urlinput = "https://www.realestate.com.au/sold/property-house-sa-fairview+park-150263784" #ideally a form

html_document = getHTML(urlinput)

soup = BeautifulSoup(html_document, 'html.parser')

print(soup)