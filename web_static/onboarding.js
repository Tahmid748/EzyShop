const form = document.querySelector('#onboarding-form');
const status = document.querySelector('#status');
const tg = window.Telegram?.WebApp;
tg?.ready(); tg?.expand();
const files = document.querySelector('#images');
const items = document.querySelector('#item-forms');
document.querySelector('#continue').addEventListener('click', () => {
  if (!form.business_name.value.trim() || !files.files.length) { status.textContent = 'Add your business name and at least one image first.'; return; }
  items.replaceChildren();
  [...files.files].forEach((file, index) => {
    const card = document.createElement('fieldset'); card.className = 'item-card';
    card.innerHTML = `<legend>Item ${index + 1}: ${file.name}</legend><button type="button" class="generate">Generate draft</button><label>Name<input class="item-name" required></label><label>Price<input class="item-price" type="number" min="0" step="0.01" required value="0"></label><label>Quantity<input class="item-quantity" type="number" min="0" required value="0"></label><label>Description<textarea class="item-description" required></textarea></label>`;
    card.querySelector('.generate').onclick = () => { const title=file.name.replace(/\.[^.]+$/, '').replace(/[-_]+/g, ' '); card.querySelector('.item-name').value=title.replace(/\b\w/g,c=>c.toUpperCase()); card.querySelector('.item-description').value=`${title} — details generated from the uploaded inventory image. Please confirm size, colour, and condition.`; };
    items.append(card);
  });
  document.querySelector('#initial-step').hidden = true; document.querySelector('#details-step').hidden = false; status.textContent = '';
});
form.addEventListener('submit', async event => {
  event.preventDefault(); status.textContent = 'Uploading and creating local image vectors…';
  const body = new FormData(form); body.append('init_data', tg?.initData || '');
  body.append('items_json', JSON.stringify([...document.querySelectorAll('.item-card')].map(card => ({name:card.querySelector('.item-name').value,price:card.querySelector('.item-price').value,quantity:card.querySelector('.item-quantity').value,description:card.querySelector('.item-description').value}))));
  const response = await fetch('/api/onboarding', {method:'POST', body});
  const result = await response.json();
  if (!response.ok) { status.textContent = result.detail || 'Could not save inventory.'; return; }
  status.textContent = `${result.images_indexed} item(s) indexed. Your shop is ready — your storefront link was sent in Telegram.`;
});
