import pandas as pd
import requests
import re
import time
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import numpy as np
import itertools
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# similarity = lambda x: np.mean([SequenceMatcher(None, a,b).ratio() for a,b in itertools.combinations(x, 2)])

def similarity(search_text, result):
    search_array = search_text.lower().split(" ")
    result_array = result.lower().split(" ")

    count = 0

    while count < len(search_array) and count < len(result_array) and result_array[count] == search_array[count]:
        count = count + 1

    return count / len(result_array)


# Get data frame from excel
def get_data_frame():
    # Read excel file
    excel = pd.read_excel(r'./excel.xlsx')

    # Prepare data_frame
    data_frame = pd.DataFrame(excel, columns=['Phone'])
    data_frame.insert(1, column='tgdd_phone', value='')
    data_frame.insert(2, column='tgdd_price', value='')
    data_frame.insert(3, column='tgdd_promotion', value='')
    data_frame.insert(4, column='fpt_phone', value='')
    data_frame.insert(5, column='fpt_price', value='')
    data_frame.insert(6, column='fpt_promotion', value='')
    data_frame.insert(7, column='vt_phone', value='')
    data_frame.insert(8, column='vt_price', value='')
    data_frame.insert(9, column='vt_promotion', value='')

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

    search_results = html.find_all('li', class_='cat42')

    if len(search_results) == 0:
        print('not found')
        return 0, 0, ''

    search_phone = ''
    max_index = 0
    max_match = 0
    for index, search_result in enumerate(search_results):
        search_result_phone_name = search_result.find('h3')
        match_percent = similarity(phoneName, search_result_phone_name.text)
        if match_percent > max_match:
          max_match = match_percent
          search_phone = search_result_phone_name.text
          max_index = index

    detail_page_link = search_results[max_index].find('a').get('href')

    # parse price from detail page
    detail_html = get_html(f'{base_link}{detail_page_link}')

    # get price
    price = 0
    area_price = detail_html.find('div', class_='area_price')
    if area_price:
      price = area_price.get_text()

    # get promotion
    promotion = ''
    area_promotion = detail_html.find('div', class_=re.compile('area_promotion.*'))
    if area_promotion:
      info_prs = area_promotion.find_all('div', class_='infopr', recursive=False)
      for info in info_prs:
          promotion += info.text

    print(f'found {search_phone}')
    return price, promotion, search_phone

def get_phone_info_at_fpt(phoneName):
    print(f'===> searching {phoneName} at FPT')

    # prepare search link
    base_link = 'https://fptshop.com.vn'
    keyword = phoneName.replace(' ', '-')
    search_link = f'{base_link}/tim-kiem/{keyword}'

    # parse product link from search result
    html = get_html(search_link)
    search_results = html.find_all('div', class_='fs-lpitem')

    if len(search_results) == 0:
        print('not found')
        return 0, 0, ''

    search_phone = ''
    max_index = 0
    max_match = 0
    for index, search_result in enumerate(search_results):
      search_result_phone_name = search_result.find('h3')
      match_percent = similarity(phoneName, search_result_phone_name.text)
      if match_percent > max_match:
        max_match = match_percent
        search_phone = search_result_phone_name.text
        max_index = index

    detail = search_results[max_index]

    if not detail:
        # Exit because cannot found phone in store
        print('not found')
        return 0, 0, ''

    # parse price from detail page
    detail_page_link = detail.find('a').get('href')
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

    print(f'found {search_phone}')
    return price, promotion, search_phone

def get_phone_info_at_viettel(phoneName):
    print(f'===> searching {phoneName} at Viettel')
    base_link = 'https://viettelstore.vn'
    request = requests.post(url = 'https://viettelstore.vn/Site/_Sys/GetUserControl.aspx', data = {
        'path': 'ProductList3Col',
        'KeyWord': phoneName,
        'customChangePage_divContainer': '#div_Danh_Sach_San_Pham',
        'UseCustomChangePage': 0,
        'PaginationVisiable': 0,
        'CatID': None,
        'PageSize': 12,
        'CurrentPage': 1,
        'SpecOrder': 'GiaThapDan',
        'SpecFilter': None,
        'FeatureFilter': None,
        'isHot': None,
    })
    html = BeautifulSoup(request.text, 'html.parser')
    search_results = html.find_all('div', class_='ProductList3Col_item')

    if len(search_results) == 0:
        print('not found')
        return 0, 0, ''

    search_phone = ''
    max_index = 0
    max_match = 0
    for index, search_result in enumerate(search_results):
      search_result_phone_name = search_result.find('p')
      match_percent = similarity(phoneName, search_result_phone_name.text)
      if match_percent > max_match:
        max_match = match_percent
        search_phone = search_result_phone_name.text
        max_index = index

    phone = search_results[max_index]

    if not phone:
        print('not found')
        return 0, 0, ''

    # Get detail page
    detail_page_link = phone.find('a').get('href')
    detail_html = get_html(f'{base_link}{detail_page_link}')

    # Get price
    price_div = detail_html.find('span', id='_price_new436')
    if not price_div:
        print('not found')
        return 0, 0, ''

    price = price_div.text

    # Get promotion
    promotion_area = detail_html.find('div', class_='body-promotion')
    if not promotion_area:
        print('not found')
        return 0, 0, ''

    promotion = promotion_area.text

    print(f'found {search_phone}')
    return price, promotion, search_phone

data_frame = get_data_frame()
for index, row in data_frame.iterrows():
    # delay before run another round
    time.sleep(5)

    phone_name = row['Phone']

    # TheGioiDiDong
    price, promotion, search_phone = get_phone_info_at_tgdd(phone_name)
    data_frame.set_value(index, 'tgdd_price', price)
    data_frame.set_value(index, 'tgdd_promotion', promotion)
    data_frame.set_value(index, 'tgdd_phone', search_phone)

    # FPT
    fpt_price, fpt_promotion, fpt_search_phone = get_phone_info_at_fpt(phone_name)
    data_frame.set_value(index, 'fpt_price', fpt_price)
    data_frame.set_value(index, 'fpt_promotion', fpt_promotion)
    data_frame.set_value(index, 'fpt_phone', fpt_search_phone)

    # Viettel Store
    vt_price, vt_promotion, vt_search_phone = get_phone_info_at_viettel(phone_name)
    data_frame.set_value(index, 'vt_price', vt_price)
    data_frame.set_value(index, 'vt_promotion', vt_promotion)
    data_frame.set_value(index, 'vt_phone', vt_search_phone)

data_frame.to_excel('result.xlsx')

# price, promotion, search_phone = get_phone_info_at_fpt('Oppo F11')
# price, promotion, search_phone = get_phone_info_at_fpt('xiaomi redmi note 8 64gb')
# print(price)
# print(promotion)
# print(search_phone)
