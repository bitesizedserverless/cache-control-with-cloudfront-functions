function handler(event) {
  var request = event.request;
  var response = event.response;
  var headers = response.headers;

  if (request.uri.match(/^.*(\.png|\.jpg)$/) && "h" in request.querystring) {
    // For an image with a hash (`?h=`) return a very long cache duration
    headers["cache-control"] = {
      value: "public, max-age=31536000, immutable",
    };
  } else {
    // Everything else must revalidate and can't cache locally
    headers["cache-control"] = {
      value: "public, max-age=0, must-revalidate",
    };
  }

  return response;
}
