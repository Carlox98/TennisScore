import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { getModelAccuracy } from '../services/api'

export default function ModelStats() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await getModelAccuracy()
        setStats(res.data)
      } catch {
        // API not ready
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <div className="text-center py-20 text-slate-400">Loading...</div>

  const metrics = stats?.model_metrics || {}
  const importance = stats?.feature_importance || {}

  const importanceData = Object.entries(importance)
    .slice(0, 15)
    .map(([name, value]) => ({ name: name.replace(/_/g, ' '), value: Math.round(value * 1000) / 10 }))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Model Performance</h1>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="Accuracy" value={`${((metrics.accuracy || 0) * 100).toFixed(1)}%`} />
        <MetricCard label="Log Loss" value={(metrics.log_loss || 0).toFixed(4)} />
        <MetricCard label="Brier Score" value={(metrics.brier_score || 0).toFixed(4)} />
        <MetricCard label="Test Predictions" value={stats?.total_predictions || metrics.test_size || 0} />
      </div>

      {/* Feature Importance */}
      {importanceData.length > 0 && (
        <div className="bg-tennis-card rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-bold mb-4">Feature Importance (Top 15)</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={importanceData} layout="vertical" margin={{ left: 100 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                width={100}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="value" fill="#22c55e" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Training Info */}
      <div className="bg-tennis-card rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-lg font-bold mb-4">Training Details</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-slate-500">Train samples:</span>{' '}
            <span className="font-medium">{metrics.train_size?.toLocaleString() || 'N/A'}</span>
          </div>
          <div>
            <span className="text-slate-500">Test samples:</span>{' '}
            <span className="font-medium">{metrics.test_size?.toLocaleString() || 'N/A'}</span>
          </div>
          <div>
            <span className="text-slate-500">Model:</span>{' '}
            <span className="font-medium">XGBoost v1</span>
          </div>
          <div>
            <span className="text-slate-500">Data source:</span>{' '}
            <span className="font-medium">Jeff Sackmann ATP (2015-2025)</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ label, value }) {
  return (
    <div className="bg-tennis-card rounded-xl p-5 border border-slate-700/50 text-center">
      <div className="text-2xl font-bold text-tennis-green">{value}</div>
      <div className="text-xs text-slate-500 mt-1">{label}</div>
    </div>
  )
}
