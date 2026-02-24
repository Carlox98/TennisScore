import { useState } from 'react'
import { Link } from 'react-router-dom'
import ProbabilityBar from './ProbabilityBar'

const SURFACE_COLORS = {
  Hard: 'bg-blue-500/20 text-blue-400',
  Clay: 'bg-orange-500/20 text-orange-400',
  Grass: 'bg-green-500/20 text-green-400',
  Carpet: 'bg-purple-500/20 text-purple-400',
}

const CONFIDENCE_BADGE = {
  High: 'bg-tennis-green/20 text-tennis-green',
  Medium: 'bg-tennis-yellow/20 text-tennis-yellow',
  Low: 'bg-red-500/20 text-red-400',
}

const FLAG_MAP = {
  USA: '🇺🇸', ESP: '🇪🇸', SRB: '🇷🇸', ITA: '🇮🇹', RUS: '🇷🇺', GER: '🇩🇪',
  FRA: '🇫🇷', GBR: '🇬🇧', AUS: '🇦🇺', SUI: '🇨🇭', ARG: '🇦🇷', CAN: '🇨🇦',
  GRE: '🇬🇷', NOR: '🇳🇴', POL: '🇵🇱', CRO: '🇭🇷', BUL: '🇧🇬', DEN: '🇩🇰',
  BRA: '🇧🇷', JPN: '🇯🇵', CHN: '🇨🇳', KOR: '🇰🇷', CZE: '🇨🇿', AUT: '🇦🇹',
  BEL: '🇧🇪', NED: '🇳🇱', CHI: '🇨🇱', RSA: '🇿🇦', POR: '🇵🇹', ROU: '🇷🇴',
}

function getFlag(nationality) {
  return FLAG_MAP[nationality] || '🏳️'
}

export default function PredictionCard({ prediction }) {
  const [expanded, setExpanded] = useState(false)
  const { player1, player2, prob_player1, prob_player2, surface, confidence, most_likely_score, score_distribution } = prediction

  const surfaceClass = SURFACE_COLORS[surface] || 'bg-slate-600/20 text-slate-400'
  const confClass = CONFIDENCE_BADGE[confidence] || ''

  return (
    <div
      className="bg-tennis-card rounded-xl p-4 card-hover cursor-pointer border border-slate-700/50"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full ${surfaceClass}`}>{surface}</span>
          {confidence && (
            <span className={`text-xs px-2 py-0.5 rounded-full ${confClass}`}>{confidence}</span>
          )}
        </div>
        {most_likely_score && (
          <span className="text-xs text-slate-500">Likely: {most_likely_score}</span>
        )}
      </div>

      <div className="flex items-center justify-between mb-3">
        <Link
          to={`/player/${player1.id}`}
          className="flex items-center gap-2 hover:text-tennis-green transition-colors"
          onClick={(e) => e.stopPropagation()}
        >
          <span>{getFlag(player1.nationality)}</span>
          <span className="font-semibold">{player1.name}</span>
          {player1.rank && <span className="text-xs text-slate-500">#{player1.rank}</span>}
        </Link>
        <span className="text-slate-600 text-sm">vs</span>
        <Link
          to={`/player/${player2.id}`}
          className="flex items-center gap-2 hover:text-tennis-green transition-colors"
          onClick={(e) => e.stopPropagation()}
        >
          {player2.rank && <span className="text-xs text-slate-500">#{player2.rank}</span>}
          <span className="font-semibold">{player2.name}</span>
          <span>{getFlag(player2.nationality)}</span>
        </Link>
      </div>

      <ProbabilityBar
        prob1={prob_player1}
        prob2={prob_player2}
        name1={player1.name?.split(' ').pop()}
        name2={player2.name?.split(' ').pop()}
      />

      {expanded && score_distribution && (
        <div className="mt-4 pt-3 border-t border-slate-700/50">
          <p className="text-xs text-slate-500 mb-2">Score Distribution</p>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(score_distribution).map(([score, prob]) => (
              <div key={score} className="flex items-center gap-2">
                <span className="text-sm font-mono w-10">{score}</span>
                <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-tennis-accent rounded-full"
                    style={{ width: `${prob * 100}%` }}
                  />
                </div>
                <span className="text-xs text-slate-400 w-12 text-right">{(prob * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
          {prediction.expected_total_games && (
            <p className="text-xs text-slate-500 mt-2">
              Expected games: {prediction.expected_total_games}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
