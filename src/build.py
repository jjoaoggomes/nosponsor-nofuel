#!/usr/bin/env python3
"""Build the offline PWA (NOSPONSOR NOFUEL) from the single-page source used for the artifact.

usage: build.py SOURCE.html FONT_DIR_CONDENSED FONT_DIR_BARLOW ICON_TTF OUT_DIR
"""
import base64, hashlib, json, os, re, shutil, sys, zipfile
from PIL import Image, ImageDraw, ImageFont

src_path, bc_dir, b_dir, icon_ttf, out = sys.argv[1:6]
os.makedirs(out, exist_ok=True)
src = open(src_path, encoding="utf-8").read()

# ---- fonts: inline the woff2 files as data URIs (no network at the track) ----
def face(family, weight, path):
    data = base64.b64encode(open(path, "rb").read()).decode()
    return ("@font-face{font-family:\"%s\";font-style:normal;font-weight:%d;font-display:swap;"
            "src:url(data:font/woff2;base64,%s) format(\"woff2\")}" % (family, weight, data))

faces = []
for w in (500, 600, 700):
    faces.append(face("Barlow Condensed", w, os.path.join(bc_dir, "barlow-condensed-latin-%d-normal.woff2" % w)))
for w in (400, 500, 600):
    faces.append(face("Barlow", w, os.path.join(b_dir, "barlow-latin-%d-normal.woff2" % w)))
font_css = "<style>" + "".join(faces) + "</style>"

# ---- split the source into head part (title/meta/style) and body part ----
cut = src.index('<div id="app">')
head_part, body_part = src[:cut], src[cut:]
head_part = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>', font_css, head_part)
head_part = re.sub(r'<meta name="claude:viewport-fit-sides"[^>]*>\s*', "", head_part)

pwa_head = """<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<meta name="theme-color" content="#0b0e13" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#e8ecf2" media="(prefers-color-scheme: light)">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="NOSPONSOR NOFUEL">
<meta name="description" content="Cronómetro de pit para RC nitro: depósito, plano de paragens, calculadora de runtime. Funciona offline.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<style>
/* standalone shell: keep content clear of notches and system bars */
html{height:100%;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);box-sizing:border-box;background:#0b0e13}
@media (prefers-color-scheme: light){html{background:#e8ecf2}}
</style>
"""
sw_script = """
<script>
if('serviceWorker' in navigator){
  window.addEventListener('load',function(){ navigator.serviceWorker.register('./sw.js').catch(function(){}); });
}
</script>
"""
index_html = pwa_head + head_part + "</head>\n<body>\n" + body_part + sw_script + "</body>\n</html>\n"
ver = hashlib.sha256(index_html.encode()).hexdigest()[:10]
index_html = index_html.replace("build dev", "build " + ver)
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(index_html)

# ---- icons ----
BG, ACCENT, OK, FG = (11, 14, 19), (78, 161, 255), (53, 208, 127), (237, 241, 247)

def icon(size, rounded, pad_frac):
    im = Image.new("RGBA", (size, size), BG + (255,))
    d = ImageDraw.Draw(im)
    if rounded:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
        bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        bg.paste(im, mask=mask)
        im = bg
        d = ImageDraw.Draw(im)
    # content inside the maskable safe zone
    box = size * (1 - 2 * pad_frac)
    fnt = ImageFont.truetype(icon_ttf, int(box * 0.62))
    txt = "NF"
    bb = d.textbbox((0, 0), txt, font=fnt)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (size - tw) / 2 - bb[0]
    y = (size - th) / 2 - bb[1] - box * 0.10
    d.text((x, y), txt, font=fnt, fill=ACCENT + (255,))
    # tank bar under the letters, 70% full (glyph bottom is at y + bb[3])
    bw, bh = box * 0.78, max(4, int(box * 0.09))
    bx, by = (size - bw) / 2, y + bb[3] + box * 0.10
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=bh / 2, fill=(29, 36, 48, 255))
    d.rounded_rectangle([bx, by, bx + bw * 0.7, by + bh], radius=bh / 2, fill=OK + (255,))
    return im

