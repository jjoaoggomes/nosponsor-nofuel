# NOSPONSOR NOFUEL

Cronómetro de pit para RC nitro (Android e iOS, 100% offline).

- Raiz do repositório: a app publicada em GitHub Pages (`index.html`, `sw.js`, `manifest.webmanifest`, ícones).
- `src/app.html`: fonte da app (página única). `src/build.py` gera a raiz a partir dela, embebendo as fontes Barlow e Barlow Condensed (pacotes `@fontsource/*` do npm) e carimbando a versão do service worker.
- Instalar: Android em Chrome → "Instalar app"; iPhone/iPad em Safari → Partilhar → "Adicionar ao Ecrã principal". Ver `LEIA-ME.txt`.
