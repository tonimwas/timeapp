import json

# Data from the user
data_lines = [
    "36.8253214\t-1.2836855\tQuickMart\tNyeri",
    "36.7627444\t-1.2979509\tOptica\tNyeri",
    "37.0752267\t0.01483\tChieni Supermarket\tNyeri",
    "36.9053368\t-0.4974289\tHopetech Computer Services\tNyeri",
    "37.077369\t0.0134831\tNanyuki General Merchants\tNyeri",
    "36.802103\t-1.2640185\tQuickMart\tNyeri",
    "37.0657504\t-0.168783\tWamboo Shopping Center\tNyeri",
    "37.1339699\t-0.4846967\tOmega Supermarkets\tNyeri",
    "37.124532\t-0.4832383\tMathai Supermarket (Karatina)\tNyeri",
    "36.9846716\t-0.4447345\tWambuguapple Farm\tNyeri",
    "36.9758261\t-0.4369553\tM-Pesa Samchi Telecomms\tNyeri",
    "36.9549134\t-0.4371666\tCiaraini Centre\tNyeri",
    "36.955685\t-0.4249194\tNyeri Mall\tNyeri",
    "36.9553429\t-0.4248746\tNaivas Supermarket Nyeri\tNyeri",
    "36.9533905\t-0.4218719\tChieni Supermarket\tNyeri",
    "36.9525446\t-0.4223856\tPrestige Plaza\tNyeri",
    "36.7109034\t-0.1419543\tNairutia Shopping center\tNyeri",
    "36.9053387\t-0.3283856\tEP Communications-Mweiga\tNyeri",
    "37.044278\t-0.0618353\tOne Stop Nanyuki\tNyeri",
    "36.8949022\t-1.3137528\tQuickMart\tNyeri",
    "36.773464\t-1.2899363\tQuickMart\tNyeri",
    "37.0755447\t0.0107654\tQuickMart\tNyeri",
    "37.021653\t-0.1699301\tChieni\tNyeri",
    "37.0445429\t-0.062421\tNanmatt Farm Shop\tNyeri",
    "36.8313768\t-1.2849108\tQuickMart\tNyeri",
    "36.7634333\t-1.2636307\tQuickMart\tNyeri",
    "36.9150496\t-1.3136754\tQuickMart\tNyeri",
    "36.9015966\t-1.1835102\tQuickMart\tNyeri",
    "36.7831953\t-1.2981566\tQuickMart\tNyeri",
    "36.8169343\t-1.3122508\tQuickMart\tNyeri",
    "36.7928528\t-1.2930205\tQuickMart\tNyeri",
    "37.0250809\t-0.5024762\tjawa hardware\tNyeri",
    "37.0393846\t-0.5095959\tmaina-road shop\tNyeri",
    "37.013386\t-0.5033037\tSHOP\tNyeri",
    "37.1512442\t-0.4017143\tKanjuri Shopping Centre\tNyeri",
    "37.1537398\t-0.398397\tJasho Bakers\tNyeri",
    "37.1561257\t-0.4005423\tRiverside Kiosk\tNyeri",
    "36.8267881\t-1.288442\tQuickMart\tNyeri",
    "37.0754509\t0.0106039\tOptica\tNyeri",
    "35.8699563\t-1.091939\tQuickMart\tNyeri",
    "36.9612224\t-0.3988572\tWorkshop\tNyeri",
    "36.9608705\t-0.3981157\trc 15\tNyeri"
]

places = []
slug_count = {}

for line in data_lines:
    parts = line.split('\t')
    if len(parts) == 4:
        lng = float(parts[0])
        lat = float(parts[1])
        if lat > 0:  # Fix positive lat
            lat = -lat
        name = parts[2]
        neighbourhood = parts[3]
        base_slug = name.lower().replace(' ', '-').replace('(', '').replace(')', '').replace('&', 'and').replace("'", '')
        count = slug_count.get(base_slug, 0) + 1
        slug_count[base_slug] = count
        slug = f"{base_slug}-{count}" if count > 1 else base_slug
        place = {
            "slug": slug,
            "name": name,
            "category": "Shop",
            "neighbourhood": neighbourhood,
            "lat": lat,
            "lng": lng,
            "entry_fee": 0,
            "avg_food": 0,
            "duration_min": 30,
            "rating": 3.5,
            "price_tier": "Budget",
            "tags": ["shop"],
            "vibes": ["local"],
            "popularity": 0.4
        }
        places.append(place)

with open('nyeri_shops.json', 'w') as f:
    json.dump(places, f, indent=4)

print(f"Generated {len(places)} places.")
