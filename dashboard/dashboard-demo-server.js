const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const port = 9000;
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
  
  // Route handling - Only Complex Dashboard
  if (pathname === '/' || pathname === '/complex' || pathname === '/dashboard') {
    pathname = '/modern-complex-demo.html';
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
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('File not found');
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
  console.log(`🚀 Complyo Complex Dashboard Server running at http://${hostname}:${port}/`);
  console.log(`🎨 Complex Dashboard (Only Version): http://${hostname}:${port}/`);
  console.log(`📰 Features: Animated Header + Dark Mode + Legal News`);
  console.log(`⚡ Server ready for requests...`);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down server...');
  server.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Received SIGTERM, shutting down...');
  server.close(() => {
    console.log('✅ Server closed');
    process.exit(0);
  });
});