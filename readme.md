# 🏛️ Permesso Checker — Verifica Permesso di Soggiorno

> Controlla se il tuo **permesso di soggiorno è pronto** usando il numero della **ricevuta Poste** (kit giallo).
> Made by [**zeinthdev-team**](https://zeinthdev-team.vercel.app) 🌐

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![Deps](https://img.shields.io/badge/dependencies-0-green)
![HTML5](https://img.shields.io/badge/HTML5-vanilla-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-gov__style-1572B6?logo=css3&logoColor=white)
![JS](https://img.shields.io/badge/JavaScript-vanilla-F7DF1E?logo=javascript&logoColor=black)
![i18n](https://img.shields.io/badge/languages-IT%20%7C%20EN%20%7C%20FR%20%7C%20AR%20%7C%20ES-orange)
![Source](https://img.shields.io/badge/source-Polizia_di_Stato-005fa8)
![Team](https://img.shields.io/badge/made_by-zeinthdev--team-111?logo=vercel&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## ✨ Cosa fa

1. Inserisci il codice della ricevuta → **N. Pratica (10)** oppure **N. Assicurata (12)**
2. L'app interroga il sito ufficiale `questure.poliziadistato.it/stranieri` e legge l'esito
3. Risultato chiaro e colorato:
   - ✅ **Pronto** → vai a ritirare (controlla SMS + ufficio)
   - 🟠 **In trattazione** → ancora in lavorazione
   - 🔴 **Non presente in archivio** → numero errato o pratica troppo recente
   - ⚪ **Errore** → sito ufficiale non raggiungibile

Nessun dato salvato sul server. Cronologia solo nel tuo browser (cancellabile).

## 🖥️ UI in stile gov

Replica fedele del sito ufficiale: barra nera, banda tricolore 🇮🇹, testata blu *Polizia di Stato — Questure*, menu, breadcrumb *Ti trovi qui*, box lingue, form ufficiale, nota SMS, footer a colonne.

Tab integrate:

| Tab | Contenuto |
|-----|-----------|
| 🏠 **Home** | Hero + avvio rapido + legenda stati |
| 🔍 **Verifica** | Form + copia esito / stampa / demo / cronologia ↻ |
| 🧾 **Dove trovo il codice?** | Schema ricevuta, Pratica vs Assicurata vs User/Password, Poste vs Questura |
| 🪜 **Le 5 fasi** | Poste → Impronte → Verifica → SMS → Ritiro |
| ❓ **FAQ** | Accordion: non trovato, tempi, pronto, pre-impronte, privacy… |
| 🏢 **Uffici e link** | Sito ufficiale, Portale Immigrazione, guida Poste, trova Questura |

## 🛠️ Tech stack

| Tech | Uso |
|------|-----|
| ![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white) **Python 3.8+ (stdlib only)** | Backend — `http.server` + `urllib`, zero `pip install` |
| ![HTML](https://img.shields.io/badge/-HTML5-E34F26?logo=html5&logoColor=white) **HTML5** | UI single-file in `INDEX_HTML` stile gov |
| ![CSS](https://img.shields.io/badge/-CSS3-1572B6?logo=css3&logoColor=white) **CSS3** | Tema Polizia, responsive, print CSS |
| ![JS](https://img.shields.io/badge/-JS-F7DF1E?logo=javascript&logoColor=black) **Vanilla JS (no framework)** | Tabs, i18n, fetch API, clipboard, localStorage |
| 🌍 **i18n custom** | IT / EN / FR / AR (RTL) / ES, persistenza lingua |
| 🏛️ **Polizia di Stato API (scraping)** | `GET questure.poliziadistato.it/stranieri/?pratica=XXX`, parse `<div class="m-ok">` |
| 🔧 **Git + GitHub** | Versionamento — `github.com/zakariaelqannaa-dv` |
| ▲ **Vercel** | Hosting team site — `zeinthdev-team.vercel.app` |

> **Zero dipendenze.** Niente Flask, niente npm. Solo `python3 gov.py`.

## 🚀 Avvio rapido

```bash
git clone https://github.com/zakariaelqannaa-dv/permesso-soggiorno-verifica.git
cd permesso-soggiorno-verifica
python3 gov.py
# apri http://127.0.0.1:8000
```

Prova veloce:

```bash
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/api/check?pratica=1234567890"
# {"ok": true, "code": "1234567890", "status": "not_found", ...}
```

## 📡 API

| Endpoint | Risposta |
|----------|----------|
| `GET /` | UI |
| `GET /api/check?pratica=XXX` | `{ok, code, status, message_it}` oppure `{ok:false, error, message}` |
| `GET /health` | `{"ok": true}` |

`status`: `ready` · `processing` · `not_found` · `unknown`

## 📁 Struttura

```
.
├── gov.py      # backend + frontend (INDEX_HTML single-file)
└── readme.md   # docs
```

## ▲ Deploy

Vercel serverless non tiene un `http.server` sempre acceso. Per la prod adatta `check_code()` a una function `/api/check.py` e servi la UI come statica. Dettagli nel codice.

## 🤝 Contribuire

```bash
git checkout -b feat/mia-modifica
git add -A && git commit -m "feat: ..."
git push -u origin feat/mia-modifica
# apri una Pull Request
```

## 👨‍💻 Maker

- **Team:** [`zeinthdev-team`](https://zeinthdev-team.vercel.app)
- **Website:** https://zeinthdev-team.vercel.app
- **GitHub:** https://github.com/zakariaelqannaa-dv

## ⚖️ Nota legale

Helper **non ufficiale** a scopo informativo. Fanno fede solo il [sito ufficiale](https://questure.poliziadistato.it/stranieri/) e l'SMS della Questura con giorno/ora/luogo del ritiro.

## 📄 License

MIT — vedi `LICENSE` (aggiungilo se distribuisci).
