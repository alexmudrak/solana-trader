const API_BASE_URL = '/api/v1'
const TOKENS_ENDPOINT = `${API_BASE_URL}/tokens`
const PRICES_ENDPOINT = `${API_BASE_URL}/prices`
const ORDERS_ENDPOINT = `${API_BASE_URL}/orders`
const PAIRS_API_ENDPOINT = `${API_BASE_URL}/pairs`
const SETTINGS_ENDPOINT = `${PAIRS_API_ENDPOINT}/settings`

let chart = null
let selectedToken = null
let previousPrice = null
let currentPrice = null
let tradingSettings = {}

async function loadTokens() {
    const response = await fetch(`${PAIRS_API_ENDPOINT}`)
    const data = await response.json()
    const tokenSelect = document.getElementById('token-select')

    data.forEach((pair) => {
        const option = document.createElement('option')
        option.value = pair.id
        option.textContent = `${pair.from_token.name} -> ${pair.to_token.name}`
        tokenSelect.appendChild(option)
        tradingSettings[pair.id] = pair.trading_setting
    })
}

async function fetchPrices(token_id) {
    const response = await fetch(`${PRICES_ENDPOINT}/${token_id}`)
    if (response.status !== 200) {
        return []
    }
    return await response.json()
}
async function fetchOrders(token_id) {
    const response = await fetch(`${ORDERS_ENDPOINT}/${token_id}`)
    if (response.status !== 200) {
        return []
    }
    return await response.json()
}
async function renderChart() {
    if (!selectedToken) {
        console.warn('No token selected')
        return
    }
    await loadTokens()
    const data = await fetchPrices(selectedToken)
    const orders_data = await fetchOrders(selectedToken)

    const currentPrice = data.prices[data.prices.length - 1]
    const ctx = document.getElementById('priceChart').getContext('2d')

    updatePriceDisplay(currentPrice)
    const availableDates = new Set(data.created.map((date) => date.slice(0, 16)))
    const buyDataset = orders_data
        .map((row) => {
            const pricePerCount = row.price / row.amount
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
                pointRotation: 180,
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
                                minute: 'H:mm',
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

    await renderPairSettings()
    await renderTable(currentPrice, orders_data)
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
    if (selectedToken === 'create-new-trader') {
        window.location.href = '/create-trader'
    } else if (selectedToken) {
        renderChart()
        document.getElementById('buy-button').disabled = false
    } else {
        document.getElementById('priceChart').style.display = 'none'
        document.getElementById('price-container').style.display = 'none'
        document.getElementById('buttons-container').style.display = 'none'
        document.getElementById('buy-button').disabled = true
    }
}

async function renderTable(currentPrice, orders_data) {
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
            hx-post="${ORDERS_ENDPOINT}/sell"
            hx-ext='json-enc'
            hx-include="#order-id-${row.id}, #amount-id-${row.id}, #token-select, #current-price-value"
            hx-target="#message">SELL</button>`
                : 'CLOSED'
        const lastSellPrice =
            row.sells.length > 0 ? row.sells[row.sells.length - 1].price : 0

        const profit =
            row.sells.length > 0
                ? lastSellPrice - row.price
                : row.amount * currentPrice - row.price

        totalProfit += profit

        tr.innerHTML = `
            <td class="border-b px-4 py-2">${new Date(row.created).toLocaleString()}</td>
            <td class="border-b px-4 py-2">${row.token}</td>
            <td class="border-b px-4 py-2">
                        <div style="display: flex; justify-content: space-between; align-items: flex-end;">
            <span>${row.amount}</span>
            <div style="font-size: 0.8em; line-height: 1; text-align: right;">
                <div>${(row.price / row.amount).toFixed(2)}</div>
                <div>${(lastSellPrice / row.amount).toFixed(2)}</div>
            </div>
        </div>
            </td>

            <td class="border-b px-4 py-2">${row.price.toFixed(2)}</td>
            <td class="border-b px-4 py-2">${profit.toFixed(2)}</</td >
            <td class="border-b px-4 py-2">${sellButton}
                <input type="hidden" id="order-id-${row.id}" name="order_id" value="${row.id}" />
                <input type="hidden" id="amount-id-${row.id}" name="amount" value="${row.amount}" />
            </td>
        `
        tbody.appendChild(tr)
        htmx.process(tbody)
    })
    const profitDisplay = document.getElementById('total-profit')
    profitDisplay.textContent = `Total Profit: $${totalProfit.toFixed(2)}`
}

async function renderPairSettings() {
    if (!selectedToken) {
        console.warn('No token selected')
        return
    }
    const settings = tradingSettings[selectedToken]

    if (settings) {
        document.getElementById('take-profit').value =
            settings.take_profit_percentage
        document.getElementById('stop-loss').value = settings.stop_loss_percentage
        document.getElementById('short-ema').value = settings.short_ema_time_period
        document.getElementById('long-ema').value = settings.long_ema_time_period
        document.getElementById('rsi-buy').value = settings.rsi_buy_threshold
        document.getElementById('rsi-sell').value = settings.rsi_sell_threshold
        document.getElementById('rsi-period').value = settings.rsi_time_period
        document.getElementById('buy-amount').value = settings.buy_amount
        document.getElementById('max-orders').value =
            settings.buy_max_orders_threshold
        const form = document.getElementById('settings-form')
        if (form) {
            form.setAttribute('hx-patch', `${SETTINGS_ENDPOINT}/${settings.id}`)
            htmx.process(form)
        }
    } else {
        console.warn('No trading settings found for Token ID:', tokenId)
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
document.addEventListener('DOMContentLoaded', () => {
    const collapsibleButton = document.querySelector('.collapsible')
    const content = document.querySelector('.content')

    collapsibleButton.addEventListener('click', () => {
        if (content.style.display === 'block') {
            content.style.display = 'none'
        } else {
            content.style.display = 'block'
        }
    })
})
