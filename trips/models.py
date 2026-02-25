from django.db import models


class Neighbourhood(models.Model):
    name = models.CharField(max_length=100, unique=True)
    lat = models.FloatField()
    lng = models.FloatField()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Place(models.Model):
    # Match the string IDs used in the frontend (e.g. "karura")
    slug = models.SlugField(primary_key=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50)

    neighbourhood = models.ForeignKey(
        Neighbourhood, related_name="places", on_delete=models.CASCADE
    )

    lat = models.FloatField()
    lng = models.FloatField()

    entry_fee = models.PositiveIntegerField(default=0)
    avg_food = models.PositiveIntegerField(default=0)
    duration_min = models.PositiveIntegerField(default=0)

    rating = models.DecimalField(max_digits=3, decimal_places=1)
    price_tier = models.CharField(max_length=20)

    # Store tags and vibes as JSON arrays of strings
    tags = models.JSONField(default=list, blank=True)
    vibes = models.JSONField(default=list, blank=True)

    popularity = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class TransportEdge(models.Model):
    """
    Explicit transport edges between neighbourhoods.

    This replaces the hard-coded `transportTable` object in the frontend.
    """

    origin = models.ForeignKey(
        Neighbourhood, related_name="outgoing_edges", on_delete=models.CASCADE
    )
    destination = models.ForeignKey(
        Neighbourhood, related_name="incoming_edges", on_delete=models.CASCADE
    )

    mode = models.CharField(max_length=50, default="Matatu")
    fare = models.PositiveIntegerField()
    minutes = models.PositiveIntegerField()

    class Meta:
        unique_together = ("origin", "destination")
        ordering = ["origin__name", "destination__name"]

    def __str__(self) -> str:
        return f"{self.origin} → {self.destination} ({self.mode})"
