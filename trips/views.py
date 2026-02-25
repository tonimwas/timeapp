from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from .models import Neighbourhood, Place, TransportEdge


@never_cache
def frontend_view(request):
    """Serve the React frontend HTML file."""
    return render(request, 'index.html')


def geo_data(request):
    """
    Return neighbourhood centers, places, and transport data in the same
    shape that the frontend expects, replacing the hard-coded JS objects.
    """
    neighbourhoods = Neighbourhood.objects.all()
    neighbourhood_centers = {
        n.name: {"lat": n.lat, "lng": n.lng} for n in neighbourhoods
    }

    places_qs = Place.objects.select_related("neighbourhood").all()
    places = []

    for p in places_qs:
        places.append(
            {
                "id": p.slug,
                "name": p.name,
                "category": p.category,
                "neighbourhood": p.neighbourhood.name,
                "coords": {"lat": p.lat, "lng": p.lng},
                "entryFee": p.entry_fee,
                "avgFood": p.avg_food,
                "durationMin": p.duration_min,
                "rating": float(p.rating),
                "priceTier": p.price_tier,
                "tags": p.tags or [],
                "vibes": p.vibes or [],
                "popularity": float(p.popularity),
            }
        )

    # Build a transport lookup table identical to the former JS object.
    edges = TransportEdge.objects.select_related("origin", "destination").all()
    transport_table = {}
    for edge in edges:
        key = f"{edge.origin.name}|{edge.destination.name}"
        transport_table[key] = {
            "mode": edge.mode,
            "fare": edge.fare,
            "minutes": edge.minutes,
        }

    return JsonResponse(
        {
            "neighbourhoodCenters": neighbourhood_centers,
            "places": places,
            "transportTable": transport_table,
        }
    )
