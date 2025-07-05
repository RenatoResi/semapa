let vistorias = [];
let paginaAtual = 1;
const itensPorPagina = 10;
let filtroAtivo = "";

async function carregarVistorias() {
    const resposta = await fetch('/vistorias');
    const data = await resposta.json();
    vistorias = data;
    aplicarFiltro();
}

function renderizarTabelaVistorias() {
    const tbody = document.querySelector('#vistorias-lista tbody');
    tbody.innerHTML = '';
    
    const inicio = (paginaAtual - 1) * itensPorPagina;
    const fim = inicio + itensPorPagina;
    const vistoriasPagina = vistorias.slice(inicio, fim);
    
    vistoriasPagina.forEach(vistoria => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${vistoria.id}</td>
            <td>${vistoria.requerimento_numero}</td>
            <td>${new Date(vistoria.vistoria_data).toLocaleString()}</td>
            <td>${vistoria.status}</td>
            <td>${vistoria.user_nome}</td>
            <td>
                ${vistoria.fotos.map(id => 
                    `<a href="/vistoria_foto/${id}" target="_blank">
                        <img src="/vistoria_foto/${id}" alt="Foto" width="50">
                    </a>`
                ).join('')}
            </td>
            <td>
                <button class="btn-editar" data-id="${vistoria.id}">Editar</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    
    atualizarPaginacao();
}

function aplicarFiltro() {
    const termo = filtroAtivo.toLowerCase();
    const vistoriasFiltradas = vistorias.filter(v => 
        (v.requerimento_numero && v.requerimento_numero.toLowerCase().includes(termo)) ||
        (v.status && v.status.toLowerCase().includes(termo)) ||
        (v.user_nome && v.user_nome.toLowerCase().includes(termo))
    );
    
    vistorias = vistoriasFiltradas;
    paginaAtual = 1;
    renderizarTabelaVistorias();
}

function atualizarPaginacao() {
    const totalPaginas = Math.ceil(vistorias.length / itensPorPagina);
    const paginacao = document.getElementById('paginacao-vistorias');
    
    paginacao.innerHTML = `
        <button onclick="paginaAnterior()" ${paginaAtual === 1 ? 'disabled' : ''}>
            Anterior
        </button>
        <span>Página ${paginaAtual} de ${totalPaginas}</span>
        <button onclick="proximaPagina()" ${paginaAtual === totalPaginas ? 'disabled' : ''}>
            Próxima
        </button>
    `;
}

function paginaAnterior() {
    if (paginaAtual > 1) {
        paginaAtual--;
        renderizarTabelaVistorias();
    }
}

function proximaPagina() {
    const totalPaginas = Math.ceil(vistorias.length / itensPorPagina);
    if (paginaAtual < totalPaginas) {
        paginaAtual++;
        renderizarTabelaVistorias();
    }
}

// Event Listeners
document.getElementById('filtro-vistoria').addEventListener('input', function(e) {
    filtroAtivo = e.target.value;
    aplicarFiltro();
});

document.getElementById('form-vistoria').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const response = await fetch('/vistoria', {
        method: 'POST',
        body: formData
    });
    
    const resultado = await response.json();
    alert(resultado.message);
    
    if (response.status === 201) {
        this.reset();
        carregarVistorias();
    }
});

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    carregarVistorias();
});
