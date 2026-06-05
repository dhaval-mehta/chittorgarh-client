from chittorgarh_client.client import InvestorGainClient, ChittorgarhClient


for ipo in ChittorgarhClient().get_live_subscription(2586):
    print(ipo.__dict__)
