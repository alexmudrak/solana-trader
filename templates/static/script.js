let chart = null
let selectedToken = null
let previousPrice = null
let currentPrice = null

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
    if (!selectedToken) {
        console.warn('No token selected')
        return
    }
    const data = await fetchPrices(selectedToken)

    const currentPrice = data.prices[data.prices.length - 1]
    const ctx = document.getElementById('priceChart').getContext('2d')

    updatePriceDisplay(currentPrice)

    const chartData = {
        labels: data.created,
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
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute',
                            displayFormats: {
                                minute: 'H:mm:ss'
                                }
                        },
                    },
                },
            },
        })
    }

    document.getElementById('priceChart').style.display = 'block'
    document.getElementById('price-container').style.display = 'block'
    document.getElementById('buttons-container').style.display = 'flex'
}
function updatePriceDisplay(currentPrice) {
    const priceDisplay = document.getElementById('current-price')

    const formattedCurrentPrice = currentPrice.toFixed(2)

    if (previousPrice !== null) {
        const difference = currentPrice - previousPrice
        const formattedDifference = difference.toFixed(2)

        if (difference > 0) {
            priceDisplay.innerHTML = `<span class="text-green-500">${formattedCurrentPrice} (+${formattedDifference})</span>`
        } else {
            priceDisplay.innerHTML = `<span class="text-red-500">${formattedCurrentPrice} (${formattedDifference})</span>`
        }
    } else {
        priceDisplay.innerHTML = `${formattedCurrentPrice}`
    }

    previousPrice = currentPrice

    const buyButton = document.getElementById('buy-button')
    const sellButton = document.getElementById('sell-button')
    buyButton.disabled = false
    sellButton.disabled = false
}
function updateChart() {
    const tokenSelect = document.getElementById('token-select')
    selectedToken = tokenSelect.value
    if (selectedToken) {
        renderChart()
        document.getElementById('buy-button').disabled = false
        document.getElementById('sell-button').disabled = false
    } else {
        document.getElementById('priceChart').style.display = 'none'
        document.getElementById('price-container').style.display = 'none'
        document.getElementById('buttons-container').style.display = 'none'
        document.getElementById('buy-button').disabled = true
        document.getElementById('sell-button').disabled = true
    }
}

function startAutoUpdate() {
    loadTokens()
    setInterval(() => {
        if (selectedToken) {
            renderChart()
        }
    }, 5000)
}

document.addEventListener('DOMContentLoaded', function() {
    startAutoUpdate()
})
