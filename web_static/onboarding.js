const form = document.querySelector('#onboarding-form');
const status = document.querySelector('#status');
const tg = window.Telegram?.WebApp;
tg?.ready(); tg?.expand();
const files = document.querySelector('#images');
const items = document.querySelector('#item-forms');
const indexing = document.querySelector('#indexing');
document.querySelector('#continue').addEventListener('click', () => {
  if (!form.business_name.value.trim() || !files.files.length) { status.textContent = 'Add your business name and at least one image first.'; return; }
  items.replaceChildren();
  [...files.files].forEach((file, index) => {
    const card = document.createElement('fieldset'); card.className = 'item-card';
    const preview = URL.createObjectURL(file);
    card.innerHTML = `<legend>Item ${index + 1}</legend><img class="item-preview" src="${preview}" alt="${file.name}"><p class="file-name">${file.name}</p><button type="button" class="generate">Generate details with AI</button><p class="generation-status" aria-live="polite"></p><label>Name<input class="item-name" required></label><label>Price (USD)<input class="item-price" type="number" min="0" step="0.01" required value="0"></label><label>Quantity<input class="item-quantity" type="number" min="0" required value="0"></label><label>Description<textarea class="item-description" required></textarea></label>`;
    card.querySelector('.generate').onclick = async event => { const button=event.currentTarget, note=card.querySelector('.generation-status'); button.disabled=true; button.textContent='Analysing image…'; note.textContent='AI is creating an editable draft.'; const body=new FormData(); body.append('image',file); try { const response=await fetch('/api/inventory/generate',{method:'POST',body}); const details=await response.json(); if(!response.ok)throw new Error(details.detail); card.querySelector('.item-name').value=details.name; card.querySelector('.item-price').value=details.price; card.querySelector('.item-quantity').value=details.quantity; card.querySelector('.item-description').value=details.description; note.textContent='Draft generated. Please review it before saving.'; } catch(error) { note.textContent=error.message || 'Generation failed. Enter details manually.'; } finally { button.disabled=false; button.textContent='Generate details with AI'; } };
    items.append(card);
  });
  document.querySelector('#initial-step').hidden = true; document.querySelector('#details-step').hidden = false; status.textContent = '';
});
form.addEventListener('submit', async event => {
  event.preventDefault(); indexing.hidden=false; status.textContent = '';
  const body = new FormData(form); body.append('init_data', tg?.initData || '');
  body.append('items_json', JSON.stringify([...document.querySelectorAll('.item-card')].map(card => ({name:card.querySelector('.item-name').value,price:card.querySelector('.item-price').value,quantity:card.querySelector('.item-quantity').value,description:card.querySelector('.item-description').value}))));
  const response = await fetch('/api/onboarding', {method:'POST', body});
  const result = await response.json();
  if (!response.ok) { indexing.hidden=true; status.textContent = result.detail || 'Could not save inventory.'; return; }
  indexing.innerHTML=`<div class="completion"><span class="success-mark">✓</span><h2>Inventory indexed</h2><p>${result.images_indexed} item(s) are ready. Your storefront link was also sent in Telegram.</p><a href="${result.storefront_url}" target="_blank" rel="noopener">Open your storefront</a><button type="button" id="close-web-app">Close</button></div>`;
  document.querySelector('#close-web-app').onclick=()=>tg?.close();
});
