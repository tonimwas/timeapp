import json

# Approximate coordinates for cities in Nyeri region
approx_coords = {
    "Nyeri": (-0.42, 36.95),
    "Karatina": (-0.49, 37.13),
    "Nanyuki": (-0.02, 37.07),
    "Naro Moru": (-0.17, 37.02),
    "Gitinga Village": (-0.02, 37.07),  # Approximate to Nanyuki
    "Muiga": (-0.42, 36.95),  # Approximate to Nyeri
    "Thomson's Falls": (-0.53, 37.02),
    "Naru Moru": (-0.17, 37.02)  # Same as Naro Moru
}

# List of hotels from the CSV data
hotels = [
    {"name": "Fishing Lodge", "city": "Nyeri"},
    {"name": "Aberdare Country Club", "city": "Nyeri"},
    {"name": "Hotel Starbucks", "city": "Karatina"},
    {"name": "Express Inn", "city": "Nyeri"},
    {"name": "Serena Mountain Lodge", "city": "Nyeri"},
    {"name": "Mount Kenya Safari Club", "city": "Nyeri"},
    {"name": "Calabash Inn", "city": "Karatina"},
    {"name": "Batain’s View Campsite", "city": "Nyeri"},
    {"name": "Oldoiyo Lengai Hotel", "city": "Karatina"},
    {"name": "Kirimara Springs Hotel", "city": "Nanyuki"},
    {"name": "The Brade Gate", "city": "Nyeri"},
    {"name": "The Old House Nanyuki", "city": "Nanyuki"},
    {"name": "Emess Hotel", "city": "Nanyuki"},
    {"name": "Maxoil Hotel", "city": "Nanyuki"},
    {"name": "Thailand Resort", "city": "Karatina"},
    {"name": "Omega Gardens Hotel", "city": "Karatina"},
    {"name": "Roswam Hotel", "city": "Karatina"},
    {"name": "Senior Chief Wambugu Hotel", "city": "Nyeri"},
    {"name": "Classic Court Hotel", "city": "Nyeri"},
    {"name": "Batian Grand Hotel", "city": "Nyeri"},
    {"name": "Eland Safari Hotel", "city": "Nyeri"},
    {"name": "Sun Guest House", "city": "Nyeri"},
    {"name": "Central Hotel Nyeri", "city": "Nyeri"},
    {"name": "Itara Garden Hotel", "city": "Nyeri"},
    {"name": "Riverside Hostel", "city": "Nyeri"},
    {"name": "Davis Court Nyeri", "city": "Nyeri"},
    {"name": "Mpeta House", "city": "Nyeri"},
    {"name": "Rhino Watch Safari Lodge", "city": "Muiga"},
    {"name": "Mt. Kenya Safari Halt Hotel", "city": "Nyeri"},
    {"name": "The Nelion", "city": "Naro Moru"},
    {"name": "Olive Shade Hotel", "city": "Naro Moru"},
    {"name": "Aberdare Prestige & Royal Cottages", "city": "Gitinga Village"},
    {"name": "Soames Hotel & Jack's Bar", "city": "Nanyuki"},
    {"name": "Napolitana Hotel", "city": "Nanyuki"},
    {"name": "Batian Guest Hotel", "city": "Nanyuki"},
    {"name": "Sarafina Art Gallery", "city": "Nanyuki"},
    {"name": "Karichota airbnb", "city": "Nyeri"},
    {"name": "Ole Samara", "city": "Nyeri"},
    {"name": "Esiankiki Resort & Spa", "city": "Nanyuki"},
    {"name": "Misty Mountain", "city": "Naru Moru"},
    {"name": "Treetops Lodge", "city": "Nyeri"},
    {"name": "Thomson's Falls Lodge", "city": "Thomson's Falls"}
]

places = []
for hotel in hotels:
    name = hotel['name']
    city = hotel['city']
    lat, lng = approx_coords.get(city, (-0.42, 36.95))  # Default to Nyeri if not found
    slug = name.lower().replace(' ', '-').replace('&', 'and').replace("'", '').replace('(', '').replace(')', '')
    place = {
        "slug": slug,
        "name": name,
        "category": "Hotel",
        "neighbourhood": city,
        "lat": lat,
        "lng": lng,
        "entry_fee": 0,
        "avg_food": 500,
        "duration_min": 120,
        "rating": 4.0,
        "price_tier": "Mid",
        "tags": ["hotel", "accommodation"],
        "vibes": ["comfortable"],
        "popularity": 0.5
    }
    places.append(place)

with open('nyeri_hotels.json', 'w') as f:
    json.dump(places, f, indent=4)

print(f"Generated {len(places)} places with approximate coordinates.")
