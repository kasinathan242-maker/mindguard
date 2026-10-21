try {
  var theme = localStorage.getItem('mindguard.theme');
  if (theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme;
} catch (e) {
  // Storage can be unavailable (private mode); the system preference applies instead.
}

try {
  var svgDataUri = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='18' fill='%232563eb'/%3E%3Ccircle cx='32' cy='32' r='14' fill='%23eff6ff'/%3E%3Ccircle cx='32' cy='32' r='7' fill='%232563eb'/%3E%3C/svg%3E";
  var links = document.querySelectorAll("link[rel*='icon']");
  links.forEach(function (link) {
    if (link.getAttribute('type') === 'image/svg+xml') {
      link.href = svgDataUri;
    }
  });
} catch (e) {}

