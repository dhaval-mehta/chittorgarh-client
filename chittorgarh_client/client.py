import datetime
from typing import Dict

from .models import IPOSubscriptionCategory, IPO, IPOType
from .utils import parse_table_from_url, build_ipo


class ChittorgarhClient:
    BASE_URL = 'https://www.chittorgarh.com/'
    SUBSCRIPTION_URL = BASE_URL + 'documents/subscription/{ipo_id}/details.html'
    MAIN_BOARD_IPO_PAGE_URL = BASE_URL + 'report/mainboard-ipo-list-in-india-bse-nse/83/'
    SME_BOARD_IPO_PAGE_URL = BASE_URL + 'report/sme-ipo-list-in-india-bse-sme-nse-emerge/84/'

    MAIN_BOARD_TABLE_XPATH = '//*[@id="report_data"]/div/table'
    SUBSCRIPTION_XPATH = '/html/body/div/div[2]/table'

    MAIN_BOARD_IPO_DATE_FORMAT = '%b %d, %Y'
    GMP_DATE_FORMAT = '%d-%b'

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

    def get_mainboard_ipo_list(self) -> list[IPO]:
        data = parse_table_from_url(self.MAIN_BOARD_IPO_PAGE_URL, self.MAIN_BOARD_TABLE_XPATH)
        ipos = []
        for name, data in data.items():
            ipos.append(self._parse_equity_ipo_data(
                url=data['url'],
                name=name,
                start_date=data['Open Date'],
                end_date=data['Close Date'],
                issue_prices=data['Issue Price (Rs)'],
                issue_size=data['Issue Size (Rs Cr.)'],
                ipo_type=IPOType.EQUITY
            ))
        return ipos

    def get_sme_ipo_list(self) -> list[IPO]:
        data = parse_table_from_url(self.SME_BOARD_IPO_PAGE_URL, self.MAIN_BOARD_TABLE_XPATH)
        ipos = []
        for name, data in data.items():
            ipos.append(self._parse_equity_ipo_data(
                url=data['url'],
                name=name,
                start_date=data['Open Date'],
                end_date=data['Close Date'],
                issue_prices=data['Issue Price (Rs)'],
                issue_size=data['Issue Size (Rs Cr.)'],
                ipo_type=IPOType.SME
            ))
        return ipos

    def _parse_equity_ipo_data(self, url, name, start_date, end_date, issue_prices, issue_size, ipo_type):
        issue_prices = issue_prices.split(" ")
        try:
            issue_size = round(float(issue_size), 2)
        except ValueError:
            pass

        if start_date != '':
            try:
                start_date = datetime.datetime.strptime(start_date, self.MAIN_BOARD_IPO_DATE_FORMAT).date()
            except ValueError:
                raise Exception('failed to parse start date')

        if end_date != '':
            try:
                end_date = datetime.datetime.strptime(end_date, self.MAIN_BOARD_IPO_DATE_FORMAT).date()
            except ValueError:
                raise Exception('failed to parse end date')

        if len(issue_prices) == 3:
            issue_price = int(float(issue_prices[2]))
        elif len(issue_prices) == 1 and issue_prices[0] != '':
            issue_price = int(float(issue_prices[0]))
        else:
            issue_price = ''

        name = name.replace("ipo", '').replace("IPO", '').replace("Ipo", '').strip()
        return IPO(
            id=url,
            name=name,
            start_date=start_date,
            end_date=end_date,
            lot_size='',
            issue_price=issue_price,
            issue_size=issue_size,
            ipo_type=ipo_type,
        )


class InvestorGainClient:
    BASE_URL = 'https://www.investorgain.com/'
    IPO_PAGE_URL = BASE_URL + '/report/live-ipo-gmp/331/ipo'

    IPO_PAGE_TABLE_XPATH = '/html/body/div[7]/div[3]/div[1]/div[4]/div/div/div[2]/table'

    IPO_PAGE_DATE_FORMAT = '%d-%b'

    def get_mainboard_ipo_list(self) -> list[IPO]:
        data = parse_table_from_url(self.IPO_PAGE_URL, self.IPO_PAGE_TABLE_XPATH)
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

    def get_sme_ipo_list(self) -> list[IPO]:
        data = parse_table_from_url(self.SME_BOARD_IPO_PAGE_URL, self.MAIN_BOARD_TABLE_XPATH)
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

