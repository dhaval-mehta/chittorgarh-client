from typing import Dict, List, Union

import lxml.html
import requests
from lxml import html

from chittorgarh_client.mapper import build_ipo, build_ncd, build_buy_back
from chittorgarh_client.models import IPOSubscriptionCategory, IPO, IPOType, NCD, BuyBack, Subscription
from chittorgarh_client.utils import parse_table_from_url, parse_table


class ChittorgarhClient:
    BASE_URL = 'https://www.chittorgarh.com/'
    SUBSCRIPTION_URL = 'https://www.chittorgarh.net/documents/subscription/{ipo_id}/subscriptions.html'
    MAIN_BOARD_IPO_PAGE_URL = 'https://webnodejs.chittorgarh.com/cloud/report/data-read/82/1/6/2026/2026-27/0/mainboard/0?search=&v=14-08'
    SME_IPO_PAGE_URL = BASE_URL + 'report/sme-ipo-list-in-india-bse-sme-nse-emerge/84/'
    NCD_PAGE_URL = BASE_URL + 'report/latest-ncd-issue-in-india/27/'
    TENDER_BUYBACK_PAGE_URL = BASE_URL + 'report/latest-buyback-issues-in-india/80/tender-offer-buyback/'

    MAIN_BOARD_IPO_TABLE_XPATH = '//*[@id="report_data"]/div/table'
    SME_IPO_TABLE_XPATH = MAIN_BOARD_IPO_TABLE_XPATH
    NCD_TABLE_XPATH = MAIN_BOARD_IPO_TABLE_XPATH
    TENDER_BUYBACK_TABLE_XPATH = MAIN_BOARD_IPO_TABLE_XPATH
    SUBSCRIPTION_XPATH = '//table[contains(@class, "watermark")]'
    SUBSCRIPTION_HEADERS = {
        'accept': '*/*',
        'cache-control': 'no-store',
        'expires': '0',
        'origin': BASE_URL.rstrip('/'),
        'pragma': 'no-cache',
        'referer': BASE_URL,
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    }

    MAIN_BOARD_IPO_DATE_FORMAT = '%d-%b-%Y'

    live_subscription_category_mapping = {
        'QIB (Ex Anchor)': IPOSubscriptionCategory.QIB,
        'Qualified Institutions': IPOSubscriptionCategory.QIB,
        'NII': IPOSubscriptionCategory.NII,
        'Non-Institutional Buyers': IPOSubscriptionCategory.NII,
        'bNII': IPOSubscriptionCategory.BHNI,
        'sNII': IPOSubscriptionCategory.SHNI,
        'Retail': IPOSubscriptionCategory.Retail,
        'Retail Investors': IPOSubscriptionCategory.Retail,
        'Employees': IPOSubscriptionCategory.Employee,
        'Total': IPOSubscriptionCategory.Total,
    }

    def get_live_subscription(self, ipo_id: Union[str, int]) -> Dict[str, Subscription]:
        response = requests.get(
            url=self.SUBSCRIPTION_URL.format(ipo_id=ipo_id),
            params={'abc': '470'},
            headers=self.SUBSCRIPTION_HEADERS,
        )
        response.raise_for_status()
        tables = html.fromstring(response.text).xpath(self.SUBSCRIPTION_XPATH)
        if len(tables) != 1:
            raise Exception('Failed to parse table')
        table = parse_table(tables[0])
        subscription_data = {}

        for category, subscription in table.items():
            mapped_category = None
            for k, v in self.live_subscription_category_mapping.items():
                if category.startswith(k):
                    mapped_category = v

            if mapped_category is None:
                continue

            bid_amount = subscription.get('Total Amt* ( Cr.)') or subscription['Total Amount (Rs Cr.)*']
            subscription_data[mapped_category] = Subscription(
                shared_offered=int(subscription['Shares Offered*'].replace(',', '')),
                shared_bid_for=int(subscription['Shares bid for'].replace(',', '')),
                bid_amount=float(bid_amount.replace(',', '')),
            )

        return subscription_data

    def get_mainboard_ipos(self) -> List[IPO]:
        resp = requests.get(url=self.MAIN_BOARD_IPO_PAGE_URL)
        resp.raise_for_status()
        ipos = []
        for row in resp.json()['reportTableData']:
            ipos.append(build_ipo(
                url=html.fragment_fromstring(row['Company'], create_parent='div').find('.//a').get('href'),
                name=row['~compare_name'],
                open_date=row['Opening Date'],
                close_date=row['Closing Date'],
                issue_prices=row['Issue Price (Rs.)'],
                issue_size=row['Total Issue Amount (Incl.Firm reservations) (Rs.cr.)'],
                ipo_type=IPOType.EQUITY,
                date_format=self.MAIN_BOARD_IPO_DATE_FORMAT,
            ))
        return ipos

    def get_sme_ipos(self) -> List[IPO]:
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

    def get_ncds(self, year=None) -> List[NCD]:
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

    def get_buy_backs(self, year=None) -> List[BuyBack]:
        params = {}
        if year is not None:
            params['year'] = year
        response = requests.get(url=self.TENDER_BUYBACK_PAGE_URL, params=params)
        response.raise_for_status()
        table = html.fromstring(response.text).xpath(self.TENDER_BUYBACK_TABLE_XPATH)
        if len(table) != 1:
            print('Failed to parse table')

        data = parse_table(table[0])
        buybacks = []
        for name, details in data.items():
            buybacks.append(build_buy_back(
                url=details['url'],
                name=name,
                record_date=details['Record Date'],
                open_date=details['Issue Open'],
                close_date=details['Issue Close'],
                buy_back_price=details['BuyBack price (Per Share)'],
                market_price=details['Current Market Price'],
                issue_size=details['Issue Size - Amount (Cr)'],
                date_format=self.MAIN_BOARD_IPO_DATE_FORMAT,
            ))
        return buybacks


