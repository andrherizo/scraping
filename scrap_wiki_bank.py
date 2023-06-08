from bs4 import BeautifulSoup
import requests
import numpy as np 
from urllib.parse import urlparse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

wiki_url = 'https://en.wikipedia.org'
url = wiki_url + '/wiki/Lists_of_banks'
excludes = ['References', 'External links', 'See also']

def filter_links(tag):
    if tag.name == "a" and tag.get("href", "").startswith("/wiki/List_of_banks_in"):
        return True
    return False
    
def is_link(chaine):
    parsed_url = urlparse(chaine)
    return parsed_url.scheme != ''
    
def scrap_banks():
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    links = soup.find_all(filter_links)
    csv_name = "banks.csv"
    with open(csv_name, "w", encoding="utf-8") as file:
        file.write('Continent;Country;Category;Name\n')
        for link in links:
            new_url = link['href']    
            continent = new_url.replace("wiki/List_of_banks_in_", '')
            continent = continent.replace("/", '').replace("the_", '')
            bk_page = requests.get(wiki_url + new_url)
            bk_soup = BeautifulSoup(bk_page.content, "html.parser")
            h2_tags = bk_soup.find_all("h2")
            for h2_tag in h2_tags:
                span_tag = h2_tag.find("span", class_="mw-headline")
                if span_tag:
                    pays = span_tag.get_text()
                    if pays not in excludes:
                        next_element = h2_tag.next_sibling
                        categorie = ''
                        while next_element:
                            if next_element.name == "h3":
                                span_stag = next_element.find("span", class_="mw-headline")
                                if span_stag:
                                    categorie = ''.join([str(item) for item in span_stag.contents if isinstance(item, str)])
                                    
                            if pays  == 'Nigeria'  and next_element.name == "p":
                                a_stag = next_element.find("a")
                                if a_stag.find_parent("sup") is None:
                                    categorie = ''.join([str(item) for item in a_stag.contents if isinstance(item, str)])
                                    
                            if next_element.name == "h2":
                                break
                                
                            if next_element.name == "ul":
                                a_tags = next_element.find_all("a")
                                a_tags_filtered = []
                                for a_tag in a_tags:
                                    if a_tag.find_parent("sup") is None and a_tag.find_parent("i") is None and a_tag.find_previous_sibling("a") is None:
                                        a_tags_filtered.append(a_tag)
                                for a_tag in a_tags_filtered:
                                    banque = a_tag.get_text()
                                    if not is_link(banque): 
                                        file.write(continent+';'+pays+';'+categorie+';'+banque+'\n')
                            next_element = next_element.next_sibling
            return csv_name
    return None
    
def convert_csv_to_list(csv):
    df = pd.read_csv(csv, sep=';')
    return [df.columns.values.tolist()] + df.values.tolist()

def write_gsheet(liste):
    scope = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name("gs_credentials.json", scope)
    client = gspread.authorize(credentials)
    sheet_name = "BankList"
    sheet = client.create(sheet_name)
    sheet.share('xxx@gmail.com', perm_type='user', role='writer')
    sheet = client.open(sheet_name).sheet1
    sheet.update(liste)

csv = scrap_banks()
if csv is not None:
    liste = convert_csv_to_list(csv)
    write_gsheet(liste)