// Client-side routes (/cases/01, /review, ...) have no file in S3: serve index.html.
// Paths with a file extension and /api/* pass through unchanged.
function handler(event) {
  var request = event.request;
  var uri = request.uri;
  if (uri.startsWith('/api/')) {
    return request;
  }
  var last = uri.split('/').pop();
  if (last.indexOf('.') === -1) {
    request.uri = '/index.html';
  }
  return request;
}
