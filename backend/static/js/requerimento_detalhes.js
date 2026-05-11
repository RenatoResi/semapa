(function(){
  const meta = document.getElementById('requerimento-meta');
  const REQ_ID = meta ? parseInt(meta.dataset.reqId, 10) : null;
  const REQ_REQUERENTE_ID = meta && meta.dataset.requerenteId ? parseInt(meta.dataset.requerenteId, 10) : null;
  const ARVORE_ID = meta && meta.dataset.arvoreId ? parseInt(meta.dataset.arvoreId, 10) : null;

  function openFotoModal(url) {
    document.getElementById('foto-modal-img').src = url;
    const m = document.getElementById('foto-modal');
    m.style.display = 'block';
  }
  function closeFotoModal() {
    const m = document.getElementById('foto-modal');
    m.style.display = 'none';
    document.getElementById('foto-modal-img').src = '';
  }
  // Expor globalmente para o botão inline no template
  window.openFotoModal = openFotoModal;
  window.closeFotoModal = closeFotoModal;

  // Inicializa minimapa baseado nas coordenadas (tentando vários campos possíveis)
  function initMiniMap(){
    const latVal = document.getElementById('input-lat').value;
    const lonVal = document.getElementById('input-lon').value;
    const lat = latVal ? parseFloat(latVal) : null;
    const lon = lonVal ? parseFloat(lonVal) : null;
    if (lat && lon && typeof maplibregl !== 'undefined') {
      const map = new maplibregl.Map({
        container: 'mini-map',
        style: {
          version: 8,
          sources: { 'sat': { type: 'raster', tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'], tileSize: 256 } },
          layers: [{ id:'sat', type:'raster', source:'sat' }]
        },
        center: [lon, lat],
        zoom: 16
      });
      new maplibregl.Marker().setLngLat([lon, lat]).addTo(map);
    } else {
      const mini = document.getElementById('mini-map');
      if (mini) mini.innerHTML = '<div style="padding:20px;">Localização não informada</div>';
    }
  }

  // Carregar fotos como blobs (endpoint servidor: /foto/<id>)
  async function carregarFotos() {
    const thumbs = document.querySelectorAll('.foto-thumb[data-photo-id]');
    thumbs.forEach(async el => {
      const id = el.dataset.photoId;
      try {
        const res = await fetch(`/foto/${id}`);
        if (!res.ok) return;
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        el.style.backgroundImage = `url(${url})`;
        el.style.backgroundSize = 'cover';
        el.style.backgroundPosition = 'center';
        el.addEventListener('click', () => openFotoModal(url));
      } catch (err) {
        // ignore
      }
    });
  }

  async function salvarRequerimento(){
    const payload = {
      numero: document.getElementById('input-numero').value,
      tipo: document.getElementById('input-tipo').value,
      motivo: document.getElementById('input-motivo').value,
      prioridade: document.getElementById('input-prioridade').value,
      status: document.getElementById('input-status').value,
      observacao: document.getElementById('input-observacao').value,
      data_abertura: document.getElementById('input-data-abertura').value || null,
      data_conclusao: document.getElementById('input-data-conclusao').value || null
    };
    try {
      const res = await fetch(`/requerimentos/${REQ_ID}`, {
        method: 'PUT',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const txt = await res.text();
        alert('Erro ao salvar: ' + txt);
        return;
      }
      alert('Alterações salvas com sucesso!');
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert('Erro ao salvar alterações.');
    }
  }

  async function salvarRequerente(){
    if (!REQ_REQUERENTE_ID) {
      return alert('Requerente não vinculado a este requerimento.');
    }
    const payload = {
      nome: document.getElementById('input-requerente-nome').value,
      telefone: document.getElementById('input-requerente-telefone').value,
      observacao: document.getElementById('input-requerente-observacoes').value
    };
    try {
      const res = await fetch(`/requerentes/${REQ_REQUERENTE_ID}`, {
        method: 'PUT',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const txt = await res.text();
        alert('Erro ao salvar requerente: ' + txt);
        return;
      }
      alert('Requerente atualizado com sucesso!');
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert('Erro ao salvar requerente.');
    }
  }

  async function salvarArvore(){
    if (!ARVORE_ID) {
      return alert('Árvore não vinculada a este requerimento.');
    }
    const payload = {
      endereco: document.getElementById('input-arvore-endereco').value,
      bairro: document.getElementById('input-arvore-bairro').value,
      latitude: document.getElementById('input-lat').value || null,
      longitude: document.getElementById('input-lon').value || null
    };
    try {
      const res = await fetch(`/arvores/${ARVORE_ID}`, {
        method: 'PUT',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const txt = await res.text();
        alert('Erro ao salvar árvore: ' + txt);
        return;
      }
      alert('Árvore atualizada com sucesso!');
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert('Erro ao salvar árvore.');
    }
  }

  function criarVistoria() {
    if (!REQ_ID) return alert('ID do requerimento não disponível');
    // Redireciona para o formulário de nova vistoria, passando o requerimento
    window.location.href = `/vistorias/nova?requerimento_id=${REQ_ID}`;
  }

  function agendarTarefa() {
    const metaReqNumero = meta ? meta.dataset.reqNumero : null;
    if (!metaReqNumero) {
      // fallback: redireciona para página de nova tarefa sem pré-preenchimento
      return window.location.href = '/tarefas/nova';
    }
    // Redireciona para o formulário de nova tarefa com o número do requerimento
    window.location.href = `/tarefas/nova?requerimento_numero=${encodeURIComponent(metaReqNumero)}`;
  }

  document.addEventListener('DOMContentLoaded', () => {
    initMiniMap();
    carregarFotos();

    const btnSalvar = document.getElementById('btn-salvar-requerimento');
    if (btnSalvar) btnSalvar.addEventListener('click', salvarRequerimento);

    const btnSalvarReq = document.getElementById('btn-salvar-requerente');
    if (btnSalvarReq) btnSalvarReq.addEventListener('click', salvarRequerente);

    const btnSalvarArv = document.getElementById('btn-salvar-arvore');
    if (btnSalvarArv) btnSalvarArv.addEventListener('click', salvarArvore);

    const btnVist = document.getElementById('btn-vistoriar');
    if (btnVist) btnVist.addEventListener('click', criarVistoria);

    const btnAg = document.getElementById('btn-agendar');
    if (btnAg) btnAg.addEventListener('click', agendarTarefa);
  });

})();
