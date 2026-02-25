import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from trips.models import Neighbourhood, Place, TransportEdge


class Command(BaseCommand):
    help = "Populate the database with sample data for Neighbourhood, Place, and TransportEdge."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Number of rows to create per model (default: 100).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count: int = options["count"]

        # Start fresh so we don't hit unique constraints when re-running.
        self.stdout.write("Clearing existing data...")
        TransportEdge.objects.all().delete()
        Place.objects.all().delete()
        Neighbourhood.objects.all().delete()

        random.seed(1)

        # --- Neighbourhoods ---
        self.stdout.write(f"Creating {count} neighbourhoods...")
        neighbourhoods = []

        # Rough Nairobi center for lat/lng jittering
        base_lat = -1.286389
        base_lng = 36.817223

        for i in range(1, count + 1):
            name = f"Neighbourhood {i}"
            # Jitter lat/lng slightly around a base point
            lat = base_lat + random.uniform(-0.2, 0.2)
            lng = base_lng + random.uniform(-0.2, 0.2)
            n = Neighbourhood.objects.create(name=name, lat=lat, lng=lng)
            neighbourhoods.append(n)

        # --- Places ---
        self.stdout.write(f"Creating {count} places...")

        categories = ["Park", "Market", "Restaurant", "Café", "Attraction", "Mall"]
        price_tiers = ["Free", "Budget", "Mid", "Premium"]
        possible_tags = [
            "outdoor",
            "indoor",
            "nature",
            "shopping",
            "food",
            "family",
            "views",
            "history",
            "art",
        ]
        possible_vibes = [
            "authentic",
            "local",
            "chill",
            "adventurous",
            "energetic",
            "scenic",
            "quiet",
        ]

        places = []

        for i in range(1, count + 1):
            name = f"Sample Place {i}"
            slug = slugify(name)
            neighbourhood = random.choice(neighbourhoods)

            # Small jitter around the neighbourhood center
            lat = neighbourhood.lat + random.uniform(-0.01, 0.01)
            lng = neighbourhood.lng + random.uniform(-0.01, 0.01)

            entry_fee = random.choice([0, 100, 200, 500, 1000, 1500])
            avg_food = random.choice([0, 200, 400, 700, 1200])
            duration_min = random.choice([45, 60, 90, 120, 180])

            rating = Decimal(str(round(random.uniform(3.0, 5.0), 1)))
            price_tier = random.choice(price_tiers)

            tags = random.sample(possible_tags, k=random.randint(2, 4))
            vibes = random.sample(possible_vibes, k=random.randint(1, 3))

            popularity = Decimal(str(round(random.uniform(0.5, 1.0), 2)))

            p = Place.objects.create(
                slug=slug,
                name=name,
                category=random.choice(categories),
                neighbourhood=neighbourhood,
                lat=lat,
                lng=lng,
                entry_fee=entry_fee,
                avg_food=avg_food,
                duration_min=duration_min,
                rating=rating,
                price_tier=price_tier,
                tags=tags,
                vibes=vibes,
                popularity=popularity,
            )
            places.append(p)

        # --- Transport edges ---
        self.stdout.write(f"Creating {count} transport edges...")

        created_edges = 0
        attempts = 0
        max_attempts = count * 10  # stop if we somehow can't find unique pairs

        while created_edges < count and attempts < max_attempts:
            attempts += 1
            origin, destination = random.sample(neighbourhoods, k=2)

            # Avoid duplicates due to unique_together
            if TransportEdge.objects.filter(origin=origin, destination=destination).exists():
                continue

            fare = random.choice([20, 30, 40, 60, 80, 100])
            minutes = random.choice([10, 15, 20, 25, 30, 40, 60])

            TransportEdge.objects.create(
                origin=origin,
                destination=destination,
                mode="Matatu",
                fare=fare,
                minutes=minutes,
            )
            created_edges += 1

        self.stdout.write(self.style.SUCCESS("Sample data created successfully."))

