export default function handler(req, res) {
  res.status(200).json({
    status: 'online',
    services: {
      dashboard: 'healthy',
      backend: 'connected',
      database: 'ready'
    },
    timestamp: new Date().toISOString()
  })
}
