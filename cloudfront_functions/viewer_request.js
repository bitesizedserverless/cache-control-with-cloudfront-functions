function handler(event) {
  var request = event.request;

  // If the asset has a .png or .jpg extension, but the ?h=<hash>
  // query string is not provided, return a 403 forbidden error.
  if (request.uri.match(/^.*(\.png|\.jpg)$/) && !("h" in request.querystring)) {
    var response = {
      statusCode: 403,
      statusDescription: "Forbidden",
      headers: { error: { value: "Cannot request image without hash" } },
    };
    return response;
  }
  return request;
}
