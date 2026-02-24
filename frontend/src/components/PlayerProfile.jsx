import { Link } from 'react-router-dom'

const SURFACE_COLORS = {
  hard: 'bg-blue-500',
  clay: 'bg-orange-500',
  grass: 'bg-green-500',
}

export default function PlayerProfile({ player }) {
  if (!player) return null

  return (
    <div className="bg-tennis-card rounded-xl p-6 border border-slate-700/50">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold">{player.name}</h2>
          <div className="flex items-center gap-3 mt-1 text-slate-400 text-sm">
            <span>{player.nationality}</span>
            {player.age && <span>{player.age} yrs</span>}
            {player.height && <span>{player.height}cm</span>}
            {player.hand && <span>{player.hand === 'R' ? 'Right-handed' : 'Left-handed'}</span>}
          </div>
        </div>
        <div className="text-right">
          {player.rank && (
            <div className="text-3xl font-bold text-tennis-green">#{player.rank}</div>
          )}
          <div className="text-sm text-slate-400">Elo {Math.round(player.elo_overall)}</div>
        </div>
      </div>

      {player.style && (
        <span className="inline-block px-3 py-1 bg-tennis-accent/20 text-tennis-accent text-xs font-medium rounded-full mb-4">
          {player.style}
        </span>
      )}

      <div className="grid grid-cols-3 gap-3 mb-4">
        <Stat label="Wins" value={player.wins} />
        <Stat label="Losses" value={player.losses} />
        <Stat label="Win Rate" value={`${(player.win_rate * 100).toFixed(1)}%`} />
      </div>

      {player.surface_records && (
        <div className="space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wider">Surface Records</p>
          {Object.entries(player.surface_records).map(([surface, record]) => (
            <div key={surface} className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full ${SURFACE_COLORS[surface] || 'bg-slate-500'}`} />
              <span className="text-sm capitalize w-14">{surface}</span>
              <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-tennis-green rounded-full"
                  style={{ width: `${record.win_rate * 100}%` }}
                />
              </div>
              <span className="text-xs text-slate-400 w-20 text-right">
                {record.wins}W {record.losses}L ({(record.win_rate * 100).toFixed(0)}%)
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="bg-slate-800/50 rounded-lg p-3 text-center">
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  )
}
