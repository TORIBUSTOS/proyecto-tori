/**
 * TORO Analytics - Charts.js
 * Funciones para renderizar gráficos con Chart.js
 */

const API_URL = 'http://localhost:8000/api';

// Referencias a los charts (para destruirlos al actualizar)
let chartIngresos = null;
let chartEgresos = null;
let chartFlujo = null;

// Paleta de colores consistente
const COLORES_INGRESOS = [
    '#10b981', // verde
    '#14b8a6', // teal
    '#06b6d4', // cyan
    '#0ea5e9', // azul claro
    '#3b82f6', // azul
    '#6366f1', // indigo
    '#8b5cf6', // violeta
    '#a855f7', // purple
];

const COLORES_EGRESOS = [
    '#ef4444', // rojo
    '#f97316', // naranja
    '#f59e0b', // amarillo
    '#eab308', // amarillo oscuro
    '#84cc16', // lima
    '#22c55e', // verde claro
    '#14b8a6', // teal
    '#06b6d4', // cyan
];

/**
 * Inicialización al cargar la página
 */
document.addEventListener('DOMContentLoaded', async () => {
    // periodo-global.js ya se encarga de inicializar y poblar el selector #mes
    // Solo necesitamos esperar un momento y cargar los gráficos
    setTimeout(async () => {
        await cargarGraficos();
    }, 100);
});


/**
 * Carga todos los gráficos
 */
async function cargarGraficos() {
    const mes = document.getElementById('mes').value;

    // Mostrar loading
    mostrarLoading();

    try {
        await Promise.all([
            renderPieIngresos(mes),
            renderPieEgresos(mes),
            mes ? renderLineFlujo(mes) : mostrarMensajeFlujo()
        ]);

        // Cargar y renderizar resumen ejecutivo
        const reporte = await fetchReporteEjecutivo(mes);
        renderResumenEjecutivo(reporte);

        // Cargar y renderizar insights
        await cargarYRenderizarInsights(mes);

        // Limpiar errores
        document.getElementById('error-container').innerHTML = '';
    } catch (error) {
        mostrarError('Error cargando gráficos: ' + error.message);
    }
}

/**
 * Muestra indicador de carga
 */
function mostrarLoading() {
    document.getElementById('error-container').innerHTML =
        '<div class="loading">⏳ Cargando gráficos...</div>';
}

/**
 * Muestra mensaje de error
 */
function mostrarError(mensaje) {
    document.getElementById('error-container').innerHTML =
        `<div class="error">❌ ${mensaje}</div>`;
}

/**
 * Muestra mensaje cuando no se puede mostrar flujo diario
 */
function mostrarMensajeFlujo() {
    const container = document.getElementById('line-flujo').parentElement;
    container.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">Selecciona un mes específico para ver el flujo diario</p>';
}

/**
 * Renderiza el pie chart de ingresos
 */
async function renderPieIngresos(mes) {
    try {
        const url = mes ? `${API_URL}/analytics/pie-ingresos?mes=${mes}` : `${API_URL}/analytics/pie-ingresos`;
        const res = await fetch(url);
        const responseData = await res.json();

        // Extraer labels y values del nuevo formato
        const labels = responseData.data.map(item => item.label);
        const values = responseData.data.map(item => item.value);

        // Destruir chart anterior si existe
        if (chartIngresos) {
            chartIngresos.destroy();
        }

        const ctx = document.getElementById('pie-ingresos');
        chartIngresos = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: COLORES_INGRESOS,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: $${value.toLocaleString('es-AR', {minimumFractionDigits: 2})} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

        // Mostrar estadísticas
        mostrarEstadisticas('stats-ingresos', values, responseData.total, 'ingresos');

    } catch (error) {
        console.error('Error renderizando pie ingresos:', error);
        throw error;
    }
}

/**
 * Renderiza el pie chart de egresos
 */
