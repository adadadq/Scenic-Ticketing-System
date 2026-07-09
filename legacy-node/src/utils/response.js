function sendJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);

  res.statusCode = statusCode;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Content-Length', Buffer.byteLength(body));
  res.end(body);
}

module.exports = {
  sendJson,
};
