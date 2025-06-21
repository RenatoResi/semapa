async function listarOrdensServico() {
    const res = await fetch('/ordens_servico');
    const lista = await res.json();
    const tbody = document.querySelector('#ordens-servico-lista tbody');
    tbody.innerHTML = '';
    lista.forEach(o => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${o.numero}</td>
            <td>${o.responsavel}</td>
            <td>${o.data_execucao ? new Date(o.data_execucao).toLocaleDateString() : ''}</td>
            <td>${o.status}</td>
            <td>${o.observacao}</td>
            <td>${o.data_emissao ? new Date(o.data_emissao).toLocaleDateString() : ''}</td>
        `;
        tbody.appendChild(tr);
    });
}
window.onload = listarOrdensServico;
