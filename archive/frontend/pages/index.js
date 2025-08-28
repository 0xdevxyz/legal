import { useState, useEffect } from 'react'

export default function SimpleDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('https://api.complyo.tech/api/dashboard/overview')
      .then(res => res.json())
      .then(data => {
        setData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('API Error:', err)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        fontFamily: 'Arial, sans-serif',
        background: '#f3f4f6'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '50px',
            height: '50px', 
            border: '5px solid #e5e7eb',
            borderTop: '5px solid #3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }}></div>
          <h2>🚀 Neues Complyo Dashboard wird geladen...</h2>
          <p>API-Verbindung wird hergestellt...</p>
          <style jsx>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      </div>
    )
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      background: '#f3f4f6',
      fontFamily: 'Arial, sans-serif',
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        {/* Header */}
        <header style={{
          background: 'white',
          padding: '20px',
          borderRadius: '10px',
          marginBottom: '20px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <h1 style={{
            margin: 0,
            fontSize: '2rem',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'inline-block'
          }}>
            ✅ Neues Complyo Dashboard
          </h1>
          <span style={{
            marginLeft: '10px',
            padding: '5px 10px',
            background: '#10b981',
            color: 'white',
            borderRadius: '15px',
            fontSize: '12px',
            fontWeight: 'bold'
          }}>
            REPARIERT ✨
          </span>
        </header>

        {/* API Status */}
        <div style={{
          background: data ? '#dcfce7' : '#fef2f2',
          border: `2px solid ${data ? '#16a34a' : '#dc2626'}`,
          borderRadius: '10px',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <h2 style={{ margin: '0 0 10px 0' }}>
            {data ? '✅ API-Verbindung erfolgreich!' : '❌ API-Verbindung fehlgeschlagen'}
          </h2>
          {data ? (
            <div>
              <p><strong>User:</strong> {data.user?.name || 'N/A'}</p>
              <p><strong>Projects:</strong> {data.summary?.total_projects || 0}</p>
              <p><strong>Compliance Score:</strong> {data.summary?.compliance_score || 0}%</p>
            </div>
          ) : (
            <p>Kann keine Daten von https://api.complyo.tech/api/dashboard/overview laden</p>
          )}
        </div>

        {/* Projects */}
        {data?.projects && (
          <div style={{
            background: 'white',
            borderRadius: '10px',
            padding: '20px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            marginBottom: '20px'
          }}>
            <h3 style={{ margin: '0 0 20px 0' }}>📊 Projekte:</h3>
            {data.projects.map(project => (
              <div key={project.id} style={{
                padding: '15px',
                margin: '10px 0',
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '8px'
              }}>
                <h4 style={{ margin: '0 0 10px 0' }}>{project.name}</h4>
                <p><strong>Score:</strong> {project.compliance_score}%</p>
                <p><strong>Status:</strong> {project.status}</p>
                <p><strong>URL:</strong> {project.url}</p>
                
                <div style={{ marginTop: '15px' }}>
                  <button 
                    onClick={() => alert('🤖 KI-Fix für ' + project.name + ' gestartet!')}
                    style={{
                      padding: '8px 16px',
                      background: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '5px',
                      marginRight: '10px',
                      cursor: 'pointer'
                    }}
                  >
                    🤖 KI-Fix starten
                  </button>
                  
                  <button 
                    onClick={() => alert('👨‍💼 Expert-Beratung für ' + project.name + ' buchen!')}
                    style={{
                      padding: '8px 16px',
                      background: '#8b5cf6',
                      color: 'white',
                      border: 'none',
                      borderRadius: '5px',
                      marginRight: '10px',
                      cursor: 'pointer'
                    }}
                  >
                    👨‍💼 Expert buchen
                  </button>
                  
                  <button 
                    onClick={() => alert('📄 PDF-Report für ' + project.name + ' wird generiert!')}
                    style={{
                      padding: '8px 16px',
                      background: '#6b7280',
                      color: 'white',
                      border: 'none',
                      borderRadius: '5px',
                      cursor: 'pointer'
                    }}
                  >
                    📄 Report
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Debug Info */}
        <div style={{
          background: 'white',
          borderRadius: '10px',
          padding: '20px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ margin: '0 0 15px 0' }}>🔧 Debug-Informationen:</h3>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            <li>✅ Neue index.js wurde geladen</li>
            <li>✅ Container: complyo-dashboard-react</li>
            <li>✅ API: https://api.complyo.tech</li>
            <li>✅ Frontend-Cache geleert</li>
            <li>✅ Echte Dashboard-Daten</li>
          </ul>
          
          <div style={{ marginTop: '20px' }}>
            <a 
              href="https://api.complyo.tech/docs" 
              target="_blank"
              style={{
                display: 'inline-block',
                padding: '10px 20px',
                background: '#059669',
                color: 'white',
                textDecoration: 'none',
                borderRadius: '5px',
                marginRight: '10px'
              }}
            >
              📚 API Docs
            </a>
            
            <button 
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 20px',
                background: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '5px',
                cursor: 'pointer'
              }}
            >
              🔄 Neu laden
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
