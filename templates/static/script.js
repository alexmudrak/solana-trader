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
    const orders_data = await fetchOrders(selectedToken)

    const currentPrice = data.prices[data.prices.length - 1]
    const ctx = document.getElementById('priceChart').getContext('2d')

    updatePriceDisplay(currentPrice)
    const availableDates = new Set(data.created.map((date) => date.slice(0, 16)))
    const buyDataset = orders_data
        .map((row) => {
            const pricePerCount = row.price / row.count
            const dateWithoutSeconds = row.created.slice(0, 16)
            return availableDates.has(dateWithoutSeconds)
                ? { x: row.created, y: pricePerCount }
                : null
        })
        .filter((item) => item !== null)

    const sellDataset = [].concat(
        ...orders_data.map((row) =>
            row.sells
                .map((sell) => {
                    const pricePerAmount = sell.price / sell.amount
                    console.log(sell)
                    const dateWithoutSeconds = sell.created.slice(0, 16)
                    return availableDates.has(dateWithoutSeconds)
                        ? { x: sell.created, y: pricePerAmount }
                        : null
                })
                .filter((item) => item !== null),
        ),
    )

    const chartData = {
        labels: data.created,
        datasets: [
            {
                label: `Token ${selectedToken} / USDC`,
                data: data.prices,
                order: 2,
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1,
                radius: 0,
                fill: false,
            },
            {
                label: `BUY Token ${selectedToken} / USDC`,
                type: 'bubble',
                order: 1,
                data: buyDataset,
                borderColor: 'rgba(255, 1, 1, 1)',
                borderWidth: 1,
                pointStyle: 'triangle',
                pointRotation: 180,
                pointRadius: 10,
                pointBorderColor: 'rgba(255, 1, 1, 1)',
                fill: false,
            },
            {
                label: `SELL Token ${selectedToken} / USDC`,
                type: 'bubble',
                order: 1,
                data: sellDataset,
                borderColor: 'rgba(0, 0, 255, 1)',
                borderWidth: 1,
                pointStyle: 'triangle',
                pointRadius: 10,
                pointBorderColor: 'rgba(0, 0, 255, 1)',
                fill: false,
            },
        ],
    }

    if (chart) {
        chart.data.labels = chartData.labels
        chart.data.datasets[0].data = data.prices
        chart.data.datasets[1].data = buyDataset
        chart.data.datasets[2].data = sellDataset
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
                                minute: 'H:mm:ss',
                            },
                        },
                        ticks: {
                            maxTicksLimit: 10,
                        },
                    },
                },
            },
        })
    }

    document.getElementById('priceChart').style.display = 'block'
    document.getElementById('price-container').style.display = 'block'
    document.getElementById('buttons-container').style.display = 'flex'

    await randerTable(currentPrice, orders_data)
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
        document.getElementById('buy-button').disabled = false
    } else {
        document.getElementById('priceChart').style.display = 'none'
        document.getElementById('price-container').style.display = 'none'
        document.getElementById('buttons-container').style.display = 'none'
        document.getElementById('buy-button').disabled = true
    }
}

async function randerTable(currentPrice, orders_data) {
    if (!selectedToken) {
        console.warn('No token selected')
        return
    }
    const tbody = document.getElementById('data-body')
    tbody.innerHTML = ''

    let totalProfit = 0

    orders_data.forEach((row) => {
        const tr = document.createElement('tr')
        const sellButton =
            row.sells.length === 0
                ? `<button class="bg-red-500 text-white px-2 py-1 rounded"
            hx-post="/api/v1/tokens/sell"
            hx-ext='json-enc'
            hx-include="#order-id-${row.id}, #amount-id-${row.id}, #token-select, #current-price-value"
            hx-target="#message">SELL</button>`
                : 'CLOSED'
        const lastSellPrice =
            row.sells.length > 0 ? row.sells[row.sells.length - 1].price : 0

        const profit =
            row.sells.length > 0
                ? lastSellPrice - row.price
                : row.count * currentPrice - row.price

        totalProfit += profit

        tr.innerHTML = `
            <td class="border-b px-4 py-2">${row.created}</td>
            <td class="border-b px-4 py-2">${row.token}</td>
            <td class="border-b px-4 py-2">
                        <div style="display: flex; justify-content: space-between; align-items: flex-end;">
            <span>${row.count}</span>
            <div style="font-size: 0.8em; line-height: 1; text-align: right;">
                <div>${(row.price / row.count).toFixed(2)}</div>
                <div>${(lastSellPrice / row.count).toFixed(2)}</div>
            </div>
        </div>
            </td>

            <td class="border-b px-4 py-2">${row.price.toFixed(2)}</td>
            <td class="border-b px-4 py-2">${profit.toFixed(2)}</</td >
            <td class="border-b px-4 py-2">${sellButton}
                <input type="hidden" id="order-id-${row.id}" name="order-id" value="${row.id}" />
                <input type="hidden" id="amount-id-${row.id}" name="amount" value="${row.count}" />
            </td>
        `
        tbody.appendChild(tr)
        htmx.process(tbody)
    })
    const profitDisplay = document.getElementById('total-profit')
    profitDisplay.textContent = `Total Profit: $${totalProfit.toFixed(2)}`
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
