let map;
let marcadoresMapa = [];
let osAtual = null;

async function listarOrdensServico() {
    try {
        const res = await fetch('/ordens_servico');
        const lista = await res.json();
        const tbody = document.querySelector('#ordens-servico-lista tbody');
        tbody.innerHTML = '';
        
        lista.forEach(os => {
            const tr = document.createElement('tr');
            tr.dataset.id = os.id;
            tr.innerHTML = `
                <td>${os.numero}</td>
                <td>${os.responsavel}</td>
                <td>${os.data_emissao ? new Date(os.data_emissao).toLocaleDateString() : ''}</td>
                <td>${os.status}</td>
                <td>${os.requerimentos ? os.requerimentos.length : 0}</td>
            `;
            tbody.appendChild(tr);
            
            // Evento para mostrar detalhes ao clicar na linha
            tr.addEventListener('click', () => {
                carregarDetalhesOS(os.id);
            });
        });
    } catch (error) {
        console.error('Erro ao carregar OS:', error);
    }
}

async function carregarDetalhesOS(osId) {
    try {
        const res = await fetch(`/ordens_servico/${osId}`);
        const os = await res.json();
        osAtual = os;
        
        // Preencher informações gerais
        document.getElementById('os-numero').textContent = os.numero;
        document.getElementById('os-responsavel').textContent = os.responsavel;
        document.getElementById('os-emissao').textContent = os.data_emissao ? new Date(os.data_emissao).toLocaleDateString() : '-';
        document.getElementById('os-execucao').textContent = os.data_execucao ? new Date(os.data_execucao).toLocaleDateString() : '-';
        document.getElementById('os-status').textContent = os.status;
        document.getElementById('os-observacao').textContent = os.observacao || '-';
        
        // Preencher requerimentos
        const tbody = document.querySelector('#requerimentos-os tbody');
        tbody.innerHTML = '';
        
        if (os.requerimentos && os.requerimentos.length > 0) {
            os.requerimentos.forEach(req => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${req.numero}</td>
                    <td>${req.tipo || '-'}</td>
                    <td>${req.motivo || '-'}</td>
                    <td>${req.requerente_nome || '-'}</td>
                    <td>${req.requerente_telefone || '-'}</td>
                    <td>${req.arvore_endereco || '-'}</td>
                `;
                tbody.appendChild(tr);
            });
            
            // Carregar mapa
            carregarMapaOS(os.requerimentos);
        } else {
            // Limpar mapa se não houver requerimentos
            if (map) {
                map.remove();
                map = null;
                marcadoresMapa = [];
            }
        }
        
        // Mostrar seção de detalhes
        document.getElementById('detalhes-os').style.display = 'block';
        
        // Configurar botão de edição
        document.getElementById('btn-editar-os').dataset.id = os.id;
        
        // Garantir que está no modo de visualização
        mostrarModoVisualizacao();
        
    } catch (error) {
        console.error('Erro ao carregar detalhes da OS:', error);
    }
}

function carregarMapaOS(requerimentos) {
    // Remover mapa existente
    if (map) {
        map.remove();
        marcadoresMapa.forEach(m => m.remove());
        marcadoresMapa = [];
    }
    
    // Criar novo mapa
    const container = document.getElementById('mapa-os');
    container.innerHTML = '';
    
    map = new maplibregl.Map({
        container: 'mapa-os',
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
    
    // Adicionar marcadores para cada requerimento com localização
    requerimentos.forEach(req => {
        if (req.arvore_latitude && req.arvore_longitude) {
            const marker = new maplibregl.Marker()
                .setLngLat([parseFloat(req.arvore_longitude), parseFloat(req.arvore_latitude)])
                .setPopup(new maplibregl.Popup().setHTML(`
                    <strong>Requerimento:</strong> ${req.numero}<br>
                    <strong>Endereço:</strong> ${req.arvore_endereco || 'N/A'}<br>
                    <strong>Requerente:</strong> ${req.requerente_nome || 'N/A'}
                `))
                .addTo(map);
            marcadoresMapa.push(marker);
        }
    });
}

function abrirEdicaoOS() {
    if (!osAtual) return;
    
    // Preencher campos de edição
    document.getElementById('os-numero-edit').textContent = osAtual.numero;
    document.getElementById('os-emissao-edit').textContent = osAtual.data_emissao ? new Date(osAtual.data_emissao).toLocaleDateString() : '-';
    document.getElementById('input-responsavel').value = osAtual.responsavel || '';
    document.getElementById('input-data-execucao').value = osAtual.data_execucao ? osAtual.data_execucao.split('T')[0] : '';
    document.getElementById('input-status').value = osAtual.status || 'Aberta';
    document.getElementById('input-observacao').value = osAtual.observacao || '';
    
    // Mostrar modo de edição
    document.getElementById('info-readonly').style.display = 'none';
    document.getElementById('info-edit').style.display = 'block';
}

function mostrarModoVisualizacao() {
    document.getElementById('info-readonly').style.display = 'block';
    document.getElementById('info-edit').style.display = 'none';
}

async function salvarEdicaoOS() {
    if (!osAtual) return;
    
    const dadosAtualizados = {
        responsavel: document.getElementById('input-responsavel').value,
        data_execucao: document.getElementById('input-data-execucao').value || null,
        status: document.getElementById('input-status').value,
        observacao: document.getElementById('input-observacao').value
    };
    
    try {
        const response = await fetch(`/ordens_servico/${osAtual.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dadosAtualizados)
        });
        
        if (!response.ok) {
            throw new Error('Erro ao salvar alterações');
        }
        
        // Recarregar dados e voltar ao modo de visualização
        await carregarDetalhesOS(osAtual.id);
        await listarOrdensServico(); // Atualizar a lista também
        
        alert('Ordem de serviço atualizada com sucesso!');
        
    } catch (error) {
        console.error('Erro ao salvar OS:', error);
        alert('Erro ao salvar alterações: ' + error.message);
    }
}

function filtrarOS() {
    const termo = document.getElementById('filtro-os').value.toLowerCase();
    document.querySelectorAll('#ordens-servico-lista tbody tr').forEach(tr => {
        const textoLinha = tr.textContent.toLowerCase();
        tr.style.display = textoLinha.includes(termo) ? '' : 'none';
    });
}

// Inicialização
window.onload = () => {
    listarOrdensServico();
    
    // Eventos para os botões de edição
    document.getElementById('btn-editar-os').addEventListener('click', abrirEdicaoOS);
    document.getElementById('btn-salvar-os').addEventListener('click', salvarEdicaoOS);
    document.getElementById('btn-cancelar-os').addEventListener('click', mostrarModoVisualizacao);
};
