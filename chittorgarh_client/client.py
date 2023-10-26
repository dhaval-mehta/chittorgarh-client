from typing import Dict, List

import requests
from lxml import html

from chittorgarh_client.mapper import build_ipo, build_ncd
from chittorgarh_client.models import IPOSubscriptionCategory, IPO, IPOType, NCD
from chittorgarh_client.utils import parse_table_from_url, parse_table


class ChittorgarhClient:
    BASE_URL = 'https://www.chittorgarh.com/'
    SUBSCRIPTION_URL = BASE_URL + 'documents/subscription/{ipo_id}/details.html'
    MAIN_BOARD_IPO_PAGE_URL = BASE_URL + 'report/mainboard-ipo-list-in-india-bse-nse/83/'
    SME_IPO_PAGE_URL = BASE_URL + 'report/sme-ipo-list-in-india-bse-sme-nse-emerge/84/'
    NCD_PAGE_URL = BASE_URL + 'report/latest-ncd-issue-in-india/27/'

    MAIN_BOARD_IPO_TABLE_XPATH = '//*[@id="report_data"]/div/table'
    SME_IPO_TABLE_XPATH = MAIN_BOARD_IPO_TABLE_XPATH
    NCD_TABLE_XPATH = MAIN_BOARD_IPO_TABLE_XPATH

    SUBSCRIPTION_XPATH = '/html/body/div/div[2]/table'

    MAIN_BOARD_IPO_DATE_FORMAT = '%b %d, %Y'

    subscription_category_mapping = {
        'QIB': IPOSubscriptionCategory.QIB,
        'NII': IPOSubscriptionCategory.NII,
        'bNII (bids above ₹10L)': IPOSubscriptionCategory.BHNI,
        'sNII (bids below ₹10L)': IPOSubscriptionCategory.SHNI,
        'Retail': IPOSubscriptionCategory.Retail,
        'Total': IPOSubscriptionCategory.Total,
    }

    def get_live_subscription_data(self, ipo_id: str | int) -> Dict[str, float]:
        table = parse_table_from_url(self.SUBSCRIPTION_URL.format(ipo_id=ipo_id), self.SUBSCRIPTION_XPATH)
        subscription_data = {}

        for category, subscription in table.items():
            category = self.subscription_category_mapping.get(category, category)
            subscription = float(subscription['Subscription (times)'])
            subscription_data[category] = subscription

        return subscription_data

    def get_mainboard_ipo_list(self) -> List[IPO]:
        data = parse_table_from_url(self.MAIN_BOARD_IPO_PAGE_URL, self.MAIN_BOARD_IPO_TABLE_XPATH)
        ipos = []
        for name, data in data.items():
            ipos.append(build_ipo(
                url=data['url'],
                name=name,
                open_date=data['Open Date'],
                close_date=data['Close Date'],
                issue_prices=data['Issue Price (Rs)'],
                issue_size=data['Issue Size (Rs Cr.)'],
                ipo_type=IPOType.EQUITY,
                date_format=self.MAIN_BOARD_IPO_DATE_FORMAT,
            ))
        return ipos

    def get_sme_ipo_list(self) -> List[IPO]:
        data = parse_table_from_url(self.SME_IPO_PAGE_URL, self.SME_IPO_TABLE_XPATH)
        ipos = []
        for name, data in data.items():
            ipos.append(build_ipo(
                url=data['url'],
                name=name,
                open_date=data['Open Date'],
                close_date=data['Close Date'],
                issue_prices=data['Issue Price (Rs)'],
                issue_size=data['Issue Size (Rs Cr.)'],
                ipo_type=IPOType.SME,
                date_format=self.MAIN_BOARD_IPO_DATE_FORMAT,
            ))
        return ipos

    def get_ncd_list(self, year=None) -> List[NCD]:
        params = {}
        if year is not None:
            params['year'] = year
        response = requests.get(url=self.NCD_PAGE_URL, params=params)
        response.raise_for_status()
        table = html.fromstring(response.text).xpath(self.NCD_TABLE_XPATH)
        if len(table) != 1:
            print('Failed to parse table')

        data = parse_table(table[0])
        ncds = []
        for name, details in data.items():
            ncds.append(build_ncd(
                url=details['url'],
                name=name,
                open_date=details['Issue Open'],
                close_date=details['Issue Close'],
                base_size=details['Issue Size - Base (Rs Cr)'],
                shelf_size=details['Issue Size - Shelf (Rs Cr)'],
                rating=details['Rating'],
                date_format=self.MAIN_BOARD_IPO_DATE_FORMAT,
            ))
        return ncds


class InvestorGainClient:
    BASE_URL = 'https://www.investorgain.com/'

    MAIN_BOARD_IPO_PAGE_URL = BASE_URL + '/report/live-ipo-gmp/331/ipo'
    SME_IPO_PAGE_URL = BASE_URL + '/report/live-ipo-gmp/331/sme'

    MAIN_BOARD_IPO_TABLE_XPATH = '/html/body/div[7]/div[3]/div[1]/div[4]/div/div/div[2]/table'
    SME_IPO_TABLE_XPATH = MAIN_BOARD_IPO_TABLE_XPATH

    IPO_PAGE_DATE_FORMAT = '%d-%b'

    def get_mainboard_ipo_list(self) -> List[IPO]:
        data = parse_table_from_url(self.MAIN_BOARD_IPO_PAGE_URL, self.MAIN_BOARD_IPO_TABLE_XPATH)
        ipos = []
        for name, data in data.items():
            ipos.append(build_ipo(
                url=data['url'],
                name=name,
                open_date=data['Open'],
                close_date=data['Close'],
                issue_prices=data['Price'],
                issue_size=data['IPO Size'],
                ipo_type=IPOType.EQUITY,
                date_format=self.IPO_PAGE_DATE_FORMAT,
                gmp=data['GMP(â\x82¹)'],
            ))
        return ipos

    def get_sme_ipo_list(self) -> List[IPO]:
        data = parse_table_from_url(self.SME_IPO_PAGE_URL, self.SME_IPO_TABLE_XPATH)
        ipos = []
        for name, data in data.items():
            ipos.append(build_ipo(
                url=data['url'],
                name=name,
                open_date=data['Open Date'],
                close_date=data['Close Date'],
                issue_prices=data['Issue Price (Rs)'],
                issue_size=data['Issue Size (Rs Cr.)'],
                ipo_type=IPOType.SME,
                date_format=self.IPO_PAGE_DATE_FORMAT,
            ))
        return ipos
