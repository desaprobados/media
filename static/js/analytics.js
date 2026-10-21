(() => {
  const token = window.CLOUDFLARE_WEB_ANALYTICS_TOKEN?.trim();
  if (!token) return;

  const beacon = document.createElement("script");
  beacon.defer = true;
  beacon.src = "https://static.cloudflareinsights.com/beacon.min.js";
  beacon.dataset.cfBeacon = JSON.stringify({ token });
  document.head.append(beacon);
})();
