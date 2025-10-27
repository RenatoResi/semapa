let requerimentosDisponiveis = [];
let requerimentosSelecionados = [];
let filteredRequerimentos = [];
let paginaReq = 1;
const porPagina = 5;
let map;
let marcadoresMapa = {};
let modoVisualizacao = 'nao-concluidos'; // 'nao-concluidos' ou 'concluidos'
let usuarioMarker = null;

// Carrega todos os requerimentos e inicializa filtrados
async function carregarSelecao() {
  try {
    const endpoint = modoVisualizacao === 'concluidos' ? '/requerimentos/concluidos' : '/requerimentos/todos';
    const res = await fetch(endpoint);
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
    document.getElementById('resposta') && (document.getElementById('resposta').innerText = `Erro: ${error.message}`);
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
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.numero}</td>
      <td>${r.tipo}</td>
      <td>${r.motivo}</td>
      <td>${r.data_abertura ? formatDateDDMMYYYY(r.data_abertura) : ''}</td>
      <td>${r.requerente_nome || ''}</td>
      <td>${gerarLinkGoogleMaps(r)}</td>
      <td>${r.arvore_bairro || ''}</td>
      <td>
        <button class="btn-selecionar" data-id="${r.id}">Selecionar</button>
        <button class="btn-whatsapp" data-id="${r.id}">Enviar WhatsApp</button>
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
      <td>${r.data_abertura ? formatDateDDMMYYYY(r.data_abertura) : ''}</td>
      <td>${r.requerente_nome || ''}</td>
      <td>${gerarLinkGoogleMaps(r)}</td>
      <td>${r.arvore_bairro || ''}</td>
      <td>
        <button class="btn-remover-selecionado" data-id="${r.id}">Remover</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Função para alternar entre modos de visualização
function alternarModoVisualizacao() {
  const switchElement = document.getElementById('switch-concluidos');
  const tituloSecao = document.getElementById('titulo-secao');
  const labelSwitch = document.getElementById('label-switch');
  const secaoSelecionados = document.getElementById('secao-selecionados');
  const colunaDataConclusao = document.getElementById('coluna-data-conclusao');
  const colunaAcoes = document.getElementById('coluna-acoes');
  
  if (switchElement.checked) {
    modoVisualizacao = 'concluidos';
    tituloSecao.textContent = 'Listagem de Requerimentos Concluídos';
    labelSwitch.textContent = 'Mostrar Requerimentos Concluídos';
    secaoSelecionados.style.display = 'none'; // Esconde tabela de selecionados
    colunaDataConclusao.style.display = 'table-cell'; // Mostra coluna data conclusão
    colunaAcoes.style.display = 'none'; // Esconde coluna ações
  } else {
    modoVisualizacao = 'nao-concluidos';
    tituloSecao.textContent = 'Listagem de Requerimentos Em Aberto';
    labelSwitch.textContent = 'Mostrar Requerimentos Concluídos';
    secaoSelecionados.style.display = 'block'; // Mostra tabela de selecionados
    colunaDataConclusao.style.display = 'none'; // Esconde coluna data conclusão
    colunaAcoes.style.display = 'table-cell'; // Mostra coluna ações
  }
  
  // Limpa seleções e recarrega dados
  requerimentosSelecionados = [];
  carregarSelecao();
}

// Event listener para o switch
document.addEventListener('DOMContentLoaded', function() {
  const switchElement = document.getElementById('switch-concluidos');
  if (switchElement) {
    switchElement.addEventListener('change', alternarModoVisualizacao);
  }
});

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
      (r.arvore_bairro?.toLowerCase() || '').includes(termo) ||
      (r.status?.toLowerCase() || '').includes(termo)
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
  const endpoint = modoVisualizacao === 'concluidos' ? '/requerimentos/concluidos' : '/requerimentos';
  const res = await fetch(`${endpoint}?order_by=${campo}&direction=${direcao}`);
  const data = await res.json();
  requerimentosDisponiveis = modoVisualizacao === 'concluidos' ? data : data.requerimentos;
  filteredRequerimentos = [...requerimentosDisponiveis];
  paginaReq = 1;
  renderTabelaRequerimentos();
  atualizarPaginacaoReq();
  criarMarcadores();  // Atualizar o mapa após ordenação
}

