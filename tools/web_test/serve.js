// 极简静态服务器：用于本地测试 Ren'Py Web 构建。
// 用法：node serve.js <web 目录> [端口=8000] [--gzip]
// --gzip 用于粗略模拟支持压缩的静态托管（是否与 GitHub Pages 一致未验证）。
const http = require('http');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const root = path.resolve(process.argv[2] || '.');
const port = parseInt(process.argv[3] || '8000', 10);
const gzip = process.argv.includes('--gzip');
const types = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.json': 'application/json',
  '.wasm': 'application/wasm', '.png': 'image/png', '.jpg': 'image/jpeg', '.zip': 'application/zip',
  '.data': 'application/octet-stream', '.symbols': 'text/plain', '.txt': 'text/plain',
};
const compressible = new Set(['.html', '.js', '.json', '.wasm', '.data', '.symbols', '.txt']);
const cache = new Map();

http.createServer((req, res) => {
  let rel = decodeURIComponent(req.url.split('?')[0]);
  if (rel.endsWith('/')) rel += 'index.html';
  const file = path.join(root, rel);
  if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404); res.end('not found'); return;
  }
  const ext = path.extname(file);
  const headers = { 'Content-Type': types[ext] || 'application/octet-stream', 'Cache-Control': 'no-cache' };
  const wantsGzip = gzip && compressible.has(ext) && /\bgzip\b/.test(req.headers['accept-encoding'] || '');
  if (wantsGzip) {
    if (!cache.has(file)) cache.set(file, zlib.gzipSync(fs.readFileSync(file), { level: 6 }));
    const body = cache.get(file);
    headers['Content-Encoding'] = 'gzip';
    headers['Content-Length'] = body.length;
    res.writeHead(200, headers); res.end(body);
  } else {
    headers['Content-Length'] = fs.statSync(file).size;
    res.writeHead(200, headers); fs.createReadStream(file).pipe(res);
  }
}).listen(port, '127.0.0.1', () => console.log(`serving ${root} on http://127.0.0.1:${port}/ gzip=${gzip}`));
