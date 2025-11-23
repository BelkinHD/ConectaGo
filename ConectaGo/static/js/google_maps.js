function loadGoogleMaps(apiKey, callback) {
  if (typeof google === 'object' && typeof google.maps === 'object') {
    callback();
    return;
  }
  const script = document.createElement('script');
  script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=${callback.name}&libraries=places`;
  script.async = true;
  script.defer = true;
  document.head.appendChild(script);
}

function initMap() {
  const mapContainer = document.getElementById('map');
  if (!mapContainer) {
    console.warn('Map container not found');
    return;
  }

  // Parse lat/lng robustly, replacing comma with dot if needed
  let latRaw = mapContainer.dataset.lat;
  let lngRaw = mapContainer.dataset.lng;

  // Replace comma with dot for decimal separator if present
  latRaw = latRaw ? latRaw.toString().replace(',', '.') : '';
  lngRaw = lngRaw ? lngRaw.toString().replace(',', '.') : '';

  const lat = parseFloat(latRaw);
  const lng = parseFloat(lngRaw);
  const locationString = mapContainer.dataset.location;

  const apiKey = mapContainer.dataset.apiKey;

  function createMapAndMarker(position) {
    console.log('Creating map at position:', position);
    const map = new google.maps.Map(mapContainer, {
      zoom: 15,
      center: position,
    });
    new google.maps.Marker({
      position: position,
      map: map,
    });
  }

  if (!isNaN(lat) && !isNaN(lng) && (lat !== 0 || lng !== 0)) {
    console.log('Using lat/lng from data attributes:', lat, lng);
    createMapAndMarker({ lat: lat, lng: lng });
  } else if (locationString && locationString.trim() !== '') {
    console.log('Geocoding location string:', locationString);
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: locationString }, (results, status) => {
      if (status === 'OK' && results[0]) {
        const position = results[0].geometry.location;
        console.log('Geocoding successful:', position.toString());
        createMapAndMarker(position);
      } else {
        console.error('Geocode was not successful for the following reason: ' + status);
        // Fallback to default location (Santiago, Chile)
        const defaultPosition = { lat: -33.4489, lng: -70.6693 };
        console.log('Using fallback default location:', defaultPosition);
        createMapAndMarker(defaultPosition);
      }
    });
  } else {
    console.warn('No valid location data available to display map.');
    // Fallback to default location (Santiago, Chile)
    const defaultPosition = { lat: -33.4489, lng: -70.6693 };
    console.log('Using fallback default location:', defaultPosition);
    createMapAndMarker(defaultPosition);
  }

  // Initialize Place Autocomplete Element for input with id 'location-input' if exists
  const input = document.getElementById('location-input');
  if (input) {
    const options = {
      componentRestrictions: { country: 'cl' },
      fields: ['address_components', 'geometry', 'icon', 'name'],
      strictBounds: false,
      types: ['establishment', 'geocode'],
    };
    const autocomplete = new google.maps.places.Autocomplete(input, options);

    autocomplete.addListener('place_changed', () => {
      const place = autocomplete.getPlace();
      if (!place.geometry) {
        console.log("No details available for input: '" + place.name + "'");
        return;
      }
      // Optionally update map center and marker
      const map = new google.maps.Map(mapContainer, {
        zoom: 15,
        center: place.geometry.location,
      });
      new google.maps.Marker({
        position: place.geometry.location,
        map: map,
      });
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const mapContainer = document.getElementById('map');
  if (!mapContainer) return;
  const apiKey = mapContainer.dataset.apiKey;
  loadGoogleMaps(apiKey, initMap);
});
