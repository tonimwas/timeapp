// GeoSpend Kenya - Algorithm demo (Nairobi sample)

// ------------------------------
// Data model (loaded from database API)
// ------------------------------

let neighbourhoodCenters = {};
let places = [];
let transportTable = {};
let geoDataLoaded = false;

async function loadGeoData() {
  try {
    if (typeof setStatus === 'function') {
      setStatus('Loading places and transport data…');
    }
    
    const response = await fetch('/api/geo-data/');
    if (!response.ok) {
      throw new Error(`Failed to load geo data: ${response.status} ${response.statusText}`);
    }
    const data = await response.json();
    neighbourhoodCenters = data.neighbourhoodCenters || {};
    places = data.places || [];
    transportTable = data.transportTable || {};
    geoDataLoaded = true;
    if (typeof setStatus === 'function') {
      setStatus('Data loaded from server. You can now generate an itinerary.');
    }
  } catch (err) {
    console.error('Error loading geo data:', err);
    geoDataLoaded = false;
    if (typeof setStatus === 'function') {
      setStatus('Failed to load data from server. Please try again later.', true);
    }
  }
}

function getTransport(origin, destination) {
  if (origin === destination) return { mode: 'Walk', fare: 0, minutes: 0 };
  const directKey = `${origin}|${destination}`;
  if (transportTable[directKey]) return transportTable[directKey];
  // Fallback: approximate matatu between centres by straight-line distance
  const originCenter = neighbourhoodCenters[origin];
  const destCenter = neighbourhoodCenters[destination];
  if (!originCenter || !destCenter) {
    return { mode: 'Matatu', fare: 80, minutes: 45 };
  }
  const km = haversineKm(originCenter, destCenter);
  const fare = Math.round(Math.max(30, km * 8)); // rough
  const minutes = Math.round(Math.max(10, km * 3));
  return { mode: 'Matatu', fare, minutes };
}

// ------------------------------
// Utilities
// ------------------------------

function haversineKm(a, b) {
  const R = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;
  const sinDLat = Math.sin(dLat / 2);
  const sinDLng = Math.sin(dLng / 2);
  const h =
    sinDLat * sinDLat +
    sinDLng * sinDLng * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
  return R * c;
}

// ------------------------------
// Algorithm stages
// ------------------------------

function stage1SpatialSearch(startNeighbourhood, radiusKm = 20) {
  const center = neighbourhoodCenters[startNeighbourhood];
  if (!center) return [];
  return places.filter((p) => {
    const d = haversineKm(center, p.coords);
    return d <= radiusKm;
  });
}

function stage2BudgetFilter(candidates, totalBudget, categoryPrefs) {
  const threshold = totalBudget * 0.6;
  return candidates.filter((p) => {
    const placeCost = p.entryFee + p.avgFood;
    if (placeCost > threshold) return false;
    if (categoryPrefs && categoryPrefs.length > 0) {
      if (!categoryPrefs.includes(p.category)) {
        // Still allow, but slightly discourage later; keep here.
        return true;
      }
    }
    return true;
  });
}

function textMatchBoost(place, queryTokens) {
  if (queryTokens.length === 0) return 0;
  const haystack = [
    ...place.tags,
    ...place.vibes,
    place.name,
    place.category,
  ]
    .join(' ')
    .toLowerCase();
  let matches = 0;
  for (const token of queryTokens) {
    if (haystack.includes(token)) matches += 1;
  }
  return Math.min(1, matches / queryTokens.length);
}

function stage3ScoreAndRank(
  candidates,
  preferredCategories,
  preferredVibes,
  freeText
) {
  const catSet = new Set(preferredCategories);
  const vibeSet = new Set(preferredVibes.map((v) => v.toLowerCase()));
  const tokens =
    freeText
      ?.toLowerCase()
      .split(/\s+/)
      .filter((t) => t.length > 2) ?? [];

  return candidates
    .map((p) => {
      const ratingNorm = p.rating / 5; // 0-1
      const ratingScore = ratingNorm; // weight ~ 30%

      const categoryMatch = catSet.size
        ? catSet.has(p.category)
          ? 1
          : 0
        : 0.5;
      const categoryScore = categoryMatch; // ~30%

      const vibeMatches = p.vibes.filter((v) =>
        vibeSet.has(v.toLowerCase())
      ).length;
      const vibeScore = Math.min(1, vibeMatches / 2); // ~20%

      const popularityScore = p.popularity ?? 0.5; // ~20%

      const textBoost = textMatchBoost(p, tokens);

      const baseScore =
        ratingScore * 0.3 +
        categoryScore * 0.3 +
        vibeScore * 0.2 +
        popularityScore * 0.2;
      const finalScore = baseScore + textBoost * 0.2;
      return { place: p, score: finalScore };
    })
    .sort((a, b) => b.score - a.score);
}

