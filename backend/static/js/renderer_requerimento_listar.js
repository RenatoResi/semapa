let requerimentosSelecionados = [];
let filteredRequerimentos = [];
let paginaReq = 1;
const porPagina = 5;
let marcadoresMapa = {};

// Carrega todos os requerimentos e inicializa filtrados
async function carregarSelecao() {
  try {
    const res = await fetch('http://localhost:5000/requerimentos/todos');
    if (!res.ok) throw new Error(`Erro HTTP! Status: ${res.status}`);
    
    requerimentosSelecionados = await res.json();
    filteredRequerimentos = [...requerimentosSelecionados];
    
    paginaReq = 1;
    renderTabelaRequerimentos();
    atualizarPaginacaoReq();
    
    carregarMapa(); // Agora usa os dados já carregados
    
  } catch (error) {
    console.error('Erro ao carregar requerimentos:', error);
    document.getElementById('resposta').innerText = `Erro: ${error.message}`;
  }
}

// Renderiza a tabela paginada
function renderTabelaRequerimentos() {
  const tbody = document.querySelector('#requerimentos-lista tbody');
  if (!tbody) return;

  tbody.innerHTML = '';
  const inicio = (paginaReq - 1) * porPagina;
  const fim = inicio + porPagina;
  
  filteredRequerimentos.slice(inicio, fim).forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="checkbox" class="select-row" value="${r.id}"></td>
      <td>${r.numero}</td>
      <td>${r.tipo}</td>
      <td>${r.motivo}</td>
      <td>${r.prioridade}</td>
      <td>${r.data_abertura ? new Date(r.data_abertura).toLocaleDateString() : ''}</td>
      <td>${r.requerente_nome || ''}</td>
      <td>${r.arvore_endereco || ''}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Atualiza os controles de paginação
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

// Filtro em todos os registros
document.getElementById('filtro-requerimento').addEventListener('input', function(e) {
  const termo = e.target.value.toLowerCase();
  
  filteredRequerimentos = requerimentosSelecionados.filter(r => {
    return (
      (r.numero?.toLowerCase() || '').includes(termo) ||
      (r.tipo?.toLowerCase() || '').includes(termo) ||
      (r.motivo?.toLowerCase() || '').includes(termo) ||
      (r.prioridade?.toLowerCase() || '').includes(termo) ||
      (r.requerente_nome?.toLowerCase() || '').includes(termo) ||
      (r.arvore_endereco?.toLowerCase() || '').includes(termo)
    );
  });
  
  paginaReq = 1;
  renderTabelaRequerimentos();
  atualizarPaginacaoReq();
});

// Seleção múltipla
document.getElementById('select-all').addEventListener('change', function() {
  document.querySelectorAll('.select-row').forEach(cb => cb.checked = this.checked);
});

// Geração de OS
document.getElementById('btn-gerar-os').addEventListener('click', async function() {
  const selecionados = Array.from(document.querySelectorAll('.select-row:checked'))
                          .map(cb => cb.value);
  
  if (!selecionados.length) {
    alert('Selecione pelo menos um requerimento!');
    return;
  }

  try {
    for (const reqId of selecionados) {
      await fetch('http://localhost:5000/ordens_servico', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          requerimento_id: reqId,
          numero: `OS-${reqId}-${Date.now()}`,
          responsavel: 'Equipe',
          observacao: ''
        })
      });
    }
    alert('Ordens de serviço geradas com sucesso!');
    carregarSelecao(); // Recarrega os dados
  } catch (error) {
    console.error('Erro ao gerar OS:', error);
    alert('Erro ao gerar ordens de serviço!');
  }
});

// Cria um marcador de cor para o mapa
function criarMarcadorCor(prioridade, destacado = false) {
  const el = document.createElement('div');
  el.style.width = destacado ? '26px' : '18px';
  el.style.height = destacado ? '26px' : '18px';
  el.style.borderRadius = '50%';
  el.style.border = destacado ? '4px solid #2196f3' : '2px solid #fff';
  el.style.boxShadow = '0 0 4px #0004';
  if (prioridade === 'urgente') {
    el.style.background = 'red';
  } else if (prioridade === 'alta') {
    el.style.background = 'yellow';
  } else {
    el.style.background = 'green';
  }
  return el;
}

// Função para atualizar destaque (mantida global)
function atualizarDestaqueMapa() {
  document.querySelectorAll('.select-row').forEach(cb => {
    const reqId = parseInt(cb.value);
    const marker = marcadoresMapa[reqId];
    if (marker) {
      const prioridade = requerimentosSelecionados.find(r => r.id === reqId)?.prioridade?.toLowerCase() || '';
      marker.setElement(criarMarcadorCor(prioridade, cb.checked));
    }
  });
}

// Event listener para checkboxes (registrado uma única vez)
document.addEventListener('change', function(e) {
  if (e.target.classList.contains('select-row')) {
    atualizarDestaqueMapa();
  }
});

// Calcula os dias desde a abertura do requerimento
function diasDesdeAbertura(dataAbertura) {
  if (!dataAbertura) return '';
  const dtAbertura = new Date(dataAbertura);
  const hoje = new Date();
  // Zera as horas para comparar só a data
  dtAbertura.setHours(0,0,0,0);
  hoje.setHours(0,0,0,0);
  const diffMs = hoje - dtAbertura;
  const diffDias = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  return diffDias;
}

// Mapa
async function carregarMapa() {
  try {
    const map = new maplibregl.Map({
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

    // Resetar marcadores ao recarregar
    marcadoresMapa = {};

    requerimentosSelecionados.forEach(r => {
        if (r.arvore_latitude && r.arvore_longitude) {
            const marker = new maplibregl.Marker({ element: criarMarcadorCor((r.prioridade || '').toLowerCase()) })
            .setLngLat([parseFloat(r.arvore_longitude), parseFloat(r.arvore_latitude)])
            .setPopup(new maplibregl.Popup().setHTML(`
                <strong>${r.tipo || 'Tipo não informado'}</strong><br>
                ${r.arvore_especie || 'Espécie não informada'}<br>
                Endereço: ${r.arvore_endereco || 'Não cadastrado'}<br>
                Requerimento: ${r.numero}<br>
                ${r.data_abertura ? diasDesdeAbertura(r.data_abertura) : '-'} dias pendentes<br>
                Motivo: ${r.motivo || 'Não informado'}<br>
                Requerente: ${r.requerente_nome || 'Não informado'}<br>
                Data de Abertura: ${r.data_abertura ? new Date(r.data_abertura).toLocaleDateString() : 'Não informada'}<br>
                Prioridade: ${r.prioridade || ''}
            `))
            .addTo(map);
            marcadoresMapa[r.id] = marker;
        }
    });

    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('select-row')) {
            atualizarDestaqueMapa();
        }
    });

    function atualizarDestaqueMapa() {
        document.querySelectorAll('.select-row').forEach(cb => {
            const reqId = parseInt(cb.value);
            const marker = marcadoresMapa[reqId];
            if (marker) {
            // Troca o elemento do marcador conforme o checkbox
            marker.setElement(criarMarcadorCor(
                (requerimentosSelecionados.find(r => r.id === reqId)?.prioridade || '').toLowerCase(),
                cb.checked
            ));
            }
        });
    }

  } catch (error) {
    console.error('Erro ao carregar mapa:', error);
  }
}

// Inicialização
window.onload = () => {
  carregarSelecao();
};
