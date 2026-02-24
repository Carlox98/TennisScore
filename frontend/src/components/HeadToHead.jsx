export default function HeadToHead({ data }) {
  if (!data) return null

  return (
    <div className="bg-tennis-card rounded-xl p-6 border border-slate-700/50">
      <h3 className="text-lg font-bold mb-4">Head-to-Head Record</h3>

      <div className="flex items-center justify-center gap-6 mb-6">
        <div className="text-center">
          <div className="text-3xl font-bold text-tennis-green">{data.p1_wins}</div>
          <div className="text-sm text-slate-400">{data.player1?.name}</div>
        </div>
        <div className="text-slate-600 text-2xl font-light">-</div>
        <div className="text-center">
          <div className="text-3xl font-bold text-red-400">{data.p2_wins}</div>
          <div className="text-sm text-slate-400">{data.player2?.name}</div>
        </div>
      </div>

      {data.surface_h2h && (
        <div className="grid grid-cols-3 gap-3 mb-4">
          {Object.entries(data.surface_h2h).map(([surface, rec]) => (
            <div key={surface} className="bg-slate-800/50 rounded-lg p-3 text-center">
              <div className="text-xs text-slate-500 capitalize mb-1">{surface}</div>
              <div className="text-sm font-semibold">{rec.p1_wins} - {rec.p2_wins}</div>
            </div>
          ))}
        </div>
      )}

      {data.history && data.history.length > 0 && (
        <div className="mt-4">
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Match History</p>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {data.history.map((m, i) => (
              <div key={i} className="flex items-center justify-between bg-slate-800/30 rounded-lg px-3 py-2 text-sm">
                <span className="text-slate-500 w-24">{m.date}</span>
                <span className={`text-xs px-2 py-0.5 rounded capitalize ${
                  m.surface === 'Hard' ? 'bg-blue-500/20 text-blue-400' :
                  m.surface === 'Clay' ? 'bg-orange-500/20 text-orange-400' :
                  'bg-green-500/20 text-green-400'
                }`}>{m.surface}</span>
                <span className="text-xs text-slate-500">{m.round}</span>
                <span className="font-medium">{m.score}</span>
                <span className={m.winner_id === data.player1?.id ? 'text-tennis-green' : 'text-red-400'}>
                  {m.winner_id === data.player1?.id ? data.player1?.name?.split(' ').pop() : data.player2?.name?.split(' ').pop()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
