import { Radar, RadarChart as ReRadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts'

export default function RadarChart({ data, color = '#22c55e' }) {
  if (!data) return null

  const chartData = [
    { stat: 'Serve', value: data.serve || 50 },
    { stat: 'Return', value: data.return || 50 },
    { stat: 'Power', value: data.power || 50 },
    { stat: 'Consistency', value: data.consistency || 50 },
    { stat: 'Clutch', value: data.clutch || 50 },
    { stat: 'Form', value: data.form || 50 },
  ]

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ReRadarChart data={chartData} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="#334155" />
        <PolarAngleAxis
          dataKey="stat"
          tick={{ fill: '#94a3b8', fontSize: 12 }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fill: '#475569', fontSize: 10 }}
        />
        <Radar
          name="Stats"
          dataKey="value"
          stroke={color}
          fill={color}
          fillOpacity={0.2}
          strokeWidth={2}
        />
      </ReRadarChart>
    </ResponsiveContainer>
  )
}
