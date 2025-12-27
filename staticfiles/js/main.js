// static/js/main.js
// small helper: get geolocation and set hidden fields so server can compute distance
function getLocation() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(function(pos){
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      const latInput = document.getElementById('lat');
      const lonInput = document.getElementById('lon');
      if (latInput) latInput.value = lat;
      if (lonInput) lonInput.value = lon;
    }, function(err){
      console.warn('geo error', err);
    });
  }
  
  document.addEventListener('DOMContentLoaded', function(){
    // try to fill location
    getLocation();
  });
  