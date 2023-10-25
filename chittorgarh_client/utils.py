import datetime
from typing import Dict, Optional

import requests
from lxml import html

from chittorgarh_client.models import IPO


def parse_table_from_url(url: str, xpath: str) -> Dict[str, Dict[str, str]]:
    response = requests.get(url=url)
    response.raise_for_status()
    table = html.fromstring(response.text).xpath(xpath)
    if len(table) != 1:
        print('Failed to parse table')
    return parse_table(table[0])


def parse_table(html_table) -> Dict[str, Dict[str, str]]:
    table = {}
    headers = [header.text_content() for header in html_table.findall('thead')[0].findall('tr')[0].findall('th')][1:]

    html_rows = html_table.findall('tbody')[0].findall('tr')
    for html_row in html_rows:
        children = html_row.getchildren()
        row = {}

        if len(children) == 1:
            continue

        key = children[0].text_content()
        for grandchild in children[0].getchildren():
            if grandchild.tag == 'a':
                row['url'] = grandchild.attrib['href'].strip()
                key = grandchild.xpath('text()')
                key = key[0] if len(key) > 0 else grandchild.text_content()
                break

        for index, td in enumerate(children[1:]):
            row[headers[index].strip()] = td.text_content().strip()

        for child in children:
            for grandchild in child.getchildren():
                if grandchild.tag == 'a':
                    row['url'] = grandchild.attrib['href'].strip()

        table[key] = row

    return table


def parse_row_based_table_from_url(url: str, xpath: str) -> Dict[str, Dict[str, str]]:
    response = requests.get(url=url)
    response.raise_for_status()
    table = html.fromstring(response.text).xpath(xpath)
    if len(table) != 1:
        print('Failed to parse table')
    return parse_row_based_table_from_url(table[0])


def parse_row_based_table(html_table) -> Dict[str, str]:
    table = {}
    rows = html_table.findall('tbody')[0].findall('tr')
    for row in rows:
        key, value = [td.text_content().strip() for td in row.findall('td')]
        table[key] = value
    return table


def is_blank(s: str) -> bool:
    return s is None \
        or s == '' \
        or s.casefold() == 'na'.casefold() \
        or s == '--'


def build_ipo(url: str, name: str, open_date: str, close_date: str, issue_prices: str,
              issue_size: str, ipo_type: str, date_format: str, gmp: Optional[str] = None) -> IPO:
    def parse_date(date):
        if date == '':
            return date
        try:
            date = datetime.datetime.strptime(date, date_format).date()
            if date.year == 1900:
                date = date.replace(year=datetime.datetime.now().year)
            return date
        except ValueError:
            raise Exception('failed to parse start date')

    try:
        issue_size = round(float(issue_size), 2)
    except ValueError:
        pass

    open_date = parse_date(open_date)
    close_date = parse_date(close_date)

    issue_prices = issue_prices.split(" ")
    if len(issue_prices) == 3:
        issue_price = int(float(issue_prices[2]))
    elif len(issue_prices) == 1 and not is_blank(issue_prices[0]):
        issue_price = int(float(issue_prices[0]))
    else:
        issue_price = ''

    if not is_blank(gmp):
        gmp = int(gmp)

    name = name.replace("ipo", '').replace("IPO", '').replace("Ipo", '').strip()
    return IPO(
        id=url,
        name=name,
        start_date=open_date,
        end_date=close_date,
        lot_size='',
        issue_price=issue_price,
        issue_size=issue_size,
        ipo_type=ipo_type,
        gmp=gmp,
    )
