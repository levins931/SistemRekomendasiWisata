function openMapsRoute(placeName, destLat, destLng) {
    let destination;

    if (placeName && placeName !== "None") {
        destination = encodeURIComponent(placeName);
    } else {
        destination = `${destLat},${destLng}`;
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                let userLat = position.coords.latitude;
                let userLng = position.coords.longitude;
                let url = `https://www.google.com/maps/dir/?api=1&origin=${userLat},${userLng}&destination=${destination}`;
                window.open(url, "_blank");
            },
            function () {
                let url = `https://www.google.com/maps/dir/?api=1&origin=Current+Location&destination=${destination}`;
                window.open(url, "_blank");
            }
        );
    } else {
        let url = `https://www.google.com/maps/dir/?api=1&origin=Current+Location&destination=${destination}`;
        window.open(url, "_blank");
    }
}
