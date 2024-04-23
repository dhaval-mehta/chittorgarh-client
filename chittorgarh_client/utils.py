import re
from typing import Dict

import requests
from lxml import html

from chittorgarh_client.models import IPOSubscriptionCategory, Subscription


def parse_table_from_url(url: str, xpath: str) -> Dict[str, Dict[str, str]]:
    response = requests.get(url=url)
    response.raise_for_status()
    table = html.fromstring(response.text).xpath(xpath)
    if len(table) != 1:
        raise Exception('Failed to parse table')
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
            k = remove_non_ascii(headers[index].strip())
            row[k] = remove_non_ascii(td.text_content().strip())

        table[remove_non_ascii(key)] = row

    return table


def parse_row_based_table_from_url(url: str, xpath: str) -> Dict[str, Dict[str, str]]:
    response = requests.get(url=url)
    response.raise_for_status()
    table = html.fromstring(response.text).xpath(xpath)
    if len(table) != 1:
        print('Failed to parse table')
    return parse_row_based_table_from_url(table[0], xpath)


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


def remove_non_ascii(text):
    return re.sub(r'[^\x00-\x7F]', "", text).strip()


def get_allotment_probabilities(subscription: Dict[str, Subscription]):
    allotment_probabilities = {}
    eligible_categories = [IPOSubscriptionCategory.BHNI, IPOSubscriptionCategory.SHNI, IPOSubscriptionCategory.Retail]
    multipliers = {
        IPOSubscriptionCategory.BHNI: 5
    }

    for k, v in subscription.items():
        if k not in eligible_categories:
            continue
        if v.subscription_percentage == 0:
            allotment_probabilities[k] = 100
            continue
        allotment_probabilities[k] = min(round(100 / v.subscription_percentage * multipliers.get(k, 1), 2), 100)
    return allotment_probabilities


def get_number_or_input(x):
    try:
        return float(x)
    except ValueError:
        return x


def get_acceptance_ratios(subscription: Dict[str, Subscription]):
    acceptance_ratios = {}
    eligible_categories = [IPOSubscriptionCategory.BHNI, IPOSubscriptionCategory.SHNI, IPOSubscriptionCategory.Retail]
    multipliers = {
        IPOSubscriptionCategory.BHNI: 5
    }

    for k, v in subscription.items():
        if k not in eligible_categories:
            continue

        ratio = v.subscription_percentage * 0.95 / multipliers.get(k, 1)

        if ratio <= 1:
            acceptance_ratios[k] = 'Confirmed'
        else:
            acceptance_ratios[k] = f'1 out of {ratio:.2f}'

    return acceptance_ratios
