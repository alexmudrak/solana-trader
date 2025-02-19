let chart

async function loadTokens() {
  const response = await fetch('/api/v1/tokens/')
  const data = await response.json()
  const tokenSelect = document.getElementById('token-select')

  data.tokens.forEach((token) => {
    const option = document.createElement('option')
    option.value = token
    option.textContent = token
    tokenSelect.appendChild(option)
  })
}

async function fetchPrices(token) {
  const response = await fetch(`/api/v1/tokens/prices/${token}`)
  return await response.json()
}

async function renderChart() {
  const data = await fetchPrices(selectedToken)
  const ctx = document.getElementById('priceChart').getContext('2d')

  const chartData = {
    labels: data.timestamps.map((ts) =>
      new Date(ts * 1000).toLocaleTimeString(),
    ),
    datasets: [
      {
        label: `Token ${selectedToken} / USDC`,
        data: data.prices,
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
        fill: false,
      },
    ],
  }

  if (chart) {
    chart.data.labels = chartData.labels
    chart.data.datasets[0].data = data.prices
    chart.update()
  } else {
    chart = new Chart(ctx, {
      type: 'line',
      data: chartData,
    })
  }
}

function updateChart() {
  const tokenSelect = document.getElementById('token-select')
  selectedToken = tokenSelect.value
  if (selectedToken) {
    renderChart()
  }
}

function startAutoUpdate() {
  loadTokens()
  renderChart()
  setInterval(() => {
    if (selectedToken) {
      renderChart()
    }
  }, 5000)
}

document.addEventListener('DOMContentLoaded', function () {
  startAutoUpdate()
})
