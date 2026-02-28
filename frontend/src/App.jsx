import { useState, useEffect, useRef } from 'react'
import L from 'leaflet'
import { LocateControl } from 'leaflet.locatecontrol'
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css'

const ORS_API_KEY = '5b3ce3597851110001cf6248f3c7d707f6f94f1c9315484e33df5f03'
const ORS_DIRECTIONS_URL = 'https://api.openrouteservice.org/v2/directions/driving-car/geojson'

function haversineKm(a, b) {
  const R = 6371
  const dLat = ((b.lat - a.lat) * Math.PI) / 180
  const dLng = ((b.lng - a.lng) * Math.PI) / 180
  const lat1 = (a.lat * Math.PI) / 180
  const lat2 = (b.lat * Math.PI) / 180
  const sinDLat = Math.sin(dLat / 2)
  const sinDLng = Math.sin(dLng / 2)
  const h = sinDLat * sinDLat + sinDLng * sinDLng * Math.cos(lat1) * Math.cos(lat2)
  const c = 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h))
  return R * c
}

function App() {
  const [neighbourhoodCenters, setNeighbourhoodCenters] = useState({})
  const [places, setPlaces] = useState([])
  const [transportTable, setTransportTable] = useState({})
  const [geoDataLoaded, setGeoDataLoaded] = useState(false)
  const [status, setStatus] = useState({ message: 'Loading places and transport data…', isError: false })
  const [result, setResult] = useState(null)
  const [totalBudget, setTotalBudget] = useState(2000)
  const [totalMinutes, setTotalMinutes] = useState(480)
  
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const markersRef = useRef([])
  const polylineRef = useRef(null)

  useEffect(() => {
    loadGeoData()
    initMap()
  }, [])

  useEffect(() => {
    if (result && mapInstanceRef.current) {
      updateMap(result.stops, document.getElementById('start-location')?.value || 'CBD')
    }
  }, [result])

  async function loadGeoData() {
    try {
      setStatus({ message: 'Loading places and transport data…', isError: false })
      const response = await fetch('/api/geo-data/')
      if (!response.ok) {
        throw new Error(`Failed to load geo data: ${response.status} ${response.statusText}`)
      }
      const data = await response.json()
      setNeighbourhoodCenters(data.neighbourhoodCenters || {})
      setPlaces(data.places || [])
      setTransportTable(data.transportTable || {})
      setGeoDataLoaded(true)
      setStatus({ message: 'Data loaded from server. You can now generate an itinerary.', isError: false })
    } catch (err) {
      console.error('Error loading geo data:', err)
      setGeoDataLoaded(false)
      setStatus({ message: 'Failed to load data from server. Please try again later.', isError: true })
    }
  }

  function initMap() {
    if (mapInstanceRef.current) return
    const nairobiCenter = [-1.286389, 36.817223]
    mapInstanceRef.current = L.map('map').setView(nairobiCenter, 12)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(mapInstanceRef.current)
    new LocateControl().addTo(mapInstanceRef.current)
    mapInstanceRef.current.on('locationfound', (e) => {
      const lat = e.latlng.lat
      const lng = e.latlng.lng
      fetch('/api/set-location/', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: `lat=${lat}&lng=${lng}`
      }).then(response => response.json()).then(data => {
        console.log('Location set:', data)
        setNeighbourhoodCenters(prev => ({ ...prev, [data.neighbourhood]: { lat, lng } }))
        setPlaces(prev => [...prev, {
          id: 'user-location',
          name: 'My Location',
          category: 'Starting Point',
          neighbourhood: data.neighbourhood,
          coords: { lat, lng },
          entryFee: 0,
          avgFood: 0,
          durationMin: 0,
          rating: 5.0,
          priceTier: 'Free',
          tags: ['user', 'location'],
          vibes: ['personal'],
          popularity: 1.0
        }])
        document.getElementById('start-location').value = data.neighbourhood
      }).catch(error => {
        console.error('Error setting location:', error)
      })
    })
  }

  async function fetchRouteSegment(from, to) {
    try {
      const body = {
        coordinates: [[from.lng, from.lat], [to.lng, to.lat]],
      }
      const response = await fetch(ORS_DIRECTIONS_URL, {
        method: 'POST',
        headers: { Authorization: ORS_API_KEY, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!response.ok) return null
      const data = await response.json()
      if (!data.features || !data.features.length) return null
      return data.features[0].geometry.coordinates.map(coord => [coord[1], coord[0]])
    } catch (error) {
      console.error('Error fetching route segment:', error)
      return null
    }
  }

  async function buildRoadRoute(latLngs) {
    const fullRoute = []
    for (let i = 0; i < latLngs.length - 1; i++) {
      const from = { lat: latLngs[i][0], lng: latLngs[i][1] }
      const to = { lat: latLngs[i + 1][0], lng: latLngs[i + 1][1] }
      const segment = await fetchRouteSegment(from, to)
      if (segment && segment.length) {
        if (fullRoute.length) segment.shift()
        fullRoute.push(...segment)
      } else {
        fullRoute.push(latLngs[i], latLngs[i + 1])
      }
    }
    return fullRoute
  }

  async function updateMap(stops, startNeighbourhood) {
    if (!mapInstanceRef.current) return
    
    markersRef.current.forEach(m => mapInstanceRef.current.removeLayer(m))
    markersRef.current = []
    if (polylineRef.current) {
      mapInstanceRef.current.removeLayer(polylineRef.current)
      polylineRef.current = null
    }

    if (!stops.length) {
      const center = neighbourhoodCenters[startNeighbourhood] || { lat: -1.286389, lng: 36.817223 }
      mapInstanceRef.current.setView([center.lat, center.lng], 12)
      return
    }

    const latLngs = []
    const startCenter = neighbourhoodCenters[startNeighbourhood]
    if (startCenter) {
      const marker = L.marker([startCenter.lat, startCenter.lng], { title: `Start: ${startNeighbourhood}` }).addTo(mapInstanceRef.current)
      marker.bindPopup(`<b>Start</b><br>${startNeighbourhood}`)
      markersRef.current.push(marker)
      latLngs.push([startCenter.lat, startCenter.lng])
    }

    stops.forEach((stop, idx) => {
      const { place } = stop
      const { lat, lng } = place.coords
      latLngs.push([lat, lng])
      const marker = L.marker([lat, lng], { title: `${idx + 1}. ${place.name}` }).addTo(mapInstanceRef.current)
      marker.bindPopup(`<b>${idx + 1}. ${place.name}</b><br>${place.category} · ${place.neighbourhood}`)
      markersRef.current.push(marker)
    })

    const roadRouteLatLngs = await buildRoadRoute(latLngs)
    if (!roadRouteLatLngs.length) {
      polylineRef.current = L.polyline(latLngs, { color: '#22c55e', weight: 4, opacity: 0.9 }).addTo(mapInstanceRef.current)
      mapInstanceRef.current.fitBounds(polylineRef.current.getBounds(), { padding: [24, 24] })
      return
    }

    polylineRef.current = L.polyline(roadRouteLatLngs, { color: '#22c55e', weight: 4, opacity: 0.9 }).addTo(mapInstanceRef.current)
    mapInstanceRef.current.fitBounds(polylineRef.current.getBounds(), { padding: [24, 24] })
  }

  function getTransport(origin, destination) {
    if (origin === destination) return { mode: 'Walk', fare: 0, minutes: 0 }
    const directKey = `${origin}|${destination}`
    if (transportTable[directKey]) return transportTable[directKey]
    const originCenter = neighbourhoodCenters[origin]
    const destCenter = neighbourhoodCenters[destination]
    if (!originCenter || !destCenter) return { mode: 'Matatu', fare: 80, minutes: 45 }
    const km = haversineKm(originCenter, destCenter)
    const fare = Math.round(Math.max(30, km * 8))
    const minutes = Math.round(Math.max(10, km * 3))
    return { mode: 'Matatu', fare, minutes }
  }

  function stage1SpatialSearch(startNeighbourhood, radiusKm = 20) {
    const center = neighbourhoodCenters[startNeighbourhood]
    if (!center) return []
    return places.filter(p => haversineKm(center, p.coords) <= radiusKm)
  }

  function stage2BudgetFilter(candidates, budget, categoryPrefs) {
    const threshold = budget * 0.6
    return candidates.filter(p => {
      const placeCost = p.entryFee + p.avgFood
      if (placeCost > threshold) return false
      return true
    })
  }

  function textMatchBoost(place, queryTokens) {
    if (queryTokens.length === 0) return 0
    const haystack = [...place.tags, ...place.vibes, place.name, place.category].join(' ').toLowerCase()
    let matches = 0
    for (const token of queryTokens) {
      if (haystack.includes(token)) matches += 1
    }
    return Math.min(1, matches / queryTokens.length)
  }

  function stage3ScoreAndRank(candidates, preferredCategories, preferredVibes, freeText) {
    const catSet = new Set(preferredCategories)
    const vibeSet = new Set(preferredVibes.map(v => v.toLowerCase()))
    const tokens = freeText?.toLowerCase().split(/\s+/).filter(t => t.length > 2) ?? []

    return candidates.map(p => {
      const ratingNorm = p.rating / 5
      const categoryMatch = catSet.size ? (catSet.has(p.category) ? 1 : 0) : 0.5
      const vibeMatches = p.vibes.filter(v => vibeSet.has(v.toLowerCase())).length
      const vibeScore = Math.min(1, vibeMatches / 2)
      const popularityScore = p.popularity ?? 0.5
      const textBoost = textMatchBoost(p, tokens)
      const baseScore = ratingNorm * 0.3 + categoryMatch * 0.3 + vibeScore * 0.2 + popularityScore * 0.2
      const finalScore = baseScore + textBoost * 0.2
      return { place: p, score: finalScore }
    }).sort((a, b) => b.score - a.score)
  }

  function stage4ItinerarySolver(ranked, startNeighbourhood, budget, minutes) {
    let remainingBudget = budget
    let remainingMinutes = minutes
    let currentNeighbourhood = startNeighbourhood
    const stops = []

    for (const { place, score } of ranked) {
      const transport = getTransport(currentNeighbourhood, place.neighbourhood)
      const placeCost = place.entryFee + place.avgFood
      const totalCost = transport.fare + placeCost
      const totalTime = transport.minutes + place.durationMin

      if (totalCost <= remainingBudget && totalTime <= remainingMinutes) {
        stops.push({
          place,
          score,
          transport,
          costBreakdown: { transport: transport.fare, entry: place.entryFee, food: place.avgFood, total: totalCost },
          timeBreakdown: { travel: transport.minutes, visit: place.durationMin, total: totalTime },
        })
        remainingBudget -= totalCost
        remainingMinutes -= totalTime
        currentNeighbourhood = place.neighbourhood
      }
    }

    return { stops, remainingBudget, remainingMinutes }
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!geoDataLoaded) {
      setStatus({ message: 'Data is still loading. Please wait a moment and try again.', isError: true })
      return
    }

    const form = e.target
    const start = form['start-location'].value
    const budget = Number(form.budget.value || 0)
    const hours = Number(form.hours.value || 0)
    const mins = hours * 60

    const preferredCategories = Array.from(form.querySelectorAll('#category-pills input:checked')).map(el => el.value)
    const preferredVibes = Array.from(form.querySelectorAll('#vibe-pills input:checked')).map(el => el.value)
    const freeText = form['free-text'].value.trim()

    if (!start || !budget || !hours) {
      setStatus({ message: 'Please provide start, budget, and time.', isError: true })
      return
    }

    setStatus({ message: 'Running itinerary algorithm…', isError: false })
    setTotalBudget(budget)
    setTotalMinutes(mins)

    const spatialCandidates = stage1SpatialSearch(start, 20)
    const budgetCandidates = stage2BudgetFilter(spatialCandidates, budget, preferredCategories)
    const ranked = stage3ScoreAndRank(budgetCandidates, preferredCategories, preferredVibes, freeText)
    const result = stage4ItinerarySolver(ranked, start, budget, mins)

    setResult(result)

    if (!result.stops.length) {
      setStatus({ message: 'No valid plan within current constraints. Try increasing budget/time or relaxing category/vibe filters.', isError: true })
    } else {
      setStatus({ message: `Generated ${result.stops.length} stops. Budget remaining: KSH ${result.remainingBudget}, time remaining: ${Math.round(result.remainingMinutes)} min.`, isError: false })
    }
  }

  const categories = ['Park', 'Market', 'Restaurant', 'Café', 'Attraction', 'Mall']
  const vibes = ['authentic', 'local', 'chill', 'adventurous', 'scenic']

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>GeoSpend Kenya</h1>
          <p className="subtitle">Itinerary & budget engine — Nairobi demo</p>
        </div>
      </header>

      <main className="app-main">
        <section className="controls">
          <h2>Trip Inputs</h2>
          <form id="trip-form" onSubmit={handleSubmit}>
            <div className="field-group">
              <label htmlFor="start-location">Starting neighbourhood</label>
              <select id="start-location" required>
                {Object.keys(neighbourhoodCenters).map(name => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>

            <div className="field-row">
              <div className="field-group">
                <label htmlFor="budget">Total budget (KSH)</label>
                <input id="budget" type="number" min="100" step="50" defaultValue="2000" required />
              </div>
              <div className="field-group">
                <label htmlFor="hours">Available time (hours)</label>
                <input id="hours" type="number" min="1" max="16" step="0.5" defaultValue="8" required />
              </div>
            </div>

            <fieldset className="field-group">
              <legend>Preferred categories</legend>
              <div className="pill-row" id="category-pills">
                {categories.map(cat => (
                  <label key={cat} className="pill">
                    <input type="checkbox" value={cat} defaultChecked={['Park', 'Market', 'Restaurant'].includes(cat)} />
                    <span>{cat}{cat === 'Café' ? 's' : cat === 'Attraction' ? 's' : cat === 'Mall' ? 's' : 's'}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset className="field-group">
              <legend>Preferred vibes</legend>
              <div className="pill-row" id="vibe-pills">
                {vibes.map(vibe => (
                  <label key={vibe} className="pill">
                    <input type="checkbox" value={vibe} defaultChecked={['authentic', 'local', 'chill'].includes(vibe)} />
                    <span>{vibe.charAt(0).toUpperCase() + vibe.slice(1)}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="field-group">
              <label htmlFor="free-text">Optional: describe what you want</label>
              <input id="free-text" type="text" placeholder="e.g. peaceful, nature, not too crowded" />
              <p className="hint">Free-text is matched against place tags (simple semantic approximation for this demo).</p>
            </div>

            <button type="submit" className="primary-btn">Generate itinerary</button>
          </form>
          <div className={`status ${status.isError ? 'error' : ''}`}>{status.message}</div>
        </section>

        <section className="results">
          <div className="results-top">
            <div className="panel">
              <h2>Itinerary</h2>
              <div className="itinerary-container">
                {!result?.stops.length ? (
                  <p className="placeholder">Enter your details on the left and click <strong>Generate itinerary</strong> to see recommended stops.</p>
                ) : (
                  result.stops.map((stop, idx) => (
                    <article key={idx} className="itinerary-stop">
                      <div className="stop-number">{idx + 1}</div>
                      <div className="stop-main">
                        <div className="stop-title-row">
                          <div className="stop-name">{stop.place.name}</div>
                          <div className="stop-chip-row">
                            <span className="chip rating">★ {stop.place.rating.toFixed(1)}</span>
                            <span className="chip neighbourhood">{stop.place.neighbourhood}</span>
                            <span className="chip category">{stop.place.category}</span>
                            <span className="chip cost">KSH {stop.costBreakdown.total}</span>
                          </div>
                        </div>
                        <div className="stop-subrow">
                          <span><strong>Transport:</strong> {stop.transport.mode} · KSH {stop.costBreakdown.transport} · {stop.timeBreakdown.travel} min</span>
                          <span><strong>Entry:</strong> KSH {stop.costBreakdown.entry}</span>
                          <span><strong>Food est.:</strong> KSH {stop.costBreakdown.food}</span>
                        </div>
                        <div className="stop-subrow">
                          <span><strong>Visit duration:</strong> {stop.timeBreakdown.visit} min</span>
                          <span><strong>Step total time:</strong> {stop.timeBreakdown.total} min</span>
                        </div>
                      </div>
                    </article>
                  ))
                )}
              </div>
            </div>
            <div className="panel summary-panel">
              <h2>Budget & time summary</h2>
              <div className="summary-container">
                {result?.stops.length ? (() => {
                  const cumulativeCost = result.stops.reduce((sum, s) => sum + s.costBreakdown.total, 0)
                  const cumulativeMinutes = result.stops.reduce((sum, s) => sum + s.timeBreakdown.total, 0)
                  const transportTotal = result.stops.reduce((sum, s) => sum + s.costBreakdown.transport, 0)
                  const placeTotal = result.stops.reduce((sum, s) => sum + s.costBreakdown.entry + s.costBreakdown.food, 0)
                  const budgetUsedPct = (cumulativeCost / totalBudget) * 100
                  const timeUsedPct = (cumulativeMinutes / totalMinutes) * 100
                  return (
                    <>
                      <div className="summary-row"><span className="summary-label">Stops visited</span><span className="summary-value">{result.stops.length}</span></div>
                      <div className="summary-row"><span className="summary-label">Total on places</span><span className="summary-value">KSH {placeTotal}</span></div>
                      <div className="summary-row"><span className="summary-label">Total on transport</span><span className="summary-value">KSH {transportTotal}</span></div>
                      <div className="summary-row"><span className="summary-label">Total spent</span><span className="summary-value summary-strong">KSH {cumulativeCost}</span></div>
                      <div className="summary-row"><span className="summary-label">Budget remaining</span><span className="summary-value summary-strong">KSH {totalBudget - cumulativeCost}</span></div>
                      <hr style={{ borderColor: 'rgba(31,41,55,0.9)', margin: '0.35rem 0' }} />
                      <div className="summary-row"><span className="summary-label">Time used</span><span className="summary-value">{cumulativeMinutes} min ({timeUsedPct.toFixed(0)}% of budgeted time)</span></div>
                      <div className="summary-row"><span className="summary-label">Time remaining</span><span className="summary-value">{Math.max(0, Math.round(result.remainingMinutes))} min</span></div>
                      <div className="summary-row"><span className="summary-label">Budget used</span><span className="summary-value">{budgetUsedPct.toFixed(0)}% of KSH {totalBudget}</span></div>
                    </>
                  )
                })() : (
                  <>
                    <div className="summary-row"><span className="summary-label">Total spent</span><span className="summary-value summary-weak">KSH 0</span></div>
                    <div className="summary-row"><span className="summary-label">Time used</span><span className="summary-value summary-weak">0 min</span></div>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="panel map-panel">
            <h2>Map</h2>
            <div id="map" className="map" ref={mapRef}></div>
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <span>GeoSpend Kenya · Nairobi demo · Algorithm prototype</span>
      </footer>
    </div>
  )
}

export default App
