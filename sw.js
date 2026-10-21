// NOSPONSOR NOFUEL · service worker · build aa7cfc3868
const CACHE='nsnf-aa7cfc3868';
const SHELL=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./apple-touch-icon.png','./keepawake.mp4'];
// cache:'reload' bypasses the browser HTTP cache (GitHub Pages sends max-age=600), so a new build is never seeded with stale files
self.addEventListener('install',e=>{ e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL.map(u=>new Request(u,{cache:'reload'})))).then(()=>self.skipWaiting())); });
self.addEventListener('activate',e=>{ e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
function withTimeout(p,ms){ return new Promise((res,rej)=>{ const t=setTimeout(()=>rej(new Error('timeout')),ms); p.then(v=>{clearTimeout(t);res(v);},e=>{clearTimeout(t);rej(e);}); }); }
// Safari asks for video with Range requests and needs 206 answers, also when served from the cache
async function rangeResponse(req){
  const cached=await caches.match(req.url,{ignoreSearch:true});
  if(!cached) return fetch(req);
  const range=req.headers.get('range'); if(!range) return cached;
  const buf=await cached.arrayBuffer(); const total=buf.byteLength;
  const m=/bytes=(\d*)-(\d*)/.exec(range);
  let start=m&&m[1]?parseInt(m[1],10):0, end=m&&m[2]?parseInt(m[2],10):total-1; if(end>=total) end=total-1; if(start>end) start=0;
  const chunk=buf.slice(start,end+1);
  return new Response(chunk,{status:206,statusText:'Partial Content',headers:{'Content-Type':cached.headers.get('Content-Type')||'video/mp4','Content-Range':'bytes '+start+'-'+end+'/'+total,'Content-Length':String(chunk.byteLength),'Accept-Ranges':'bytes'}});
}
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  const url=new URL(e.request.url);
  if(url.origin!==self.location.origin) return;
  if(url.pathname.endsWith('.mp4')){ e.respondWith(rangeResponse(e.request)); return; }
  const isPage=e.request.mode==='navigate'||url.pathname.endsWith('/')||url.pathname.endsWith('/index.html');
  if(isPage){
    e.respondWith(withTimeout(fetch(new Request(e.request.url,{cache:'no-cache',credentials:'same-origin'})),4000).then(res=>{
      if(res&&res.ok){ const copy=res.clone(); caches.open(CACHE).then(c=>{ c.put('./index.html',copy.clone()); c.put('./',copy); }); }
      return res;
    }).catch(()=>caches.match('./index.html')));
    return;
  }
  e.respondWith(caches.match(e.request,{ignoreSearch:true}).then(hit=>hit||fetch(e.request).then(res=>{
    if(res&&res.ok){ const copy=res.clone(); caches.open(CACHE).then(c=>c.put(e.request,copy)); }
    return res;
  })));
});
