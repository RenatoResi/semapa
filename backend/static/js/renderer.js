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
    const response = await fetch('http://localhost:5000/requerente', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    exibirResposta(await response.json());
    formRequerente.reset();
    listarRequerentes();
});

// Cadastrar Árvore
formArvore = document.getElementById('form-arvore')
formArvore?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(formArvore));
    const response = await fetch('http://localhost:5000/arvores', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    exibirResposta(await response.json());
    formArvore.reset();
    listarArvores();
    carregarArvoresNoMapa();
});


// Listagens
async function listarRequerentes() {
    try {
        const res = await fetch('http://localhost:5000/requerentes');
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        const lista = await res.json();
        const tbody = document.querySelector('#requerentes-lista tbody');
        if (tbody) {
            tbody.innerHTML = '';
            lista.forEach(r => {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${r.id}</td><td>${r.nome}</td><td>${r.telefone}</td><td>${r.observacao}</td>`;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Erro ao listar requerentes:', error);
        document.getElementById('resposta').innerText = 'Erro ao carregar requerentes: ' + error.message;
    }
}

async function listarArvores() {
    try {
        const res = await fetch('http://localhost:5000/arvores');
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        const lista = await res.json();
        const tbody = document.querySelector('#arvores-lista tbody');
        if (tbody) {
            tbody.innerHTML = '';
            lista.forEach(a => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${a.id}</td>
                    <td>${a.especie}</td>
                    <td>${a.endereco}</td>
                    <td>${a.bairro}</td>
                    <td>${formatarData(a.data_plantio)}</td>
                    <td><button onclick="gerarKMLArvore(${a.id})" class="btn-kml">Gerar KML</button></td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error('Erro ao listar árvores:', error);
        document.getElementById('resposta').innerText = 'Erro ao carregar árvores: ' + error.message;
    }
}

// KML - Geral
async function gerarKML() {
    try {
        const response = await fetch('http://localhost:5000/gerar_kml');
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
        const response = await fetch(`http://localhost:5000/gerar_kml/${arvoreId}`);
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

async function carregarArvoresNoMapa() {
    try {
        const res = await fetch('http://localhost:5000/arvores');
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
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

// Modificar a função listarArvores
async function listarArvores() {
    try {
        const res = await fetch('http://localhost:5000/arvores');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const lista = await res.json();
        
        const tbody = document.querySelector('#arvores-lista tbody');
        tbody.innerHTML = '';
        lista.forEach(a => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${a.id}</td>
                <td>${a.especie}</td>
                <td>${a.endereco}</td>
                <td>${a.bairro}</td>
                <td>${formatarData(a.data_plantio)}</td>
                <td><button onclick="gerarKMLArvore(${a.id})" class="btn-kml">Gerar KML</button></td>
            `;
            tbody.appendChild(tr);
        });
        
    } catch (error) {
        console.error('Erro ao listar árvores:', error);
        document.getElementById('resposta').innerText = 'Erro ao carregar árvores: ' + error.message;
    }
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


window.onload = () => {
    listarRequerentes();
    listarArvores();
    carregarArvoresNoMapa();
};
