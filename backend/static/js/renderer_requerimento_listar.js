async function listarRequerimentos() {
    const res = await fetch('http://localhost:5000/requerimentos');
    const lista = await res.json();
    const tbody = document.querySelector('#requerimentos-lista tbody');
    tbody.innerHTML = '';
    lista.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><input type="checkbox" class="select-row" value="${r.id}"></td>
            <td>${r.numero}</td>
            <td>${r.tipo}</td>
            <td>${r.motivo}</td>
            <td>${r.prioridade}</td>
            <td>${new Date(r.data_abertura).toLocaleDateString()}</td>
            <td>${r.requerente_nome}</td>
            <td>${r.arvore_endereco}</td>
        `;
        tbody.appendChild(tr);
    });
}

document.getElementById('select-all').addEventListener('change', function() {
    document.querySelectorAll('.select-row').forEach(cb => cb.checked = this.checked);
});
document.getElementById('btn-gerar-os').addEventListener('click', async function() {
    const selecionados = Array.from(document.querySelectorAll('.select-row:checked')).map(cb => cb.value);
    if (!selecionados.length) {
        alert('Selecione pelo menos um requerimento!');
        return;
    }
    for (const reqId of selecionados) {
        // Aqui pode-se pedir dados adicionais, mas vamos criar OS básica:
        await fetch('http://localhost:5000/ordens_servico', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({requerimento_id: reqId, numero: 'OS-' + reqId, responsavel: 'Equipe', observacao: ''})
        });
    }
    alert('Ordens de serviço geradas!');
    listarRequerimentos();
});

// Mapa dos requerimentos
async function carregarMapa() {
    const res = await fetch('http://localhost:5000/requerimentos');
    const requerimentos = await res.json();
    const resArv = await fetch('http://localhost:5000/arvores');
    const arvores = await resArv.json();
    const arvoresMap = {};
    arvores.forEach(a => arvoresMap[a.id] = a);

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
    requerimentos.forEach(r => {
        const arvore = arvoresMap[r.arvore_id];
        if (arvore) {
            new maplibregl.Marker({ color: 'red' })
                .setLngLat([parseFloat(arvore.longitude), parseFloat(arvore.latitude)])
                .setPopup(new maplibregl.Popup().setHTML(`<strong>${arvore.especie}</strong><br>Req: ${r.numero}`))
                .addTo(map);
        }
    });
}
window.onload = () => { listarRequerimentos(); carregarMapa(); };
