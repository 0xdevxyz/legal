export default function handler(req, res) {
  res.status(200).json({
    status: 'healthy',
    service: 'complyo-dashboard',
    version: '2.0.0',
    timestamp: new Date().toISOString()
  })
}
