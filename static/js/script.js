let currentData = null;

async function uploadData() {
    const fileInput = document.getElementById('file_input');
    if (!fileInput.files[0]) {
        alert('Please select a CSV file first');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch('/upload_dataset', { 
            method: 'POST', 
            body: formData 
        });
        
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.message || 'Upload failed');
        }

        if (data.status === 'success') {
            const sel = document.getElementById('prod');
            sel.innerHTML = '';
            
            data.products.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p;
                opt.textContent = p === 'ALL_PRODUCTS' ? 'All Products (Combined)' : p;
                sel.appendChild(opt);
            });
            
            document.getElementById('params').classList.remove('hidden');
            alert(`[OK] Success! Loaded ${data.records.toLocaleString()} records with ${data.products.length - 1} products.`);
        } else {
            throw new Error(data.message || 'Unknown error');
        }
    } catch (err) {
        console.error('Upload error:', err);
        alert('[X] Error uploading file: ' + err.message);
    }
}

async function runSim() {
    const prod = document.getElementById('prod').value;
    const growth = document.getElementById('growth').value;
    const hCost = document.getElementById('h_cost').value;
    const oCost = document.getElementById('o_cost').value;

    if (!prod) {
        alert('Please select a product');
        return;
    }

    const formData = new FormData();
    formData.append('product_id', prod);
    formData.append('growth_rate', growth);
    formData.append('holding_pct', hCost);
    formData.append('ordering_cost', oCost);

    const btn = document.querySelector('.btn-run');
    const originalText = btn.textContent;
    
    try {
        document.getElementById('output').classList.add('hidden');
        btn.textContent = '[WAIT] RUNNING ANALYSIS...';
        btn.disabled = true;
        
        const res = await fetch('/run_analysis', { 
            method: 'POST', 
            body: formData 
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.message || 'Analysis failed');
        }
        
        if (data.status === 'error') {
            throw new Error(data.message);
        }

        currentData = data;
        
        document.getElementById('output').classList.remove('hidden');
        document.getElementById('report_html').innerHTML = currentData.html_report;

        renderAllCharts(currentData);
        
        document.getElementById('output').scrollIntoView({ behavior: 'smooth' });
        
    } catch (err) {
        console.error('Analysis error:', err);
        alert('[X] Error running analysis: ' + err.message);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

function renderAllCharts(data) {
    // Destroy existing charts
    if (window.Chart && window.Chart.instances) {
        Chart.helpers.each(Chart.instances, (instance) => {
            instance.destroy();
        });
    }

    renderForecastChart(data);
    renderChannelAllocation(data);
    renderProfitWaterfall(data);
    renderInventoryCosts(data);
}

function renderForecastChart(data) {
    const ctx = document.getElementById('fcChart');
    if (!ctx) return;

    const models = Object.keys(data.forecast.errors);
    const errors = Object.values(data.forecast.errors);
    const winner = data.forecast.winner;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: models,
            datasets: [{
                label: 'Forecast Error (SMAPE %)',
                data: errors,
                backgroundColor: models.map(m => m === winner ? '#16a34a' : '#94a3b8'),
                borderColor: models.map(m => m === winner ? '#15803d' : '#64748b'),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                title: {
                    display: true,
                    text: `Winner: ${winner} Model`,
                    font: { size: 14, weight: 'bold' },
                    color: '#16a34a'
                },
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `Error: ${ctx.parsed.y.toFixed(2)}%`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Error %' }
                }
            }
        }
    });

    addCaption(ctx, `<strong>Forecast Tournament:</strong> Compared Prophet, XGBoost, and ARIMA models on 60-day validation set. ${winner} achieved lowest SMAPE error (${errors[models.indexOf(winner)].toFixed(2)}%) and was selected for 2025 demand projection.`);
}

