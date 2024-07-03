import datetime
from typing import Optional

from chittorgarh_client.models import IPO, NCD, BuyBack
from chittorgarh_client.utils import is_blank, get_number_or_input


def parse_date(date, date_format):
    if date == '' or date is None:
        return date
    if 'y' not in date_format.lower():
        date_format += '|%Y'
        date += '|2000'
    try:
        date = datetime.datetime.strptime(date, date_format).date()
        today = datetime.date.today()
        if date.year == 2000:
            date = date.replace(year=today.year)
            if (today - date).days > 180:
                date = date.replace(year=date.year + 1)
            elif (date - today).days > 90:
                date = date.replace(year=date.year - 1)
        return date
    except ValueError:
        raise Exception('failed to parse start date')


def build_ipo(url: str, name: str, open_date: str, close_date: str, issue_prices: str,
              issue_size: str, ipo_type: str, date_format: str, gmp: Optional[str] = None,
              allotment_date: Optional[str] = None, listing_date: Optional[str] = None) -> IPO:
    try:
        issue_size = round(float(issue_size), 2)
    except ValueError:
        pass

    open_date = parse_date(open_date, date_format)
    close_date = parse_date(close_date, date_format)
    allotment_date = parse_date(allotment_date, date_format)
    listing_date = parse_date(listing_date, date_format)

    issue_prices = issue_prices.split(" ")
    if len(issue_prices) == 3:
        issue_price = int(float(issue_prices[2]))
    elif len(issue_prices) == 1 and not is_blank(issue_prices[0]):
        issue_price = int(float(issue_prices[0]))
    else:
        issue_price = ''

    if not is_blank(gmp):
        gmp = float(gmp)
    else:
        gmp = None

    if url.endswith('/'):
        url = url[:len(url) - 1]

    name = name.replace("ipo", '').replace("IPO", '').replace("Ipo", '').strip()
    return IPO(
        id=url.split('/')[-1],
        name=name,
        open_date=open_date,
        close_date=close_date,
        allotment_date=allotment_date,
        listing_date=listing_date,
        lot_size='',
        issue_price=issue_price,
        issue_size=issue_size,
        ipo_type=ipo_type,
        gmp=gmp,
    )


def build_ncd(url: str, name: str, open_date: str, close_date: str, base_size: str, shelf_size: str, rating: str,
              date_format: str) -> NCD:
    open_date = parse_date(open_date, date_format)
    close_date = parse_date(close_date, date_format)

    return NCD(
        id=url,
        name=name,
        open_date=open_date,
        close_date=close_date,
        base_size=base_size,
        shelf_size=shelf_size,
        rating=rating,
    )


def build_buy_back(url: str, name: str, record_date: str, open_date: str, close_date: str, buy_back_price: str,
                   market_price: str, issue_size: str, date_format: str) -> BuyBack:
    record_date = parse_date(record_date, date_format)
    open_date = parse_date(open_date, date_format)
    close_date = parse_date(close_date, date_format)
    buy_back_price = get_number_or_input(buy_back_price)
    market_price = get_number_or_input(market_price)
    issue_size = get_number_or_input(issue_size)

    return BuyBack(
        id=url,
        name=name,
        record_date=record_date,
        open_date=open_date,
        close_date=close_date,
        buy_back_price=buy_back_price,
        market_price=market_price,
        issue_size=issue_size,
    )
