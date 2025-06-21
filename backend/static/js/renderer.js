// Função utilitária
function exibirResposta(result) {
    document.getElementById('resposta').innerText = JSON.stringify(result, null, 2);
}

// Função para formatar data no padrão brasileiro
function formatarData(dataISO) {
    if (!dataISO) return '';
    const data = new Date(dataISO);
    const dia = String(data.getDate()).padStart(2, '0');
    const mes = String(data.getMonth() + 1).padStart(2, '0');
    const ano = data.getFullYear();
    return `${dia}/${mes}/${ano}`;
}

// Cadastrar Requerente
formRequerente = document.getElementById('form-requerente')
formRequerente?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(formRequerente));
    const response = await fetch('/requerente', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    exibirResposta(await response.json());
    formRequerente.reset();
    listarRequerentes();
    document.getElementById('cadastro-arvore').scrollIntoView({ behavior: 'smooth' });
});

// Cadastrar Árvore
formArvore = document.getElementById('form-arvore')
formArvore?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(formArvore));
    const response = await fetch('/arvores', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    exibirResposta(await response.json());
    formArvore.reset();
    listarArvores();
    carregarArvoresNoMapa();
    window.location.href = 'requerimento';
});


// Listagens
let currentPageReq = 1;
const perPageReq = 5;

async function listarRequerentes(page = 1) {
    try {
        const res = await fetch(`/requerentes?page=${page}&per_page=${perPageReq}`);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        const data = await res.json();
        const requerentes = data.requerentes || data;

        const tbody = document.querySelector('#requerentes-lista tbody');
        if (tbody) {
            tbody.innerHTML = '';
            requerentes.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${r.id}</td><td>${r.nome}</td><td>${r.telefone}</td><td>${r.observacao}</td>`;
                tbody.appendChild(tr);
            });
        }

        currentPageReq = page;
        atualizarControlesPaginaReq(data.total);

    } catch (error) {
        console.error('Erro ao listar requerentes:', error);
        document.getElementById('resposta').innerText = 'Erro ao carregar requerentes: ' + error.message;
    }
}

function atualizarControlesPaginaReq(total) {
    const paginacao = document.getElementById('paginacao-requerentes');
    if (!paginacao) return;

    paginacao.innerHTML = `
        <button onclick="listarRequerentes(${currentPageReq - 1})" ${currentPageReq === 1 ? 'disabled' : ''}>
            Anterior
        </button>
        <span>Página ${currentPageReq} (Total: ${total})</span>
        <button onclick="listarRequerentes(${currentPageReq + 1})" ${currentPageReq * perPageReq >= total ? 'disabled' : ''}>
            Próxima
        </button>
    `;
}

// KML - Geral
async function gerarKML() {
    try {
        const response = await fetch('/gerar_kml');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
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

// KML - Individual por árvore
async function gerarKMLArvore(arvoreId) {
    try {
        const response = await fetch(`/gerar_kml/${arvoreId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
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

// Mapa
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
    map.addSource('perimetros', {
        type: 'geojson',
        data: 'static/files/cravinhos.geojson' // Caminho para seu arquivo
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

async function carregarArvoresNoMapa() {
    try {
        const res = await fetch('/arvores/todos'); // ou um valor alto para pegar todas
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        const data = await res.json();
        const arvores = data.arvores || data; // compatível com ambos formatos

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

let currentPage = 1;
const perPage = 5;

async function listarArvores(page = 1) {
    try {
        const res = await fetch(`/arvores?page=${page}&per_page=${perPage}`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        
        const tbody = document.querySelector('#arvores-lista tbody');
        tbody.innerHTML = '';
        data.arvores.forEach(a => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${a.id}</td>
                <td>${a.especie}</td>
                <td>${a.endereco}</td>
                <td>${a.bairro}</td>
                <td><button onclick="gerarKMLArvore(${a.id})" class="btn-kml">Gerar KML</button></td>
            `;
            tbody.appendChild(tr);
        });

        currentPage = page;
        atualizarControlesPagina(data.total);
        
    } catch (error) {
        console.error('Erro ao listar árvores:', error);
        document.getElementById('resposta').innerText = 'Erro ao carregar árvores: ' + error.message;
    }
}

function atualizarControlesPagina(total) {
    const paginacao = document.getElementById('paginacao-arvores');
    if (!paginacao) return;

    paginacao.innerHTML = `
        <button onclick="listarArvores(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
            Anterior
        </button>
        <span>Página ${currentPage} (Total: ${total})</span>
        <button onclick="listarArvores(${currentPage + 1})" ${currentPage * perPage >= total ? 'disabled' : ''}>
            Próxima
        </button>
    `;
}

function formatarTelefone(campo) {
    let valor = campo.value.replace(/\D/g, ''); // Remove caracteres não numéricos
    let formato = '';

    if (valor.length <= 10) { // Formato para telefone fixo (XX XXXX-XXXX)
        formato = valor.replace(/^(\d{2})(\d{4})(\d{0,4})$/, '($1) $2-$3');
    } else { // Formato para celular (XX XXXXX-XXXX)
        formato = valor.replace(/^(\d{2})(\d{5})(\d{0,4})$/, '($1) $2-$3');
    }

    campo.value = formato;
}

// Verificar se o requerente já existe
document.addEventListener('DOMContentLoaded', function() {
    const nomeInput = document.getElementById('nome');
    const erroDiv = document.getElementById('nome-erro');

    nomeInput.addEventListener('blur', function() {
        const nome = nomeInput.value.trim();
        if (nome.length < 3) {
            nomeInput.classList.remove('erro');
            erroDiv.style.display = 'none';
            return;
        }
        fetch(`/api/requerente/existe?nome=${encodeURIComponent(nome)}`)
            .then(response => response.json())
            .then(data => {
                if (data.exists) {
                    nomeInput.classList.add('erro');
                    erroDiv.textContent = `Esse requerente já existe (id=${data.id})`;
                    erroDiv.style.display = 'block';
                } else {
                    nomeInput.classList.remove('erro');
                    erroDiv.style.display = 'none';
                }
            })
            .catch(() => {
                nomeInput.classList.remove('erro');
                erroDiv.style.display = 'none';
            });
    });
});

function setupAutocomplete(inputId, endpoint) {
    const input = document.getElementById(inputId);
    let sugestoesDiv;

    input.addEventListener('input', async function() {
        const valor = input.value.trim();
        if (valor.length < 2) {
            removeSugestoes();
            return;
        }
        const res = await fetch(`${endpoint}?query=${encodeURIComponent(valor)}`);
        const sugestoes = await res.json();

        removeSugestoes();
        if (sugestoes.length === 0) return;

        sugestoesDiv = document.createElement('div');
        sugestoesDiv.className = 'autocomplete-sugestoes';
        sugestoes.forEach(sugestao => {
            const div = document.createElement('div');
            div.textContent = sugestao;
            div.onmousedown = () => {
                input.value = sugestao;
                removeSugestoes();
            };
            sugestoesDiv.appendChild(div);
        });

        input.parentNode.appendChild(sugestoesDiv);
    });

    input.addEventListener('blur', function() {
        setTimeout(removeSugestoes, 100);
    });

    function removeSugestoes() {
        if (sugestoesDiv) {
            sugestoesDiv.remove();
            sugestoesDiv = null;
        }
    }
}

// Ative o autocomplete nos campos
setupAutocomplete('bairro', '/api/sugestoes/bairros');
setupAutocomplete('endereco', '/api/sugestoes/enderecos');



window.onload = () => {
    listarRequerentes(1);
    listarArvores(1);
    carregarArvoresNoMapa();
};
