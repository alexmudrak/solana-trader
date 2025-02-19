let chart;

async function renderChart() {
    const data = await fetch('/api/v1/tokens/prices/SOL').then((res) => res.json())
    const ctx = document.getElementById('priceChart').getContext('2d');
    const chartData = {
        labels: data.timestamps.map(ts => new Date(ts * 1000).toLocaleTimeString()),
        datasets: [
            {
                label: 'Token Price',
                data: data.prices,
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
                fill: false
            }
        ],
    };
    if (chart) {
        chart.data.labels = chartData.labels;
        chart.data.datasets[0].data = data.prices;
        chart.update();
    } else {
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: 'Token Price',
                        data: data.prices,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1,
                    },
                ],
            },
        });
    }
}

function startAutoUpdate() {
    renderChart();
    setInterval(renderChart, 5000);
}

document.addEventListener('DOMContentLoaded', function () {
    startAutoUpdate();
});
