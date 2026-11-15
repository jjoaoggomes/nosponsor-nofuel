#!/usr/bin/env python3
"""Build the tyre stock PWA (Pneus RC 1/8 TT) into /pneus of the published site.

usage (from the repository root): python3 src/pneus/build.py
Reuses the Barlow fonts already embedded in the root index.html, so it needs no network.
"""
import hashlib, json, os, re
from PIL import Image, ImageDraw

here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(here))
out = os.path.join(root, "pneus")
os.makedirs(out, exist_ok=True)

src = open(os.path.join(here, "app.html"), encoding="utf-8").read()
main = open(os.path.join(root, "index.html"), encoding="utf-8").read()
fonts = re.search(r"<style>@font-face.*?</style>", main, re.S).group(0)

cut = src.index('<div id="app">')
head_part, body_part = src[:cut].replace("<!--FONTS-->", fonts), src[cut:]

head = """<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0b0e13" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#e8ecf2" media="(prefers-color-scheme: light)">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Pneus RC">
<meta name="description" content="Stock de pneus RC 1/8 TT por marca, modelo e dureza. Funciona offline.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<style>html{padding-top:env(safe-area-inset-top,0px)}</style>
"""
sw_script = """
<script>
if('serviceWorker' in navigator){
  window.addEventListener('load',function(){ navigator.serviceWorker.register('./sw.js').catch(function(){}); });
}
</script>
"""
index_html = head + head_part + "</head>\n<body>\n" + body_part + sw_script + "</body>\n</html>\n"
ver = hashlib.sha256(index_html.encode()).hexdigest()[:10]
index_html = index_html.replace("build dev", "build " + ver)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(index_html)

# ---- icon: a knobby tyre seen from the side, drawn large then scaled down ----
def icon(size, pad):
    n = 1024
    im = Image.new("RGB", (n, n), "#0b0e13")
    d = ImageDraw.Draw(im)
    c, r = n / 2, n / 2 - pad
    import math
    for i in range(18):  # knobs
        a = 2 * math.pi * i / 18
        x, y = c + math.cos(a) * r, c + math.sin(a) * r
        k = r * 0.13
        d.ellipse([x - k, y - k, x + k, y + k], fill="#ff4fb0")
    d.ellipse([c - r, c - r, c + r, c + r], fill="#ff4fb0")
    r2 = r * 0.60
    d.ellipse([c - r2, c - r2, c + r2, c + r2], fill="#0b0e13")
    r3 = r * 0.44
    d.ellipse([c - r3, c - r3, c + r3, c + r3], fill="#edf1f7")
    r4 = r * 0.12
    d.ellipse([c - r4, c - r4, c + r4, c + r4], fill="#0b0e13")
    return im.resize((size, size), Image.LANCZOS)

icon(512, 250).save(os.path.join(out, "icon-512.png"), optimize=True)  # maskable: stays inside the safe zone
icon(192, 170).save(os.path.join(out, "icon-192.png"), optimize=True)
icon(180, 190).save(os.path.join(out, "apple-touch-icon.png"), optimize=True)

manifest = {
    "name": "Pneus RC 1/8 TT",
    "short_name": "Pneus RC",
    "description": "Stock de pneus RC 1/8 TT por marca, modelo e dureza, 100% offline.",
    "lang": "pt",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#0b0e13",
    "theme_color": "#0b0e13",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}
json.dump(manifest, open(os.path.join(out, "manifest.webmanifest"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- service worker: page network-first (short timeout), the rest cache-first; only touches its own caches,
# because this app shares the origin with NOSPONSOR NOFUEL ----
sw = """// Pneus RC 1/8 TT · service worker · build %s
const CACHE='pneus-%s';
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
""" % (ver, ver)
open(os.path.join(out, "sw.js"), "w", encoding="utf-8").write(sw)
print("build", ver, "pneus/index.html", len(index_html.encode()) // 1024, "KB")