// Selecionar e remover requerimento
document.addEventListener('click', function(e) {
  // Selecionar (apenas para não concluídos) - botão da tabela
  if (e.target.classList.contains('btn-selecionar') && modoVisualizacao === 'nao-concluidos') {
    const id = parseInt(e.target.dataset.id);
    const req = requerimentosDisponiveis.find(r => r.id === id);
    if (req && !requerimentosSelecionados.some(r => r.id === id)) {
      requerimentosSelecionados.push(req);
      renderTabelaRequerimentos();
      renderTabelaSelecionados();
      criarMarcadores();
    }
  }

  // Selecionar pelo botão no popup do mapa
  if (e.target.classList.contains('btn-selecionar-mapa') && modoVisualizacao === 'nao-concluidos') {
    const id = parseInt(e.target.dataset.id);
    const req = requerimentosDisponiveis.find(r => r.id === id);
    if (req && !requerimentosSelecionados.some(r => r.id === id)) {
      requerimentosSelecionados.push(req);
      renderTabelaRequerimentos();
      renderTabelaSelecionados();
      criarMarcadores();
    }
    // fechar popup do marcador selecionado
    if (map && marcadoresMapa[id] && marcadoresMapa[id].getPopup) {
      marcadoresMapa[id].getPopup().remove();
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
  // Editar inline (apenas para não concluídos)
  if (e.target.classList.contains('btn-editar-inline') && modoVisualizacao === 'nao-concluidos') {
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
      <td>${r.status || ''}</td>
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

  // Enviar WhatsApp (tabela)
  if (e.target.classList.contains('btn-whatsapp')) {
    const id = parseInt(e.target.dataset.id);
    const req = requerimentosDisponiveis.find(r => r.id === id) || filteredRequerimentos.find(r => r.id === id);
    abrirWhatsAppPara(req);
  }

  // Enviar WhatsApp (botão no popup do mapa)
  if (e.target.classList.contains('btn-whatsapp-mapa')) {
    const id = parseInt(e.target.dataset.id);
    const req = requerimentosDisponiveis.find(r => r.id === id) || filteredRequerimentos.find(r => r.id === id);
    abrirWhatsAppPara(req);
  }
});

// Gerar OS apenas para selecionados (apenas para não concluídos)
document.getElementById('btn-gerar-os').addEventListener('click', async function() {
  if (modoVisualizacao === 'concluidos') return;
  
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

      map.addSource('semapa', {
        type: 'geojson',
        data: 'static/files/semapa.geojson' // ajuste o caminho conforme necessário
      });

      map.addLayer({
          id: 'semapa-sede',
          type: 'circle',
          source: 'semapa',
          paint: {
            'circle-color': '#ffffff',        // Cor de preenchimento: branco
            'circle-radius': 10,               // Raio do círculo
            'circle-stroke-color': '#000000', // Cor da borda: preto
            'circle-stroke-width': 2          // Espessura da borda
          }
      });

      map.addSource('bairros', {
        type: 'geojson',
        data: 'static/files/bairros.geojson'
      });

      map.addLayer({
          id: 'bairros-fill',
          type: 'fill',
          source: 'bairros',
          paint: {
              'fill-color': '#ffff00ff',
              'fill-opacity': 0.2
          }
      });

      map.addLayer({
          id: 'bairros-borda',
          type: 'line',
          source: 'bairros',
          paint: {
              'line-color': '#000000ff',
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

      // botão selecionar no popup (apenas para não concluídos e quando não selecionado)
      let botaoSelecionar = '';
      if (modoVisualizacao === 'nao-concluidos' && !selecionado) {
        botaoSelecionar = `<br><button class="btn-selecionar-mapa" data-id="${r.id}">Selecionar</button>`;
      }
      let botaoWhatsApp = '';
      if (r.requerente_telefone) {
        botaoWhatsApp = `<br><button class="btn-whatsapp-mapa" data-id="${r.id}">Enviar WhatsApp</button>`;
      }
      const marker = new maplibregl.Marker({ element: criarMarcadorCor((r.prioridade || '').toLowerCase(), selecionado) })
        .setLngLat([parseFloat(r.arvore_longitude), parseFloat(r.arvore_latitude)])
        .setPopup(new maplibregl.Popup().setHTML(`
          <strong>${r.tipo || 'Tipo não informado'}</strong><br>
          Motivo: ${r.motivo || 'Não informado'}<br>
          Requerimento: ${r.numero}<br>
          Data de Abertura: ${r.data_abertura ? formatDateDDMMYYYY(r.data_abertura) : 'Não informada'}<br>
          ${r.data_abertura && modoVisualizacao === 'nao-concluidos' ? diasDesdeAbertura(r.data_abertura) : '-'} ${modoVisualizacao === 'nao-concluidos' ? 'dias pendentes' : ''}<br>
          ${modoVisualizacao === 'concluidos' && r.data_conclusao ? 'Data de Conclusão: ' + formatDateDDMMYYYY(r.data_conclusao) + '<br>' : ''}
          Endereço: ${gerarLinkGoogleMaps(r)}<br>
          Bairro: ${r.arvore_bairro || 'Não cadastrado'}<br>
          Requerente: ${r.requerente_nome || 'Não informado'}<br>
          Telefone: ${r.requerente_telefone || 'Não informado'}
          ${botaoSelecionar}
          ${botaoWhatsApp}
        `))
        .addTo(map);
      marcadoresMapa[r.id] = marker;
    }
  });
}

function criarMarcadorCor(prioridade, selecionado = false) {
  const el = document.createElement('div');
  el.className = 'map-marker';

  if (selecionado) {
    el.classList.add('selected');
  } else {
    // Usa 'normal' como fallback se a prioridade não for uma das esperadas
    const priorityClass = ['urgente', 'alta', 'baixa'].includes(prioridade) ? prioridade : 'normal';
    el.classList.add(`priority-${priorityClass}`);
  }
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

// Helper para formatar telefone para WhatsApp (adiciona DDI 55 se provável Brasil)
function formatPhoneForWhatsApp(phone) {
  if (!phone) return null;
  let digits = phone.replace(/\D/g, '');
  // remover zeros à esquerda
  digits = digits.replace(/^0+/, '');
  // se parecer número local (8-11 dígitos) e não tiver DDI, assume 55
  if (!digits.startsWith('55') && (digits.length >= 8 && digits.length <= 11)) {
    digits = '55' + digits;
  }
  return digits;
}

// Helper para formatar data dd/mm/aaaa
function formatDateDDMMYYYY(dateInput) {
  if (!dateInput) return '';
  const d = new Date(dateInput);
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
}

// Helper para abrir WhatsApp com mensagem pré-preenchida
function abrirWhatsAppPara(req) {
  if (!req) return;
  const phone = formatPhoneForWhatsApp(req.requerente_telefone || '');
  if (!phone) {
    alert('Telefone do requerente não disponível.');
    return;
  }
  const nome = req.requerente_nome || '';
  const numero = req.numero || '';
  const data = req.data_abertura ? formatDateDDMMYYYY(req.data_abertura) : '';
  const endereco = req.arvore_endereco || '';
  const tipo = (req.tipo || '').toString().toLowerCase();
  const motivo = (req.motivo || '').toString().toLowerCase();
  const mensagem = `Olá ${nome}, tudo bem?\nMeu nome é Renato, sou o Engenheiro Florestal responsável pela arborização urbana da Secretaria do Meio Ambiente de Cravinhos.\nReferente ao requerimento ${numero}, de data ${data}, solicitando serviço de ${tipo} de árvore localizada na ${endereco}, pelo seguinte motivo: ${motivo}.`;
  const texto = encodeURIComponent(mensagem);
  const isMobile = /Mobi|Android/i.test(navigator.userAgent);
  const url = isMobile ? `https://wa.me/${phone}?text=${texto}` : `https://web.whatsapp.com/send?phone=${phone}&text=${texto}`;
  window.open(url, '_blank');
}

// Helper para gerar link do Google Maps (usa coordenadas se disponíveis, senão usa endereço)
function gerarLinkGoogleMaps(r) {
  const enderecoTexto = (r.arvore_endereco || '').trim();
  const bairroTexto = (r.arvore_bairro || '').trim();
  let url = '';
  if (r.arvore_latitude && r.arvore_longitude) {
    const lat = parseFloat(r.arvore_latitude);
    const lon = parseFloat(r.arvore_longitude);
    // usa coordenadas para centralizar no mapa
    url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(lat + ',' + lon)}`;
  } else if (enderecoTexto || bairroTexto) {
    // busca por texto do endereço
    const q = encodeURIComponent([enderecoTexto, bairroTexto].filter(Boolean).join(' '));
    url = `https://www.google.com/maps/search/?api=1&query=${q}`;
  } else {
    // fallback para abrir Google Maps
    url = 'https://www.google.com/maps';
  }
  const label = enderecoTexto || 'Ver no Maps';
  return `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`;
}

// Solicita posição e mostra marcador no mapa
function mostrarMinhaLocalizacao() {
  if (!map || !navigator.geolocation) {
    alert('Geolocalização não disponível neste navegador.');
    return;
  }

  navigator.geolocation.getCurrentPosition((pos) => {
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;

    // remove marcador antigo
    if (usuarioMarker) usuarioMarker.remove();

    // criar elemento do marcador (bolinha azul)
    const el = document.createElement('div');
    el.className = 'user-location-marker';

    usuarioMarker = new maplibregl.Marker({ element: el })
      .setLngLat([lon, lat])
      .addTo(map);

    // centraliza e aproxima
    map.flyTo({ center: [lon, lat], zoom: 16 });
  }, (err) => {
    alert('Não foi possível obter sua posição: ' + (err.message || err.code));
  }, {
    enableHighAccuracy: true,
    timeout: 10000,
    maximumAge: 60000
  });
}

// adiciona botão de controle ao mapa (após inicializar o mapa)
function adicionarControleMinhaLocalizacao() {
  const geoControl = {
    onAdd: function(mapInstance) {
      this._btn = document.createElement('button');
      this._btn.type = 'button';
      this._btn.title = 'Mostrar minha localização';
      this._btn.className = 'maplibregl-ctrl-icon location-btn';
      this._btn.textContent = '📍';
      this._btn.onclick = mostrarMinhaLocalizacao;

      this._container = document.createElement('div');
      this._container.className = 'maplibregl-ctrl maplibregl-ctrl-group';
      this._container.appendChild(this._btn);
      return this._container;
    },
    onRemove: function() {
      this._container.parentNode.removeChild(this._container);
      this._map = undefined;
    }
  };
  map.addControl(geoControl, 'top-right');
}

// chamar ao inicializar o mapa
// dentro de inicializarMapa(), após map.addControl(new maplibregl.NavigationControl());
/* exemplo:
  map.addControl(new maplibregl.NavigationControl());
  adicionarControleMinhaLocalizacao();
*/
// Inicialização correta
window.onload = () => {
  inicializarMapa();
  carregarSelecao().then(() => {
    criarMarcadores();
  });
};
