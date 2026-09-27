document.getElementById('y').textContent = new Date().getFullYear();
const btns = document.querySelectorAll('.filters button');
btns.forEach(b => b.addEventListener('click', () => {
  btns.forEach(x => x.classList.toggle('on', x === b));
  document.querySelectorAll('.card').forEach(c => {
    c.classList.toggle('hide', b.dataset.f !== 'all' && !c.dataset.tags.split(' ').includes(b.dataset.f));
  });
}));
