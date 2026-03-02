/* Minimal API client used by frontend templates
 * - Uses Fetch API
 * - Adds Authorization header when token available
 */
export async function request(path, { method = 'GET', body = null, headers = {} } = {}) {
  const opts = { method, headers: { 'Accept': 'application/json', ...headers } };
  const token = localStorage.getItem('api_token');
  if (token) opts.headers['Authorization'] = `Bearer ${token}`;
  if (body && !(body instanceof FormData)) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  } else if (body) {
    opts.body = body; // FormData
  }

  const res = await fetch(path, opts);
  if (!res.ok) {
    const txt = await res.text();
    const err = new Error(`Request failed ${res.status}`);
    err.status = res.status;
    err.body = txt;
    throw err;
  }
  return res.json();
}
