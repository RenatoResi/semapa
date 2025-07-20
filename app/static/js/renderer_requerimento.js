let requerentesSelecionados = [];
let arvoresSelecionadas = [];
let paginaReq = 1;
let paginaArv = 1;
const porPagina = 5;
let filteredRequerentes = [];
let filteredArvores = [];


function renderTabelaRequerentes() {
  const tbodyReq = document.querySelector('#tabela-selecao-requerente tbody');
  tbodyReq.innerHTML = '';
  const inicio = (paginaReq - 1) * porPagina;
  const fim = inicio + porPagina;
  filteredRequerentes.slice(inicio, fim).forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${r.id}</td><td>${r.nome}</td><td><button type="button">Selecionar</button></td>`;
    tr.querySelector('button').onclick = () => {
      document.getElementById('requerente-id').value = r.id;
    };
    tbodyReq.appendChild(tr);
  });
  atualizarPaginacaoReq();
}

function renderTabelaArvores() {
  const tbodyArv = document.querySelector('#tabela-selecao-arvore tbody');
  tbodyArv.innerHTML = '';
  const inicio = (paginaArv - 1) * porPagina;
  const fim = inicio + porPagina;
  filteredArvores.slice(inicio, fim).forEach(a => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${a.id}</td><td>${a.especie}</td><td>${a.endereco}</td><td>${a.bairro}</td><td><button type="button">Selecionar</button></td>`;
    tr.querySelector('button').onclick = () => {
      document.getElementById('arvore-id').value = a.id;
    };
    tbodyArv.appendChild(tr);
  });
  atualizarPaginacaoArv();
}

function atualizarPaginacaoReq() {
  const paginacao = document.getElementById('paginacao-requerentes');
  if (!paginacao) return;
  const totalPaginas = Math.ceil(filteredRequerentes.length / porPagina);
  paginacao.innerHTML = `
    <button onclick="paginaAnteriorReq()" ${paginaReq === 1 ? 'disabled' : ''}>Anterior</button>
    <span>Página ${paginaReq} de ${totalPaginas}</span>
    <button onclick="proximaPaginaReq()" ${paginaReq === totalPaginas ? 'disabled' : ''}>Próxima</button>
  `;
}

function atualizarPaginacaoArv() {
  const paginacao = document.getElementById('paginacao-arvores');
  if (!paginacao) return;
  const totalPaginas = Math.ceil(filteredArvores.length / porPagina);
  paginacao.innerHTML = `
    <button onclick="paginaAnteriorArv()" ${paginaArv === 1 ? 'disabled' : ''}>Anterior</button>
    <span>Página ${paginaArv} de ${totalPaginas}</span>
    <button onclick="proximaPaginaArv()" ${paginaArv === totalPaginas ? 'disabled' : ''}>Próxima</button>
  `;
}

function paginaAnteriorReq() {
  if (paginaReq > 1) {
    paginaReq--;
    renderTabelaRequerentes();
  }
}
function proximaPaginaReq() {
  const totalPaginas = Math.ceil(requerentesSelecionados.length / porPagina);
  if (paginaReq < totalPaginas) {
    paginaReq++;
    renderTabelaRequerentes();
  }
}
function paginaAnteriorArv() {
  if (paginaArv > 1) {
    paginaArv--;
    renderTabelaArvores();
  }
}
function proximaPaginaArv() {
  const totalPaginas = Math.ceil(arvoresSelecionadas.length / porPagina);
  if (paginaArv < totalPaginas) {
    paginaArv++;
    renderTabelaArvores();
  }
}

async function carregarSelecao() {
  // Requerentes
  const resReq = await fetch('/requerentes/todos');
  const dataReq = await resReq.json();
  requerentesSelecionados = dataReq.requerentes || dataReq;
  filteredRequerentes = [...requerentesSelecionados];
  paginaReq = 1;
  renderTabelaRequerentes();

  // Árvores
  const resArv = await fetch('/arvores/todos');
  const dataArv = await resArv.json();
  arvoresSelecionadas = dataArv.arvores || dataArv;
  filteredArvores = [...arvoresSelecionadas];
  paginaArv = 1;
  renderTabelaArvores();
}


document.getElementById('filtro-requerente').addEventListener('input', function(e) {
  const termo = e.target.value.toLowerCase();
  
  // Filtra a lista completa
  filteredRequerentes = requerentesSelecionados.filter(r => 
    r.nome.toLowerCase().includes(termo)
  );
  
  paginaReq = 1;
  renderTabelaRequerentes(); // Atualiza a exibição
});

document.getElementById('filtro-arvore').addEventListener('input', function(e) {
  const termo = e.target.value.toLowerCase();
  
  filteredArvores = arvoresSelecionadas.filter(a => {
    const especie = a.especie ? a.especie.toLowerCase() : '';
    const endereco = a.endereco ? a.endereco.toLowerCase() : '';
    const bairro = a.bairro ? a.bairro.toLowerCase() : '';
    
    return (
      especie.includes(termo) ||
      endereco.includes(termo) ||
      bairro.includes(termo)
    );
  });
  
  paginaArv = 1;
  renderTabelaArvores();
  console.log('Dados brutos:', arvoresSelecionadas[0]); // Verifique as propriedades
  console.log('Dados filtrados:', filteredArvores[0]); // Verifique as propriedades
  console.log('Termo de filtro:', termo); // Verifique o termo de filtro
});

document.getElementById('form-requerimento').addEventListener('submit', async function(e) {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(this));
  const response = await fetch('/requerimento', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  const resultado = await response.json();
  document.getElementById('resposta').innerText = JSON.stringify(resultado, null, 2);
  this.reset();
});

window.onload = carregarSelecao;
