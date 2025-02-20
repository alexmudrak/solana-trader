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
async function fetchOrders(token) {
    const response = await fetch(`/api/v1/tokens/orders/${token}`)
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
                            unit: 'hour',
                            displayFormats: {
                                hour: 'H:mm:ss',
                            },
                        },
                        ticks: {
                            maxTicksLimit: 24,
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
    const priceInput = document.getElementById('current-price-value')

    priceInput.value = currentPrice

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
    buyButton.disabled = false
}
function updateChart() {
    const tokenSelect = document.getElementById('token-select')
    selectedToken = tokenSelect.value
    if (selectedToken) {
        renderChart()
        randerTable()
        document.getElementById('buy-button').disabled = false
    } else {
        document.getElementById('priceChart').style.display = 'none'
        document.getElementById('price-container').style.display = 'none'
        document.getElementById('buttons-container').style.display = 'none'
        document.getElementById('buy-button').disabled = true
    }
}

async function randerTable() {
    if (!selectedToken) {
        console.warn('No token selected')
        return
    }
    const data = await fetchOrders(selectedToken)

    const tbody = document.getElementById('data-body')
    tbody.innerHTML = ''
    data.forEach((row) => {
        const tr = document.createElement('tr')
        let actionCell
        if (row.action === 'BUY') {
            actionCell = `
                <td class="border-b px-4 py-2">

                    <button class="w-1/2 px-4 py-2 ml-1 bg-red-500 text-white font-semibold rounded hover:bg-red-600 transition">SELL</button>
                </td>
            `
        } else {
            actionCell = `<td class="border-b px-4 py-2">CLOSE</td>`
        }
        tr.innerHTML = `
            <td class="border-b px-4 py-2">${row.date}</td>
            <td class="border-b px-4 py-2">${row.token}</td>
            <td class="border-b px-4 py-2">${row.count}</td>
            <td class="border-b px-4 py-2">${row.price}</td>
            ${actionCell}
        `
        tbody.appendChild(tr)
    })
}

function startAutoUpdate() {
    loadTokens()
    setInterval(() => {
        if (selectedToken) {
            renderChart()
            randerTable()
        }
    }, 5000)
}

document.addEventListener('DOMContentLoaded', function() {
    startAutoUpdate()
})
