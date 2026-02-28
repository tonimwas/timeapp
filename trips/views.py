from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache

from .models import Place
from .utils import calculate_transport, get_neighbourhood


@never_cache
def frontend_view(request):
    """Serve the React frontend HTML file."""
    return render(request, 'index.html')


def geo_data(request):
    """
    Return neighbourhood centers, places, and transport data in the same
    shape that the frontend expects, replacing the hard-coded JS objects.
    """
    places_qs = Place.objects.all()
    places = []

    # Collect neighbourhood data
    neighbourhood_data = {}  # name -> {"places": [], "lat_sum": 0, "lng_sum": 0, "count": 0}

    for p in places_qs:
        neighbourhood = p.neighbourhood or "General"  # Default if blank

        if neighbourhood not in neighbourhood_data:
            neighbourhood_data[neighbourhood] = {"places": [], "lat_sum": 0.0, "lng_sum": 0.0, "count": 0}

        neighbourhood_data[neighbourhood]["places"].append(p)
        neighbourhood_data[neighbourhood]["lat_sum"] += p.lat
        neighbourhood_data[neighbourhood]["lng_sum"] += p.lng
        neighbourhood_data[neighbourhood]["count"] += 1

        places.append(
            {
                "id": p.slug,
                "name": p.name,
                "category": p.category,
                "neighbourhood": neighbourhood,
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

    # Compute neighbourhood centers
    neighbourhood_centers = {}
    for name, data in neighbourhood_data.items():
        if data["count"] > 0:
            avg_lat = data["lat_sum"] / data["count"]
            avg_lng = data["lng_sum"] / data["count"]
            neighbourhood_centers[name] = {"lat": avg_lat, "lng": avg_lng}

    # Build transport table between neighbourhoods
    neighbourhood_names = list(neighbourhood_centers.keys())
    transport_table = {}
    for i, origin in enumerate(neighbourhood_names):
        origin_coords = neighbourhood_centers[origin]
        for j, dest in enumerate(neighbourhood_names):
            if i != j:  # No self-loops
                dest_coords = neighbourhood_centers[dest]
                mode, fare, minutes = calculate_transport(
                    origin_coords["lat"], origin_coords["lng"],
                    dest_coords["lat"], dest_coords["lng"]
                )
                key = f"{origin}|{dest}"
                transport_table[key] = {
                    "mode": mode,
                    "fare": fare,
                    "minutes": minutes,
                }

    return JsonResponse(
        {
            "neighbourhoodCenters": neighbourhood_centers,
            "places": places,
            "transportTable": transport_table,
        }
    )


def set_location(request):
    """
    Set the user's starting location by creating a Place at their coordinates,
    with neighbourhood determined via reverse geocoding.
    """
    if request.method == 'POST':
        lat = request.POST.get('lat')
        lng = request.POST.get('lng')
        if not lat or not lng:
            return JsonResponse({'status': 'error', 'message': 'Missing lat or lng'})
        neighbourhood = get_neighbourhood(float(lat), float(lng))
        slug = f"user-location-{lat}-{lng}".replace('.', '-')
        Place.objects.create(
            slug=slug,
            name="My Location",
            category="Starting Point",
            neighbourhood=neighbourhood,
            lat=float(lat),
            lng=float(lng),
            entry_fee=0,
            avg_food=0,
            duration_min=0,
            rating=5.0,
            price_tier="Free",
            tags=["user", "location"],
            vibes=["personal"],
            popularity=1.0
        )
        return JsonResponse({'status': 'success', 'neighbourhood': neighbourhood})
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})
