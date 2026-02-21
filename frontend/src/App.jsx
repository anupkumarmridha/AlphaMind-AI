import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Doughnut, Radar } from 'react-chartjs-2';
import './index.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

function App() {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const [data, setData] = useState({
    equityCurve: [],
    labels: [],
    metrics: {
      winRate: 0,
      profitFactor: 0,
      totalReturn: 0,
      maxDrawdown: 0,
      sharpeRatio: 0,
      alpha: 0
    },
    trades: [],
    logs: [],
    agentWeights: []
  });
  const [shareStatus, setShareStatus] = useState(null);

  useEffect(() => {
    // Generate mock data representing the AlphaMind AI paper trading backend
    const labels = Array.from({ length: 30 }, (_, i) => `Day ${i + 1}`);
    let equity = 10000;
    const equityCurve = [equity];

    for (let i = 1; i < 30; i++) {
      const change = (Math.random() - 0.45) * 500; // Slight upward bias
      equity += change;
      equityCurve.push(equity);
    }

    const mockTrades = [
      { id: 1, symbol: 'NVDA', action: 'BUY', profit: 4.2, time: '10:30 AM', entry: 120.45, confidence: 0.88, reason: "Strong EMA cross and bullish AI sector news.", holding: '1-3 Days', target: 128.50, stopLoss: 116.00, exitPrice: 125.51, hitTarget: true },
      { id: 2, symbol: 'AAPL', action: 'SELL', profit: -1.5, time: '11:15 AM', entry: 185.20, confidence: 0.65, reason: "RSI overbought (78), negative sentiment in supply chain.", holding: '1 Day', target: 178.00, stopLoss: 188.50, exitPrice: 187.98, hitTarget: false },
      { id: 3, symbol: 'TSLA', action: 'BUY', profit: 8.4, time: '1:45 PM', entry: 195.10, confidence: 0.72, reason: "Breakout above resistance + positive event impact.", holding: '2-5 Days', target: 212.00, stopLoss: 188.00, exitPrice: 211.49, hitTarget: true },
      { id: 4, symbol: 'MSFT', action: 'BUY', profit: 2.1, time: '2:20 PM', entry: 405.30, confidence: 0.91, reason: "Solid earnings beat, technicals aligned with uptrend.", holding: '1-2 Days', target: 415.00, stopLoss: 400.00, exitPrice: 413.81, hitTarget: true },
      { id: 5, symbol: 'AMD', action: 'SELL', profit: 0.5, time: '3:10 PM', entry: 160.80, confidence: 0.58, reason: "Risk agent hard veto due to extreme localized volatility.", holding: '1 Day', target: 154.00, stopLoss: 163.00, exitPrice: 159.99, hitTarget: false },
    ];

    const mockLogs = [
      { id: 101, timestamp: '10:28:45 AM', agent: '⚙️ Technical', level: 'INFO', type: 'Analysis', message: 'EMA(9,21) bullish cross confirmed on NVDA.', detail: 'RSI: 58 (neutral) · MACD: +0.42 · Price above 21 EMA · Trend: BULLISH' },
      { id: 102, timestamp: '10:29:12 AM', agent: '📰 Event', level: 'SIGNAL', type: 'Sentiment', message: '5 news articles analyzed — high impact detected.', detail: 'NVDA AI sector headlines: +0.82 sentiment score · Event weight raised to 0.3' },
      { id: 103, timestamp: '10:29:55 AM', agent: '🛡️ Risk', level: 'CLEAR', type: 'Veto Check', message: 'Risk check PASSED. Hard Veto: FALSE.', detail: 'VIX: 14.2 (low) · Beta: 1.12 · Position size: 5% (within limit)' },
      { id: 104, timestamp: '10:30:10 AM', agent: '🧠 Fusion', level: 'DECISION', type: 'Trade', message: 'Final Decision: BUY NVDA @ $120.45', detail: 'Tech: 0.5 · Event: 0.3 · Risk: 0.2 · Confidence: 88% · Target: $128.50 · SL: $116.00' },
      { id: 105, timestamp: '11:10:05 AM', agent: '⚙️ Technical', level: 'WARN', type: 'Analysis', message: 'AAPL RSI at 78 — overbought territory.', detail: 'MACD histogram shrinking · Bearish divergence forming · Price near upper Bollinger band' },
      { id: 106, timestamp: '11:12:30 AM', agent: '📰 Event', level: 'SIGNAL', type: 'Sentiment', message: 'Negative sentiment extracted from AAPL supply chain.', detail: 'Sentiment score: -0.61 · Source: Reuters, Bloomberg · Impact: HIGH' },
      { id: 107, timestamp: '11:15:00 AM', agent: '🧠 Fusion', level: 'DECISION', type: 'Trade', message: 'Final Decision: SELL AAPL @ $185.20', detail: 'Tech: 0.4 · Event: 0.45 · Risk: 0.15 · Confidence: 65% · Target: $178.00 · SL: $188.50' },
      { id: 108, timestamp: '01:40:22 PM', agent: '🛡️ Risk', level: 'WARN', type: 'Veto Check', message: 'TSLA volatility spiking — HIGH risk detected.', detail: 'TSLA 1-hr vol > 2.5σ · Position cap enforced: 2.5% max · Veto: FALSE (reduced size)' },
      { id: 109, timestamp: '01:45:10 PM', agent: '🧠 Fusion', level: 'DECISION', type: 'Trade', message: 'BUY TSLA @ $195.10 — position halved by Risk override.', detail: 'Normal size 5% → 2.5% · Confidence: 72% · Target: $212.00 · SL: $188.00' },
      { id: 110, timestamp: '03:08:45 PM', agent: '🛡️ Risk', level: 'CRITICAL', type: 'Veto', message: 'CRITICAL: AMD volatility > 3 std devs. Hard Veto issued.', detail: 'AMD realized vol: 3.2σ spike · Veto threshold breached · Trade BLOCKED' },
      { id: 111, timestamp: '03:09:50 PM', agent: '🧠 Fusion', level: 'VETO', type: 'Trade', message: 'HARD VETO received. Pending AMD trade CANCELED.', detail: 'Risk Agent override accepted · No position opened · Capital preserved' },
    ];

    const mockAgentWeights = Array.from({ length: 30 }, () => {
      // Simulate regime changes. Mostly it's tech heavy, but sometimes event takes over (earnings)
      // or risk takes over (volatility spikes)
      const regime = Math.random();
      if (regime > 0.8) return { tech: 0.2, event: 0.7, risk: 0.1 }; // Event Driven
      if (regime < 0.2) return { tech: 0.3, event: 0.2, risk: 0.5 }; // Risk Off
      return { tech: 0.6, event: 0.2, risk: 0.2 }; // Normal Technical
    });

    setData({
      equityCurve,
      labels,
      metrics: {
        winRate: 64.2,
        profitFactor: 1.85,
        totalReturn: ((equity - 10000) / 10000) * 100,
        maxDrawdown: -4.2,
        sharpeRatio: 2.14,
        alpha: 8.5
      },
      trades: mockTrades,
      logs: mockLogs,
      agentWeights: mockAgentWeights,
      learnings: [
        { topic: 'Macro Environment', insight: 'VIX is suppressed (14.2). The Fusion Engine has reduced Risk Agent veto power by 15% to capitalize on the low-volatility bullish trend.' },
        { topic: 'Sector Rotation', insight: 'Semiconductor momentum is slowing. The Learning Engine has flagged NVDA and AMD for potential mean-reversion pullbacks in the next 48 hours.' },
        { topic: 'Event Impact', insight: 'Recent supply chain rumors heavily impacted AAPL. The Event Agent is currently overweighting sentiment data for consumer electronics by 1.5x.' },
        { topic: 'Risk Sizing', insight: 'Due to consecutive winning trades, the portfolio beta is sitting at 1.15. Position sizing for the next 3 trades will be hard-capped at 3% to preserve capital.' }
      ]
    });
  }, []);

  const trackEvent = async (name, payload = {}) => {
    const event = { name, payload, timestamp: new Date().toISOString() };
    console.log('[analytics]', event);
    try {
      await fetch(`${API_BASE_URL}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(event),
      });
    } catch (error) {
      // Swallow errors to avoid blocking UI on analytics.
    }
  };

  const buildShareText = () => {
    const topTrade = [...data.trades].sort((a, b) => b.profit - a.profit)[0];
    const totalReturn = data.metrics.totalReturn >= 0 ? `+${data.metrics.totalReturn.toFixed(2)}%` : `${data.metrics.totalReturn.toFixed(2)}%`;
    const winRate = `${data.metrics.winRate.toFixed(1)}%`;
    const sharpe = data.metrics.sharpeRatio.toFixed(2);
    const topTradeText = topTrade ? `Top trade: ${topTrade.symbol} ${topTrade.profit > 0 ? '+' : ''}${topTrade.profit}%` : 'Top trade: N/A';
    return `AlphaMind AI snapshot — Total Return ${totalReturn}, Win Rate ${winRate}, Sharpe ${sharpe}. ${topTradeText}`;
  };

  const handleShareClick = async () => {
    const shareText = buildShareText();
    const shareUrl = window.location.href;
    setShareStatus(null);
    trackEvent('share_clicked', { surface: 'header_cta' });

    if (navigator.share) {
      try {
        await navigator.share({
          title: 'AlphaMind AI Performance Snapshot',
          text: shareText,
          url: shareUrl,
        });
        setShareStatus({ type: 'success', message: 'Snapshot shared.' });
        trackEvent('share_completed', { method: 'web_share' });
        return;
      } catch (error) {
        // Fall back to clipboard if share is cancelled or unsupported.
      }
    }

    try {
      await navigator.clipboard.writeText(`${shareText} ${shareUrl}`);
      setShareStatus({ type: 'success', message: 'Snapshot copied to clipboard.' });
      trackEvent('share_completed', { method: 'clipboard' });
    } catch (error) {
      setShareStatus({ type: 'error', message: 'Unable to share right now.' });
    }
  };

  const chartData = {
    labels: data.labels,
    datasets: [
      {
        fill: true,
        label: 'Portfolio Value ($)',
        data: data.equityCurve,
        borderColor: '#22d3ee',
        backgroundColor: 'rgba(34, 211, 238, 0.1)',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f8fafc',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
      },
    },
    scales: {
      x: {
        display: false,
        grid: { display: false }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8' }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  };

  const trustChartData = {
    labels: data.labels,
    datasets: [
      {
        fill: true,
        label: 'Technical Weight',
        data: data.agentWeights.map(w => w.tech * 100),
        backgroundColor: 'rgba(34, 211, 238, 0.5)',
        borderColor: 'rgba(34, 211, 238, 0.8)',
        borderWidth: 1,
        tension: 0.3,
        pointRadius: 0
      },
      {
        fill: true,
        label: 'Event Weight',
        data: data.agentWeights.map(w => w.event * 100),
        backgroundColor: 'rgba(168, 85, 247, 0.5)',
        borderColor: 'rgba(168, 85, 247, 0.8)',
        borderWidth: 1,
        tension: 0.3,
        pointRadius: 0
      },
      {
        fill: true,
        label: 'Risk Weight',
        data: data.agentWeights.map(w => w.risk * 100),
        backgroundColor: 'rgba(245, 158, 11, 0.5)',
        borderColor: 'rgba(245, 158, 11, 0.8)',
        borderWidth: 1,
        tension: 0.3,
        pointRadius: 0
      }
    ]
  };

  const trustChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        align: 'end',
        labels: { boxWidth: 12, usePointStyle: true, color: '#94a3b8', font: { size: 10 } }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f8fafc',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
      },
    },
    scales: {
      x: { display: false, stacked: true },
      y: { stacked: true, max: 100, display: false }
    },
    interaction: { mode: 'nearest', axis: 'x', intersect: false }
  };

  const barData = {
    labels: data.trades.map(t => t.symbol),
    datasets: [
      {
        label: 'PnL %',
        data: data.trades.map(t => t.profit),
        backgroundColor: data.trades.map(t => t.profit > 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'),
        borderColor: data.trades.map(t => t.profit > 0 ? 'rgba(16, 185, 129, 1)' : 'rgba(239, 68, 68, 1)'),
        borderWidth: 1,
        borderRadius: 4,
      }
    ]
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f8fafc',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
      }
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
      y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#94a3b8', font: { size: 10 } } }
    }
  };

  const wins = data.trades.filter(t => t.profit > 0).length;
  const losses = data.trades.filter(t => t.profit <= 0).length;

  const doughnutData = {
    labels: ['Winning Trades', 'Losing Trades'],
    datasets: [
      {
        data: [wins, losses],
        backgroundColor: ['rgba(16, 185, 129, 0.8)', 'rgba(239, 68, 68, 0.8)'],
        borderColor: ['rgba(16, 185, 129, 1)', 'rgba(239, 68, 68, 1)'],
        borderWidth: 1,
        hoverOffset: 4
      }
    ]
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#e2e8f0', padding: 20, font: { family: 'Inter', size: 11 } }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f8fafc',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
      }
    },
    cutout: '70%',
  };

  const radarData = {
    labels: ['Trend Strength', 'Momentum', 'Event Sentiment', 'Volatility Risk', 'Macro Alignment'],
    datasets: [{
      label: 'Latest Trade Signal Matrix',
      data: [85, 78, 92, 45, 60],
      backgroundColor: 'rgba(34, 211, 238, 0.2)',
      borderColor: 'rgba(34, 211, 238, 1)',
      pointBackgroundColor: 'rgba(34, 211, 238, 1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(34, 211, 238, 1)',
      borderWidth: 1,
    }]
  };

  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        pointLabels: { color: '#94a3b8', font: { size: 9, family: 'Inter' } },
        ticks: { display: false, min: 0, max: 100 }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#f8fafc',
        bodyColor: '#94a3b8',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
      }
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8 flex flex-col max-w-7xl mx-auto w-full">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-br from-slate-50 to-accent-cyan bg-clip-text text-transparent tracking-tight">
            AlphaMind AI
          </h1>
          <p className="text-slate-400 mt-1 text-sm">Autonomous Multi-Agent Trading Intelligence</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleShareClick}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-accent-cyan/20 border border-accent-cyan/40 text-xs font-semibold text-accent-cyan hover:bg-accent-cyan/30 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5 5 5M12 6v12m7 0H5" />
            </svg>
            Share Snapshot
          </button>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700 text-xs font-medium text-slate-300">
            <svg className="w-4 h-4 text-accent-indigo" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Horizon: Swing (1-3 Days)
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-dark-panel border border-dark-border text-sm font-medium text-accent-cyan shadow-md shadow-accent-cyan/10 animate-pulse">
            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
            System Live & Learning
          </div>
        </div>
      </header>
      {shareStatus && (
        <div className={`mb-6 px-4 py-2 rounded-lg border text-xs font-medium ${shareStatus.type === 'success' ? 'border-emerald-400/40 bg-emerald-400/10 text-emerald-300' : 'border-red-400/40 bg-red-400/10 text-red-300'}`}>
          {shareStatus.message}
        </div>
      )}

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="glass-panel flex flex-col min-h-[400px]">
            <h2 className="text-lg font-semibold text-slate-50 mb-4">Performance Curve</h2>
            <div className="flex-1 w-full relative">
              <Line options={chartOptions} data={chartData} />
            </div>
          </div>

          <div className="glass-panel flex flex-col min-h-[200px]">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-lg font-semibold text-slate-50">Dynamic Agent Trust (Fusion Weights)</h2>
              <span className="text-xs text-slate-400">Shows how LangGraph orchestrates decision-making regimes</span>
            </div>
            <div className="flex-1 w-full relative">
              <Line options={trustChartOptions} data={trustChartData} />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel flex flex-col min-h-[300px]">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-sm font-semibold text-slate-50 uppercase tracking-wider">Trade Returns</h2>
              </div>
              <div className="flex-1 w-full relative">
                <Bar options={barOptions} data={barData} />
              </div>
            </div>

            <div className="glass-panel flex flex-col min-h-[300px]">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-sm font-semibold text-slate-50 uppercase tracking-wider">Signal Matrix</h2>
                <span className="text-[10px] text-accent-cyan bg-accent-cyan/10 px-2 py-0.5 rounded border border-accent-cyan/20">Latest Trade</span>
              </div>
              <div className="flex-1 w-full relative">
                <Radar options={radarOptions} data={radarData} />
              </div>
            </div>

            <div className="glass-panel flex flex-col min-h-[300px]">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-sm font-semibold text-slate-50 uppercase tracking-wider">Risk Engine Heatmap</h2>
              </div>
              <div className="flex-1 flex flex-col gap-3">
                <div className="bg-slate-900/40 border border-slate-700/50 rounded-lg p-3 flex justify-between items-center">
                  <div className="flex flex-col">
                    <span className="text-xs font-medium text-slate-400">Market Volatility (VIX)</span>
                    <span className="text-[10px] text-slate-500">Dictates global risk vetoes</span>
                  </div>
                  <span className="text-xs font-bold text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded">14.2 (LOW)</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-700/50 rounded-lg p-3 flex justify-between items-center">
                  <div className="flex flex-col">
                    <span className="text-xs font-medium text-slate-400">Portfolio Beta</span>
                    <span className="text-[10px] text-slate-500">Sensitivity to market swings</span>
                  </div>
                  <span className="text-xs font-bold text-slate-100 bg-slate-700/50 px-2 py-1 rounded">1.15 (NORMAL)</span>
                </div>
                <div className="bg-slate-900/40 border border-amber-500/30 rounded-lg p-3 flex justify-between items-center">
                  <div className="flex flex-col">
                    <span className="text-xs font-medium text-slate-400">Sector Exposure (Tech)</span>
                    <span className="text-[10px] text-slate-500">Concentration risk active</span>
                  </div>
                  <span className="text-xs font-bold text-amber-500 bg-amber-500/10 px-2 py-1 rounded">68% (ELEVATED)</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-700/50 rounded-lg p-3 flex justify-between items-center">
                  <div className="flex flex-col">
                    <span className="text-xs font-medium text-slate-400">Position Sizing</span>
                    <span className="text-[10px] text-slate-500">Auto-adjusted algorithmically</span>
                  </div>
                  <span className="text-xs font-bold text-emerald-400 bg-emerald-400/10 px-2 py-1 rounded">Normal (5%)</span>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-panel">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
              <h2 className="text-lg font-semibold text-slate-50">Active AI Directives & Learnings</h2>
              <span className="text-xs bg-accent-indigo/20 text-accent-indigo border border-accent-indigo/30 px-3 py-1 rounded-full">Self-Explanation Layer</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.learnings?.map((item, index) => (
                <div key={index} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex gap-4 items-start relative overflow-hidden group">
                  <div className="absolute top-0 left-0 w-1 h-full bg-accent-cyan/80"></div>
                  <div className="flex-1">
                    <h3 className="text-sm font-bold text-slate-200 mb-1">{item.topic}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed font-mono">{item.insight}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Agent Accuracy Scoreboard */}
          <div className="glass-panel">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-5 gap-2">
              <div>
                <h2 className="text-base font-semibold text-slate-50">Agent Accuracy Scoreboard</h2>
                <p className="text-[10px] text-slate-500 mt-0.5">How often each agent's signal matched the profitable outcome</p>
              </div>
              <span className="text-xs text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2 py-1 rounded-full">Based on 5 trades</span>
            </div>
            <div className="flex flex-col gap-4">
              {[
                { agent: '⚙️ Technical Agent', acc: 80, trades: 4, role: 'Reads RSI, EMA, MACD & price action', color: 'bg-blue-500' },
                { agent: '📰 Event Agent', acc: 75, trades: 4, role: 'Scores news sentiment & macro events', color: 'bg-purple-500' },
                { agent: '🛡️ Risk Agent', acc: 100, trades: 2, role: 'Vetoes trades when risk thresholds are breached', color: 'bg-amber-500' },
                { agent: '🧠 Fusion Agent', acc: 80, trades: 5, role: 'Synthesizes all agent signals into a final decision', color: 'bg-emerald-500' },
              ].map((a) => (
                <div key={a.agent} className="flex flex-col gap-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-semibold text-slate-200">{a.agent}</span>
                      <p className="text-[10px] text-slate-500">{a.role}</p>
                    </div>
                    <span className="text-xs font-bold text-slate-100 font-mono">{a.acc}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div className={`${a.color} h-2 rounded-full transition-all duration-700`} style={{ width: `${a.acc}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Live Technical Signals */}
          <div className="glass-panel">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-5 gap-2">
              <div>
                <h2 className="text-base font-semibold text-slate-50">Live Technical Signals</h2>
                <p className="text-[10px] text-slate-500 mt-0.5">Real-time indicator readings the Technical Agent is processing, with targets and prediction accuracy</p>
              </div>
              <span className="flex items-center gap-1.5 text-xs text-emerald-400">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>Live
              </span>
            </div>
            <div className="grid grid-cols-1 gap-4">
              {[
                {
                  sym: 'NVDA', price: 120.45, overall: 'BUY', overallColor: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
                  holding: '1-3 Days (Swing)', target: 128.50, stopLoss: 116.00,
                  predictedHits: 7, actualHits: 6, totalSignals: 8,
                  explanation: 'EMA cross confirmed bullish momentum. RSI near neutral suggests room to run. MACD histogram positive.',
                  indicators: [
                    { name: 'RSI(14)', value: '58', label: 'Neutral', color: 'text-slate-300', desc: 'Momentum oscillator. Below 70 = not overbought, room to move up.' },
                    { name: 'MACD', value: 'Bullish Cross', label: '', color: 'text-emerald-400', desc: 'Signal line crossed above zero — short-term trend flipping bullish.' },
                    { name: 'EMA Status', value: 'Above 21 EMA ✓', label: '', color: 'text-emerald-400', desc: 'Price is above its 21-day average — the AI considers this a buy zone.' },
                    { name: 'Bollinger', value: 'Inside Bands', label: '', color: 'text-slate-300', desc: 'Price is within normal volatility range — no extreme stretch risk.' },
                  ]
                },
                {
                  sym: 'AAPL', price: 185.20, overall: 'SELL', overallColor: 'text-red-400 bg-red-400/10 border-red-400/20',
                  holding: '1 Day (Intraday)', target: 178.00, stopLoss: 188.50,
                  predictedHits: 5, actualHits: 3, totalSignals: 6,
                  explanation: 'RSI at 78 is overbought — historically the AI has seen mean reversion here. MACD diverging bearishly. Near upper Bollinger Band.',
                  indicators: [
                    { name: 'RSI(14)', value: '78', label: 'Overbought', color: 'text-red-400', desc: 'Reading above 70 = overbought. The AI sells into strength expecting a pullback.' },
                    { name: 'MACD', value: 'Bearish Diverge', label: '', color: 'text-red-400', desc: 'Histogram shrinking while price rises — momentum divergence signals reversal risk.' },
                    { name: 'EMA Status', value: 'Below 9 EMA ✗', label: '', color: 'text-red-400', desc: 'Price fell beneath the fast 9-day average — early bearish warning.' },
                    { name: 'Bollinger', value: 'Upper Band Hit', label: '', color: 'text-amber-400', desc: 'Price touched the upper band — statistically likely to revert toward the mean.' },
                  ]
                },
                {
                  sym: 'TSLA', price: 195.10, overall: 'BUY', overallColor: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
                  holding: '2-5 Days (Swing)', target: 212.00, stopLoss: 188.00,
                  predictedHits: 9, actualHits: 8, totalSignals: 11,
                  explanation: 'Breakout above key resistance confirmed by expanding Bollinger Bands. MACD bullish. Higher risk due to elevated volatility — position size reduced by Risk Agent.',
                  indicators: [
                    { name: 'RSI(14)', value: '62', label: 'Mild Momentum', color: 'text-amber-400', desc: 'Between 50-70 = momentum building but not extreme. AI treats this as a healthy entry zone.' },
                    { name: 'MACD', value: 'Bullish Cross', label: '', color: 'text-emerald-400', desc: 'Signal line crossed above — short-term bullish bias confirmed.' },
                    { name: 'EMA Status', value: 'Above 21 EMA ✓', label: '', color: 'text-emerald-400', desc: 'Holding above 21-day average post-breakout — trend is intact.' },
                    { name: 'Bollinger', value: 'Expanding', label: '', color: 'text-amber-400', desc: 'Bands widening = volatility increasing. Good for momentum trades but raises stop-out risk.' },
                  ]
                },
              ].map((s) => {
                const hitPct = Math.round((s.actualHits / s.totalSignals) * 100);
                return (
                  <div key={s.sym} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col gap-4">
                    {/* Header */}
                    <div className="flex flex-wrap justify-between items-center gap-2">
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-slate-100 text-sm">{s.sym}</span>
                        <span className="text-xs text-slate-400 font-mono">${s.price}</span>
                      </div>
                      <span className={`text-xs font-bold px-2.5 py-1 rounded border ${s.overallColor}`}>Signal: {s.overall}</span>
                    </div>

                    {/* AI Explanation */}
                    <p className="text-[10px] text-slate-400 leading-relaxed bg-slate-950/40 rounded-lg px-3 py-2 border border-slate-800/50 italic">{s.explanation}</p>

                    {/* Indicators with explanations */}
                    <div className="grid grid-cols-1 gap-2">
                      {s.indicators.map((ind) => (
                        <div key={ind.name} className="flex flex-col gap-0.5">
                          <div className="flex justify-between items-center">
                            <span className="text-[10px] font-semibold text-slate-400">{ind.name}</span>
                            <span className={`text-[10px] font-mono font-bold ${ind.color}`}>{ind.value}{ind.label ? ` (${ind.label})` : ''}</span>
                          </div>
                          <p className="text-[9px] text-slate-600 leading-tight">{ind.desc}</p>
                        </div>
                      ))}
                    </div>

                    {/* Trade Plan */}
                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-slate-800/50 rounded-lg p-2 flex flex-col gap-0.5">
                        <span className="text-[9px] text-slate-500 uppercase tracking-wide">Hold Period</span>
                        <span className="text-xs font-semibold text-slate-200">{s.holding}</span>
                      </div>
                      <div className="bg-emerald-900/20 border border-emerald-800/30 rounded-lg p-2 flex flex-col gap-0.5">
                        <span className="text-[9px] text-emerald-500 uppercase tracking-wide">Target</span>
                        <span className="text-xs font-bold text-emerald-400 font-mono">${s.target}</span>
                      </div>
                      <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-2 flex flex-col gap-0.5">
                        <span className="text-[9px] text-red-500 uppercase tracking-wide">Stop Loss</span>
                        <span className="text-xs font-bold text-red-400 font-mono">${s.stopLoss}</span>
                      </div>
                    </div>

                    {/* Prediction Accuracy */}
                    <div className="flex flex-col gap-1.5">
                      <div className="flex justify-between items-center">
                        <span className="text-[9px] text-slate-500 uppercase tracking-wide">Signal Prediction Accuracy</span>
                        <span className="text-[10px] font-bold text-slate-200">{s.actualHits}/{s.totalSignals} hit ({hitPct}%)</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${hitPct >= 75 ? 'bg-emerald-500' : hitPct >= 50 ? 'bg-amber-400' : 'bg-red-500'}`}
                          style={{ width: `${hitPct}%` }}
                        ></div>
                      </div>
                      <p className="text-[9px] text-slate-600">How often this symbol's predicted signal direction matched the actual outcome across all historical trades.</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>


          {/* Market Conditions Bulletin */}
          <div className="glass-panel">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-2">
              <div>
                <h2 className="text-base font-semibold text-slate-50">Market Conditions Bulletin</h2>
                <p className="text-[10px] text-slate-500 mt-0.5">Fusion Agent's real-time macro assessment</p>
              </div>
              <span className="text-[10px] text-slate-500">Updated: 3:15 PM</span>
            </div>
            <div className="flex flex-col gap-3">
              <div className="flex gap-3 items-center">
                <span className="text-xl">📈</span>
                <div>
                  <span className="text-xs font-bold text-emerald-400">Regime: RISK-ON / TRENDING</span>
                  <p className="text-[10px] text-slate-400 mt-0.5">Broad market is in a low-volatility uptrend. VIX below 20 signals institutional confidence. The Risk Agent's veto power is reduced.</p>
                </div>
              </div>
              <div className="h-px bg-slate-800"></div>
              <div className="flex gap-3 items-center">
                <span className="text-xl">🏭</span>
                <div>
                  <span className="text-xs font-bold text-amber-400">Sector Watch: Semiconductors Cooling</span>
                  <p className="text-[10px] text-slate-400 mt-0.5">AI/chip momentum is decelerating after a strong Q1 run. NVDA and AMD showing early reversal signals. Reducing new entries in this sub-sector.</p>
                </div>
              </div>
              <div className="h-px bg-slate-800"></div>
              <div className="flex gap-3 items-center">
                <span className="text-xl">📰</span>
                <div>
                  <span className="text-xs font-bold text-blue-400">Event Radar: Supply Chain & Fed Minutes</span>
                  <p className="text-[10px] text-slate-400 mt-0.5">Supply chain disruption headlines are pressuring consumer tech. Fed minutes due Thursday — Event Agent is reducing exposure ahead of potential rate commentary to avoid event-driven whipsaws.</p>
                </div>
              </div>
            </div>
          </div>

        </div>

        <div className="flex flex-col gap-6">
          <div className="glass-panel">
            <h2 className="text-lg font-semibold text-slate-50 mb-4">Key Metrics</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900/40 p-4 rounded-xl border border-white/5 flex flex-col gap-1">
                <span className="text-sm font-medium text-slate-400">Net Profit</span>
                <span className="text-[10px] text-slate-500">Absolute $ gained since inception</span>
                <span className={`text-2xl font-bold ${data.metrics.totalReturn >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                  ${(10000 * (data.metrics.totalReturn / 100)).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </span>
              </div>
              <div className="bg-slate-900/40 p-4 rounded-xl border border-white/5 flex flex-col gap-1">
                <span className="text-sm font-medium text-slate-400">Total Return</span>
                <span className="text-[10px] text-slate-500">% growth vs. starting capital</span>
                <span className={`text-2xl font-bold ${data.metrics.totalReturn >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                  {data.metrics.totalReturn >= 0 ? '+' : ''}{data.metrics.totalReturn.toFixed(2)}%
                </span>
              </div>
              <div className="bg-slate-900/40 p-4 rounded-xl border border-white/5 flex flex-col gap-1">
                <span className="text-sm font-medium text-slate-400">Win Rate</span>
                <span className="text-[10px] text-slate-500">Of all trades, how many were profitable</span>
                <span className="text-2xl font-bold text-slate-50">{data.metrics.winRate.toFixed(1)}%</span>
              </div>
              <div className="bg-slate-900/40 p-4 rounded-xl border border-white/5 flex flex-col gap-1">
                <span className="text-sm font-medium text-slate-400">Sharpe Ratio</span>
                <span className="text-[10px] text-slate-500">Return per unit of risk. &gt;2 = excellent</span>
                <span className="text-2xl font-bold text-accent-cyan">{data.metrics.sharpeRatio.toFixed(2)}</span>
              </div>
              <div className="bg-slate-900/40 p-4 rounded-xl border border-white/5 flex flex-col gap-1">
                <span className="text-sm font-medium text-slate-400">Alpha</span>
                <span className="text-[10px] text-slate-500">Outperformance vs. S&P 500 benchmark</span>
                <span className="text-2xl font-bold text-emerald-500">+{data.metrics.alpha.toFixed(1)}%</span>
              </div>
              <div className="bg-slate-900/40 p-4 rounded-xl border border-white/5 flex flex-col gap-1 col-span-2">
                <span className="text-sm font-medium text-slate-400">Max Drawdown</span>
                <span className="text-[10px] text-slate-500">Largest peak-to-trough loss; lower is safer</span>
                <span className="text-2xl font-bold text-red-500">{data.metrics.maxDrawdown.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          <div className="glass-panel">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-2">
              <h2 className="text-base font-semibold text-slate-50">Performance Deep Dive</h2>
              <span className="text-xs text-slate-500">Computed from all executed trades</span>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Profit Factor', sub: 'Avg Win ÷ Avg Loss. >1.5 is strong', value: '1.85', color: 'text-emerald-400' },
                { label: 'Calmar Ratio', sub: 'Return / Drawdown. Higher = safer', value: '4.14', color: 'text-accent-cyan' },
                { label: 'Win Streak', sub: 'Current consecutive profitable trades', value: '3 🔥', color: 'text-amber-400' },
                { label: 'Avg Win', sub: 'Mean profit on winning trades', value: '+3.8%', color: 'text-emerald-400' },
                { label: 'Avg Loss', sub: 'Mean loss on losing trades', value: '-1.5%', color: 'text-red-400' },
                { label: 'Expected Value', sub: 'WinRate×AvgWin − LossRate×AvgLoss', value: '+1.9%', color: 'text-accent-cyan' },
              ].map((stat) => (
                <div key={stat.label} className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 flex flex-col gap-1">
                  <span className="text-xs font-semibold text-slate-300">{stat.label}</span>
                  <span className="text-[10px] text-slate-500 leading-tight">{stat.sub}</span>
                  <span className={`text-xl font-bold mt-1 font-mono ${stat.color}`}>{stat.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-50">Agent Network Logs</h2>
                <p className="text-[10px] text-slate-500 mt-0.5">Real-time messages between all AI agents in the LangGraph pipeline</p>
              </div>
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-cyan opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-cyan"></span>
              </span>
            </div>
            <div className="flex flex-col gap-2 overflow-y-auto custom-scrollbar pr-1" style={{ maxHeight: '520px' }}>
              {data.logs.map((log) => {
                const levelStyle = {
                  'INFO': 'text-blue-400 bg-blue-400/10 border-blue-400/20',
                  'SIGNAL': 'text-purple-400 bg-purple-400/10 border-purple-400/20',
                  'CLEAR': 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
                  'DECISION': 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
                  'WARN': 'text-amber-400 bg-amber-400/10 border-amber-400/20',
                  'CRITICAL': 'text-red-400 bg-red-400/10 border-red-400/20',
                  'VETO': 'text-red-400 bg-red-400/10 border-red-400/20',
                }[log.level] || 'text-slate-400 bg-slate-400/10 border-slate-400/20';
                const agentColor = log.agent.includes('Technical') ? 'text-blue-400 border-blue-700' :
                  log.agent.includes('Event') ? 'text-purple-400 border-purple-700' :
                    log.agent.includes('Risk') ? 'text-amber-400 border-amber-700' :
                      'text-emerald-400 border-emerald-700';
                return (
                  <div key={log.id} className={`bg-slate-900/60 border rounded-xl p-3 flex flex-col gap-1.5 border-slate-800`}>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[9px] text-slate-500 font-mono">{log.timestamp}</span>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${levelStyle}`}>{log.level}</span>
                      <span className={`text-[9px] font-semibold ${agentColor}`}>{log.agent}</span>
                      <span className="text-[9px] text-slate-600">· {log.type}</span>
                    </div>
                    <p className="text-xs text-slate-200 font-mono leading-snug">{log.message}</p>
                    <p className="text-[9px] text-slate-500 leading-relaxed border-t border-slate-800 pt-1.5 mt-0.5">{log.detail}</p>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="glass-panel flex-1 flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-slate-50">Detailed AI Trade Log</h2>
              <span className="text-[10px] text-slate-500">Entry · Plan · Outcome per trade</span>
            </div>
            <div className="flex flex-col flex-1 overflow-y-auto pr-2 custom-scrollbar gap-4">
              {data.trades.map((trade) => (
                <div key={trade.id} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col gap-3">
                  {/* Row 1: Header */}
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-50 text-base">{trade.symbol}</span>
                      <span className={`text-xs font-bold px-2.5 py-1 rounded-md tracking-wide ${trade.action === 'BUY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                        {trade.action}
                      </span>
                      <span className="text-xs text-slate-500">{trade.time}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded font-semibold border ${trade.hitTarget ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20' : 'text-red-400 bg-red-400/10 border-red-400/20'}`}>
                        {trade.hitTarget ? '✓ Target Hit' : '✗ Stopped Out'}
                      </span>
                      <span className={`font-mono text-lg font-bold ${trade.profit > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {trade.profit > 0 ? '+' : ''}{trade.profit}%
                      </span>
                    </div>
                  </div>

                  {/* Row 2: Prices — 2x2 grid */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-slate-800/50 rounded-lg p-2.5 flex flex-col gap-0.5">
                      <span className="text-[9px] text-slate-500 uppercase tracking-wide">Entry Price</span>
                      <span className="text-sm font-mono text-slate-200">${trade.entry.toFixed(2)}</span>
                    </div>
                    <div className="bg-emerald-900/20 border border-emerald-800/30 rounded-lg p-2.5 flex flex-col gap-0.5">
                      <span className="text-[9px] text-emerald-500 uppercase tracking-wide">🎯 Target</span>
                      <span className="text-sm font-mono font-bold text-emerald-400">${trade.target.toFixed(2)}</span>
                    </div>
                    <div className="bg-red-900/20 border border-red-800/30 rounded-lg p-2.5 flex flex-col gap-0.5">
                      <span className="text-[9px] text-red-500 uppercase tracking-wide">🛑 Stop Loss</span>
                      <span className="text-sm font-mono font-bold text-red-400">${trade.stopLoss.toFixed(2)}</span>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-2.5 flex flex-col gap-0.5">
                      <span className="text-[9px] text-slate-500 uppercase tracking-wide">Exit Price</span>
                      <span className="text-sm font-mono text-slate-200">${trade.exitPrice.toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Row 3: Hold & Confidence side-by-side */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-slate-800/50 rounded-lg p-2.5 flex flex-col gap-0.5">
                      <span className="text-[9px] text-slate-500 uppercase tracking-wide">⏱ Hold Period</span>
                      <span className="text-sm text-slate-200">{trade.holding}</span>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-2.5 flex flex-col gap-1">
                      <div className="flex justify-between">
                        <span className="text-[9px] text-slate-500 uppercase tracking-wide">AI Confidence</span>
                        <span className="text-[10px] font-mono font-bold text-accent-cyan">{(trade.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-accent-cyan rounded-full" style={{ width: `${trade.confidence * 100}%` }}></div>
                      </div>
                    </div>
                  </div>

                  {/* Row 4: Narrative */}
                  <div className="bg-slate-950/40 rounded-lg px-3 py-2 border border-slate-800/50">
                    <p className="text-xs text-slate-400 leading-relaxed italic">
                      <span className="text-accent-indigo font-semibold not-italic mr-1">AI Narrative:</span>
                      {trade.reason}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
