import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from trips.models import Place


class Command(BaseCommand):
    help = "Load Places data from a JSON file. Appends to existing Places."

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Path to JSON file containing Places data.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options["file_path"]

        if not os.path.exists(file_path):
            raise CommandError(f"File does not exist: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in file: {exc}")

        if not isinstance(data, list):
            raise CommandError("JSON must be a list of Place objects.")

        # No clearing, append to existing data
        # self.stdout.write("Clearing existing Places...")
        # Place.objects.all().delete()

        # Load new data
        self.stdout.write(f"Loading {len(data)} Places...")

        for item in data:
            try:
                Place.objects.create(
                    slug=item["slug"],
                    name=item["name"],
                    category=item["category"],
                    neighbourhood=item.get("neighbourhood", ""),
                    lat=item["lat"],
                    lng=item["lng"],
                    entry_fee=item.get("entry_fee", 0),
                    avg_food=item.get("avg_food", 0),
                    duration_min=item.get("duration_min", 0),
                    rating=item["rating"],
                    price_tier=item["price_tier"],
                    tags=item.get("tags", []),
                    vibes=item.get("vibes", []),
                    popularity=item.get("popularity", 0.5),
                )
            except KeyError as exc:
                raise CommandError(f"Missing required field in Place data: {exc}")
            except Exception as exc:
                raise CommandError(f"Error creating Place '{item.get('name', 'unknown')}': {exc}")

        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {len(data)} Places."))