async function renderPieEgresos(mes) {
    try {
        const url = mes ? `${API_URL}/analytics/pie-egresos?mes=${mes}` : `${API_URL}/analytics/pie-egresos`;
        const res = await fetch(url);
        const responseData = await res.json();

        // Extraer labels y values del nuevo formato
        const labels = responseData.data.map(item => item.label);
        const values = responseData.data.map(item => item.value);

        // Destruir chart anterior si existe
        if (chartEgresos) {
            chartEgresos.destroy();
        }

        const ctx = document.getElementById('pie-egresos');
        chartEgresos = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: COLORES_EGRESOS,
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: $${value.toLocaleString('es-AR', {minimumFractionDigits: 2})} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });

        // Mostrar estadísticas
        mostrarEstadisticas('stats-egresos', values, responseData.total, 'egresos');

    } catch (error) {
        console.error('Error renderizando pie egresos:', error);
        throw error;
    }
}

/**
 * Renderiza el line chart de flujo diario
 */
async function renderLineFlujo(mes) {
    try {
        const res = await fetch(`${API_URL}/analytics/flujo-diario?mes=${mes}`);
        const data = await res.json();

        // Destruir chart anterior si existe
        if (chartFlujo) {
            chartFlujo.destroy();
        }

        // Si no hay canvas (fue reemplazado por mensaje), recrearlo
        let canvas = document.getElementById('line-flujo');
        if (!canvas) {
            const container = document.querySelector('.chart-card.full-width .chart-container');
            container.innerHTML = '<canvas id="line-flujo"></canvas>';
            canvas = document.getElementById('line-flujo');
        }

        const ctx = canvas;
        chartFlujo = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dias.map(d => formatearFecha(d)),
                datasets: [
                    {
                        label: 'Ingresos',
                        data: data.ingresos,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    },
                    {
                        label: 'Egresos',
                        data: data.egresos,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: true,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    },
                    {
                        label: 'Neto',
                        data: data.neto,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: false,
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        borderDash: [5, 5]
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            padding: 20,
                            font: {
                                size: 13
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y || 0;
                                return `${label}: $${value.toLocaleString('es-AR', {minimumFractionDigits: 2})}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString('es-AR');
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        // Mostrar estadísticas de flujo
        mostrarEstadisticasFlujo('stats-flujo', data);

    } catch (error) {
        console.error('Error renderizando line flujo:', error);
        throw error;
    }
}

/**
 * Formatea una fecha YYYY-MM-DD a DD/MM
 */
function formatearFecha(fechaStr) {
    const [year, month, day] = fechaStr.split('-');
    return `${day}/${month}`;
}

/**
 * Muestra estadísticas para pie charts
 */
function mostrarEstadisticas(containerId, datos, total, tipo) {
    const container = document.getElementById(containerId);

    const count = datos.length;
    const avg = count > 0 ? total / count : 0;

    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Total ${tipo}</div>
            <div class="stat-value ${tipo === 'ingresos' ? 'positive' : 'negative'}">
                $${total.toLocaleString('es-AR', {minimumFractionDigits: 2})}
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Categorías</div>
            <div class="stat-value">${count}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Promedio</div>
            <div class="stat-value">
                $${avg.toLocaleString('es-AR', {minimumFractionDigits: 2})}
            </div>
        </div>
    `;
}

/**
 * Muestra estadísticas para el flujo diario
 */
function mostrarEstadisticasFlujo(containerId, data) {
    const container = document.getElementById(containerId);

    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Total Ingresos</div>
            <div class="stat-value positive">
                $${data.total_ingresos.toLocaleString('es-AR', {minimumFractionDigits: 2})}
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Egresos</div>
            <div class="stat-value negative">
                $${data.total_egresos.toLocaleString('es-AR', {minimumFractionDigits: 2})}
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Balance Neto</div>
            <div class="stat-value ${data.balance >= 0 ? 'positive' : 'negative'}">
                $${data.balance.toLocaleString('es-AR', {minimumFractionDigits: 2})}
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Días registrados</div>
            <div class="stat-value">${data.dias.length}</div>
        </div>
    `;
}

// ============================================
// RESUMEN EJECUTIVO (DESDE /api/reportes)
// ============================================

/**
 * Fetch del reporte ejecutivo completo
 */
async function fetchReporteEjecutivo(mes) {
    const url = mes ? `${API_URL}/reportes?mes=${mes}` : `${API_URL}/reportes`;
    const res = await fetch(url);
    const data = await res.json();
    return data.reporte || data;
}

/**
 * Renderiza el resumen ejecutivo completo
 */
function renderResumenEjecutivo(reporte) {
    const container = document.getElementById('resumen-ejecutivo');
    if (!container || !reporte) return;

    const saldos = reporte.saldos || {};
    const clasif = reporte.clasificacion || {};
    const ingresos = reporte.desglose_ingresos || [];
    const egresos = reporte.desglose_egresos || [];

    const money = (v) =>
        (v ?? 0).toLocaleString('es-AR', { minimumFractionDigits: 2 });

    container.innerHTML = `
        <h3>📋 Resumen Ejecutivo</h3>

        <h4>💰 Saldos Bancarios</h4>
        <table class="simple-table">
            <tr><td>Saldo Inicial</td><td>$${money(saldos.saldo_inicial)}</td></tr>
            <tr><td>Total Ingresos</td><td>$${money(saldos.ingresos_total)}</td></tr>
            <tr><td>Total Egresos</td><td>$${money(saldos.egresos_total)}</td></tr>
            <tr><td>Saldo Final</td><td>$${money(saldos.saldo_final)}</td></tr>
            <tr><td>Variación del Mes</td><td>$${money(saldos.variacion)}</td></tr>
        </table>

        <h4>📊 Clasificación</h4>
        <table class="simple-table">
            <tr><td>Total movimientos</td><td>${clasif.total_movimientos || 0}</td></tr>
            <tr><td>Clasificados</td><td>${clasif.clasificados || 0}</td></tr>
            <tr><td>Sin clasificar</td><td>${clasif.sin_clasificar || 0}</td></tr>
            <tr><td>% Clasificados</td><td>${clasif.pct_clasificados || 0}%</td></tr>
        </table>

        <h4>💵 Desglose de Ingresos</h4>
        <table class="simple-table">
            ${ingresos.map(i =>
                `<tr><td>${i.categoria}</td><td>$${money(i.monto)}</td></tr>`
            ).join('')}
        </table>

        <h4>💸 Desglose de Egresos</h4>
        <table class="simple-table">
            ${egresos.map(e =>
                `<tr><td>${e.categoria}</td><td>$${money(e.monto)}</td></tr>`
            ).join('')}
        </table>
    `;
}

// ============================================
// INSIGHTS FINANCIEROS/OPERATIVOS
// ============================================

/**
 * Carga y renderiza los insights del período
 */
async function cargarYRenderizarInsights(mes) {
    try {
        const url = mes ? `${API_URL}/insights?mes=${mes}` : `${API_URL}/insights`;
        const res = await fetch(url);
        const data = await res.json();

        if (data.status === 'success') {
            renderInsights(data.insights);
        }
    } catch (error) {
        console.error('Error cargando insights:', error);
        // Mostrar mensaje de error si falla
        const container = document.getElementById('insights-content');
        if (container) {
            container.innerHTML = '<div class="no-insights">No se pudieron cargar los insights.</div>';
        }
    }
}

/**
 * Renderiza los insights en el DOM
 */
function renderInsights(insights) {
    const container = document.getElementById('insights-content');
    if (!container) return;

    // Si no hay insights
    if (!insights || insights.length === 0) {
        container.innerHTML = '<div class="no-insights">No se detectaron patrones relevantes en este período.</div>';
        return;
    }

    // Renderizar insights (máximo 7 según especificación)
    const insightsHTML = insights.slice(0, 7).map(insight => `
        <div class="insight-card">
            <div class="insight-title">${insight.title}</div>
            <div class="insight-message">${insight.message}</div>
            <div class="insight-action">${insight.action}</div>
        </div>
    `).join('');

    container.innerHTML = insightsHTML;
}