function stage4ItinerarySolver(
  ranked,
  startNeighbourhood,
  totalBudget,
  totalMinutes
) {
  let remainingBudget = totalBudget;
  let remainingMinutes = totalMinutes;
  let currentNeighbourhood = startNeighbourhood;

  const stops = [];

  for (const { place, score } of ranked) {
    const transport = getTransport(
      currentNeighbourhood,
      place.neighbourhood
    );
    const placeCost = place.entryFee + place.avgFood;
    const totalCost = transport.fare + placeCost;
    const totalTime = transport.minutes + place.durationMin;

    if (totalCost <= remainingBudget && totalTime <= remainingMinutes) {
      stops.push({
        place,
        score,
        transport,
        costBreakdown: {
          transport: transport.fare,
          entry: place.entryFee,
          food: place.avgFood,
          total: totalCost,
        },
        timeBreakdown: {
          travel: transport.minutes,
          visit: place.durationMin,
          total: totalTime,
        },
      });
      remainingBudget -= totalCost;
      remainingMinutes -= totalTime;
      currentNeighbourhood = place.neighbourhood;
    }
  }

  return {
    stops,
    remainingBudget,
    remainingMinutes,
  };
}

// ------------------------------
// Map handling (Leaflet)
// ------------------------------

let map;
let mapMarkers = [];
let mapPolyline;

// ------------------------------
// Road routing via OpenRouteService
// ------------------------------

// Using the same API key as in routeexample.js
const ORS_API_KEY =
  '5b3ce3597851110001cf6248f3c7d707f6f94f1c9315484e33df5f03';
const ORS_DIRECTIONS_URL =
  'https://api.openrouteservice.org/v2/directions/driving-car/geojson';

