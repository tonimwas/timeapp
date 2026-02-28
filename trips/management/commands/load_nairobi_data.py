from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from trips.models import Neighbourhood, Place, TransportEdge


@transaction.atomic
def load_nairobi_real_data(*, stdout):
    # Clear existing data
    stdout.write("Clearing existing data...")
    TransportEdge.objects.all().delete()
    Place.objects.all().delete()
    Neighbourhood.objects.all().delete()

    # --- Real Nairobi Neighbourhoods ---
    stdout.write("Creating Nairobi neighbourhoods...")
    
    neighbourhoods_data = [
        {"name": "CBD", "lat": -1.286389, "lng": 36.817223},
        {"name": "Westlands", "lat": -1.2686, "lng": 36.8046},
        {"name": "Gigiri", "lat": -1.2367, "lng": 36.8158},
        {"name": "Langata", "lat": -1.3636, "lng": 36.784},
        {"name": "Runda", "lat": -1.2139, "lng": 36.8214},
        {"name": "State House", "lat": -1.2679, "lng": 36.8082},
        {"name": "Parklands", "lat": -1.2596, "lng": 36.8226},
        {"name": "Kenyatta", "lat": -1.3301, "lng": 36.8552},
        {"name": "Kilimani", "lat": -1.2956, "lng": 36.8024},
        {"name": "Karen", "lat": -1.3358, "lng": 36.7249},
        {"name": "Eastleigh", "lat": -1.2711, "lng": 36.8489},
        {"name": "Lavington", "lat": -1.2958, "lng": 36.7613},
    ]

    neighbourhoods = {}
    for data in neighbourhoods_data:
        n = Neighbourhood.objects.create(
            name=data["name"],
            lat=data["lat"],
            lng=data["lng"],
        )
        neighbourhoods[data["name"]] = n
        stdout.write(f"  Created: {n.name}")

    # --- Real Nairobi Places ---
    stdout.write("Creating real Nairobi places...")

    places_data = [
        # Parks
        {"slug": "uhuru-park", "name": "Uhuru Park", "category": "Park", "neighbourhood": "CBD", 
         "lat": -1.286389, "lng": 36.817223, "entry_fee": 0, "avg_food": 200, "duration_min": 60,
         "rating": 4.2, "price_tier": "Free", "tags": ["nature", "lake", "walk", "relaxing"], 
         "vibes": ["chill", "scenic"], "popularity": 0.8},
        
        {"slug": "karura-forest", "name": "Karura Forest", "category": "Park", "neighbourhood": "Gigiri",
         "lat": -1.2444, "lng": 36.8253, "entry_fee": 100, "avg_food": 250, "duration_min": 180,
         "rating": 4.7, "price_tier": "Budget", "tags": ["nature", "hiking", "biking", "forest", "waterfall"],
         "vibes": ["adventurous", "scenic", "chill"], "popularity": 0.9},
        
        {"slug": "nairobi-arboretum", "name": "Nairobi Arboretum", "category": "Park", "neighbourhood": "Kilimani",
         "lat": -1.2903, "lng": 36.8037, "entry_fee": 50, "avg_food": 200, "duration_min": 90,
         "rating": 4.3, "price_tier": "Budget", "tags": ["nature", "trees", "walk", "relaxing"],
         "vibes": ["chill", "scenic", "quiet"], "popularity": 0.75},
        
        {"slug": "city-park", "name": "City Park", "category": "Park", "neighbourhood": "Parklands",
         "lat": -1.2731, "lng": 36.8267, "entry_fee": 0, "avg_food": 150, "duration_min": 60,
         "rating": 4.0, "price_tier": "Free", "tags": ["nature", "monkeys", "walk"],
         "vibes": ["chill", "scenic"], "popularity": 0.6},
        
        # Markets
        {"slug": "maasai-market", "name": "Maasai Market", "category": "Market", "neighbourhood": "CBD",
         "lat": -1.2892, "lng": 36.8219, "entry_fee": 0, "avg_food": 150, "duration_min": 90,
         "rating": 4.0, "price_tier": "Free", "tags": ["souvenirs", "handicrafts", "shopping", "culture"],
         "vibes": ["authentic", "local", "chill"], "popularity": 0.9},
        
        {"slug": "city-market", "name": "City Market", "category": "Market", "neighbourhood": "CBD",
         "lat": -1.2833, "lng": 36.8219, "entry_fee": 0, "avg_food": 200, "duration_min": 60,
         "rating": 3.8, "price_tier": "Free", "tags": ["fresh-produce", "local", "food"],
         "vibes": ["authentic", "local", "energetic"], "popularity": 0.7},
        
        {"slug": "village-market", "name": "Village Market", "category": "Mall", "neighbourhood": "Gigiri",
         "lat": -1.2291, "lng": 36.8128, "entry_fee": 0, "avg_food": 800, "duration_min": 120,
         "rating": 4.3, "price_tier": "Premium", "tags": ["shopping", "food", "entertainment", "movies"],
         "vibes": ["chill", "scenic"], "popularity": 0.85},
        
        {"slug": "westgate-mall", "name": "Westgate Mall", "category": "Mall", "neighbourhood": "Westlands",
         "lat": -1.2691, "lng": 36.8067, "entry_fee": 0, "avg_food": 600, "duration_min": 120,
         "rating": 4.1, "price_tier": "Premium", "tags": ["shopping", "cinema", "food", "entertainment"],
         "vibes": ["chill"], "popularity": 0.8},
        
        {"slug": "galleria-mall", "name": "Galleria Mall", "category": "Mall", "neighbourhood": "Langata",
         "lat": -1.3536, "lng": 36.7753, "entry_fee": 0, "avg_food": 500, "duration_min": 90,
         "rating": 3.9, "price_tier": "Mid", "tags": ["shopping", "food", "cinema", "family"],
         "vibes": ["chill"], "popularity": 0.7},
        
        {"slug": "the-hub", "name": "The Hub Karen", "category": "Mall", "neighbourhood": "Karen",
         "lat": -1.3392, "lng": 36.7148, "entry_fee": 0, "avg_food": 700, "duration_min": 120,
         "rating": 4.4, "price_tier": "Premium", "tags": ["shopping", "food", "cinema", "modern"],
         "vibes": ["chill", "scenic"], "popularity": 0.85},
        
        # Attractions
        {"slug": "nairobi-museum", "name": "Nairobi National Museum", "category": "Attraction", "neighbourhood": "CBD",
         "lat": -1.2734, "lng": 36.8162, "entry_fee": 200, "avg_food": 300, "duration_min": 120,
         "rating": 4.5, "price_tier": "Budget", "tags": ["history", "culture", "art", "artifacts"],
         "vibes": ["authentic", "local"], "popularity": 0.7},
        
        {"slug": "sarakasi-trust", "name": "Sarakasi Trust", "category": "Attraction", "neighbourhood": "CBD",
         "lat": -1.2833, "lng": 36.8219, "entry_fee": 150, "avg_food": 400, "duration_min": 90,
         "rating": 4.4, "price_tier": "Mid", "tags": ["performance", "arts", "culture", "dance", "acrobatics"],
         "vibes": ["authentic", "local"], "popularity": 0.6},
        
        {"slug": "safari-walk", "name": "Safari Walk", "category": "Attraction", "neighbourhood": "Langata",
         "lat": -1.3647, "lng": 36.8583, "entry_fee": 250, "avg_food": 350, "duration_min": 150,
         "rating": 4.3, "price_tier": "Mid", "tags": ["nature", "walk", "animals", "wildlife"],
         "vibes": ["chill", "scenic", "authentic"], "popularity": 0.75},
        
        {"slug": "giraffe-centre", "name": "Giraffe Centre", "category": "Attraction", "neighbourhood": "Langata",
         "lat": -1.3747, "lng": 36.7478, "entry_fee": 500, "avg_food": 400, "duration_min": 90,
         "rating": 4.6, "price_tier": "Mid", "tags": ["wildlife", "giraffes", "conservation", "nature"],
         "vibes": ["adventurous", "authentic", "scenic"], "popularity": 0.9},
        
        {"slug": "mamba-village", "name": "Mamba Village", "category": "Attraction", "neighbourhood": "Langata",
         "lat": -1.3558, "lng": 36.7556, "entry_fee": 300, "avg_food": 500, "duration_min": 90,
         "rating": 4.1, "price_tier": "Mid", "tags": ["crocodiles", "reptiles", "wildlife", "nature"],
         "vibes": ["adventurous", "authentic"], "popularity": 0.65},
        
        {"slug": "karen-blixen", "name": "Karen Blixen Museum", "category": "Attraction", "neighbourhood": "Karen",
         "lat": -1.3347, "lng": 36.7125, "entry_fee": 400, "avg_food": 450, "duration_min": 90,
         "rating": 4.4, "price_tier": "Mid", "tags": ["history", "colonial", "culture", "house"],
         "vibes": ["authentic", "scenic", "chill"], "popularity": 0.7},
        
        {"slug": "bomas-kenya", "name": "Bomas of Kenya", "category": "Attraction", "neighbourhood": "Langata",
         "lat": -1.3733, "lng": 36.7711, "entry_fee": 350, "avg_food": 400, "duration_min": 150,
         "rating": 4.5, "price_tier": "Mid", "tags": ["culture", "traditional", "dance", "music", "homesteads"],
         "vibes": ["authentic", "local", "adventurous"], "popularity": 0.8},
        
        {"slug": "nairobi-national-park", "name": "Nairobi National Park", "category": "Attraction", "neighbourhood": "Langata",
         "lat": -1.3754, "lng": 36.8351, "entry_fee": 1000, "avg_food": 500, "duration_min": 240,
         "rating": 4.8, "price_tier": "Premium", "tags": ["wildlife", "safari", "lions", "rhinos", "nature"],
         "vibes": ["adventurous", "scenic", "authentic"], "popularity": 0.95},
        
        # Cafés
        {"slug": "java-westlands", "name": "Java House Westlands", "category": "Café", "neighbourhood": "Westlands",
         "lat": -1.2686, "lng": 36.8046, "entry_fee": 0, "avg_food": 450, "duration_min": 45,
         "rating": 4.2, "price_tier": "Mid", "tags": ["coffee", "food", "wifi", "work-friendly"],
         "vibes": ["chill", "authentic"], "popularity": 0.85},
        
        {"slug": "artcaffe-gigiri", "name": "Artcaffe Gigiri", "category": "Café", "neighbourhood": "Gigiri",
         "lat": -1.2314, "lng": 36.8153, "entry_fee": 0, "avg_food": 600, "duration_min": 60,
         "rating": 4.3, "price_tier": "Mid", "tags": ["coffee", "bakery", "pizza", "wifi"],
         "vibes": ["chill", "scenic"], "popularity": 0.8},
        
        {"slug": "wasp-and-sprout", "name": "Wasp & Sprout", "category": "Café", "neighbourhood": "Lavington",
         "lat": -1.2958, "lng": 36.7613, "entry_fee": 0, "avg_food": 500, "duration_min": 60,
         "rating": 4.5, "price_tier": "Mid", "tags": ["coffee", "brunch", "organic", "cozy"],
         "vibes": ["chill", "authentic", "scenic"], "popularity": 0.75},
        
        {"slug": "connect-coffee", "name": "Connect Coffee", "category": "Café", "neighbourhood": "Westlands",
         "lat": -1.2675, "lng": 36.8075, "entry_fee": 0, "avg_food": 400, "duration_min": 45,
         "rating": 4.4, "price_tier": "Mid", "tags": ["coffee", "specialty", "roastery", "wifi"],
         "vibes": ["chill", "authentic"], "popularity": 0.7},
        
        # Restaurants
        {"slug": "tamarind-restaurant", "name": "Tamarind Restaurant", "category": "Restaurant", "neighbourhood": "Langata",
         "lat": -1.3611, "lng": 36.7889, "entry_fee": 0, "avg_food": 1200, "duration_min": 90,
         "rating": 4.6, "price_tier": "Premium", "tags": ["fine-dining", "seafood", "view", "romantic"],
         "vibes": ["scenic", "chill"], "popularity": 0.8},
        
        {"slug": "carnivore-restaurant", "name": "Carnivore Restaurant", "category": "Restaurant", "neighbourhood": "Langata",
         "lat": -1.3289, "lng": 36.7856, "entry_fee": 0, "avg_food": 1500, "duration_min": 120,
         "rating": 4.5, "price_tier": "Premium", "tags": ["nyama-choma", "meat", "traditional", "bbq"],
         "vibes": ["authentic", "local", "adventurous"], "popularity": 0.9},
        
        {"slug": "mama-rocks", "name": "Mama Rocks", "category": "Restaurant", "neighbourhood": "Westlands",
         "lat": -1.2691, "lng": 36.8055, "entry_fee": 0, "avg_food": 800, "duration_min": 90,
         "rating": 4.4, "price_tier": "Premium", "tags": ["gourmet", "burgers", "african-fusion", "street-food"],
         "vibes": ["chill", "authentic", "local"], "popularity": 0.8},
        
        {"slug": "ola-parklands", "name": "Ola Energy Parklands", "category": "Restaurant", "neighbourhood": "Parklands",
         "lat": -1.2596, "lng": 36.8226, "entry_fee": 0, "avg_food": 350, "duration_min": 60,
         "rating": 3.8, "price_tier": "Mid", "tags": ["fast-food", "convenience", "24-hour"],
         "vibes": ["local", "chill"], "popularity": 0.6},
        
        {"slug": "talisman-restaurant", "name": "Talisman Restaurant", "category": "Restaurant", "neighbourhood": "Karen",
         "lat": -1.3367, "lng": 36.7194, "entry_fee": 0, "avg_food": 1000, "duration_min": 90,
         "rating": 4.7, "price_tier": "Premium", "tags": ["gourmet", "garden", "international", "romantic"],
         "vibes": ["scenic", "chill", "authentic"], "popularity": 0.85},
        
        {"slug": "about-thyme", "name": "About Thyme", "category": "Restaurant", "neighbourhood": "Kilimani",
         "lat": -1.2956, "lng": 36.7924, "entry_fee": 0, "avg_food": 900, "duration_min": 90,
         "rating": 4.5, "price_tier": "Premium", "tags": ["mediterranean", "garden", "romantic", "quiet"],
         "vibes": ["chill", "scenic", "authentic"], "popularity": 0.75},
        
        {"slug": "mojo-fried-chicken", "name": "Mojo Fried Chicken", "category": "Restaurant", "neighbourhood": "Westlands",
         "lat": -1.2703, "lng": 36.8083, "entry_fee": 0, "avg_food": 600, "duration_min": 60,
         "rating": 4.2, "price_tier": "Mid", "tags": ["fried-chicken", "fast-casual", "trendy"],
         "vibes": ["chill", "energetic"], "popularity": 0.8},
        
        {"slug": "fogo-gaucho", "name": "Fogo Gaucho", "category": "Restaurant", "neighbourhood": "Westlands",
         "lat": -1.2679, "lng": 36.8067, "entry_fee": 0, "avg_food": 1800, "duration_min": 120,
         "rating": 4.6, "price_tier": "Premium", "tags": ["brazilian", "steakhouse", "all-you-can-eat", "meat"],
         "vibes": ["chill", "energetic"], "popularity": 0.85},
    ]

    for data in places_data:
        neighbourhood = neighbourhoods.get(data["neighbourhood"])
        if not neighbourhood:
            stdout.write(f"  Skipping {data['name']} - neighbourhood not found")
            continue
        
        p = Place.objects.create(
            slug=data["slug"],
            name=data["name"],
            category=data["category"],
            neighbourhood=neighbourhood,
            lat=data["lat"],
            lng=data["lng"],
            entry_fee=data["entry_fee"],
            avg_food=data["avg_food"],
            duration_min=data["duration_min"],
            rating=Decimal(str(data["rating"])),
            price_tier=data["price_tier"],
            tags=data["tags"],
            vibes=data["vibes"],
            popularity=Decimal(str(data["popularity"])),
        )
        stdout.write(f"  Created: {p.name}")

    # --- Transport Edges ---
    stdout.write("Creating transport edges...")

    transport_data = [
        # CBD connections
        ("CBD", "Westlands", 50, 20),
        ("Westlands", "CBD", 50, 20),
        ("CBD", "Gigiri", 80, 35),
        ("Gigiri", "CBD", 80, 35),
        ("CBD", "Langata", 60, 30),
        ("Langata", "CBD", 60, 30),
        ("CBD", "Kilimani", 40, 15),
        ("Kilimani", "CBD", 40, 15),
        ("CBD", "Parklands", 50, 20),
        ("Parklands", "CBD", 50, 20),
        ("CBD", "Eastleigh", 50, 20),
        ("Eastleigh", "CBD", 50, 20),
        ("CBD", "Karen", 100, 45),
        ("Karen", "CBD", 100, 45),
        
        # Westlands connections
        ("Westlands", "Gigiri", 40, 15),
        ("Gigiri", "Westlands", 40, 15),
        ("Westlands", "Langata", 70, 25),
        ("Langata", "Westlands", 70, 25),
        ("Westlands", "Parklands", 30, 10),
        ("Parklands", "Westlands", 30, 10),
        ("Westlands", "Kilimani", 30, 12),
        ("Kilimani", "Westlands", 30, 12),
        ("Westlands", "Karen", 80, 35),
        ("Karen", "Westlands", 80, 35),
        
        # Gigiri connections
        ("Gigiri", "Langata", 90, 40),
        ("Langata", "Gigiri", 90, 40),
        ("Gigiri", "Runda", 30, 10),
        ("Runda", "Gigiri", 30, 10),
        ("Gigiri", "Karen", 70, 30),
        ("Karen", "Gigiri", 70, 30),
        
        # Langata connections
        ("Langata", "Karen", 40, 15),
        ("Karen", "Langata", 40, 15),
        ("Langata", "Kilimani", 50, 20),
        ("Kilimani", "Langata", 50, 20),
        
        # Kilimani connections
        ("Kilimani", "Parklands", 40, 15),
        ("Parklands", "Kilimani", 40, 15),
        
        # Lavington connections
        ("Lavington", "Westlands", 35, 12),
        ("Westlands", "Lavington", 35, 12),
        ("Lavington", "Kilimani", 30, 10),
        ("Kilimani", "Lavington", 30, 10),
        ("Lavington", "Karen", 50, 20),
        ("Karen", "Lavington", 50, 20),
    ]

    for origin_name, dest_name, fare, minutes in transport_data:
        origin = neighbourhoods.get(origin_name)
        destination = neighbourhoods.get(dest_name)
        if not origin or not destination:
            continue
        
        # Check if edge already exists
        if not TransportEdge.objects.filter(origin=origin, destination=destination).exists():
            TransportEdge.objects.create(
                origin=origin,
                destination=destination,
                mode="Matatu",
                fare=fare,
                minutes=minutes,
            )
            stdout.write(f"  Created: {origin_name} → {dest_name}")

    stdout.write("Real Nairobi data loaded successfully!")


class Command(BaseCommand):
    help = "Load real Nairobi neighbourhood, place, and transport data."

    @transaction.atomic
    def handle(self, *args, **options):
        load_nairobi_real_data(stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS("Real Nairobi data loaded successfully!"))
