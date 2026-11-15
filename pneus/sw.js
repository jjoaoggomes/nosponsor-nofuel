// NOSPONSOR NOTYRES · service worker · build 932dc482c6
const CACHE='pneus-932dc482c6';
const SHELL=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./apple-touch-icon.png'];
self.addEventListener('install',e=>{ e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL.map(u=>new Request(u,{cache:'reload'})))).then(()=>self.skipWaiting())); });
self.addEventListener('activate',e=>{ e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('pneus-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
function withTimeout(p,ms){ return new Promise((res,rej)=>{ const t=setTimeout(()=>rej(new Error('timeout')),ms); p.then(v=>{clearTimeout(t);res(v);},e=>{clearTimeout(t);rej(e);}); }); }
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  const url=new URL(e.request.url);
  if(url.origin!==self.location.origin) return;
  const isPage=e.request.mode==='navigate'||url.pathname.endsWith('/')||url.pathname.endsWith('/index.html');
  if(isPage){
    e.respondWith(withTimeout(fetch(new Request(e.request.url,{cache:'no-cache',credentials:'same-origin'})),4000).then(res=>{
      if(res&&res.ok){ const copy=res.clone(); caches.open(CACHE).then(c=>{ c.put('./index.html',copy.clone()); c.put('./',copy); }); }
      return res;
    }).catch(()=>caches.open(CACHE).then(c=>c.match('./index.html'))));
    return;
  }
  e.respondWith(caches.open(CACHE).then(c=>c.match(e.request,{ignoreSearch:true}).then(hit=>hit||fetch(e.request).then(res=>{
    if(res&&res.ok) c.put(e.request,res.clone());
    return res;
  }))));
});
