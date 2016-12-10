import just
usm = just.read("data/money/us.json")

usd_min = set([x[0] for x in usm['symbols']["$"]] +
              [x[0] for x in usm['currencies']["dollar"]] +
              [x[0] for x in usm['currencies']["bucks"]])

usm['keywords'] = {k: v for k, v in usm['keywords'].items() if v in usd_min}
usm['symbols'] = {"$": usm['symbols']['$']}
usm['currencies'] = {"dollar": usm['currencies']['dollar'],
                     "bucks": usm['currencies']['bucks']}
usm['abbrevs'] = [x for x in usm['abbrevs'] if x in usm['keywords'].values()]

usm = just.write(usm, "data/money/us_min.json")
