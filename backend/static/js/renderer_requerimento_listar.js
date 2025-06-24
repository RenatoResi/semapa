let requerimentosDisponiveis = [];
let requerimentosSelecionados = [];
let filteredRequerimentos = [];
let paginaReq = 1;
const porPagina = 5;
let map;
let marcadoresMapa = {};

// Carrega todos os requerimentos e inicializa filtrados
async function carregarSelecao() {
  try {
    const res = await fetch('/requerimentos/todos');
    if (!res.ok) throw new Error(`Erro HTTP! Status: ${res.status}`);
    requerimentosDisponiveis = await res.json();
    filteredRequerimentos = [...requerimentosDisponiveis];
    paginaReq = 1;
    renderTabelaRequerimentos();
    renderTabelaSelecionados();
    atualizarPaginacaoReq();
    criarMarcadores();  // Atualiza o mapa com todos os dados iniciais
  } catch (error) {
    console.error('Erro ao carregar requerimentos:', error);
    document.getElementById('resposta').innerText = `Erro: ${error.message}`;
  }
}

// Renderiza a tabela principal
function renderTabelaRequerimentos() {
  const tbody = document.querySelector('#requerimentos-lista tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  const inicio = (paginaReq - 1) * porPagina;
  const fim = inicio + porPagina;
  filteredRequerimentos.slice(inicio, fim).forEach(r => {
    if (requerimentosSelecionados.some(sel => sel.id === r.id)) return;
    const tr = document.createElement('tr');
    tr.dataset.id = r.id;
    tr.innerHTML = `
      <td>${r.numero}</td>
      <td>${r.tipo}</td>
      <td>${r.motivo}</td>
      <td>${r.prioridade}</td>
      <td>${r.data_abertura ? new Date(r.data_abertura).toLocaleDateString() : ''}</td>
      <td>${r.requerente_nome || ''}</td>
      <td>${r.arvore_endereco || ''}</td>
      <td>${r.arvore_bairro || ''}</td>
      <td>
        <button class="btn-editar-inline">Editar</button>
        <button class="btn-selecionar" data-id="${r.id}">Selecionar</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Renderiza a tabela de selecionados
function renderTabelaSelecionados() {
  const tbody = document.querySelector('#requerimentos-selecionados tbody');
  if (!tbody) return;
  tbody.innerHTML = '';
  requerimentosSelecionados.forEach(r => {
    const tr = document.createElement('tr');
    tr.dataset.id = r.id;
    tr.innerHTML = `
      <td>${r.numero}</td>
      <td>${r.tipo}</td>
      <td>${r.motivo}</td>
      <td>${r.prioridade}</td>
      <td>${r.data_abertura ? new Date(r.data_abertura).toLocaleDateString() : ''}</td>
      <td>${r.requerente_nome || ''}</td>
      <td>${r.arvore_endereco || ''}</td>
      <td>${r.arvore_bairro || ''}</td>
      <td>
        <button class="btn-remover-selecionado" data-id="${r.id}">Remover</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Paginação
function atualizarPaginacaoReq() {
  const paginacao = document.getElementById('paginacao-requerimentos');
  if (!paginacao) return;
  const totalPaginas = Math.ceil(filteredRequerimentos.length / porPagina);
  paginacao.innerHTML = `
    <button onclick="paginaAnteriorReq()" ${paginaReq === 1 ? 'disabled' : ''}>
      Anterior
    </button>
    <span>Página ${paginaReq} de ${totalPaginas}</span>
    <button onclick="proximaPaginaReq()" ${paginaReq === totalPaginas ? 'disabled' : ''}>
      Próxima
    </button>
  `;
}

function paginaAnteriorReq() {
  if (paginaReq > 1) {
    paginaReq--;
    renderTabelaRequerimentos();
    atualizarPaginacaoReq();
  }
}

function proximaPaginaReq() {
  const totalPaginas = Math.ceil(filteredRequerimentos.length / porPagina);
  if (paginaReq < totalPaginas) {
    paginaReq++;
    renderTabelaRequerimentos();
    atualizarPaginacaoReq();
  }
}

// Filtro
document.getElementById('filtro-requerimento').addEventListener('input', function(e) {
  const termo = e.target.value.toLowerCase();
  filteredRequerimentos = requerimentosDisponiveis.filter(r => {
    return (
      (r.numero?.toLowerCase() || '').includes(termo) ||
      (r.tipo?.toLowerCase() || '').includes(termo) ||
      (r.motivo?.toLowerCase() || '').includes(termo) ||
      (r.prioridade?.toLowerCase() || '').includes(termo) ||
      (r.requerente_nome?.toLowerCase() || '').includes(termo) ||
      (r.arvore_endereco?.toLowerCase() || '').includes(termo) ||
      (r.arvore_bairro?.toLowerCase() || '').includes(termo)
    );
  });
  
  // Resetar paginação e renderizar imediatamente
  paginaReq = 1;
  renderTabelaRequerimentos();
  atualizarPaginacaoReq();
  criarMarcadores();  // Atualizar o mapa com os resultados filtrados
});

// Ordenação
async function ordenarRequerimentos() {
  const campo = document.getElementById('ordenar-campo').value;
  const direcao = document.getElementById('ordenar-direcao').value;
  const res = await fetch(`/requerimentos?order_by=${campo}&direction=${direcao}`);
  const data = await res.json();
  requerimentosDisponiveis = data.requerimentos;
  filteredRequerimentos = [...requerimentosDisponiveis];
  paginaReq = 1;
  renderTabelaRequerimentos();
  atualizarPaginacaoReq();
  criarMarcadores();  // Atualizar o mapa após ordenação
}

// Selecionar e remover requerimento
document.addEventListener('click', function(e) {
  // Selecionar
  if (e.target.classList.contains('btn-selecionar')) {
    const id = parseInt(e.target.dataset.id);
    const req = requerimentosDisponiveis.find(r => r.id === id);
    if (req && !requerimentosSelecionados.some(r => r.id === id)) {
      requerimentosSelecionados.push(req);
      renderTabelaRequerimentos();
      renderTabelaSelecionados();
      criarMarcadores();
    }
  }
  // Remover da seleção
  if (e.target.classList.contains('btn-remover-selecionado')) {
    const id = parseInt(e.target.dataset.id);
    requerimentosSelecionados = requerimentosSelecionados.filter(r => r.id !== id);
    renderTabelaRequerimentos();
    renderTabelaSelecionados();
    criarMarcadores();
  }
  // Editar inline
  if (e.target.classList.contains('btn-editar-inline')) {
    const tr = e.target.closest('tr');
    const id = parseInt(tr.dataset.id);
    const r = requerimentosDisponiveis.find(r => r.id === id);
    if (!r) return;
    tr.innerHTML = `
      <td></td>
      <td><input type="text" value="${r.tipo || ''}" class="input-inline" data-field="tipo"></td>
      <td><input type="text" value="${r.motivo || ''}" class="input-inline" data-field="motivo"></td>
      <td>
        <select class="input-inline" data-field="prioridade">
          <option${r.prioridade === 'Urgente' ? ' selected' : ''}>Urgente</option>
          <option${r.prioridade === 'Alta' ? ' selected' : ''}>Alta</option>
          <option${r.prioridade === 'Normal' ? ' selected' : ''}>Normal</option>
        </select>
      </td>
      <td><input type="date" value="${r.data_abertura ? r.data_abertura.split('T')[0] : ''}" class="input-inline" data-field="data_abertura"></td>
      <td>${r.requerente_nome || ''}</td>
      <td>${r.arvore_endereco || ''}</td>
      <td>${r.arvore_bairro || ''}</td>
      <td>
        <button class="btn-salvar-inline" data-id="${r.id}">Salvar</button>
        <button class="btn-cancelar-inline">Cancelar</button>
      </td>
    `;
  }
  // Cancelar edição
  if (e.target.classList.contains('btn-cancelar-inline')) {
    renderTabelaRequerimentos();
    atualizarPaginacaoReq();
  }
  // Salvar edição
  if (e.target.classList.contains('btn-salvar-inline')) {
    const tr = e.target.closest('tr');
    const id = parseInt(e.target.dataset.id);
    const inputs = tr.querySelectorAll('.input-inline');
    const payload = {};
    inputs.forEach(input => {
      const campo = input.dataset.field;
      payload[campo] = input.value;
    });
    fetch(`/requerimentos/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(res => {
      if (!res.ok) throw new Error('Erro ao atualizar');
      return res.json();
    })
    .then(() => {
      alert('Requerimento atualizado!');
      carregarSelecao().then(() => criarMarcadores());
    })
    .catch(err => {
      alert('Erro: ' + err.message);
    });
  }
});

// Gerar OS apenas para selecionados
document.getElementById('btn-gerar-os').addEventListener('click', async function() {
  if (!requerimentosSelecionados.length) {
    alert('Selecione pelo menos um requerimento!');
    return;
  }
  try {
    // Gera um número único para a OS
    const numeroOS = `OS-${Date.now()}`;
    const response = await fetch('/ordens_servico', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        requerimento_ids: requerimentosSelecionados.map(r => r.id),
        numero: numeroOS,
        responsavel: 'Equipe',
        observacao: ''
      })
    });
    if (!response.ok) throw new Error('Erro ao gerar OS');
    alert('Ordem de serviço gerada com sucesso!');
    requerimentosSelecionados = [];
    renderTabelaRequerimentos();
    renderTabelaSelecionados();
    criarMarcadores();
    carregarSelecao().then(() => criarMarcadores());
  } catch (error) {
    console.error('Erro ao gerar OS:', error);
    alert('Erro ao gerar ordem de serviço!');
  }
});

// Mapa
function inicializarMapa() {
  map = new maplibregl.Map({
    container: 'map',
    style: {
      version: 8,
      sources: {
        'satellite': {
          type: 'raster',
          tiles: [
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
          ],
          tileSize: 256,
          attribution: '© Esri'
        }
      },
      layers: [{
        id: 'satellite-layer',
        type: 'raster',
        source: 'satellite',
        minzoom: 0,
        maxzoom: 19
      }]
    },
    center: [-47.7319, -21.3381],
    zoom: 13
  });
  map.addControl(new maplibregl.NavigationControl());
  
  map.on('load', function () {
      map.addSource('perimetros', {
          type: 'geojson',
          data: 'static/files/cravinhos.geojson'
      });

      map.addLayer({
          id: 'perimetros-fill',
          type: 'fill',
          source: 'perimetros',
          paint: {
              'fill-color': '#0080ff',
              'fill-opacity': 0
          }
      });

      map.addLayer({
          id: 'perimetros-borda',
          type: 'line',
          source: 'perimetros',
          paint: {
              'line-color': '#0050a0',
              'line-width': 2
          }
      });
  });
}

function criarMarcadores() {
  // Remove marcadores antigos, se existirem
  Object.values(marcadoresMapa).forEach(marker => marker.remove());
  marcadoresMapa = {};

  // Usar filteredRequerimentos em vez de requerimentosDisponiveis
  filteredRequerimentos.forEach(r => {
    if (r.arvore_latitude && r.arvore_longitude) {
      const selecionado = requerimentosSelecionados.some(sel => sel.id == r.id);
      const marker = new maplibregl.Marker({ element: criarMarcadorCor((r.prioridade || '').toLowerCase(), selecionado) })
        .setLngLat([parseFloat(r.arvore_longitude), parseFloat(r.arvore_latitude)])
        .setPopup(new maplibregl.Popup().setHTML(`
          <strong>${r.tipo || 'Tipo não informado'}</strong><br>
          ${r.arvore_especie || 'Espécie não informada'}<br>
          Endereço: ${r.arvore_endereco || 'Não cadastrado'}<br>
          Bairro: ${r.arvore_bairro || 'Não cadastrado'}<br>
          Requerimento: ${r.numero}<br>
          ${r.data_abertura ? diasDesdeAbertura(r.data_abertura) : '-'} dias pendentes<br>
          Motivo: ${r.motivo || 'Não informado'}<br>
          Requerente: ${r.requerente_nome || 'Não informado'}<br>
          Telefone: ${r.requerente_telefone || 'Não informado'}<br>
          Data de Abertura: ${r.data_abertura ? new Date(r.data_abertura).toLocaleDateString() : 'Não informada'}<br>
          Prioridade: ${r.prioridade || ''}
        `))
        .addTo(map);
      marcadoresMapa[r.id] = marker;
    }
  });
}

function criarMarcadorCor(prioridade, selecionado = false) {
  const el = document.createElement('div');
  el.style.width = selecionado ? '26px' : '18px';
  el.style.height = selecionado ? '26px' : '18px';
  el.style.borderRadius = '50%';
  el.style.border = selecionado ? '4px solid #2196f3' : '2px solid #fff';
  el.style.boxShadow = '0 0 4px #0004';
  el.style.background = selecionado ? '#2196f3' :
    (prioridade === 'urgente' ? 'red' : prioridade === 'alta' ? 'yellow' : 'green');
  return el;
}

function diasDesdeAbertura(dataAbertura) {
  if (!dataAbertura) return '';
  const dtAbertura = new Date(dataAbertura);
  const hoje = new Date();
  dtAbertura.setHours(0,0,0,0);
  hoje.setHours(0,0,0,0);
  const diffMs = hoje - dtAbertura;
  const diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  return diffDias;
}

// Inicialização correta
window.onload = () => {
  inicializarMapa();
  carregarSelecao().then(() => {
    criarMarcadores();
  });
};
