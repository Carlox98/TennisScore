import { useState } from 'react'
import SearchPlayer from '../components/SearchPlayer'
import HeadToHead from '../components/HeadToHead'
import PredictionCard from '../components/PredictionCard'
import { comparePlayers, getCustomPrediction } from '../services/api'

export default function H2HPage() {
  const [p1, setP1] = useState(null)
  const [p2, setP2] = useState(null)
  const [h2h, setH2h] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [surface, setSurface] = useState('Hard')
  const [bestOf, setBestOf] = useState(3)
  const [loading, setLoading] = useState(false)

  async function handleCompare() {
    if (!p1 || !p2) return
    setLoading(true)
    try {
      const [h2hRes, predRes] = await Promise.all([
        comparePlayers(p1.id, p2.id),
        getCustomPrediction(p1.id, p2.id, surface, bestOf),
      ])
      setH2h(h2hRes.data)
      setPrediction(predRes.data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Head-to-Head Comparison</h1>

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
            onClick={handleCompare}
            disabled={!p1 || !p2 || loading}
            className="px-6 py-2 bg-tennis-green text-black font-semibold rounded-lg hover:bg-tennis-green/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Loading...' : 'Compare'}
          </button>
        </div>
      </div>

      {prediction && (
        <PredictionCard prediction={prediction} />
      )}

      {h2h && <HeadToHead data={h2h} />}
    </div>
  )
}
