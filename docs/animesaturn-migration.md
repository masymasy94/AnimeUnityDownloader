# AnimeSaturn — migrazione sito (provider disattivato)

**Stato:** `AnimeSaturnProvider` **de-registrato** in `backend/app/main.py` (commit `cce2bac`).
Il file `backend/app/services/providers/animesaturn_provider.py` è rimasto in repo (lo
importa `backend/tests/test_download_path_containment.py` per la stabilità degli ID) ma non
è più tra le fonti: non compare in `/api/sites`, ricerca, o player.

**Perché:** AnimeSaturn ha migrato *tutto* il sito. Il provider puntava ai vecchi endpoint,
quindi ogni ricerca faceva `response.json()` su una pagina 404 HTML → `Expecting value:
line 1 column 1 (char 0)` → 0 risultati sempre. animeunity e animeworld non sono toccati.

## Cosa è cambiato (vecchio → nuovo)

| Passo | Vecchio (nel provider) | Nuovo (sito live, 2026-08) |
|---|---|---|
| Dominio | `https://www.animesaturn.cx` | **`https://www.animesaturn.net`** (il `.cx` fa 302 sul `.net`) |
| Ricerca | `GET /index.php?search=1&key=<q>` → **JSON** array | `GET /filter?key=<q>` → **HTML**, card con `href="/anime/<slug>"` |
| Lista episodi | pagina `/anime/<slug>`, `soup.select("a.bottone-ep")`, href `/ep/...` | pagina `/anime/<slug>`, link **`/episode/<slug>/ep-N`** (numero nell'URL) |
| Pagina player | link `/watch?...` sulla pagina episodio | pulsante "Guarda lo streaming" → **`/anime/<slug>/ep-N`** (≠ `/episode/...`) |
| Sorgente video | `file:"...mp4"` inline / `<source>` | `<iframe src="https://play.saturncdn.net/embed/<id>?token=<k>&expires=<e>">` |

## Come si arriva al media (nuovo flusso, da implementare in `resolve_download_url`)

1. `GET /anime/<slug>/ep-N` → estrai l'iframe:
   `https://play.saturncdn.net/embed/<id>?token=<k>&expires=<e>`
2. La pagina embed espone `window.__E = {i:<id>, k:"<token>", e:<expires>}` e carica
   `assets/js/embed/embed.js`, che fa:
   `fetch("/embed/" + i + "/playlist?token=" + encodeURIComponent(k) + "&expires=" + e)`
3. `GET https://play.saturncdn.net/embed/<id>/playlist?token=<k>&expires=<e>`
   (Referer = la URL embed) → **JSON** `{"d":"<stringa offuscata>","p":"","t":""}`.

## Nodo aperto: decodifica del campo `d`

Il media URL (m3u8/mp4) **non è in chiaro** nella risposta `/playlist`: sta nel campo `d`,
offuscato lato client. La logica di decodifica è dentro `embed.js` (minificato) — va
reversata da lì. Esempio reale catturato (token già scaduto):

```
d = "UUZNRRFZG0pEEUIHAU1GVllRH0dEEQNQCUkEBFsBS01WQF4a..."  (base64-ish, poi de-XOR)
```

Sospetto uno schema tipo `base64 → XOR con chiave derivata da token/expires`. Prossimo
passo per il rewrite: leggere la funzione in `embed.js` che consuma `window.__E` e il campo
`d`, e replicarla in Python.

## Note pratiche

- Serve **`curl_cffi` con `impersonate="chrome"`** (Cloudflare); httpx semplice regge le
  pagine HTML ma non dare per scontato l'embed/playlist.
- ID episodio stabili: il provider usa `zlib.crc32(href) % 10_000_000` — mantenere lo stesso
  schema o le vecchie voci in DB (download tracciati) non combaciano più.
