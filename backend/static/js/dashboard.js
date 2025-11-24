document.addEventListener('DOMContentLoaded', function () {
    // lê dados injetados pelo template
    const graficoDados = window.graficoDados || { meses: [], emitidos: [], concluidos: [], saldo: [] };
    const graficoPie = window.graficoPie || { labels: [], data: [] };

    // Linha: requerimentos por mês
    const lineCanvas = document.getElementById('requerimentosChart');
    if (lineCanvas && typeof Chart !== 'undefined') {
        const ctx = lineCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: graficoDados.meses,
                datasets: [
                    {
                        label: 'Requerimentos Emitidos',
                        data: graficoDados.emitidos,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13,110,253,0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointBackgroundColor: '#0d6efd',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    },
                    {
                        label: 'Requerimentos Concluídos',
                        data: graficoDados.concluidos,
                        borderColor: '#198754',
                        backgroundColor: 'rgba(25,135,84,0.1)',
                        tension: 0.4,
                        fill: true,
                        pointRadius: 5,
                        pointBackgroundColor: '#198754',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2
                    },
                    {
                        label: 'Saldo Acumulado',
                        data: graficoDados.saldo,
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255,193,7,0.1)',
                        tension: 0.4,
                        fill: false,
                        pointRadius: 5,
                        pointBackgroundColor: '#ffc107',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        borderWidth: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    // Pizza: tipos de requerimentos
    const pieCanvas = document.getElementById('pieRequerimentos');
    if (pieCanvas && typeof Chart !== 'undefined') {
        const pctx = pieCanvas.getContext('2d');
        const colors = [
            '#0d6efd', '#198754', '#ffc107', '#dc3545', '#6f42c1',
            '#0dcaf0', '#fd7e14', '#20c997', '#6610f2', '#adb5bd',
            '#e83e8c', '#343a40'
        ];
        new Chart(pctx, {
            type: 'pie',
            data: {
                labels: graficoPie.labels,
                datasets: [{
                    data: graficoPie.data,
                    backgroundColor: colors.slice(0, graficoPie.labels.length),
                    borderColor: '#fff',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right' }
                }
            }
        });
    }
});