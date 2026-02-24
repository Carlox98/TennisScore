import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getPlayerProfile } from '../services/api'
import PlayerProfile from '../components/PlayerProfile'
import RadarChart from '../components/RadarChart'

export default function PlayerPage() {
  const { id } = useParams()
  const [player, setPlayer] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const res = await getPlayerProfile(id)
        setPlayer(res.data)
      } catch {
        setError('Player not found')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  if (loading) return <div className="text-center py-20 text-slate-400">Loading...</div>
  if (error) return <div className="text-center py-20 text-red-400">{error}</div>
  if (!player) return null

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PlayerProfile player={player} />
        <div className="bg-tennis-card rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-bold mb-2">Player Radar</h3>
          <RadarChart data={player.radar} />
        </div>
      </div>

      {/* Elo per Surface */}
      <div className="bg-tennis-card rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-lg font-bold mb-4">Elo by Surface</h3>
        <div className="grid grid-cols-3 gap-4">
          <EloCard label="Hard" value={player.elo_hard} color="blue" />
          <EloCard label="Clay" value={player.elo_clay} color="orange" />
          <EloCard label="Grass" value={player.elo_grass} color="green" />
        </div>
      </div>

      {/* Recent Matches */}
      {player.recent_matches && player.recent_matches.length > 0 && (
        <div className="bg-tennis-card rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-bold mb-4">Recent Matches</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-500 text-left">
                  <th className="pb-2">Date</th>
                  <th className="pb-2">Surface</th>
                  <th className="pb-2">Round</th>
                  <th className="pb-2">Opponent</th>
                  <th className="pb-2">Score</th>
                  <th className="pb-2">Result</th>
                </tr>
              </thead>
              <tbody>
                {player.recent_matches.map((m, i) => (
                  <tr key={i} className="border-t border-slate-700/30">
                    <td className="py-2 text-slate-400">{m.date}</td>
                    <td className="py-2">
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        m.surface === 'Hard' ? 'bg-blue-500/20 text-blue-400' :
                        m.surface === 'Clay' ? 'bg-orange-500/20 text-orange-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>{m.surface}</span>
                    </td>
                    <td className="py-2 text-slate-400">{m.round}</td>
                    <td className="py-2">{m.opponent?.name}</td>
                    <td className="py-2 font-mono">{m.score}</td>
                    <td className="py-2">
                      <span className={m.won ? 'text-tennis-green' : 'text-red-400'}>
                        {m.won ? 'W' : 'L'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function EloCard({ label, value, color }) {
  const colors = {
    blue: 'from-blue-500/20 to-blue-500/5 border-blue-500/30',
    orange: 'from-orange-500/20 to-orange-500/5 border-orange-500/30',
    green: 'from-green-500/20 to-green-500/5 border-green-500/30',
  }
  return (
    <div className={`bg-gradient-to-b ${colors[color]} rounded-lg p-4 border text-center`}>
      <div className="text-2xl font-bold">{Math.round(value)}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  )
}
