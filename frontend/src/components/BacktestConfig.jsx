import { useState } from 'react';

export default function BacktestConfig({ onRunBacktest }) {
  const [symbol, setSymbol] = useState('AAPL');
  const [startDate, setStartDate] = useState('2023-01-01');
  const [endDate, setEndDate] = useState('2023-12-31');
  const [interval, setInterval] = useState('1d');
  const [initialCapital, setInitialCapital] = useState(100000);
  
  // Strategy config
  const [technicalWeight, setTechnicalWeight] = useState(0.5);
  const [eventWeight, setEventWeight] = useState(0.2);
  const [riskWeight, setRiskWeight] = useState(0.3);
  const [maxPositionSize, setMaxPositionSize] = useState(0.10);
  const [maxOpenPositions, setMaxOpenPositions] = useState(3);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/api/backtest/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          start_date: startDate,
          end_date: endDate,
          interval,
          initial_capital: initialCapital,
          strategy_config: {
            name: 'custom',
            technical_weight: technicalWeight,
            event_weight: eventWeight,
            risk_weight: riskWeight,
            max_position_size: maxPositionSize,
            max_open_positions: maxOpenPositions,
          },
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start backtest');
      }

      const data = await response.json();
      onRunBacktest(data.job_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6">Backtest Configuration</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Configuration */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Symbol
            </label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Interval
            </label>
            <select
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="1d">1 Day</option>
              <option value="1h">1 Hour</option>
              <option value="15m">15 Minutes</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Initial Capital ($)
          </label>
          <input
            type="number"
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        {/* Strategy Configuration */}
        <div className="border-t pt-6">
          <h3 className="text-lg font-semibold mb-4">Strategy Parameters</h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Technical Weight: {technicalWeight.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={technicalWeight}
                onChange={(e) => setTechnicalWeight(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Event Weight: {eventWeight.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={eventWeight}
                onChange={(e) => setEventWeight(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Risk Weight: {riskWeight.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={riskWeight}
                onChange={(e) => setRiskWeight(Number(e.target.value))}
                className="w-full"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Position Size (%)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="1"
                  value={maxPositionSize * 100}
                  onChange={(e) => setMaxPositionSize(Number(e.target.value) / 100)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Open Positions
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={maxOpenPositions}
                  onChange={(e) => setMaxOpenPositions(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Starting Backtest...' : 'Run Backtest'}
        </button>
      </form>
    </div>
  );
}