async function fetchRouteSegment(from, to) {
  try {
    const body = {
      coordinates: [
        [from.lng, from.lat],
        [to.lng, to.lat],
      ],
    };

    const response = await fetch(ORS_DIRECTIONS_URL, {
      method: 'POST',
      headers: {
        Authorization: ORS_API_KEY,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      console.warn(
        'OpenRouteService API error:',
        response.status,
        response.statusText
      );
      return null;
    }

    const data = await response.json();
    if (!data.features || !data.features.length) {
      console.warn('OpenRouteService returned no route for segment');
      return null;
    }

    // Convert [lng, lat] to [lat, lng] for Leaflet
    return data.features[0].geometry.coordinates.map((coord) => [
      coord[1],
      coord[0],
    ]);
  } catch (error) {
    console.error('Error fetching route segment from OpenRouteService:', error);
    return null;
  }
}

async function buildRoadRoute(latLngs) {
  const fullRoute = [];

  for (let i = 0; i < latLngs.length - 1; i++) {
    const from = { lat: latLngs[i][0], lng: latLngs[i][1] };
    const to = { lat: latLngs[i + 1][0], lng: latLngs[i + 1][1] };

    const segment = await fetchRouteSegment(from, to);

    if (segment && segment.length) {
      // Avoid duplicating the joint point where segments meet
      if (fullRoute.length) {
        segment.shift();
      }
      fullRoute.push(...segment);
    } else {
      // Fallback: straight line if routing fails for this pair
      fullRoute.push(latLngs[i], latLngs[i + 1]);
    }
  }

  return fullRoute;
}

function initMap() {
  const nairobiCenter = [-1.286389, 36.817223];
  map = L.map('map').setView(nairobiCenter, 12);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map);
}

async function updateMap(stops, startNeighbourhood) {
  if (!map) return;

  // Clear previous markers and polylines
  mapMarkers.forEach((m) => map.removeLayer(m));
  mapMarkers = [];
  if (mapPolyline) {
    map.removeLayer(mapPolyline);
    mapPolyline = null;
  }

  if (!stops.length) {
    const center = neighbourhoodCenters[startNeighbourhood] ?? {
      lat: -1.286389,
      lng: 36.817223,
    };
    map.setView([center.lat, center.lng], 12);
    return;
  }

  const latLngs = [];

  // Start marker (start neighbourhood)
  const startCenter = neighbourhoodCenters[startNeighbourhood];
  if (startCenter) {
    const marker = L.marker([startCenter.lat, startCenter.lng], {
      title: `Start: ${startNeighbourhood}`,
    }).addTo(map);
    marker.bindPopup(`<b>Start</b><br>${startNeighbourhood}`);
    mapMarkers.push(marker);
    latLngs.push([startCenter.lat, startCenter.lng]);
  }

  stops.forEach((stop, idx) => {
    const { place } = stop;
    const { lat, lng } = place.coords;
    latLngs.push([lat, lng]);
    const marker = L.marker([lat, lng], {
      title: `${idx + 1}. ${place.name}`,
    }).addTo(map);
    marker.bindPopup(
      `<b>${idx + 1}. ${place.name}</b><br>${place.category} · ${
        place.neighbourhood
      }`
    );
    mapMarkers.push(marker);
  });

  // Build a route that follows actual roads between the points
  const roadRouteLatLngs = await buildRoadRoute(latLngs);

  if (!roadRouteLatLngs.length) {
    // Fallback to straight lines if routing completely fails
    mapPolyline = L.polyline(latLngs, {
      color: '#22c55e',
      weight: 4,
      opacity: 0.9,
    }).addTo(map);

    map.fitBounds(mapPolyline.getBounds(), { padding: [24, 24] });
    return;
  }

  mapPolyline = L.polyline(roadRouteLatLngs, {
    color: '#22c55e',
    weight: 4,
    opacity: 0.9,
  }).addTo(map);

  map.fitBounds(mapPolyline.getBounds(), { padding: [24, 24] });
}

// ------------------------------
// Rendering
// ------------------------------

function renderItinerary(result, totalBudget, totalMinutes) {
  const container = document.getElementById('itinerary-container');
  const summaryEl = document.getElementById('summary-container');

  container.innerHTML = '';
  summaryEl.innerHTML = '';

  if (!result.stops.length) {
    container.innerHTML =
      '<p class="placeholder">No valid itinerary within these constraints. Try increasing budget or time, or relaxing preferences.</p>';

    summaryEl.innerHTML = `
      <div class="summary-row">
        <span class="summary-label">Total spent</span>
        <span class="summary-value summary-weak">KSH 0</span>
      </div>
      <div class="summary-row">
        <span class="summary-label">Time used</span>
        <span class="summary-value summary-weak">0 min</span>
      </div>
    `;
    return;
  }

  let cumulativeCost = 0;
  let cumulativeMinutes = 0;
  let transportTotal = 0;
  let placeTotal = 0;

  result.stops.forEach((stop, idx) => {
    const { place, costBreakdown, timeBreakdown, transport } = stop;
    cumulativeCost += costBreakdown.total;
    cumulativeMinutes += timeBreakdown.total;
    transportTotal += costBreakdown.transport;
    placeTotal += costBreakdown.entry + costBreakdown.food;

    const el = document.createElement('article');
    el.className = 'itinerary-stop';
    el.innerHTML = `
      <div class="stop-number">${idx + 1}</div>
      <div class="stop-main">
        <div class="stop-title-row">
          <div class="stop-name">${place.name}</div>
          <div class="stop-chip-row">
            <span class="chip rating">★ ${place.rating.toFixed(1)}</span>
            <span class="chip neighbourhood">${place.neighbourhood}</span>
            <span class="chip category">${place.category}</span>
            <span class="chip cost">KSH ${costBreakdown.total}</span>
          </div>
        </div>
        <div class="stop-subrow">
          <span><strong>Transport:</strong> ${transport.mode} · KSH ${
      costBreakdown.transport
    } · ${timeBreakdown.travel} min</span>
          <span><strong>Entry:</strong> KSH ${costBreakdown.entry}</span>
          <span><strong>Food est.:</strong> KSH ${costBreakdown.food}</span>
        </div>
        <div class="stop-subrow">
          <span><strong>Visit duration:</strong> ${
            timeBreakdown.visit
          } min</span>
          <span><strong>Step total time:</strong> ${
            timeBreakdown.total
          } min</span>
          <span><strong>Running total:</strong> KSH ${cumulativeCost} · ${cumulativeMinutes} min</span>
        </div>
      </div>
    `;
    container.appendChild(el);
  });

  const budgetUsedPct = (cumulativeCost / totalBudget) * 100;
  const timeUsedPct = (cumulativeMinutes / totalMinutes) * 100;

  summaryEl.innerHTML = `
    <div class="summary-row">
      <span class="summary-label">Stops visited</span>
      <span class="summary-value">${result.stops.length}</span>
    </div>
    <div class="summary-row">
      <span class="summary-label">Total on places</span>
      <span class="summary-value">KSH ${placeTotal}</span>
    </div>
    <div class="summary-row">
      <span class="summary-label">Total on transport</span>
      <span class="summary-value">KSH ${transportTotal}</span>
    </div>
    <div class="summary-row">
      <span class="summary-label">Total spent</span>
      <span class="summary-value summary-strong">KSH ${cumulativeCost}</span>
    </div>
    <div class="summary-row">
      <span class="summary-label">Budget remaining</span>
      <span class="summary-value summary-strong">KSH ${
        totalBudget - cumulativeCost
      }</span>
    </div>
    <hr style="border-color: rgba(31,41,55,0.9); margin: 0.35rem 0;" />
    <div class="summary-row">
      <span class="summary-label">Time used</span>
      <span class="summary-value">${cumulativeMinutes} min (${timeUsedPct.toFixed(
        0
      )}% of budgeted time)</span>
    </div>
    <div class="summary-row">
      <span class="summary-label">Time remaining</span>
      <span class="summary-value">${Math.max(
        0,
        Math.round(result.remainingMinutes)
      )} min</span>
    </div>
    <div class="summary-row">
      <span class="summary-label">Budget used</span>
      <span class="summary-value">${budgetUsedPct.toFixed(
        0
      )}% of KSH ${totalBudget}</span>
    </div>
  `;
}

// ------------------------------
// Form handling
// ------------------------------

function collectCheckedValues(containerId) {
  const container = document.getElementById(containerId);
  const values = [];
  if (!container) return values;
  container
    .querySelectorAll('input[type=checkbox]:checked')
    .forEach((el) => values.push(el.value));
  return values;
}

function setStatus(message, isError = false) {
  const statusEl = document.getElementById('status');
  statusEl.textContent = message;
  statusEl.classList.toggle('error', !!isError);
}

function onFormSubmit(event) {
  event.preventDefault();
  if (!geoDataLoaded) {
    setStatus('Data is still loading. Please wait a moment and try again.', true);
    return;
  }
  const start = document.getElementById('start-location').value;
  const budget = Number(document.getElementById('budget').value || 0);
  const hours = Number(document.getElementById('hours').value || 0);
  const totalMinutes = hours * 60;
  const preferredCategories = collectCheckedValues('category-pills');
  const preferredVibes = collectCheckedValues('vibe-pills');
  const freeText = document.getElementById('free-text').value.trim();

  if (!start || !budget || !hours) {
    setStatus('Please provide start, budget, and time.', true);
    return;
  }

  setStatus('Running itinerary algorithm…');

  // Stage 1
  const spatialCandidates = stage1SpatialSearch(start, 20);

  // Stage 2
  const budgetCandidates = stage2BudgetFilter(
    spatialCandidates,
    budget,
    preferredCategories
  );

  // Stage 3
  const ranked = stage3ScoreAndRank(
    budgetCandidates,
    preferredCategories,
    preferredVibes,
    freeText
  );

  // Stage 4
  const result = stage4ItinerarySolver(
    ranked,
    start,
    budget,
    totalMinutes
  );

  renderItinerary(result, budget, totalMinutes);
  updateMap(result.stops, start);

  if (!result.stops.length) {
    setStatus(
      'No valid plan within current constraints. Try increasing budget/time or relaxing category/vibe filters.',
      true
    );
  } else {
    setStatus(
      `Generated ${result.stops.length} stops. Budget remaining: KSH ${
        result.remainingBudget
      }, time remaining: ${Math.round(result.remainingMinutes)} min.`
    );
  }
}

// ------------------------------
// Init
// ------------------------------

window.addEventListener('DOMContentLoaded', () => {
  initMap();
  loadGeoData();  // fetch from backend
  const form = document.getElementById('trip-form');
  form.addEventListener('submit', onFormSubmit);
});

