const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const port = 8081;
const hostname = '0.0.0.0';

// MIME type mapping
const mimeTypes = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon',
  '.svg': 'image/svg+xml'
};

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url);
  let pathname = parsedUrl.pathname;
  
  console.log(`${new Date().toISOString()} - ${req.method} ${pathname}`);
  
  // Route handling
  if (pathname === '/') {
    pathname = '/homepage.html';
  } else if (pathname === '/dsgvo') {
    pathname = '/dsgvo-landing.html';
  }
  
  // Construct file path
  const filePath = path.join(__dirname, pathname);
  
  // Security check - prevent directory traversal
  const normalizedPath = path.normalize(filePath);
  if (!normalizedPath.startsWith(__dirname)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    res.end('Forbidden');
    return;
  }
  
  // Check if file exists and serve it
  fs.readFile(filePath, (err, data) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // Return simple 404 page with navigation
        res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(`
          <!DOCTYPE html>
          <html lang="de">
          <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Seite nicht gefunden - Complyo Landing Pages</title>
            <style>
              body { font-family: Inter, sans-serif; text-align: center; padding: 2rem; background: #f9fafb; }
              .container { max-width: 600px; margin: 0 auto; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
              h1 { color: #1f2937; margin-bottom: 1rem; }
              .links { display: flex; gap: 1rem; justify-content: center; margin-top: 2rem; }
              .btn { background: #2563eb; color: white; padding: 0.75rem 1.5rem; border-radius: 8px; text-decoration: none; }
              .btn:hover { background: #1d4ed8; }
            </style>
          </head>
          <body>
            <div class="container">
              <h1>🚀 Complyo Landing Pages Demo</h1>
              <p>Seite nicht gefunden. Hier sind die verfügbaren Landing Pages:</p>
              <div class="links">
                <a href="/" class="btn">🏠 Homepage</a>
                <a href="/dsgvo" class="btn">🚨 DSGVO Landing</a>
                <a href="/homepage.html" class="btn">📄 Homepage (Direct)</a>
                <a href="/dsgvo-landing.html" class="btn">⚖️ DSGVO (Direct)</a>
              </div>
            </div>
          </body>
          </html>
        `);
      } else {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Internal server error');
      }
      console.error(`Error serving ${pathname}:`, err.message);
      return;
    }
    
    // Determine content type
    const ext = path.extname(filePath).toLowerCase();
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    
    // Add CORS headers
    res.writeHead(200, {
      'Content-Type': contentType,
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
    
    res.end(data);
  });
});

server.listen(port, hostname, () => {
  console.log(`🎯 Complyo Landing Pages Server running at http://${hostname}:${port}/`);
  console.log(`🏠 Homepage: http://${hostname}:${port}/ or /homepage.html`);
  console.log(`🚨 DSGVO Landing: http://${hostname}:${port}/dsgvo or /dsgvo-landing.html`);
  console.log(`🎨 CSS Styles: http://${hostname}:${port}/landing-styles.css`);
  console.log(`⚡ Server ready for requests...`);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down landing pages server...');
  server.close(() => {
    console.log('✅ Landing pages server closed');
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Received SIGTERM, shutting down landing pages server...');
  server.close(() => {
    console.log('✅ Landing pages server closed');
    process.exit(0);
  });
});