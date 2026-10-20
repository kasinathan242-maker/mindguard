// Applies a saved light/dark preference before first paint. Loaded as an external file because
// the Content-Security-Policy forbids inline scripts.
try {
  var theme = localStorage.getItem('mindguard.theme');
  if (theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme;
} catch (e) {
  // Storage can be unavailable (private mode); the system preference applies instead.
}
