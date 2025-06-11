async function carregarSelecao() {
  const resReq = await fetch('http://localhost:5000/requerentes');
  const requerentes = await resReq.json();
  const tbodyReq = document.querySelector('#tabela-selecao-requerente tbody');
  tbodyReq.innerHTML = '';
  requerentes.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${r.id}</td><td>${r.nome}</td><td><button type="button">Selecionar</button></td>`;
    tr.querySelector('button').onclick = () => {
      document.getElementById('requerente-id').value = r.id;
    };
    tbodyReq.appendChild(tr);
  });

  const resArv = await fetch('http://localhost:5000/arvores');
  const arvores = await resArv.json();
  const tbodyArv = document.querySelector('#tabela-selecao-arvore tbody');
  tbodyArv.innerHTML = '';
  arvores.forEach(a => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${a.id}</td><td>${a.especie}</td><td>${a.endereco}</td><td>${a.bairro}</td><td><button type="button">Selecionar</button></td>`;
    tr.querySelector('button').onclick = () => {
      document.getElementById('arvore-id').value = a.id;
    };
    tbodyArv.appendChild(tr);
  });
}

document.getElementById('filtro-requerente').addEventListener('input', function(e) {
  const termo = e.target.value.toLowerCase();
  document.querySelectorAll('#tabela-selecao-requerente tbody tr').forEach(tr => {
    tr.style.display = tr.children[1].textContent.toLowerCase().includes(termo) ? '' : 'none';
  });
});

document.getElementById('filtro-arvore').addEventListener('input', function(e) {
  const termo = e.target.value.toLowerCase();
  document.querySelectorAll('#tabela-selecao-arvore tbody tr').forEach(tr => {
    tr.style.display = tr.children[1].textContent.toLowerCase().includes(termo) ? '' : 'none';
  });
});

document.getElementById('form-requerimento').addEventListener('submit', async function(e) {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(this));
  const response = await fetch('http://localhost:5000/requerimento', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const resultado = await response.json();
  document.getElementById('resposta').innerText = JSON.stringify(resultado, null, 2);
  this.reset();
});

window.onload = carregarSelecao;
