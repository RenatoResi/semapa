// Utilitário: exibe JSON de resposta
function exibirResposta(result) {
    document.getElementById('resposta').innerText = JSON.stringify(result, null, 2);
}

// Formatar data brasileira
function formatarData(dataISO) {
    if (!dataISO) return '';
    const data = new Date(dataISO);
    return `${data.getDate().toString().padStart(2, '0')}/${(data.getMonth() + 1).toString().padStart(2, '0')}/${data.getFullYear()}`;
}

// ----------- CADASTRO DE REQUERENTE -----------
const formRequerente = document.getElementById('form-requerente');
formRequerente?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(formRequerente));
    const response = await fetch('/requerente', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    exibirResposta(await response.json());
    listarRequerentes();
    formRequerente.reset();
});

// ----------- CADASTRO DE ÁRVORE -----------
const formArvore = document.getElementById('form-arvore');
formArvore?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(formArvore));
    const response = await fetch('/arvores', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    exibirResposta(await response.json());
    listarArvores();
    formArvore.reset();
    carregarArvoresNoMapa();
});

// ----------- LISTAGEM DE REQUERENTES -----------
let currentPageReq = 1;
const perPageReq = 5;

async function listarRequerentes(page = 1) {
    try {
        const res = await fetch(`/requerentes?page=${page}&per_page=${perPageReq}`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        const requerentes = Array.isArray(data) ? data : (data.requerentes || []);
        const total = data.total ?? requerentes.length;
        const tbody = document.querySelector('#requerentes-lista tbody');
        if (tbody) {
            tbody.innerHTML = '';
            requerentes.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${r.id}</td><td>${r.nome}</td><td>${r.telefone ?? ""}</td><td>${r.observacao ?? ""}</td>`;
                tbody.appendChild(tr);
            });
        }
        currentPageReq = page;
        atualizarControlesPaginaReq(total);
    } catch (error) {
        console.error('Erro ao listar requerentes:', error);
        document.getElementById('resposta').innerText = 'Erro ao carregar requerentes: ' + error.message;
    }
}

function atualizarControlesPaginaReq(total) {
    const paginacao = document.getElementById('paginacao-requerentes');
    if (!paginacao) return;
    paginacao.innerHTML = `
        <button onclick="listarRequerentes(${currentPageReq - 1})" ${currentPageReq === 1 ? 'disabled' : ''}>Anterior</button>
        <span>Página ${currentPageReq} (Total: ${total})</span>
        <button onclick="listarRequerentes(${currentPageReq + 1})" ${currentPageReq * perPageReq >= total ? 'disabled' : ''}>Próxima</button>
    `;
}

// ----------- LISTAGEM DE ÁRVORES -----------
let currentPage = 1;
const perPage = 5;

async function listarArvores(page = 1) {
    try {
        const res = await fetch(`/arvores?page=${page}&per_page=${perPage}`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        const arvores = Array.isArray(data) ? data : (data.arvores || []);
        const total = data.total ?? arvores.length;
        const tbody = document.querySelector('#arvores-lista tbody');
        if (tbody) {
            tbody.innerHTML = '';
            arvores.forEach(a => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${a.id}</td><td>${a.especie ?? ""}</td><td>${a.endereco ?? ""}</td><td>${a.bairro ?? ""}</td>
                    <td><button onclick="gerarKMLArvore(${a.id})" class="btn-kml">Gerar KML</button></td>`;
                tbody.appendChild(tr);
            });
        }
        currentPage = page;
        atualizarControlesPagina(total);
    } catch (error) {
        console.error('Erro ao listar árvores:', error);
        document.getElementById('resposta').innerText = 'Erro ao carregar árvores: ' + error.message;
    }
}

function atualizarControlesPagina(total) {
    const paginacao = document.getElementById('paginacao-arvores');
    if (!paginacao) return;
    paginacao.innerHTML = `
        <button onclick="listarArvores(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Anterior</button>
        <span>Página ${currentPage} (Total: ${total})</span>
        <button onclick="listarArvores(${currentPage + 1})" ${currentPage * perPage >= total ? 'disabled' : ''}>Próxima</button>
    `;
}

// ----------- KML -----------

async function gerarKML() {
    try {
        const response = await fetch('/gerar_kml');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const blob = await response.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'arvores_semapa.kml';
        link.click();
    } catch (error) {
        console.error('Erro ao gerar KML:', error);
        document.getElementById('resposta').innerText = 'Erro ao gerar KML: ' + error.message;
    }
}

async function gerarKMLArvore(arvoreId) {
    try {
        const response = await fetch(`/gerar_kml/${arvoreId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const blob = await response.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `arvore_${arvoreId}.kml`;
        link.click();
    } catch (error) {
        console.error('Erro ao gerar KML da árvore:', error);
        document.getElementById('resposta').innerText = 'Erro ao gerar KML da árvore: ' + error.message;
    }
}

// ----------- MAPA -----------
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
let marker = null;
map.on('click', function(e) {
    const { lng, lat } = e.lngLat;
    if (marker) marker.remove();
    marker = new maplibregl.Marker().setLngLat([lng, lat]).addTo(map);
    const latField = document.querySelector('input[name="latitude"]');
    const lngField = document.querySelector('input[name="longitude"]');
    if (latField) latField.value = lat.toFixed(6);
    if (lngField) lngField.value = lng.toFixed(6);
});

map.on('load', function () {
    map.addSource('perimetros', { type: 'geojson', data: 'static/files/cravinhos.geojson'});
    map.addLayer({ id: 'perimetros-fill', type: 'fill', source: 'perimetros',
        paint: { 'fill-color': '#0080ff', 'fill-opacity': 0 }});
    map.addLayer({ id: 'perimetros-borda', type: 'line', source: 'perimetros',
        paint: { 'line-color': '#0050a0', 'line-width': 2 }});
});

async function carregarArvoresNoMapa() {
    try {
        const res = await fetch('/arvores'); // Usar sempre o endpoint padrão RESTful
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const arvores = await res.json();
        arvores.forEach(a => {
            new maplibregl.Marker({ color: 'green' })
                .setLngLat([parseFloat(a.longitude), parseFloat(a.latitude)])
                .setPopup(new maplibregl.Popup().setHTML(`<strong>${a.especie}</strong><br>${a.endereco}`))
                .addTo(map);
        });
    } catch (error) {
        console.error('Erro ao carregar árvores no mapa:', error);
    }
}

window.onload = () => {
    listarRequerentes(1);
    listarArvores(1);
    carregarArvoresNoMapa();
};
