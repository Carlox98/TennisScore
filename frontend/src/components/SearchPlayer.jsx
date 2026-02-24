import { useState, useEffect, useRef } from 'react'
import { searchPlayers } from '../services/api'

export default function SearchPlayer({ onSelect, placeholder = 'Search player...' }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const ref = useRef()

  useEffect(() => {
    if (query.length < 2) {
      setResults([])
      setOpen(false)
      return
    }
    setLoading(true)
    const timer = setTimeout(async () => {
      try {
        const res = await searchPlayers(query)
        setResults(res.data || [])
        setOpen(true)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div ref={ref} className="relative w-full">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-tennis-green/50 focus:border-tennis-green"
      />
      {loading && (
        <div className="absolute right-3 top-3">
          <div className="w-4 h-4 border-2 border-tennis-green border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      {open && results.length > 0 && (
        <div className="absolute z-50 w-full mt-1 bg-slate-800 border border-slate-600 rounded-lg shadow-xl max-h-60 overflow-y-auto">
          {results.map((p) => (
            <button
              key={p.id}
              className="w-full px-4 py-2.5 text-left hover:bg-slate-700 flex items-center justify-between transition-colors"
              onClick={() => {
                onSelect(p)
                setQuery(p.name)
                setOpen(false)
              }}
            >
              <span className="font-medium">{p.name}</span>
              <span className="text-xs text-slate-400">
                {p.nationality} &middot; Elo {Math.round(p.elo || 1500)}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