function renderChannelAllocation(data) {
    const ctx = document.getElementById('allocChart');
    if (!ctx) return;

    const allocation = data.scenarios.optimized.allocation;
    const channels = Object.keys(allocation);
    const volumes = Object.values(allocation);

    const colors = {
        'Amazon': '#FF9900',
        'Flipkart': '#2874F0',
        'Own_Website': '#8B5CF6'
    };

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: channels,
            datasets: [{
                data: volumes,
                backgroundColor: channels.map(ch => colors[ch] || '#94a3b8'),
                borderColor: '#ffffff',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                title: {
                    display: true,
                    text: 'Optimized Channel Mix (2025)',
                    font: { size: 14, weight: 'bold' }
                },
                legend: {
                    position: 'bottom',
                    labels: { padding: 12, font: { size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const label = ctx.label || '';
                            const value = ctx.parsed || 0;
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value.toLocaleString()} units (${pct}%)`;
                        }
                    }
                }
            }
        }
    });

    addCaption(ctx, `<strong>Strategic Allocation:</strong> Linear programming optimized inventory distribution across channels. Minimum 18% to Direct-to-Consumer builds brand equity (Rs.${(volumes[channels.indexOf('Own_Website')] * 450).toLocaleString()} 3-year LTV) while maintaining marketplace presence for volume.`);
}

function renderProfitWaterfall(data) {
    const ctx = document.getElementById('waterfallChart');
    if (!ctx) return;

    // FIXED: Use correct data paths
    const historical = data.historical.totals[0];  // hist_profit is at index 0
    const histLost = data.historical.totals[1];     // hist_lost is at index 1
    const optimized = data.scenarios.optimized.profit;
    
    const histMetrics = data.historical.channel_metrics;  // FIXED: correct path
    const optMetrics = data.scenarios.optimized.financials;
    
    console.log('[DEBUG] Waterfall Data:', {
        historical,
        histLost,
        optimized,
        histMetrics,
        optMetrics
    });
    
    let histLogistics = 0, optLogistics = 0;
    let histMarketing = 0, optMarketing = 0;
    let histFees = 0, optFees = 0;
    let histRevenue = 0, optRevenue = 0;
    
    // Calculate historical totals
    for (let ch in histMetrics) {
        histLogistics += histMetrics[ch].Logistics || 0;
        histMarketing += histMetrics[ch].Marketing || 0;
        histFees += histMetrics[ch].Fees || 0;
        histRevenue += histMetrics[ch].Revenue || 0;
    }
    
    // Calculate optimized totals
    for (let ch in optMetrics) {
        optLogistics += optMetrics[ch].Logistics || 0;
        optMarketing += optMetrics[ch].Marketing || 0;
        optFees += optMetrics[ch].Fees || 0;
        optRevenue += optMetrics[ch].Revenue || 0;
    }
    
    // Calculate savings (positive = cost reduction = profit increase)
    const logisticsSavings = histLogistics - optLogistics;
    const marketingSavings = histMarketing - optMarketing;
    const feeSavings = histFees - optFees;
    const revIncrease = optRevenue - histRevenue;
    const opportunityCapture = histLost * 0.3; // 30% margin on captured lost sales
    
    console.log('[DEBUG] Savings Breakdown:', {
        logisticsSavings,
        marketingSavings,
        feeSavings,
        revIncrease,
        opportunityCapture
    });
    
    // Waterfall categories
    const categories = [
        'Historical\nProfit',
        'Logistics\nSavings',
        'Marketing\nEfficiency',
        'Fee\nNegotiation',
        'Inventory\nOptimization',
        'Optimized\nProfit'
    ];
    
    // Build waterfall: start with historical, add each improvement
    let cumulative = historical;
    const chartData = [];
    const colors = [];
    
    // 1. Historical baseline (gray)
    chartData.push({ x: categories[0], y: [0, historical] });
    colors.push('#94a3b8');
    
    // 2. Logistics savings (green if positive)
    const afterLogistics = cumulative + logisticsSavings;
    chartData.push({ x: categories[1], y: [cumulative, afterLogistics] });
    colors.push(logisticsSavings > 0 ? '#16a34a' : '#dc2626');
    cumulative = afterLogistics;
    
    // 3. Marketing savings (green if positive)
    const afterMarketing = cumulative + marketingSavings;
    chartData.push({ x: categories[2], y: [cumulative, afterMarketing] });
    colors.push(marketingSavings > 0 ? '#16a34a' : '#dc2626');
    cumulative = afterMarketing;
    
    // 4. Fee savings (green if positive)
    const afterFees = cumulative + feeSavings;
    chartData.push({ x: categories[3], y: [cumulative, afterFees] });
    colors.push(feeSavings > 0 ? '#16a34a' : '#dc2626');
    cumulative = afterFees;
    
    // 5. Inventory optimization (green)
    const afterInventory = cumulative + opportunityCapture;
    chartData.push({ x: categories[4], y: [cumulative, afterInventory] });
    colors.push('#16a34a');
    cumulative = afterInventory;
    
    // 6. Final optimized (purple)
    chartData.push({ x: categories[5], y: [0, optimized] });
    colors.push('#8B5CF6');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Profit Flow',
                data: chartData,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 2,
                parsing: {
                    yAxisKey: 'y'
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                title: {
                    display: true,
                    text: 'Profit Transformation Waterfall',
                    font: { size: 14, weight: 'bold' }
                },
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const dataPoint = ctx.raw;
                            if (Array.isArray(dataPoint.y)) {
                                const start = dataPoint.y[0];
                                const end = dataPoint.y[1];
                                const delta = end - start;
                                return [
                                    `From: ₹${start.toLocaleString()}`,
                                    `To: ₹${end.toLocaleString()}`,
                                    `Change: ${delta >= 0 ? '+' : ''}₹${delta.toLocaleString()}`
                                ];
                            }
                            return `₹${dataPoint.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: (val) => {
                            if (val >= 1000000) {
                                return '₹' + (val / 1000000).toFixed(1) + 'M';
                            } else if (val >= 1000) {
                                return '₹' + (val / 1000).toFixed(0) + 'K';
                            }
                            return '₹' + val.toLocaleString();
                        }
                    },
                    title: { display: true, text: 'Cumulative Profit (₹)' }
                }
            }
        }
    });

    const totalGain = optimized - historical;
    const gainPct = ((totalGain / Math.abs(historical)) * 100).toFixed(1);
    const gainColor = totalGain >= 0 ? 'green' : 'red';
    
    addCaption(ctx, `<strong>Value Creation Path:</strong> Starting from historical profit of ₹${(historical/1000000).toFixed(1)}M, we achieve ₹${(optimized/1000000).toFixed(1)}M through: Logistics savings (₹${(logisticsSavings/1000000).toFixed(1)}M), Marketing efficiency (₹${(marketingSavings/1000000).toFixed(1)}M), Fee negotiation (₹${(feeSavings/1000000).toFixed(1)}M), and Inventory optimization (₹${(opportunityCapture/1000000).toFixed(1)}M). <span style="color: ${gainColor}; font-weight: bold;">Total: ${totalGain >= 0 ? '+' : ''}₹${(totalGain/1000000).toFixed(1)}M (${gainPct}%)</span>`);
}

