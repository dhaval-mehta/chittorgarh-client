from chittorgarh_client.client import InvestorGainClient

for ipo in InvestorGainClient().get_sme_ipos():
    print(ipo.__dict__)
