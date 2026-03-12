import { useState, useEffect } from 'react';

export default function BacktestResults({ resultId }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!resultId) return;

    const fetchResult = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/backtest/results/${resultId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch backtest result');
        }

        const data = await response.json();
        setResult(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchResult();
  }, [resultId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-gray-600">Loading results...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-md">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const { performance, baseline, period, strategy } = result;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">Backtest Results</h2>
        
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Symbol:</span>
            <span className="ml-2 font-semibold">{result.symbol}</span>
          </div>
          <div>
            <span className="text-gray-600">Period:</span>
            <span className="ml-2 font-semibold">
              {new Date(period.start_date).toLocaleDateString()} - {new Date(period.end_date).toLocaleDateString()}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Strategy:</span>
            <span className="ml-2 font-semibold">{strategy.name}</span>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Performance Metrics</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <MetricCard
            label="Total Return"
            value={performance.total_return}
            highlight={true}
          />
          <MetricCard
            label="Win Rate"
            value={performance.win_rate}
          />
          <MetricCard
            label="Sharpe Ratio"
            value={performance.sharpe_ratio}
          />
          <MetricCard
            label="Max Drawdown"
            value={performance.max_drawdown}
            negative={true}
          />
          <MetricCard
            label="Profit Factor"
            value={performance.profit_factor}
          />
          <MetricCard
            label="Total Trades"
            value={performance.total_trades}
          />
          <MetricCard
            label="Avg Trade Duration"
            value={performance.avg_trade_duration_hours}
          />
          <MetricCard
            label="Final Equity"
            value={performance.final_equity}
          />
        </div>
      </div>

      {/* Baseline Comparison */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">vs Buy & Hold</h3>
        
        <div className="grid grid-cols-2 gap-6">
          <div>
            <div className="text-sm text-gray-600 mb-1">Buy & Hold Return</div>
            <div className="text-2xl font-bold">{baseline.buy_hold_return}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600 mb-1">Alpha (Excess Return)</div>
            <div className="text-2xl font-bold text-green-600">{baseline.alpha}</div>
          </div>
        </div>
      </div>

      {/* Trade Distribution */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Trade Distribution</h3>
        
        <div className="grid grid-cols-2 gap-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-3xl font-bold text-green-600">
              {result.trade_distribution.wins}
            </div>
            <div className="text-sm text-gray-600 mt-1">Winning Trades</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-3xl font-bold text-red-600">
              {result.trade_distribution.losses}
            </div>
            <div className="text-sm text-gray-600 mt-1">Losing Trades</div>
          </div>
        </div>
      </div>

      {/* Equity Curve Placeholder */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Equity Curve</h3>
        <div className="h-64 flex items-center justify-center bg-gray-50 rounded">
          <p className="text-gray-500">Chart visualization (requires Chart.js integration)</p>
        </div>
      </div>

      {/* Export Buttons */}
      <div className="flex gap-4">
        <button
          onClick={() => window.open(`http://localhost:8000/api/backtest/results/${resultId}`, '_blank')}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Export JSON
        </button>
        <button
          className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
        >
          Export CSV
        </button>
      </div>
    </div>
  );
}

function MetricCard({ label, value, highlight = false, negative = false }) {
  const colorClass = highlight
    ? 'text-blue-600'
    : negative
    ? 'text-red-600'
    : 'text-gray-900';

  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <div className="text-sm text-gray-600 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${colorClass}`}>{value}</div>
    </div>
  );
}
