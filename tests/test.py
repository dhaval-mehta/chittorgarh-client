import datetime

from chittorgarh_client.client import ChittorgarhClient, InvestorGainClient

ipos = ChittorgarhClient().get_mainboard_ipos()
ipos = [ipo for ipo in ipos if ipo.close_date and datetime.date.today() == ipo.close_date]
for ipo in ipos:
    subscription = ChittorgarhClient().get_live_subscription(ipo.id)
    print(subscription)