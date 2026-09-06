// Browser Geolocation Service Wrapper

export function getCurrentCoordinates() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("Geolocation is not supported by your browser."));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: Math.round(position.coords.accuracy * 10) / 10,
          timestamp: position.timestamp,
        });
      },
      (error) => {
        let msg = "Unable to retrieve your location.";
        switch (error.code) {
          case error.PERMISSION_DENIED:
            msg = "Location permission was denied. Location is strictly required for attendance.";
            break;
          case error.POSITION_UNAVAILABLE:
            msg = "Location information is unavailable. Ensure your GPS is enabled.";
            break;
          case error.TIMEOUT:
            msg = "The request to get user location timed out. Please try again.";
            break;
        }
        reject(new Error(msg));
      },
      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 10000,
      }
    );
  });
}
