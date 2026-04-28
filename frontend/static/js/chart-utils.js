/**
 * Shared Chart.js utilities: dataLabels plugin and horizontal bar chart factory.
 * Requires Chart.js to be loaded first.
 */

const dataLabelsPlugin = {
    id: 'dataLabels',
    afterDatasetsDraw(chart) {
        const { ctx, chartArea: { right } } = chart;
        chart.data.datasets.forEach((dataset, datasetIndex) => {
            const meta = chart.getDatasetMeta(datasetIndex);
            meta.data.forEach((datapoint, index) => {
                const value = dataset.data[index];
                if (value === null || value === undefined) return;

                const { x, y } = datapoint.getProps(['x', 'y']);
                ctx.font = '11px Arial';
                const textWidth = ctx.measureText(value).width;
                const padding = 6;

                if (x + padding + textWidth < right - 4) {
                    ctx.fillStyle = '#333';
                    ctx.textAlign = 'left';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(value, x + padding, y);
                } else {
                    ctx.fillStyle = '#fff';
                    ctx.textAlign = 'right';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(value, x - padding, y);
                }
            });
        });
    }
};

Chart.register(dataLabelsPlugin);

/**
 * Create a horizontal bar chart with standard styling.
 * @param {Object} opts
 * @param {string} opts.canvasId      - ID of the <canvas> element
 * @param {string} opts.containerId   - ID of the wrapper div (for dynamic height)
 * @param {string[]} opts.labels      - Y-axis labels (player names)
 * @param {number[]} opts.data        - Data values
 * @param {string} opts.datasetLabel  - Legend label for the dataset
 * @param {string} opts.color         - Bar fill colour (rgba)
 * @param {string} opts.borderColor   - Bar border colour (rgba)
 * @param {string} opts.xAxisTitle    - X-axis title text
 * @param {number} [opts.barPercentage=0.75]
 * @param {number} [opts.categoryPercentage=0.85]
 * @param {boolean} [opts.integerTicks=false] - Force integer ticks on x-axis
 * @returns {Chart}
 */
function initHorizontalBarChart(opts) {
    const numItems = opts.labels.length;
    const chartHeight = Math.max(300, numItems * 32 + 80);
    document.getElementById(opts.containerId).style.height = chartHeight + 'px';

    const ctx = document.getElementById(opts.canvasId).getContext('2d');
    const ticksConfig = { font: { size: 11 } };
    if (opts.integerTicks) ticksConfig.precision = 0;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: opts.labels,
            datasets: [{
                label: opts.datasetLabel,
                data: opts.data,
                backgroundColor: opts.color,
                borderColor: opts.borderColor,
                borderWidth: 1,
                borderRadius: 3,
                barPercentage: opts.barPercentage || 0.75,
                categoryPercentage: opts.categoryPercentage || 0.85
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { right: 50 } },
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    beginAtZero: true,
                    title: { display: true, text: opts.xAxisTitle, font: { size: 11 } },
                    ticks: ticksConfig
                },
                y: {
                    ticks: { font: { size: 12 }, autoSkip: false, maxRotation: 0 }
                }
            }
        }
    });
}