icon(512, False, 0.16).save(os.path.join(out, "icon-512.png"))     # maskable: safe zone respected
icon(192, False, 0.16).save(os.path.join(out, "icon-192.png"))
icon(180, False, 0.12).convert("RGB").save(os.path.join(out, "apple-touch-icon.png"))  # iOS rounds it itself

# ---- manifest ----
manifest = {
    "name": "NOSPONSOR NOFUEL",
    "short_name": "NSNF",
    "description": "Cronómetro de pit para RC nitro, 100% offline.",
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

# ---- service worker: the page itself is network-first (short timeout) so a new build is used on the
# first opening with network; everything else is cache-first. Offline always falls back to the cache. ----
sw = """// NOSPONSOR NOFUEL · service worker · build %s
const CACHE='nsnf-%s';
const SHELL=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png','./apple-touch-icon.png'];
self.addEventListener('install',e=>{ e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())); });
self.addEventListener('activate',e=>{ e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())); });
function withTimeout(p,ms){ return new Promise((res,rej)=>{ const t=setTimeout(()=>rej(new Error('timeout')),ms); p.then(v=>{clearTimeout(t);res(v);},e=>{clearTimeout(t);rej(e);}); }); }
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  const url=new URL(e.request.url);
  if(url.origin!==self.location.origin) return;
  const isPage=e.request.mode==='navigate'||url.pathname.endsWith('/')||url.pathname.endsWith('/index.html');
  if(isPage){
    e.respondWith(withTimeout(fetch(e.request),2500).then(res=>{
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
""" % (ver, ver)
open(os.path.join(out, "sw.js"), "w", encoding="utf-8").write(sw)

readme = """NOSPONSOR NOFUEL · app offline para Android e iOS
=================================================

Conteúdo desta pasta (publicar tal e qual, todos os ficheiros na mesma pasta):
  index.html            a app completa (fontes incluídas, sem dependências externas)
  sw.js                 service worker: guarda a app no aparelho para funcionar sem rede
  manifest.webmanifest  nome, ícone e modo ecrã inteiro para "Adicionar ao ecrã inicial"
  icon-192.png, icon-512.png, apple-touch-icon.png

1. Publicar numa morada HTTPS (obrigatório para funcionar offline e para instalar)
   Qualquer uma serve, todas gratuitas:
   - GitHub Pages: repositório novo, carregar estes ficheiros, Settings > Pages > Branch main > Save.
     Fica em https://<utilizador>.github.io/<repositório>/
   - Netlify Drop (app.netlify.com/drop): arrastar a pasta, fica logo publicada.
   - Cloudflare Pages: igual, arrastar a pasta.

2. Instalar nos aparelhos (uma vez, com rede)
   Android (Chrome): abrir a morada > menu ⋮ > "Instalar app" (ou "Adicionar ao ecrã inicial").
   iPhone/iPad (Safari, obrigatoriamente Safari): abrir a morada > botão Partilhar > "Adicionar ao Ecrã principal".
   Abrir uma vez a partir do ícone. A partir daí funciona sem rede, em ecrã inteiro.

3. Atualizar
   Substituir os ficheiros na mesma morada. Na próxima abertura com rede o aparelho descarrega a versão nova
   e usa-a na abertura seguinte. Histórico, calibrações e configurações ficam no aparelho e não se perdem.

Notas
   - Cada aparelho tem o seu histórico e as suas configurações (guardados localmente, sem conta nem servidor).
   - iOS não vibra (limitação do sistema); os sons funcionam depois do primeiro toque.
   - Para não perder o histórico no iPhone/iPad, usar sempre a app instalada no ecrã inicial, não o Safari.

Build %s
""" % ver
open(os.path.join(out, "LEIA-ME.txt"), "w", encoding="utf-8").write(readme)

zip_path = os.path.join(os.path.dirname(out.rstrip("/")), "NOSPONSOR-NOFUEL-pwa.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for name in sorted(os.listdir(out)):
        z.write(os.path.join(out, name), arcname="NOSPONSOR-NOFUEL/" + name)
print("build", ver, "index.html", len(index_html.encode()) // 1024, "KB ->", zip_path)
