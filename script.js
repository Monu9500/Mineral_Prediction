let map = null;
let rockData = [];
let filteredRocks = [];
let markers = [];
let gpsEnabled = false;
let userMarker = null;

// DOM elements
const searchForm = document.getElementById("searchForm");
const searchInput = document.getElementById("searchInput");
const clearSearchBtn = document.getElementById("clearSearch");
const gpsToggle = document.getElementById("gpsToggle");
const resetViewBtn = document.getElementById("resetView");
const locationCount = document.getElementById("locationCount");
const loadingOverlay = document.getElementById("loadingOverlay");
const locationSearchForm = document.getElementById("locationSearchForm");
const locationSearchInput = document.getElementById("locationSearchInput");

// Custom icon for location search
const locationIcon = L.icon({
  iconUrl: "/static/map_page/icon-2.png",
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32]
});

// Initialize map & data
document.addEventListener("DOMContentLoaded", async () => {
  initMap();
  await loadRockData();
  hideLoading();
  updateLocationCount();
  setupEvents();
});

// Load rock data from API
async function loadRockData() {
  const res = await fetch("/api/rocks");
  rockData = await res.json();
}

// Event listeners
function setupEvents() {
  searchForm.addEventListener("submit", handleRockSearch);
  clearSearchBtn.addEventListener("click", clearSearch);
  locationSearchForm.addEventListener("submit", handleLocationSearch);
  gpsToggle.addEventListener("click", toggleGPS);
  resetViewBtn.addEventListener("click", resetMap);
}

// Rock search
function handleRockSearch(e) {
  e.preventDefault();
  const term = searchInput.value.trim().toLowerCase();
  filteredRocks = term ? rockData.filter(r => r.Rocks.toLowerCase().includes(term)) : [];
  showMarkers(filteredRocks);
  updateLocationCount();
}

// Location search
function handleLocationSearch(e) {
  e.preventDefault();
  const term = locationSearchInput.value.trim().toLowerCase();
  filteredRocks = term ? rockData.filter(r => r.Place.toLowerCase().includes(term)) : [];
  showLocationMarkers(filteredRocks); // show with custom icon
  updateLocationCount();
}

// Clear search
function clearSearch() {
  searchInput.value = "";
  filteredRocks = [];
  clearMarkers();
  updateLocationCount();
}

// Initialize Leaflet map
function initMap() {
  map = L.map("map").setView([20, 0], 2);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap contributors" }).addTo(map);
}

// Show rock markers (default icon)
function showMarkers(rocks) {
  clearMarkers();
  markers = rocks.map(r =>
    L.marker([r.Latitude, r.Longitude])
      .addTo(map)
      //.bindPopup(`<strong>${r.Rocks}</strong><br>${r.Place}`)
      .bindPopup(`<a href="/rock/${r.Id}"><strong>${r.Rocks}</strong></a><br>${r.Place}`)

  );
}

// Show location markers with custom icon
function showLocationMarkers(rocks) {
  clearMarkers();
  markers = rocks.map(r =>
    L.marker([r.Latitude, r.Longitude], { icon: locationIcon })
      .addTo(map)
      //.bindPopup(`<strong>${r.Rocks}</strong><br>${r.Place}`)
      .bindPopup(`<a href="/rock/${r.Id}"><strong>${r.Rocks}</strong></a><br>${r.Place}`)

  );
}

// Clear all markers
function clearMarkers() {
  markers.forEach(m => map.removeLayer(m));
  markers = [];
}

// Reset view
function resetMap() {
  map.setView([20, 0], 2);
  clearMarkers();
  filteredRocks = [];
  updateLocationCount();
}

// Update counter
function updateLocationCount() {
  locationCount.textContent = `${filteredRocks.length} rock location${filteredRocks.length !== 1 ? 's' : ''}`;
}

// Toggle GPS
function toggleGPS() {
  if (!gpsEnabled) {
    navigator.geolocation?.getCurrentPosition(pos => {
      const { latitude, longitude } = pos.coords;
      if (userMarker) map.removeLayer(userMarker);
      userMarker = L.marker([latitude, longitude]).addTo(map).bindPopup("You are here").openPopup();
      map.setView([latitude, longitude], 8);
      gpsEnabled = true;
      gpsToggle.textContent = "GPS On";
    }, () => alert("Cannot get location"));
  } else {
    if (userMarker) map.removeLayer(userMarker);
    gpsEnabled = false;
    gpsToggle.textContent = "GPS Off";
  }
}

// Hide loading overlay
function hideLoading() {
  loadingOverlay?.classList.add("hidden");
}


