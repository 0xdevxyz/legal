import { useState, useEffect } from 'react';

export default function DebugDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        console.log('🔍 Fetching from: https://api.complyo.tech');
        
        const response = await fetch('https://api.complyo.tech/api/dashboard/overview', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
        });
        
        console.log('📡 Response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('✅ Data received:', result);
        
        setData(result);
        setError(null);
      } catch (err) {
        console.error('❌ Fetch Error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    
    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', background: '#f0f0f0', minHeight: '100vh' }}>
        <h1 style={{ color: '#333' }}>🔍 Dashboard Debug Mode</h1>
        <div style={{ padding: '20px', background: 'white', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
          <p>⏳ Loading dashboard data from https://api.complyo.tech...</p>
          <div style={{ 
            width: '100%', 
            height: '20px', 
            background: '#ddd', 
            borderRadius: '10px',
            overflow: 'hidden',
            marginTop: '20px'
          }}>
            <div style={{
              width: '50%',
              height: '100%',
              background: 'linear-gradient(45deg, #3b82f6, #8b5cf6)',
              animation: 'pulse 2s infinite'
            }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', background: '#f0f0f0', minHeight: '100vh' }}>
        <h1 style={{ color: '#dc2626' }}>❌ Dashboard Debug Error</h1>
        <div style={{ padding: '20px', background: '#fee', border: '2px solid #dc2626', borderRadius: '8px', marginBottom: '20px' }}>
          <h3 style={{ margin: '0 0 10px 0' }}>Fehler Details:</h3>
          <p><strong>Error:</strong> {error}</p>
          <p><strong>API URL:</strong> https://api.complyo.tech</p>
          <p><strong>Endpoint:</strong> /api/dashboard/overview</p>
        </div>
        
        <div style={{ padding: '20px', background: 'white', borderRadius: '8px', marginBottom: '20px' }}>
          <h3 style={{ margin: '0 0 15px 0' }}>🔧 Debug-Informationen:</h3>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            <li>Frontend Container: complyo-dashboard-react</li>
            <li>Backend Container: complyo-backend-direct</li>
            <li>Expected API: https://api.complyo.tech</li>
            <li>Status: Backend läuft, Frontend hatte Connection-Probleme</li>
          </ul>
        </div>
        
        <button 
          onClick={() => window.location.reload()} 
          style={{
            padding: '12px 24px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          🔄 Retry Loading
        </button>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', background: '#f0f0f0', minHeight: '100vh' }}>
      <h1 style={{ color: '#059669' }}>✅ Dashboard Debug - SUCCESS!</h1>
      
      <div style={{ marginBottom: '20px', padding: '20px', background: '#d1fae5', border: '2px solid #059669', borderRadius: '8px' }}>
        <h3 style={{ margin: '0 0 15px 0' }}>🎉 API Connection Working!</h3>
        <p><strong>User:</strong> {data?.user?.name || 'N/A'}</p>
        <p><strong>Projects:</strong> {data?.summary?.total_projects || 0}</p>
        <p><strong>Compliance Score:</strong> {data?.summary?.compliance_score || 0}%</p>
        <p><strong>Issues Found:</strong> {data?.summary?.issues_found || 0}</p>
      </div>

      <div style={{ marginBottom: '20px', background: 'white', borderRadius: '8px', padding: '20px' }}>
        <h3 style={{ margin: '0 0 15px 0' }}>📊 Projects:</h3>
        {data?.projects?.length > 0 ? (
          data.projects.map(project => (
            <div key={project.id} style={{ 
              padding: '15px', 
              margin: '10px 0', 
              background: '#f8f9fa', 
              border: '1px solid #ddd', 
              borderRadius: '8px' 
            }}>
              <h4 style={{ margin: '0 0 10px 0', color: '#374151' }}>{project.name}</h4>
              <p style={{ margin: '5px 0' }}>
                <strong>Score:</strong> {project.compliance_score}% | 
                <strong> Status:</strong> {project.status} | 
                <strong> Issues:</strong> {project.issues}
              </p>
              <p style={{ margin: '5px 0', fontSize: '14px', color: '#6b7280' }}>
                <strong>URL:</strong> {project.url}
              </p>
              <p style={{ margin: '5px 0', fontSize: '12px', color: '#9ca3af' }}>
                Last scan: {new Date(project.last_scan).toLocaleString()}
              </p>
            </div>
          ))
        ) : (
          <p style={{ color: '#6b7280' }}>No projects found</p>
        )}
      </div>

      <div style={{ marginBottom: '20px', background: 'white', borderRadius: '8px', padding: '20px' }}>
        <h3 style={{ margin: '0 0 15px 0' }}>📰 Recent Activity:</h3>
        {data?.recent_activity?.length > 0 ? (
          data.recent_activity.map(activity => (
            <div key={activity.id} style={{ 
              padding: '10px', 
              margin: '5px 0', 
              background: '#f1f3f4', 
              borderLeft: '4px solid #3b82f6',
              borderRadius: '4px'
            }}>
              <p style={{ margin: '0', fontSize: '14px' }}>
                <strong>{activity.type}:</strong> {activity.description}
              </p>
              <small style={{ color: '#6b7280' }}>
                {new Date(activity.timestamp).toLocaleString()}
              </small>
            </div>
          ))
        ) : (
          <p style={{ color: '#6b7280' }}>No recent activity</p>
        )}
      </div>

      <div style={{ marginTop: '30px', padding: '20px', background: '#eff6ff', borderRadius: '8px' }}>
        <h3 style={{ margin: '0 0 15px 0' }}>🔧 Next Steps:</h3>
        <ol style={{ margin: 0, paddingLeft: '20px' }}>
          <li>✅ Debug-Dashboard funktioniert</li>
          <li>✅ API-Verbindung erfolgreich</li>
          <li>✅ Daten werden korrekt geladen</li>
          <li>🎯 Hauptdashboard wird als nächstes repariert</li>
        </ol>
        
        <div style={{ marginTop: '20px' }}>
          <a 
            href="/" 
            style={{
              display: 'inline-block',
              padding: '10px 20px',
              background: '#3b82f6',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '6px',
              marginRight: '10px'
            }}
          >
            🏠 Zurück zum Hauptdashboard
          </a>
          <button 
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              background: '#059669',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            🔄 Neu laden
          </button>
        </div>
      </div>
    </div>
  );
}
