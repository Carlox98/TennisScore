import { useState, useEffect } from 'react'
import PredictionCard from '../components/PredictionCard'
import SearchPlayer from '../components/SearchPlayer'
import { getCustomPrediction, getUpcomingPredictions } from '../services/api'

export default function Home() {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(false)
  const [p1, setP1] = useState(null)
  const [p2, setP2] = useState(null)
  const [surface, setSurface] = useState('Hard')
  const [bestOf, setBestOf] = useState(3)
  const [customPrediction, setCustomPrediction] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadUpcoming()
  }, [])

  async function loadUpcoming() {
    try {
      const res = await getUpcomingPredictions()
      setPredictions(res.data || [])
    } catch {
      // API may not be ready yet
    }
  }

  async function handlePredict() {
    if (!p1 || !p2) return
    setLoading(true)
    setError(null)
    try {
      const res = await getCustomPrediction(p1.id, p2.id, surface, bestOf)
      setCustomPrediction(res.data)
    } catch (err) {
      setError('Prediction failed. Make sure the model is trained.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Custom Prediction */}
      <section>
        <h2 className="text-xl font-bold mb-4">Custom Prediction</h2>
        <div className="bg-tennis-card rounded-xl p-6 border border-slate-700/50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Player 1</label>
              <SearchPlayer onSelect={setP1} placeholder="Search player 1..." />
              {p1 && <span className="text-xs text-tennis-green mt-1 block">{p1.name}</span>}
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Player 2</label>
              <SearchPlayer onSelect={setP2} placeholder="Search player 2..." />
              {p2 && <span className="text-xs text-tennis-green mt-1 block">{p2.name}</span>}
            </div>
          </div>
          <div className="flex flex-wrap gap-4 items-end">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Surface</label>
              <select
                value={surface}
                onChange={(e) => setSurface(e.target.value)}
                className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="Hard">Hard</option>
                <option value="Clay">Clay</option>
                <option value="Grass">Grass</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Format</label>
              <select
                value={bestOf}
                onChange={(e) => setBestOf(Number(e.target.value))}
                className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
              >
                <option value={3}>Best of 3</option>
                <option value={5}>Best of 5</option>
              </select>
            </div>
            <button
              onClick={handlePredict}
              disabled={!p1 || !p2 || loading}
              className="px-6 py-2 bg-tennis-green text-black font-semibold rounded-lg hover:bg-tennis-green/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Predicting...' : 'Predict'}
            </button>
          </div>
          {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
        </div>

        {customPrediction && (
          <div className="mt-4">
            <PredictionCard prediction={customPrediction} />
          </div>
        )}
      </section>

      {/* Recent Predictions */}
      {predictions.length > 0 && (
        <section>
          <h2 className="text-xl font-bold mb-4">Recent Predictions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {predictions.map((p, i) => (
              <PredictionCard key={p.id || i} prediction={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
