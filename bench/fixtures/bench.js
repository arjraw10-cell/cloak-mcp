function post(event, data) {
  return fetch('api/' + event, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)})
    .then(() => { const s = document.getElementById('status'); if (s) s.textContent = 'Saved.'; });
}
