let especies = [];

document.addEventListener('DOMContentLoaded', function() {
    fetchEspecies();
    document.querySelectorAll('.filtros select').forEach(function(select) {
        select.addEventListener('change', filtrarTabela);
    });
});

function fetchEspecies() {
    fetch('/especies')
        .then(response => response.json())
        .then(data => {
            especies = data;
            renderTabela(especies);
        })
        .catch(err => {
            alert('Erro ao carregar espécies: ' + err);
        });
}

function renderTabela(lista) {
    const tbody = document.querySelector('#tabelaEspecies tbody');
    tbody.innerHTML = '';
    lista.forEach(e => {
        let tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${e.link_foto ? `<img src="${e.link_foto}" alt="Foto de ${e.nome_popular}" class="foto-especie" style="max-width:80px;max-height:80px;cursor:pointer;">` : '—'}</td>
            <td>${e.nome_popular}</td>
            <td><em>${e.nome_cientifico}</em></td>
            <td>${capitalize(e.porte)}</td>
            <td>${e.altura_min && e.altura_max ? `${e.altura_min}–${e.altura_max}` : '—'}</td>
            <td>${e.longevidade_min && e.longevidade_max ? `${e.longevidade_min}–${e.longevidade_max} anos` : '—'}</td>
            <td>${e.deciduidade || ''}</td>
            <td>${e.cor_flor || ''}</td>
            <td>${e.epoca_floracao || ''}</td>
            <td>${capitalize(e.fruto_comestivel)}</td>
            <td>${e.epoca_frutificacao || ''}</td>
            <td>${e.necessidade_rega || ''}</td>
            <td>${e.observacoes || ''}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filtrarTabela() {
    let porte = document.getElementById('filtroPorte').value.toLowerCase();
    let deciduidade = document.getElementById('filtroDeciduidade').value.toLowerCase();
    let fruto = document.getElementById('filtroFruto').value.toLowerCase();
    let rega = document.getElementById('filtroRega').value.toLowerCase();

    let filtradas = especies.filter(e => {
        return (!porte || (e.porte && e.porte.toLowerCase() === porte)) &&
               (!deciduidade || (e.deciduidade && e.deciduidade.toLowerCase() === deciduidade)) &&
               (!fruto || (e.fruto_comestivel && e.fruto_comestivel.toLowerCase() === fruto)) &&
               (!rega || (e.necessidade_rega && e.necessidade_rega.toLowerCase() === rega));
    });
    renderTabela(filtradas);
}

function resetFiltros() {
    document.getElementById('filtroPorte').value = '';
    document.getElementById('filtroDeciduidade').value = '';
    document.getElementById('filtroFruto').value = '';
    document.getElementById('filtroRega').value = '';
    filtrarTabela();
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Abrir modal ao clicar na foto
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('foto-especie')) {
        abrirModalFoto(e.target.src, e.target.alt);
    }
});

function abrirModalFoto(src, alt) {
    document.getElementById('img-modal-foto').src = src;
    document.getElementById('img-modal-foto').alt = alt;
    document.getElementById('modal-foto').style.display = 'flex';
}

function fecharModalFoto() {
    document.getElementById('modal-foto').style.display = 'none';
    document.getElementById('img-modal-foto').src = '';
}

// Fechar ao clicar fora da imagem
document.getElementById('modal-foto').addEventListener('click', function(e) {
    if (e.target === this) fecharModalFoto();
});
// Fechar modal com ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        fecharModalFoto();
    }
});