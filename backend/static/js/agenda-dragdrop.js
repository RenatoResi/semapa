document.addEventListener('DOMContentLoaded', function() {
    let requerimentos = [];
    let currentPage = 1;
    let totalPages = 1;
    let debounceTimer;

    // Segurança: obter elementos apenas depois do DOM
    const filtroOrdenacaoEl = document.getElementById('filtro-ordenacao');
    const buscaRequisEl = document.getElementById('busca-requis');
    const prevPageEl = document.getElementById('prev-page');
    const nextPageEl = document.getElementById('next-page');
    const loadingEl = document.getElementById('requerimentos-loading');
    const containerEl = document.getElementById('requerimentos-container');
    const pageInfoEl = document.getElementById('page-info');

    // Se algum elemento essencial não existir, aborta e loga
    if (!containerEl || !loadingEl) {
        console.error('Agenda drag & drop: elementos essenciais não encontrados no DOM.');
        return;
    }

    // Carregar requerimentos iniciais
    carregarRequerimentos();

    // Event listeners (com guard)
    if (filtroOrdenacaoEl) filtroOrdenacaoEl.addEventListener('change', debounce(() => { currentPage = 1; carregarRequerimentos(); }, 300));
    if (buscaRequisEl) buscaRequisEl.addEventListener('input', debounce(() => { currentPage = 1; carregarRequerimentos(); }, 500));
    if (prevPageEl) prevPageEl.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            carregarRequerimentos();
        }
    });
    if (nextPageEl) nextPageEl.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            carregarRequerimentos();
        }
    });

    function debounce(func, wait) {
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(debounceTimer);
                debounceTimer = null;
                func(...args);
            };
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(later, wait);
        };
    }

    async function carregarRequerimentos() {
        const orderBy = filtroOrdenacaoEl ? filtroOrdenacaoEl.value : 'id-desc';
        const busca = buscaRequisEl ? buscaRequisEl.value.trim() : '';

        loadingEl.style.display = 'block';
        containerEl.style.display = 'none';

        const params = new URLSearchParams({
            page: currentPage,
            order_by: orderBy,
            busca: busca
        });

        try {
            const resp = await fetch(`/tarefas/api/requerimentos?${params.toString()}`, { cache: 'no-store' });
            if (!resp.ok) {
                const txt = await resp.text().catch(()=> '');
                throw new Error(`HTTP ${resp.status} ${resp.statusText} - ${txt}`);
            }
            const data = await resp.json();
            requerimentos = Array.isArray(data.requerimentos) ? data.requerimentos : (data.requerimentos || []);
            currentPage = data.page || 1;
            totalPages = data.total_pages || 1;
            renderizarRequerimentos({ requerimentos });
            atualizarPaginacao({ page: currentPage, total_pages: totalPages });
            initDragDrop();
            // também atacha cliques em task-cards já existentes no DOM
            attachTaskCardClicks(document.querySelectorAll('.task-card'));
            attachAddTaskButtons(document.querySelectorAll('.btn-add-task'));
        } catch (error) {
            console.error('Erro ao carregar requerimentos:', error);
            containerEl.innerHTML =
                '<div class="text-center p-4 text-danger"><i class="fas fa-exclamation-triangle"></i> Erro ao carregar requerimentos</div>';
        } finally {
            loadingEl.style.display = 'none';
            containerEl.style.display = 'grid';
        }
    }

    function renderizarRequerimentos(data) {
        const container = containerEl;
        if (!container) return;
        if (!data || !data.requerimentos || data.requerimentos.length === 0) {
            container.innerHTML = '<div class="text-center p-4 text-muted">Nenhum requerimento disponível</div>';
            return;
        }

        container.innerHTML = data.requerimentos.map(r => `
            <div class="requerimento-card" draggable="true" data-id="${r.id}">
                <div class="card-header">
                    <div>
                        <div class="card-tipo"># ${r.numero || ''}</div>
                        <div class="card-numero">${r.tipo || ''}</div>
                        <div class="card-tipo">Prioridade ${r.prioridade || ''}</div>
                    </div>
                    <div class="card-complexidade">${r.complexidade || ''}</div>
                </div>
                <div class="card-bairro">${r.bairro || ''}</div>
            </div>
        `).join('');
    }

    function atualizarPaginacao(data) {
        if (!pageInfoEl) return;
        pageInfoEl.textContent = `${data.page} / ${data.total_pages}`;
        if (prevPageEl) prevPageEl.disabled = data.page === 1;
        if (nextPageEl) nextPageEl.disabled = data.page >= data.total_pages;
    }

    function initDragDrop() {
        const cards = document.querySelectorAll('.requerimento-card');
        const dropzones = document.querySelectorAll('.drop-area');

        // desligar listeners antigos (evitar duplicatas)
        cards.forEach(card => {
            card.removeEventListener('dragstart', handleDragStart);
            card.removeEventListener('dragend', handleDragEnd);
        });
        dropzones.forEach(zone => {
            zone.removeEventListener('dragover', handleDragOver);
            zone.removeEventListener('drop', handleDrop);
            zone.removeEventListener('dragleave', handleDragLeave);
            zone.removeEventListener('dragenter', handleDragEnter);
        });

        cards.forEach(card => {
            card.addEventListener('dragstart', handleDragStart);
            card.addEventListener('dragend', handleDragEnd);
        });

        dropzones.forEach(zone => {
            zone.addEventListener('dragover', handleDragOver);
            zone.addEventListener('drop', handleDrop);
            zone.addEventListener('dragleave', handleDragLeave);
            zone.addEventListener('dragenter', handleDragEnter);
        });

        // Atachar clique em task-cards já presentes no DOM (ex.: tarefas renderizadas pelo servidor)
        const taskCards = document.querySelectorAll('.task-card');
        attachTaskCardClicks(taskCards);

        // Atachar botões de adicionar tarefas caso existam
        attachAddTaskButtons(document.querySelectorAll('.btn-add-task'));
    }

    // abre modal com detalhes da tarefa (busca fragmento)
    async function openTarefaModal(tarefaId) {
        if (!tarefaId) return;
        const modalEl = document.getElementById('tarefa-modal');
        const modalContent = document.getElementById('tarefa-modal-content');
        if (!modalEl || !modalContent) {
            // fallback: abrir em nova janela
            window.open(`/tarefas/${tarefaId}/detalhes`, `tarefa_${tarefaId}`);
            return;
        }

        try {
            const resp = await fetch(`/tarefas/${tarefaId}/detalhes?partial=1`, { cache: 'no-store' });
            if (!resp.ok) {
                throw new Error('Não foi possível obter detalhes da tarefa');
            }
            const html = await resp.text();
            modalContent.innerHTML = html;

            // close handlers inside fragment
            const closeBtns = modalContent.querySelectorAll('.modal-close-btn');
            closeBtns.forEach(b => b.addEventListener('click', () => hideModal()));

            // show modal usando Bootstrap se disponível, senão fallback simples
            if (window.bootstrap && typeof window.bootstrap.Modal === 'function') {
                const bsModal = new bootstrap.Modal(modalEl);
                bsModal.show();
                // guarda referência para fechar depois se necessário
                modalEl._bsModal = bsModal;
            } else {
                modalEl.style.display = 'block';
                modalEl.classList.add('show');
            }
        } catch (err) {
            console.error(err);
            alert('Erro ao carregar detalhes da tarefa');
        }
    }

    function hideModal() {
        const modalEl = document.getElementById('tarefa-modal');
        if (!modalEl) return;
        if (modalEl._bsModal) {
            modalEl._bsModal.hide();
        } else {
            modalEl.style.display = 'none';
            modalEl.classList.remove('show');
        }
        const modalContent = document.getElementById('tarefa-modal-content');
        if (modalContent) modalContent.innerHTML = '';
    }

    // anexa listener de clique a um ou mais elementos task-card
    function attachTaskCardClicks(nodeList) {
        if (!nodeList) return;
        nodeList.forEach(card => {
            // evita múltiplos listeners
            card.style.cursor = 'pointer';
            card.removeEventListener('click', taskCardClickHandler);
            card.addEventListener('click', taskCardClickHandler);
        });
    }

    function taskCardClickHandler(e) {
        const el = e.currentTarget;
        const tarefaId = el.dataset.tarefaId || el.getAttribute('data-tarefa-id');
        if (tarefaId) {
            openTarefaModal(tarefaId);
        }
    }

    function attachAddTaskButtons(nodeList) {
        if (!nodeList) return;
        nodeList.forEach(btn => {
            btn.removeEventListener('click', addTaskClickHandler);
            btn.addEventListener('click', addTaskClickHandler);
        });
    }

    function addTaskClickHandler(e) {
        const date = e.currentTarget.dataset.date;
        if (!date) return;
        // abre página de criação de tarefa com data preenchida
        const url = `/tarefas/nova?data_prevista=${encodeURIComponent(date)}`;
        window.location.href = url;
    }

    function handleDragStart(e) {
        e.target.classList.add('dragging');
        try { e.dataTransfer.setData('text/plain', e.target.dataset.id); } catch (err) {}
        e.dataTransfer.effectAllowed = 'move';
    }

    function handleDragEnd(e) {
        e.target.classList.remove('dragging');
        document.querySelectorAll('.day-column').forEach(col => col.classList.remove('drag-over'));
    }

    function handleDragEnter(e) {
        e.preventDefault();
    }

    function handleDragOver(e) {
        e.preventDefault();
        try { e.dataTransfer.dropEffect = 'move'; } catch (err) {}
        const dayCol = e.currentTarget.closest('.day-column');
        if (dayCol) dayCol.classList.add('drag-over');
    }

    function handleDragLeave(e) {
        const dayCol = e.currentTarget.closest('.day-column');
        if (dayCol && !e.currentTarget.contains(e.relatedTarget)) {
            dayCol.classList.remove('drag-over');
        }
    }

    async function handleDrop(e) {
        e.preventDefault();
        const requerimentoId = e.dataTransfer.getData('text/plain');
        const dropArea = e.currentTarget;
        const dayColumn = dropArea.closest('.day-column');

        if (!dayColumn) {
            mostrarToast('Área de destino inválida', 'error');
            return;
        }

        dayColumn.classList.remove('drag-over');

        // Verificar se já existe tarefa para este requerimento no dia
        const existingCard = dropArea.querySelector(`[data-requerimento-id="${requerimentoId}"]`);
        if (existingCard) {
            mostrarToast('Requerimento já agendado neste slot!', 'warning');
            return;
        }

        try {
            const response = await fetch('/tarefas/api/agendar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    requerimento_id: requerimentoId,
                    data_prevista: dayColumn.dataset.data,
                    periodo: dropArea.dataset.drop
                })
            });

            const data = await response.json().catch(()=>({ success: false, error: 'Resposta inválida' }));

            if (response.ok && data.success) {
                // Criar card visual
                const original = document.querySelector(`[data-id="${requerimentoId}"]`);
                if (original) {
                    const card = original.cloneNode(true);
                    card.classList.remove('requerimento-card');
                    card.classList.add('task-card', 'placed');
                    card.draggable = false;
                    // usar atributo compatível com server-rendered markup
                    card.dataset.tarefaId = data.tarefa_id;
                    card.dataset.requerimentoId = requerimentoId;
                    card.innerHTML = `
                        <div class="task-title">#${requerimentoId} - ${data.descricao}</div>
                        <div class="task-status text-success">✅ Agendada (ID: ${data.tarefa_id})</div>
                    `;
                    const placeholder = dropArea.querySelector('.drop-placeholder');
                    if (placeholder) placeholder.remove();
                    dropArea.appendChild(card);

                    // atacha clique ao novo card
                    attachTaskCardClicks([card]);
                }
                mostrarToast(`✅ Requerimento #${requerimentoId} agendado!`, 'success');

                // Recarregar lista para remover o card usado
                carregarRequerimentos();
            } else {
                const errMsg = data.error || `HTTP ${response.status}`;
                mostrarToast(`Erro: ${errMsg}`, 'error');
            }
        } catch (error) {
            console.error('Erro:', error);
            mostrarToast('Erro ao agendar tarefa', 'error');
        }
    }

    function mostrarToast(mensagem, tipo = 'success') {
        // Toast simples no console por enquanto - você pode implementar um toast UI
        const bg = tipo === 'success' ? '#4CAF50' : tipo === 'error' ? '#f44336' : '#ff9800';
        console.log(`%c${mensagem}`, `background: ${bg}; color: white; padding: 8px 12px; border-radius: 4px;`);
    }

    // fecha modal ao clicar fora (fallback)
    document.addEventListener('click', function(ev) {
        const modal = document.getElementById('tarefa-modal');
        if (!modal) return;
        if (modal.style.display === 'block' || modal.classList.contains('show')) {
            const content = document.getElementById('tarefa-modal-content');
            if (content && !content.contains(ev.target) && !ev.target.classList.contains('task-card')) {
                // evita fechar ao clicar em cards
                hideModal();
            }
        }
    });
});
