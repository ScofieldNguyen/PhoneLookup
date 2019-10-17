import pandas as pd
import requests
import re
import time
from bs4 import BeautifulSoup

# Get data frame from excel
def get_data_frame():
    # Read excel file
    excel = pd.read_excel(r'./excel.xlsx')

    # Prepare data_frame
    data_frame = pd.DataFrame(excel, columns=['Phone'])
    data_frame.insert(1, column='tgdd_price', value='')
    data_frame.insert(2, column='tgdd_promotion', value='')
    data_frame.insert(3, column='fpt_price', value='')
    data_frame.insert(4, column='fpt_promotion', value='')
    data_frame.insert(5, column='vt_price', value='')
    data_frame.insert(6, column='vt_promotion', value='')

    return data_frame

def get_html(url):
    code = requests.get(url)
    plain = code.text
    html = BeautifulSoup(plain, 'html.parser')
    return html

def get_phone_info_at_tgdd(phoneName):
    print(f'===> searching {phoneName} at thegioididong')
    # prepare search link
    base_link = 'https://www.thegioididong.com'
    keyword = phoneName.replace(' ', '+')
    search_link = f'{base_link}/tim-kiem?key={keyword}'

    # parse product link from search result
    html = get_html(search_link)
    detail_page_link = html.find_all('li', class_='cat42')[0].find('a').get('href')

    # parse price from detail page
    detail_html = get_html(f'{base_link}{detail_page_link}')

    # get price
    price = 0
    area_price = detail_html.find('div', class_='area_price')
    if area_price:
      price = area_price.find('strong').get_text()

    # get promotion
    promotion = ''
    area_promotion = detail_html.find('div', class_=re.compile('area_promotion.*'))
    if area_promotion:
      info_prs = area_promotion.find_all('div', class_='infopr')
      for info in info_prs:
          promotion += info.text

    return price, promotion

def get_phone_info_at_fpt(phoneName):
    print(f'===> searching {phoneName} at FPT')

    # prepare search link
    base_link = 'https://fptshop.com.vn'
    keyword = phoneName.replace(' ', '-')
    search_link = f'{base_link}/tim-kiem/{keyword}'

    # parse product link from search result
    html = get_html(search_link)
    detail_page_link = html.find_all('div', class_='fs-lpitem')[0].find('a').get('href')

    # parse price from detail page
    detail_html = get_html(f'{base_link}{detail_page_link}')

    # get price
    price = 0
    area_price = detail_html.find('p', class_='fs-dtprice')
    if area_price:
      price = area_price.text

    # get promotion
    promotion = ''
    area_promotion = detail_html.find('div', class_="fk-sales")
    if area_promotion:
      promotion = area_promotion.text

    return price, promotion

data_frame = get_data_frame()
for index, row in data_frame.iterrows():
    # delay before run another round
    time.sleep(5)

    phone_name = row['Phone']

    # TheGioiDiDong
    price, promotion = get_phone_info_at_tgdd(phone_name)
    data_frame.set_value(index, 'tgdd_price', price)
    data_frame.set_value(index, 'tgdd_promotion', promotion)

    # FPT
    fpt_price, fpt_promotion = get_phone_info_at_fpt(phone_name)
    data_frame.set_value(index, 'fpt_price', fpt_price)
    data_frame.set_value(index, 'fpt_promotion', fpt_promotion)


# get_phone_info_at_fpt('Vivo S1')
data_frame.to_excel('result.xlsx')
