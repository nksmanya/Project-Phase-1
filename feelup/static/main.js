function toggleComments(id) {
  const el = document.getElementById('comments-' + id);
  if (!el) return;
  el.classList.toggle('d-none');
}