function renderInventoryCosts(data) {
    const ctx = document.getElementById('invChart');
    if (!ctx) return;

    const qPlan = data.inventory.quarterly_plan;
    
    const quarters = qPlan.map(q => q.Quarter);
    const capitals = qPlan.map(q => q.Capital);
    const demands = qPlan.map(q => q.Demand);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: quarters,
            datasets: [{
                label: 'Capital Required (₹)',
                data: capitals,
                backgroundColor: '#8B5CF6',
                borderColor: '#7c3aed',
                borderWidth: 2,
                yAxisID: 'y'
            }, {
                label: 'Demand Forecast',
                data: demands,
                type: 'line',
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                borderWidth: 3,
                tension: 0.4,
                yAxisID: 'y1',
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                title: {
                    display: true,
                    text: 'Quarterly Inventory Investment Plan',
                    font: { size: 14, weight: 'bold' }
                },
                legend: {
                    position: 'top',
                    labels: { padding: 10, font: { size: 11 } }
                },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            if (ctx.dataset.label.includes('Capital')) {
                                return `Capital: ₹${ctx.parsed.y.toLocaleString()}`;
                            } else {
                                return `Demand: ${ctx.parsed.y.toLocaleString()} units`;
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Capital (₹)' },
                    ticks: {
                        callback: (val) => '₹' + (val / 1000000).toFixed(1) + 'M'
                    }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Units' },
                    grid: { drawOnChartArea: false },
                    ticks: {
                        callback: (val) => (val / 1000).toFixed(0) + 'K'
                    }
                }
            }
        }
    });

    const totalCapital = capitals.reduce((a, b) => a + b, 0);
    const peakQuarter = qPlan[3];
    addCaption(ctx, `<strong>EOQ-Based Planning:</strong> Order ${data.inventory.EOQ.toLocaleString()} units per batch. Q4 peak requires ${peakQuarter.Batches} batches (₹${(peakQuarter.Capital/1000000).toFixed(1)}M capital) to meet festive demand surge. Total annual inventory investment: ₹${(totalCapital/1000000).toFixed(1)}M.`);
}

function addCaption(ctx, html) {
    const parent = ctx.parentElement;
    const existing = parent.querySelector('.chart-caption');
    if (existing) existing.remove();
    
    const caption = document.createElement('p');
    caption.className = 'chart-caption';
    caption.innerHTML = html;
    parent.appendChild(caption);
}