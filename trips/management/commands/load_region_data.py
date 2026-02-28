import json
import random
import urllib.parse
import urllib.request
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from trips.management.commands.load_nairobi_data import load_nairobi_real_data
from trips.models import Neighbourhood, Place, TransportEdge


def _normalize_region_name(region: str) -> str:
    return " ".join(region.strip().lower().split())


def _geocode_region(region: str) -> tuple[float, float, str]:
    query = urllib.parse.urlencode({"q": region, "format": "json", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{query}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "timeapp/1.0",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = response.read().decode("utf-8")
    except Exception as exc:  # pragma: no cover
        raise CommandError(
            f"Failed to geocode region '{region}'. "
            "Check your internet connection or try a more specific name (e.g. 'Nyeri County, Kenya')."
        ) from exc

    try:
        results = json.loads(payload)
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise CommandError("Geocoding service returned invalid JSON.") from exc

    if not results:
        raise CommandError(
            f"No geocoding results for '{region}'. Try a more specific query."
        )

    top = results[0]
    try:
        lat = float(top["lat"])
        lng = float(top["lon"])
        display_name = str(top.get("display_name") or region)
    except (KeyError, ValueError, TypeError) as exc:  # pragma: no cover
        raise CommandError("Geocoding response missing lat/lon.") from exc

    return lat, lng, display_name


@transaction.atomic
def _load_generated_region_data(*, stdout, region_label: str, center_lat: float, center_lng: float, seed: int, neighbourhood_count: int, place_count: int, edge_count: int):
    stdout.write("Clearing existing data...")
    TransportEdge.objects.all().delete()
    Place.objects.all().delete()
    Neighbourhood.objects.all().delete()

    random.seed(seed)

    stdout.write(f"Creating neighbourhoods for {region_label}...")

    neighbourhoods: list[Neighbourhood] = []
    for i in range(1, neighbourhood_count + 1):
        name = f"{region_label} Area {i}"
        lat = center_lat + random.uniform(-0.12, 0.12)
        lng = center_lng + random.uniform(-0.12, 0.12)
        neighbourhoods.append(Neighbourhood.objects.create(name=name, lat=lat, lng=lng))

    stdout.write(f"Creating places for {region_label}...")

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
        "local",
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

    for i in range(1, place_count + 1):
        name = f"{region_label} Place {i}"
        slug = slugify(f"{region_label}-{i}-{name}")
        neighbourhood = random.choice(neighbourhoods)

        lat = neighbourhood.lat + random.uniform(-0.01, 0.01)
        lng = neighbourhood.lng + random.uniform(-0.01, 0.01)

        entry_fee = random.choice([0, 50, 100, 200, 300, 500, 1000])
        avg_food = random.choice([0, 150, 200, 350, 400, 700, 1200])
        duration_min = random.choice([30, 45, 60, 90, 120, 180, 240])

        rating = Decimal(str(round(random.uniform(3.2, 4.9), 1)))
        popularity = Decimal(str(round(random.uniform(0.5, 1.0), 2)))

        Place.objects.create(
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
            price_tier=random.choice(price_tiers),
            tags=random.sample(possible_tags, k=random.randint(2, 4)),
            vibes=random.sample(possible_vibes, k=random.randint(1, 3)),
            popularity=popularity,
        )

    stdout.write(f"Creating transport edges for {region_label}...")

    created_edges = 0
    attempts = 0
    max_attempts = edge_count * 20

    while created_edges < edge_count and attempts < max_attempts:
        attempts += 1
        origin, destination = random.sample(neighbourhoods, k=2)

        if TransportEdge.objects.filter(origin=origin, destination=destination).exists():
            continue

        fare = random.choice([20, 30, 40, 60, 80, 100, 120])
        minutes = random.choice([8, 10, 12, 15, 20, 25, 30, 40, 60])

        TransportEdge.objects.create(
            origin=origin,
            destination=destination,
            mode="Matatu",
            fare=fare,
            minutes=minutes,
        )
        created_edges += 1

    stdout.write(f"Loaded generated data for {region_label}.")


class Command(BaseCommand):
    help = "Load trip data for any region (Kenya counties/constituencies or any place worldwide)."

    def add_arguments(self, parser):
        parser.add_argument(
            "region",
            type=str,
            help="Region name to load (e.g. 'nairobi', 'nyeri', 'Nyeri County, Kenya', 'Berlin, Germany').",
        )
        parser.add_argument(
            "--mode",
            choices=["auto", "nairobi_real", "generated"],
            default="auto",
            help="auto uses the real Nairobi dataset when region is Nairobi; otherwise generated. (default: auto)",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=1,
            help="Random seed for generated datasets (default: 1).",
        )
        parser.add_argument(
            "--neighbourhoods",
            type=int,
            default=12,
            help="Neighbourhood count for generated datasets (default: 12).",
        )
        parser.add_argument(
            "--places",
            type=int,
            default=40,
            help="Place count for generated datasets (default: 40).",
        )
        parser.add_argument(
            "--edges",
            type=int,
            default=60,
            help="Transport edge count for generated datasets (default: 60).",
        )
        parser.add_argument(
            "--no-geocode",
            action="store_true",
            help="Skip geocoding and require --lat/--lng for generated mode.",
        )
        parser.add_argument(
            "--lat",
            type=float,
            default=None,
            help="Center latitude for generated mode (only used with --no-geocode).",
        )
        parser.add_argument(
            "--lng",
            type=float,
            default=None,
            help="Center longitude for generated mode (only used with --no-geocode).",
        )

    def handle(self, *args, **options):
        region: str = options["region"]
        mode: str = options["mode"]

        normalized = _normalize_region_name(region)

        if mode == "auto":
            mode = "nairobi_real" if normalized in {"nairobi", "nairobi county"} else "generated"

        if mode == "nairobi_real":
            load_nairobi_real_data(stdout=self.stdout)
            self.stdout.write(self.style.SUCCESS("Real Nairobi data loaded successfully!"))
            return

        if options["no_geocode"]:
            lat = options["lat"]
            lng = options["lng"]
            if lat is None or lng is None:
                raise CommandError("When using --no-geocode, you must provide both --lat and --lng.")
            display_name = region
        else:
            lat, lng, display_name = _geocode_region(region)

        _load_generated_region_data(
            stdout=self.stdout,
            region_label=display_name,
            center_lat=lat,
            center_lng=lng,
            seed=int(options["seed"]),
            neighbourhood_count=int(options["neighbourhoods"]),
            place_count=int(options["places"]),
            edge_count=int(options["edges"]),
        )

        self.stdout.write(self.style.SUCCESS(f"Region data loaded successfully for: {display_name}"))
