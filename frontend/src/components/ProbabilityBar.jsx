import { useEffect, useState } from 'react'

export default function ProbabilityBar({ prob1, prob2, name1, name2 }) {
  const [width, setWidth] = useState(50)
  const pct1 = Math.round((prob1 || 0.5) * 100)
  const pct2 = 100 - pct1

  useEffect(() => {
    const timer = setTimeout(() => setWidth(pct1), 100)
    return () => clearTimeout(timer)
  }, [pct1])

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className={pct1 >= pct2 ? 'text-tennis-green font-semibold' : 'text-slate-400'}>
          {name1} {pct1}%
        </span>
        <span className={pct2 > pct1 ? 'text-tennis-green font-semibold' : 'text-slate-400'}>
          {pct2}% {name2}
        </span>
      </div>
      <div className="h-3 bg-slate-700 rounded-full overflow-hidden flex">
        <div
          className="prob-bar bg-gradient-to-r from-tennis-green to-emerald-400 rounded-l-full"
          style={{ width: `${width}%` }}
        />
        <div
          className="prob-bar bg-gradient-to-r from-red-500 to-red-400 rounded-r-full"
          style={{ width: `${100 - width}%` }}
        />
      </div>
    </div>
  )
}