class InvestorGainClient:
    BASE_URL = 'https://webnodejs.investorgain.com'
    ORIGIN_URL = 'https://www.investorgain.com'

    MAIN_BOARD_IPO_PAGE_URL = BASE_URL + '/cloud/v2/report/data-read/331/1/6/2026/2026-27/0/ipo?search=&v=22-18'
    SME_IPO_PAGE_URL = BASE_URL + '/cloud/v2/report/data-read/331/1/6/2026/2026-27/0/sme?search=&v=22-18'

    IPO_PAGE_DATE_FORMAT = '%Y-%m-%d'

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'origin': self.ORIGIN_URL,
            'referer': self.ORIGIN_URL + '/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        })

    def get_mainboard_ipos(self) -> List[IPO]:
        data = self.session.get(self.MAIN_BOARD_IPO_PAGE_URL).json()['reportTableData']
        ipos = []
        for item in data:
            ipos.append(build_ipo(
                url=item['~urlrewrite_folder_name'],
                name=item['~ipo_name'],
                open_date=item['~Srt_Open'],
                close_date=item['~Srt_Close'],
                allotment_date=item['~Srt_BoA_Dt'],
                listing_date=item['~Str_Listing'],
                issue_prices=item['Price (₹)'],
                issue_size=item['IPO Size'].strip(),
                gmp_percentage=item['~gmp_percent_calc'],
                ipo_type=IPOType.EQUITY,
                date_format=self.IPO_PAGE_DATE_FORMAT,
            ))
        return ipos

    def get_sme_ipos(self) -> List[IPO]:
        data = self.session.get(self.SME_IPO_PAGE_URL).json()['reportTableData']
        ipos = []
        for item in data:
            ipos.append(build_ipo(
                url=item['~urlrewrite_folder_name'],
                name=item['~ipo_name'],
                open_date=item['~Srt_Open'],
                close_date=item['~Srt_Close'],
                allotment_date=item['~Srt_BoA_Dt'],
                listing_date=item['~Str_Listing'],
                issue_prices=item['Price (₹)'],
                issue_size=item['IPO Size'].strip(),
                gmp_percentage=item['~gmp_percent_calc'],
                ipo_type=IPOType.SME,
                date_format=self.IPO_PAGE_DATE_FORMAT,
            ))
        return ipos