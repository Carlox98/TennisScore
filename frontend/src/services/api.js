import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

export const getUpcomingPredictions = () => api.get('/predictions/upcoming')

export const getCustomPrediction = (p1, p2, surface = 'Hard', bestOf = 3) =>
  api.get('/predictions/custom', { params: { p1, p2, surface, best_of: bestOf } })

export const getPlayerProfile = (id) => api.get(`/players/${id}`)

export const getPlayerForm = (id) => api.get(`/players/${id}/form`)

export const searchPlayers = (q) => api.get('/players/search', { params: { q } })

export const comparePlayers = (p1, p2) => api.get('/players/compare', { params: { p1, p2 } })

export const getRankings = (limit = 100) => api.get('/rankings', { params: { limit } })

export const getTournaments = (surface) => api.get('/tournaments', { params: { surface } })

export const getModelAccuracy = () => api.get('/model/accuracy')

export const getHealth = () => api.get('/health')

export default api
