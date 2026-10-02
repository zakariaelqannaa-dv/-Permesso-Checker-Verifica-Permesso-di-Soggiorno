#!/usr/bin/env python3
"""
Permesso di Soggiorno Checker
-----------------------------
Web app (stdlib only) in stile Polizia di Stato per verificare se il
permesso di soggiorno e' pronto, usando il numero della ricevuta Poste.

  - Numero pratica: 10 caratteri
  - Numero assicurata: 12 caratteri

Fonte ufficiale: https://questure.poliziadistato.it/stranieri/
Questa app interroga il sito ufficiale e mostra il risultato in modo
piu' leggibile + multilingua. Nessun dato salvato lato server.

Run:
    python3 gov.py
    -> http://127.0.0.1:8000

Nessuna dipendenza (solo Python 3.8+).
"""

import html as htmlmod
import json
import re
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = 8000

OFFICIAL_BASE = "https://questure.poliziadistato.it/stranieri/"
TIMEOUT = 20

# ---------------------------------------------------------------- backend

VALID_RE = re.compile(r"^[A-Za-z0-9]{10}$|^[A-Za-z0-9]{12}$")


def clean_code(raw: str) -> str:
    """Remove everything except letters/digits, uppercase."""
    if not raw:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", raw.strip()).upper()


def fetch_official(code: str) -> str:
    params = urllib.parse.urlencode(
        {"pratica": code, "lang": "italian", "mime": "1", "invia": "Invia"}
    )
    url = OFFICIAL_BASE + "?" + params
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Permesso-Checker)"}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        charset = r.headers.get_content_charset() or "utf-8"
        return r.read().decode(charset, errors="ignore")


def parse_result(html_page: str) -> dict:
    m = re.search(r'<div class="m-ok">(.*?)</div>', html_page, re.S | re.I)
    if not m:
        return {"status": "unknown", "message_it": "Risposta non riconosciuta dal sito ufficiale."}
    inner = m.group(1)
    text = re.sub(r"<[^>]+>", " ", inner)
    text = htmlmod.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    low = text.lower()
    if "non è presente in archivio" in low or "non e' presente" in low or "not present" in low:
        status = "not_found"
    elif "trattazione" in low or "in lavorazione" in low or "processing" in low:
        status = "processing"
    elif "pronto" in low or "ritiro" in low or "consegna" in low or "ready" in low:
        status = "ready"
    else:
        status = "unknown"
    return {"status": status, "message_it": text}


def check_code(raw: str) -> dict:
    code = clean_code(raw)
    if len(code) not in (10, 12):
        return {
            "ok": False,
            "error": "CODE_LENGTH",
            "message": f"Codice non valido: ho letto {len(code)} caratteri ('{code}') dopo aver rimosso spazi/simboli. Deve essere 10 (pratica) o 12 (assicurata).",
        }
    if not VALID_RE.match(code):
        return {
            "ok": False,
            "error": "CODE_INVALID",
            "message": "Il codice deve contenere solo lettere e numeri.",
        }
    try:
        html_page = fetch_official(code)
    except Exception as e:
        return {"ok": False, "error": "FETCH_FAILED", "message": f"Impossibile contattare il sito ufficiale: {e}"}
    parsed = parse_result(html_page)
    return {"ok": True, "code": code, **parsed}


# ---------------------------------------------------------------- frontend (stile Polizia di Stato)

INDEX_HTML = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Permesso di soggiorno | Verifica pratica</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#fff;color:#222;font-size:15px;line-height:1.5}
/* barra nera superiore come sito ufficiale */
.topbar{background:#111;color:#ddd;font-size:12px}
.topbar .wrap{max-width:1000px;margin:0 auto;padding:6px 12px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.topbar a{color:#ddd;text-decoration:none;margin-right:14px}.topbar a:hover{text-decoration:underline}
/* tricolore */
.tricolore{height:4px;background:linear-gradient(to right,#009246 33%,#fff 33%,#fff 66%,#ce2b37 66%)}
/* testata */
.testata{max-width:1000px;margin:0 auto;padding:14px 12px;display:flex;align-items:center;gap:14px;border-bottom:4px solid #005fa8}
.stemma{width:56px;height:56px;border-radius:50%;background:#005fa8;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:11px;text-align:center;line-height:1.1;flex-shrink:0}
.testata h1{margin:0;color:#005fa8;font-size:26px;letter-spacing:.5px}
.testata small{color:#555;font-size:13px}
/* menu blu */
.menu{background:#005fa8;color:#fff;font-size:13px;font-weight:bold}
.menu .wrap{max-width:1000px;margin:0 auto;padding:0 12px;display:flex;gap:6px;flex-wrap:wrap}
.menu button{background:none;border:none;color:#fff;font-size:13px;font-weight:bold;padding:10px 8px;cursor:pointer}
.menu button:hover,.menu button.active{background:#004a85;text-decoration:underline}
/* home hero */
.hero{background:#eaf2fb;border:1px solid #bcd3ee;border-radius:8px;padding:20px;margin:12px 0}
.hero h3{margin:0 0 8px;color:#005fa8;font-size:20px}
.hero p{margin:6px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:12px 0}
.cards button{text-align:left;background:#fff;border:1px solid #ccc;border-radius:8px;padding:12px;cursor:pointer}
.cards button:hover{border-color:#005fa8;background:#f6faff}
.cards b{color:#005fa8;display:block;margin-bottom:4px}
.status-legend{font-size:14px;margin:10px 0}
#toast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:#111;color:#fff;padding:10px 16px;border-radius:8px;font-size:14px;display:none;z-index:99}
@media print{.topbar,.menu,.tabs,.box-lingue,.btn-row,.btn-invia,footer,.crumb,#tabs{display:none!important}.tabpage{display:block!important;border:none}}
/* breadcrumb */
.crumb{max-width:1000px;margin:0 auto;padding:8px 12px;font-size:12px;color:#666}
.crumb a{color:#005fa8}
/* contenuto */
.container{max-width:1000px;margin:0 auto;padding:0 12px 30px}
h2{color:#222;font-size:24px;margin:14px 0 6px}
/* box lingue come ufficiale */
.box-lingue{background:#e9e9e9;padding:10px;margin:10px 0 18px;font-size:13px}
.box-lingue .lbl{display:inline-block;background:#005fa8;color:#fff;padding:2px 8px;border-radius:3px;font-weight:bold}
.lang-btns{margin-top:8px;display:flex;gap:6px;flex-wrap:wrap}
.lang-btns button{border:1px solid #bbb;background:#fff;padding:5px 12px;font-size:13px;cursor:pointer;border-radius:4px}
.lang-btns button.active{background:#005fa8;color:#fff;border-color:#005fa8}
/* tabs aiuto */
.tabs{display:flex;gap:0;border-bottom:2px solid #005fa8;margin:14px 0 0;flex-wrap:wrap}
.tabs button{border:1px solid #ccc;border-bottom:none;background:#f1f1f1;padding:9px 14px;font-size:13px;cursor:pointer;font-weight:bold;color:#333}
.tabs button.active{background:#005fa8;color:#fff;border-color:#005fa8}
.tabpage{display:none;border:1px solid #ccc;border-top:none;padding:18px;background:#fff}
.tabpage.active{display:block}
/* form pratica come ufficiale */
.form-pratica{max-width:620px;margin:0 auto;text-align:left}
.form-pratica label{text-transform:uppercase;font-weight:bold;font-size:14px;display:block;margin:8px 0}
.form-pratica input{width:100%;font-size:20px;letter-spacing:2px;text-transform:uppercase;padding:12px;border:1px solid #999;border-radius:4px}
.form-pratica input:focus{outline:2px solid #005fa8}
.btn-invia{width:100%;margin-top:12px;background:#005fa8;color:#fff;border:none;padding:13px;font-size:17px;font-weight:bold;border-radius:4px;cursor:pointer}
.btn-invia:hover{background:#004a85}.btn-invia:disabled{opacity:.6}
.btn-row{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.btn-row button,.btn-row a{flex:1;min-width:140px;padding:10px;font-size:13px;border:1px solid #005fa8;background:#fff;color:#005fa8;border-radius:4px;cursor:pointer;text-align:center;text-decoration:none}
.btn-row button:hover,.btn-row a:hover{background:#eaf2fb}
.note{font-style:italic;color:#777;font-size:13px;margin-top:14px;border-top:1px solid #ccc;padding-top:10px}
/* risultato stile m-ok ufficiale + colori nostri */
.m-ok{text-align:center;margin:18px 0;padding:18px;border-radius:8px;display:none;font-size:17px}
.m-ok.show{display:block}
.m-ok.ready{background:#e7f6ec;border:2px solid #198754}
.m-ok.processing{background:#fff8e6;border:2px solid #e8890c}
.m-ok.not_found{background:#fdecec;border:2px solid #ce2b37}
.m-ok.unknown,.m-ok.error{background:#eef1f6;border:2px solid #666}
.m-ok .big{font-size:46px}
.m-ok.ready .big{color:#198754}.m-ok.processing .big{color:#e8890c}.m-ok.not_found .big{color:#ce2b37}
.m-ok h3{margin:8px 0}
.m-ok code{background:#fff;padding:2px 8px;border-radius:4px;border:1px solid #ccc}
/* tabelle aiuto */
table.help{width:100%;border-collapse:collapse;font-size:14px;margin:10px 0}
table.help th,table.help td{border:1px solid #ccc;padding:8px;text-align:left}
table.help th{background:#005fa8;color:#fff}
.ricevuta{border:2px dashed #005fa8;padding:14px;background:#f6faff;border-radius:8px;font-family:monospace;font-size:14px;margin:10px 0}
.timeline{margin:10px 0;padding-left:0;list-style:none}
.timeline li{padding:10px 10px 10px 44px;position:relative;border-left:3px solid #005fa8;margin-left:14px;background:#f8fafd;margin-bottom:8px;border-radius:0 8px 8px 0}
.timeline li b.num{position:absolute;left:-17px;top:8px;width:30px;height:30px;background:#005fa8;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center}
details{border:1px solid #ccc;border-radius:6px;margin:8px 0;padding:10px;background:#fafafa}
details summary{font-weight:bold;cursor:pointer;color:#005fa8}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:bold;color:#fff}
.b-green{background:#198754}.b-orange{background:#e8890c}.b-red{background:#ce2b37}.b-grey{background:#666}
.hist{font-size:13px}ul.hist{padding-left:18px}
/* footer come ufficiale */
footer{border-top:1px solid #ccc;margin-top:20px;background:#f5f5f5;font-size:13px}
footer .cols{max-width:1000px;margin:0 auto;padding:18px 12px;display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px}
footer b{color:#005fa8}
footer a{color:#333;text-decoration:none;display:block;margin:4px 0}footer a:hover{text-decoration:underline}
.legal{text-align:center;font-size:12px;color:#888;padding:12px;border-top:1px solid #ddd}
.rtl{direction:rtl}.rtl .form-pratica{text-align:right}
@media(max-width:640px){.testata h1{font-size:20px}.tabs button{flex:1;font-size:12px;padding:8px 6px}}
</style>
</head>
<body>
<div class="topbar"><div class="wrap">
<div><a href="https://www.interno.gov.it/">Ministero dell'Interno</a><a href="https://www.poliziadistato.it/">Polizia di Stato</a><a href="https://www.poste.it/">Poste Italiane</a></div>
<div><span id="top-lang">Lingua / Language</span></div>
</div></div>
<div class="tricolore"></div>
<div class="testata">
<div class="stemma">PS<br>★</div>
<div><h1 id="t-h1">Polizia di Stato — Questure</h1><small id="t-head-sub">Servizio stranieri · Verifica permesso di soggiorno (helper non ufficiale)</small> <small>· by <a href="https://zeinthdev-team.vercel.app" target="_blank" rel="noopener" style="color:#005fa8;font-weight:bold">zeinthdev-team</a></small></div>
</div>
<div class="menu"><div class="wrap"><button data-goto="home" class="active">HOME</button><button data-goto="verifica">VERIFICA</button><button data-goto="dove">DOVE TROVO IL CODICE</button><button data-goto="faq">AIUTO / FAQ</button><button data-goto="uffici">UFFICI</button></div></div>
<div class="crumb"><span id="t-youare">Ti trovi qui:</span> <a href="#" id="crumb-home">Home</a> &gt; <a href="#">Stranieri</a> &gt; <b id="t-crumb-here">Verifica pratica</b></div>

<div class="container">
<h2 id="t-title">Permesso di soggiorno</h2>

<div class="box-lingue">
<div><span id="t-langsel">Lingua selezionata:</span> <span class="lbl" id="lbl-lang">italiano</span></div>
<div class="lang-btns" id="langs"></div>
</div>

<div class="tabs" id="tabs">
<button data-tab="home" class="active">🏠 <span data-i="tab0">Home</span></button>
<button data-tab="verifica">🔍 <span data-i="tab1">Verifica</span></button>
<button data-tab="dove">🧾 <span data-i="tab2">Dove trovo il codice?</span></button>
<button data-tab="fasi">🪜 <span data-i="tab3">Le 5 fasi</span></button>
<button data-tab="faq">❓ <span data-i="tab4">FAQ / Aiuto</span></button>
<button data-tab="uffici">🏢 <span data-i="tab5">Uffici e link</span></button>
</div>

<!-- TAB HOME -->
<div class="tabpage active" id="page-home">
<div class="hero">
<h3 id="t-hero-t">Controlla se il tuo permesso è pronto in 10 secondi</h3>
<p id="t-hero-s">Inserisci il numero della ricevuta Poste (pratica 10 o assicurata 12). Interroghiamo il sito ufficiale della Polizia di Stato.</p>
<p style="font-size:13px">Made by <a href="https://zeinthdev-team.vercel.app" target="_blank" rel="noopener" style="color:#005fa8;font-weight:bold">zeinthdev-team</a> · <a href="https://zeinthdev-team.vercel.app" target="_blank" rel="noopener">zeinthdev-team.vercel.app</a></p>
<div class="btn-row" style="max-width:480px">
<button id="btn-start" style="background:#005fa8;color:#fff;border-color:#005fa8;font-weight:bold">🔍 <span data-i="start">Inizia verifica</span></button>
<button id="btn-demo2">🧪 <span data-i="demo">Prova demo</span></button>
</div>
</div>
<div class="cards">
<button data-goto="dove"><b>🧾 <span data-i="c1t">Dove trovo il codice?</span></b><span data-i="c1s">Foto-guida ricevuta Poste, pratica vs assicurata.</span></button>
<button data-goto="fasi"><b>🪜 <span data-i="c2t">Le 5 fasi</span></b><span data-i="c2s">Da Poste alle impronte fino all'SMS di ritiro.</span></button>
<button data-goto="faq"><b>❓ <span data-i="c3t">Non trovato? Aiuto</span></b><span data-i="c3s">Cosa significano pronto / trattazione / non presente.</span></button>
</div>
<div class="status-legend" id="t-legend"></div>
</div>

<!-- TAB VERIFICA -->
<div class="tabpage" id="page-verifica">
<div class="form-pratica">
<label for="code" id="t-label">Numero pratica o assicurata</label>
<input id="code" maxlength="12" placeholder="es. 1234567890" autocomplete="off">
<button class="btn-invia" id="btn">Invia</button>
<div class="btn-row">
<button id="btn-demo">🧪 <span data-i="demo">Prova demo</span></button>
<button id="btn-copy">📋 <span data-i="copy">Copia esito</span></button>
<button id="btn-print">🖨️ <span data-i="print">Stampa</span></button>
<a href="https://questure.poliziadistato.it/stranieri/" target="_blank" rel="noopener">🏛️ <span data-i="official">Sito ufficiale</span></a>
</div>
<div class="m-ok" id="result"></div>
<p class="note" id="t-note">Inserisci il numero di pratica (10 caratteri) o il tuo numero di assicurata (12 caratteri) della richiesta del tuo permesso di soggiorno.<br>Oltre all'avviso visualizzabile tramite questo sistema informatico, sullo stato del procedimento, sarà inviato al cittadino straniero un SMS con giorno, ora e luogo del ritiro.</p>
<div class="official" style="font-size:12px;color:#666">Fonte: <a href="https://questure.poliziadistato.it/stranieri/" target="_blank" rel="noopener">questure.poliziadistato.it/stranieri</a> · <span id="t-disc">Helper non ufficiale. Nessun dato salvato sul server.</span></div>
</div>
<div style="margin-top:16px"><b id="t-hist-t">Ultime ricerche (solo su questo dispositivo)</b> <button id="btn-clear" style="font-size:12px">✖ <span data-i="clear">cancella</span></button>
<ul class="hist" id="hist"></ul></div>
</div>

<!-- TAB DOVE -->
<div class="tabpage" id="page-dove">
<div id="c-dove"></div>
</div>

<!-- TAB FASI -->
<div class="tabpage" id="page-fasi">
<div id="c-fasi"></div>
</div>

<!-- TAB FAQ -->
<div class="tabpage" id="page-faq">
<div id="c-faq"></div>
</div>

<!-- TAB UFFICI -->
<div class="tabpage" id="page-uffici">
<div id="c-uffici"></div>
</div>

</div>

<footer><div class="cols">
<div><b>Chi siamo</b><a href="https://www.poliziadistato.it/">Polizia di Stato</a><a href="https://questure.poliziadistato.it/">Le Questure</a></div>
<div><b>Per il cittadino</b><a href="https://www.poliziadistato.it/articolo/15002">Stranieri</a><a href="https://www.poste.it/guida-rilascio-e-rinnovo-permesso-di-soggiorno">Guida Poste</a></div>
<div><b>Servizi online</b><a href="https://questure.poliziadistato.it/stranieri/">Verifica pratica (ufficiale)</a><a href="https://www.portaleimmigrazione.it/">Portale Immigrazione</a></div>
<div><b>Maker</b><a href="https://zeinthdev-team.vercel.app" target="_blank" rel="noopener">🌐 zeinthdev-team — website</a><a href="https://github.com/zakariaelqannaa-dv" target="_blank" rel="noopener">GitHub: zakariaelqannaa-dv</a><a href="/health">Stato servizio (health)</a></div>
</div>
<div class="legal">Made by <a href="https://zeinthdev-team.vercel.app" target="_blank" rel="noopener" style="display:inline;color:#005fa8;font-weight:bold">zeinthdev-team</a> · Helper non ufficiale — fai fede al sito ufficiale e all'SMS della Questura. · <span id="t-foot">Conferma sempre sul sito ufficiale.</span></div>
</footer>
<div id="toast"></div>

<script>
const I18N = {
it:{langName:"italiano",h1:"Polizia di Stato — Questure",headSub:"Servizio stranieri · Verifica permesso di soggiorno (helper non ufficiale)",youAre:"Ti trovi qui:",crumbHere:"Verifica pratica",title:"Permesso di soggiorno",langSel:"Lingua selezionata:",tab1:"Verifica",tab2:"Dove trovo il codice?",tab3:"Le 5 fasi",tab4:"FAQ / Aiuto",tab5:"Uffici e link",label:"Numero pratica o assicurata",btn:"Invia",copy:"Copia esito",print:"Stampa",official:"Sito ufficiale",clear:"cancella",note:"Inserisci il numero di pratica (10 caratteri) o il tuo numero di assicurata (12 caratteri) della richiesta del tuo permesso di soggiorno.<br>Oltre all'avviso visualizzabile tramite questo sistema informatico, sullo stato del procedimento, sarà inviato al cittadino straniero un SMS con giorno, ora e luogo del ritiro.",disc:"Helper non ufficiale. Nessun dato salvato sul server.",histT:"Ultime ricerche (solo su questo dispositivo)",foot:"Conferma sempre sul sito ufficiale.",ready:"PERMESSO PRONTO — PUOI RITIRARLO",processing:"PRATICA IN TRATTAZIONE",not_found:"NON PRESENTE IN ARCHIVIO",unknown:"RISPOSTA NON RICONOSCIUTA",error:"ERRORE",checking:"Controllo in corso…",needCode:"Inserisci un codice di 10 o 12 caratteri."},
en:{langName:"english",h1:"State Police — Questure",headSub:"Foreigners service · Residence permit check (unofficial helper)",youAre:"You are here:",crumbHere:"File check",title:"Residence permit",langSel:"Selected language:",tab1:"Check",tab2:"Where is my code?",tab3:"5 steps",tab4:"FAQ / Help",tab5:"Offices & links",label:"Pratica or assicurata number",btn:"Send",copy:"Copy result",print:"Print",official:"Official site",clear:"clear",note:"Enter the 10-character pratica number or your 12-character assicurata number.<br>In addition to this system, you will receive an SMS with day, time and place to collect the permit.",disc:"Unofficial helper. No data stored on server.",histT:"Recent checks (only on this device)",foot:"Always confirm on the official site.",ready:"PERMIT READY — YOU CAN COLLECT IT",processing:"FILE UNDER PROCESSING",not_found:"NOT FOUND IN ARCHIVE",unknown:"UNKNOWN RESPONSE",error:"ERROR",checking:"Checking…",needCode:"Enter a 10 or 12 character code."},
fr:{langName:"français",h1:"Police d'État — Questure",headSub:"Service étrangers · Vérification du titre (assistant non officiel)",youAre:"Vous êtes ici :",crumbHere:"Vérification",title:"Titre de séjour",langSel:"Langue sélectionnée :",tab1:"Vérifier",tab2:"Où est mon code ?",tab3:"5 étapes",tab4:"FAQ / Aide",tab5:"Bureaux & liens",label:"Numéro pratica ou assicurata",btn:"Envoyer",copy:"Copier",print:"Imprimer",official:"Site officiel",clear:"effacer",note:"Saisissez le numéro pratica (10 caractères) ou assicurata (12 caractères).<br>En plus de cet avis, vous recevrez un SMS avec jour, heure et lieu du retrait.",disc:"Assistant non officiel. Aucune donnée sauvegardée.",histT:"Recherches récentes (cet appareil)",foot:"Confirmez toujours sur le site officiel.",ready:"TITRE PRÊT — À RETIRER",processing:"DOSSIER EN COURS",not_found:"INTROUVABLE",unknown:"RÉPONSE INCONNUE",error:"ERREUR",checking:"Vérification…",needCode:"Saisissez un code de 10 ou 12 caractères."},
ar:{langName:"العربية",h1:"الشرطة الإيطالية — Questure",headSub:"خدمة الأجانب · التحقق من تصريح الإقامة (مساعد غير رسمي)",youAre:"أنت هنا:",crumbHere:"التحقق",title:"تصريح الإقامة",langSel:"اللغة المختارة:",tab1:"تحقق",tab2:"أين الرقم؟",tab3:"الخطوات الخمس",tab4:"أسئلة شائعة",tab5:"مكاتب وروابط",label:"رقم Pratica أو Assicurata",btn:"إرسال",copy:"نسخ النتيجة",print:"طباعة",official:"الموقع الرسمي",clear:"مسح",note:"أدخل رقم Pratica (10 أحرف) أو رقم Assicurata (12 حرفًا).<br>بالإضافة لهذا النظام ستصلك رسالة SMS بيوم ومكان الاستلام.",disc:"مساعد غير رسمي. لا تُحفظ أي بيانات.",histT:"عمليات البحث الأخيرة (هذا الجهاز)",foot:"أكّد دائمًا عبر الموقع الرسمي.",ready:"التصريح جاهز — يمكنك استلامه",processing:"الملف قيد المعالجة",not_found:"غير موجود في الأرشيف",unknown:"رد غير معروف",error:"خطأ",checking:"جارٍ التحقق…",needCode:"أدخل رمزًا من 10 أو 12 حرفًا."},
es:{langName:"español",h1:"Policía de Estado — Questure",headSub:"Servicio extranjeros · Verificación (ayudante no oficial)",youAre:"Estás aquí:",crumbHere:"Verificación",title:"Permiso de residencia",langSel:"Idioma seleccionado:",tab1:"Verificar",tab2:"¿Dónde está mi código?",tab3:"5 pasos",tab4:"FAQ / Ayuda",tab5:"Oficinas y enlaces",label:"Número pratica o assicurata",btn:"Enviar",copy:"Copiar",print:"Imprimir",official:"Sitio oficial",clear:"borrar",note:"Introduce el número pratica (10) o assicurata (12).<br>Además de este aviso recibirás un SMS con día, hora y lugar de recogida.",disc:"Ayudante no oficial. Sin datos guardados.",histT:"Últimas búsquedas (este dispositivo)",foot:"Confirma siempre en el sitio oficial.",ready:"PERMISO LISTO — PUEDES RECOGERLO",processing:"EXPEDIENTE EN TRÁMITE",not_found:"NO ENCONTRADO",unknown:"RESPUESTA DESCONOCIDA",error:"ERROR",checking:"Verificando…",needCode:"Introduce un código de 10 o 12 caracteres."}
};

const HELP = {
it:{dove:`<h3>🧾 Dove trovo il codice sulla ricevuta Poste?</h3>
<div class="ricevuta">RICEVUTA POSTE — KIT GIALLO<br>------------------------------<br>N. PRATICA ....: <b>1234567890</b> (10 caratteri)<br>N. ASSICURATA .: <b>123456789012</b> (12 cifre)<br>USER / PASSWORD : servono solo per PortaleImmigrazione<br>------------------------------<br>Usa PRATICA oppure ASSICURATA, senza spazi.</div>
<table class="help"><tr><th>Codice</th><th>Lunghezza</th><th>Dove</th><th>Quando usarlo</th></tr>
<tr><td><b>N. Pratica</b></td><td>10</td><td>Ricevuta sportello / kit</td><td>Sempre — va bene per questure.poliziadistato.it</td></tr>
<tr><td><b>N. Assicurata</b></td><td>12</td><td>Scontrino spedizione</td><td>Alternativa allo stesso sito ufficiale</td></tr>
<tr><td><b>User/Password</b></td><td>variabile</td><td>Ricevuta Poste</td><td>Solo su <a href="https://www.portaleimmigrazione.it/" target="_blank">portaleimmigrazione.it</a> (fase Poste)</td></tr></table>
<p><b>Poste vs Questura:</b> <span class="badge b-orange">Poste</span> = i primi giorni (accettazione/spedizione kit) si vede su Portale Immigrazione. <span class="badge b-green">Questura</span> = dopo le impronte, si vede qui / sul sito ufficiale.</p>
<p><b>Errori comuni:</b> confondere 0 con O, 1 con I; copiare anche "N." o i trattini; usare un codice vecchio di un rinnovo precedente. Pulisci e riprova: solo lettere+numeri.</p>`,
fasi:`<h3>🪜 Le 5 fasi (timeline)</h3><ol class="timeline">
<li><b class="num">1</b><b>Spedizione kit in Poste</b><br>Conserva ricevuta + scontrino assicurata. Su portaleimmigrazione.it vedi accettazione/spedizione.</li>
<li><b class="num">2</b><b>Convocazione + impronte in Questura</b><br>Porta passaporto + ricevute + foto. Da qui la pratica entra nel sistema Polizia.</li>
<li><b class="num">3</b><b>Verifica online qui</b><br>Inserisci pratica (10) o assicurata (12). Se "non presente" subito dopo le impronte è normale: riprova dopo giorni.</li>
<li><b class="num">4</b><b>SMS della Questura</b><br>Giorno, ora e luogo del ritiro. È la comunicazione ufficiale, non basta solo il sito.</li>
<li><b class="num">5</b><b>Ritiro con ricevuta + passaporto</b><br>Controlla nome/ufficio indicati nell'esito "pronto".</li></ol>`,
faq:`<h3>❓ FAQ</h3>
<details open><summary>“Non presente in archivio” — ho sbagliato?</summary>Non necessariamente. Cause: numero digitato male · pratica troppo recente (specie prima delle impronte) · stai usando un codice di una pratica vecchia. Verifica i 10/12 caratteri, riprova tra qualche giorno, e controlla anche con l'altro codice (pratica vs assicurata).</details>
<details><summary>“In trattazione” — quanto manca?</summary>Tempi variabili per Questura (settimane/mesi). Ricontrolla ogni pochi giorni. Solo l'SMS conferma il ritiro.</details>
<details><summary>“Pronto” — cosa faccio?</summary>Leggi ufficio/giorno/ora nell'esito e nell'SMS. Porta passaporto + ricevuta + vecchio permesso se rinnovo. <button onclick="window.print()">🖨️ Stampa esito</button></details>
<details><summary>Prima delle impronte non trova nulla, è normale?</summary>Sì. Il sito Polizia si aggiorna dopo i rilievi in Questura. Prima segui la fase Poste su Portale Immigrazione con user/password della ricevuta.</details>
<details><summary>Posso controllare per un familiare?</summary>Sì, basta il suo numero pratica/assicurata. Non servono nome o data di nascita su questo sito.</details>
<details><summary>Il sito ufficiale è giù, cosa faccio?</summary>Aspetta e riprova. Questa app mostra “Impossibile contattare il sito ufficiale”. Usa il link Sito ufficiale per verifica diretta.</details>
<details><summary>È sicuro inserire il codice qui?</summary>Il codice da solo non identifica senza altri dati, ma per prudenza: cronologia solo sul tuo browser (cancellabile), nessun invio a terzi oltre al sito ufficiale al momento della verifica.</details>`,
uffici:`<h3>🏢 Uffici e link utili</h3>
<table class="help"><tr><th>Cosa</th><th>Link</th><th>A cosa serve</th></tr>
<tr><td>Verifica ufficiale</td><td><a href="https://questure.poliziadistato.it/stranieri/" target="_blank">questure.poliziadistato.it/stranieri</a></td><td>Stesso controllo senza intermediari</td></tr>
<tr><td>Portale Immigrazione</td><td><a href="https://www.portaleimmigrazione.it/" target="_blank">portaleimmigrazione.it</a></td><td>Fase Poste (user/password ricevuta)</td></tr>
<tr><td>Guida Poste</td><td><a href="https://www.poste.it/guida-rilascio-e-rinnovo-permesso-di-soggiorno" target="_blank">poste.it — guida</a></td><td>Kit, ricevuta, convocazione</td></tr>
<tr><td>Trova Questura</td><td><a href="https://questure.poliziadistato.it/" target="_blank">Le Questure sul web</a></td><td>Indirizzi e uffici immigrazione</td></tr></table>
<p> allo sportello porta sempre: passaporto + ricevuta Poste + convocazione + foto + vecchio permesso (rinnovo).</p>`},
en:{dove:`<h3>🧾 Where is the code on the Poste receipt?</h3><div class="ricevuta">POSTE RECEIPT — YELLOW KIT<br>N. PRATICA ....: <b>1234567890</b> (10 chars)<br>N. ASSICURATA .: <b>123456789012</b> (12 digits)</div><p><b>Poste vs Questura:</b> Poste phase (first days) → Portale Immigrazione with user/password. After fingerprints → check here / official Polizia site with pratica (10) or assicurata (12).</p>`,
fasi:`<h3>🪜 5 steps</h3><ol class="timeline"><li><b class="num">1</b><b>Send kit at Poste</b> — keep receipt.</li><li><b class="num">2</b><b>Fingerprints at Questura</b> — bring passport + receipts.</li><li><b class="num">3</b><b>Check online here</b> — pratica (10) or assicurata (12).</li><li><b class="num">4</b><b>Questura SMS</b> — day/time/place.</li><li><b class="num">5</b><b>Collect</b> with passport + receipt.</li></ol>`,
faq:`<h3>❓ FAQ</h3><details open><summary>"Not found" — did I fail?</summary>Not necessarily: typo, file too recent (esp. before fingerprints), or old code. Try both pratica and assicurata, retry in a few days.</details><details><summary>"Processing" — how long?</summary>Weeks/months depending on Questura. Only the SMS confirms collection.</details><details><summary>"Ready" — what now?</summary>Check office/day in result + SMS. Bring passport + receipt.</details>`,
uffici:`<h3>🏢 Links</h3><table class="help"><tr><th>What</th><th>Link</th></tr><tr><td>Official check</td><td><a href="https://questure.poliziadistato.it/stranieri/" target="_blank">questure.poliziadistato.it/stranieri</a></td></tr><tr><td>Portale Immigrazione</td><td><a href="https://www.portaleimmigrazione.it/" target="_blank">portaleimmigrazione.it</a></td></tr><tr><td>Find Questura</td><td><a href="https://questure.poliziadistato.it/" target="_blank">Questure web</a></td></tr></table>`},
fr:{dove:`<h3>🧾 Où est le code ?</h3><div class="ricevuta">RÉCÉPISSÉ POSTE — KIT JAUNE<br>N. PRATICA ....: <b>1234567890</b> (10)<br>N. ASSICURATA .: <b>123456789012</b> (12)</div><p><b>Poste vs Questura :</b> phase Poste → Portale Immigrazione (user/password). Après empreintes → ici / site officiel.</p>`,
fasi:`<h3>🪜 5 étapes</h3><ol class="timeline"><li><b class="num">1</b><b>Envoi kit à la Poste</b>.</li><li><b class="num">2</b><b>Empreintes à la Questura</b>.</li><li><b class="num">3</b><b>Vérif ici</b> — pratica (10) ou assicurata (12).</li><li><b class="num">4</b><b>SMS Questura</b>.</li><li><b class="num">5</b><b>Retrait</b> avec passeport + récépissé.</li></ol>`,
faq:`<h3>❓ FAQ</h3><details open><summary>« Introuvable » ?</summary>Faute de frappe, dossier trop récent (avant empreintes) ou vieux code. Essayez pratica et assicurata.</details><details><summary>« En cours » ?</summary>Semaines/mois. Seul le SMS confirme.</details><details><summary>« Prêt » ?</summary>Vérifiez bureau/jour + SMS. Apportez passeport + récépissé.</details>`,
uffici:`<h3>🏢 Liens</h3><table class="help"><tr><th>Quoi</th><th>Lien</th></tr><tr><td>Vérif officielle</td><td><a href="https://questure.poliziadistato.it/stranieri/" target="_blank">questure.poliziadistato.it/stranieri</a></td></tr><tr><td>Portale Immigrazione</td><td><a href="https://www.portaleimmigrazione.it/" target="_blank">portaleimmigrazione.it</a></td></tr></table>`},
ar:{dove:`<h3>🧾 أين الرقم في الإيصال؟</h3><div class="ricevuta">إيصال البريد — الطقم الأصفر<br>N. PRATICA ....: <b>1234567890</b> (10)<br>N. ASSICURATA .: <b>123456789012</b> (12)</div><p><b>البريد مقابل Questura:</b> مرحلة البريد → Portale Immigrazione. بعد البصمات → تحقق هنا.</p>`,
fasi:`<h3>🪜 الخطوات الخمس</h3><ol class="timeline"><li><b class="num">1</b><b>إرسال الطقم في البريد</b>.</li><li><b class="num">2</b><b>البصمات في Questura</b>.</li><li><b class="num">3</b><b>تحقق هنا</b>.</li><li><b class="num">4</b><b>رسالة SMS</b>.</li><li><b class="num">5</b><b>الاستلام</b> بالجواز + الإيصال.</li></ol>`,
faq:`<h3>❓ أسئلة شائعة</h3><details open><summary>«غير موجود»؟</summary>خطأ كتابة أو ملف حديث (قبل البصمات) أو رمز قديم. جرّب الرقمين.</details><details><summary>«قيد المعالجة»؟</summary>أسابيع/أشهر. رسالة SMS هي التأكيد.</details><details><summary>«جاهز»؟</summary>تحقق من المكتب/اليوم + SMS. أحضر الجواز + الإيصال.</details>`,
uffici:`<h3>🏢 روابط</h3><table class="help"><tr><th>ماذا</th><th>رابط</th></tr><tr><td>تحقق رسمي</td><td><a href="https://questure.poliziadistato.it/stranieri/" target="_blank">questure.poliziadistato.it/stranieri</a></td></tr><tr><td>Portale Immigrazione</td><td><a href="https://www.portaleimmigrazione.it/" target="_blank">portaleimmigrazione.it</a></td></tr></table>`},
es:{dove:`<h3>🧾 ¿Dónde está el código?</h3><div class="ricevuta">RECIBO POSTE — KIT AMARILLO<br>N. PRATICA ....: <b>1234567890</b> (10)<br>N. ASSICURATA .: <b>123456789012</b> (12)</div><p><b>Poste vs Questura:</b> fase Poste → Portale Immigrazione. Tras huellas → aquí / sitio oficial.</p>`,
fasi:`<h3>🪜 5 pasos</h3><ol class="timeline"><li><b class="num">1</b><b>Envío en Poste</b>.</li><li><b class="num">2</b><b>Huellas en Questura</b>.</li><li><b class="num">3</b><b>Verifica aquí</b>.</li><li><b class="num">4</b><b>SMS Questura</b>.</li><li><b class="num">5</b><b>Recogida</b> con pasaporte + recibo.</li></ol>`,
faq:`<h3>❓ FAQ</h3><details open><summary>«No encontrado»?</summary>Error de escritura, expediente reciente o código viejo. Prueba ambos.</details><details><summary>«En trámite»?</summary>Semanas/meses. Solo el SMS confirma.</details><details><summary>«Listo»?</summary>Revisa oficina/día + SMS. Lleva pasaporte + recibo.</details>`,
uffici:`<h3>🏢 Enlaces</h3><table class="help"><tr><th>Qué</th><th>Enlace</th></tr><tr><td>Verificación oficial</td><td><a href="https://questure.poliziadistato.it/stranieri/" target="_blank">questure.poliziadistato.it/stranieri</a></td></tr><tr><td>Portale Immigrazione</td><td><a href="https://www.portaleimmigrazione.it/" target="_blank">portaleimmigrazione.it</a></td></tr></table>`}
};

let lang = localStorage.getItem('pds-lang') || 'it';
let lastResult = "";
const HOME_TXT = {
it:{tab0:"Home",start:"Inizia verifica",demo:"Prova demo",c1t:"Dove trovo il codice?",c1s:"Foto-guida ricevuta Poste, pratica vs assicurata.",c2t:"Le 5 fasi",c2s:"Da Poste alle impronte fino all'SMS di ritiro.",c3t:"Non trovato? Aiuto",c3s:"Cosa significano pronto / trattazione / non presente.",heroT:"Controlla se il tuo permesso è pronto in 10 secondi",heroS:"Inserisci il numero della ricevuta Poste (pratica 10 o assicurata 12). Interroghiamo il sito ufficiale della Polizia di Stato.",legend:"<span class='badge b-green'>✅ Pronto</span> ritira con SMS+ufficio · <span class='badge b-orange'>🟠 Trattazione</span> ancora in lavoro · <span class='badge b-red'>🔴 Non presente</span> numero errato o troppo recente",copied:"Esito copiato ✓",cleared:"Cronologia cancellata",noResult:"Prima fai una verifica, poi copia.",demoMsg:"Codice demo inserito, controllo in corso…"},
en:{tab0:"Home",start:"Start check",demo:"Try demo",c1t:"Where is my code?",c1s:"Poste receipt guide, pratica vs assicurata.",c2t:"5 steps",c2s:"From Poste to fingerprints to SMS.",c3t:"Not found? Help",c3s:"What ready / processing / not found mean.",heroT:"Check if your permit is ready in 10 seconds",heroS:"Enter your Poste receipt number (pratica 10 or assicurata 12). We query the official Polizia di Stato site.",legend:"<span class='badge b-green'>✅ Ready</span> collect with SMS · <span class='badge b-orange'>🟠 Processing</span> still in progress · <span class='badge b-red'>🔴 Not found</span> wrong number or too recent",copied:"Result copied ✓",cleared:"History cleared",noResult:"Run a check first.",demoMsg:"Demo code entered, checking…"},
fr:{tab0:"Accueil",start:"Commencer",demo:"Essai démo",c1t:"Où est mon code ?",c1s:"Guide récépissé Poste.",c2t:"5 étapes",c2s:"De la Poste au SMS.",c3t:"Introuvable ? Aide",c3s:"Prêt / en cours / introuvable.",heroT:"Vérifiez votre titre en 10 secondes",heroS:"Saisissez le numéro Poste (pratica 10 ou assicurata 12).",legend:"<span class='badge b-green'>✅ Prêt</span> · <span class='badge b-orange'>🟠 En cours</span> · <span class='badge b-red'>🔴 Introuvable</span>",copied:"Copié ✓",cleared:"Effacé",noResult:"Vérifiez d'abord.",demoMsg:"Code démo, vérification…"},
ar:{tab0:"الرئيسية",start:"ابدأ التحقق",demo:"جرّب مثال",c1t:"أين الرقم؟",c1s:"دليل الإيصال.",c2t:"الخطوات الخمس",c2s:"من البريد إلى الرسالة.",c3t:"غير موجود؟ مساعدة",c3s:"ماذا تعني الحالات.",heroT:"تحقق خلال 10 ثوانٍ",heroS:"أدخل رقم الإيصال (10 أو 12).",legend:"<span class='badge b-green'>✅ جاهز</span> · <span class='badge b-orange'>🟠 قيد المعالجة</span> · <span class='badge b-red'>🔴 غير موجود</span>",copied:"تم النسخ ✓",cleared:"تم المسح",noResult:"تحقق أولًا.",demoMsg:"تم إدخال رمز تجريبي…"},
es:{tab0:"Inicio",start:"Empezar",demo:"Probar demo",c1t:"¿Dónde está mi código?",c1s:"Guía del recibo.",c2t:"5 pasos",c2s:"De Poste al SMS.",c3t:"¿No encontrado? Ayuda",c3s:"Listo / trámite / no encontrado.",heroT:"Verifica en 10 segundos",heroS:"Introduce el número Poste (10 o 12).",legend:"<span class='badge b-green'>✅ Listo</span> · <span class='badge b-orange'>🟠 En trámite</span> · <span class='badge b-red'>🔴 No encontrado</span>",copied:"Copiado ✓",cleared:"Borrado",noResult:"Verifica primero.",demoMsg:"Código demo, verificando…"}};
function toast(msg){const el=document.getElementById('toast');el.textContent=msg;el.style.display='block';clearTimeout(el._t);el._t=setTimeout(()=>el.style.display='none',2200);}
function goTab(name){document.querySelectorAll('#tabs button').forEach(x=>x.classList.toggle('active',x.dataset.tab===name));document.querySelectorAll('.tabpage').forEach(x=>x.classList.toggle('active',x.id==='page-'+name));document.querySelectorAll('.menu button').forEach(x=>x.classList.toggle('active',x.dataset.goto===name));const t=I18N[lang]||I18N.it;const map={home:t.title,dove:HELP[lang]?.dove?'':''};document.getElementById('t-crumb-here').textContent={home:t.title,verifica:t.tab1,dove:t.tab2,fasi:t.tab3,faq:t.tab4,uffici:t.tab5}[name]||name;window.scrollTo({top:0,behavior:'smooth'});}
function applyLang(){
  const t = I18N[lang] || I18N.it;
  const H = HELP[lang] || HELP.it;
  document.documentElement.lang = lang;
  document.getElementById('t-h1').textContent = t.h1;
  document.getElementById('t-head-sub').textContent = t.headSub;
  document.getElementById('t-youare').textContent = t.youAre;
  document.getElementById('t-crumb-here').textContent = t.crumbHere;
  document.getElementById('t-title').textContent = t.title;
  document.getElementById('t-langsel').textContent = t.langSel;
  document.getElementById('lbl-lang').textContent = t.langName;
  document.querySelector('[data-i="tab1"]').textContent = t.tab1;
  document.querySelector('[data-i="tab2"]').textContent = t.tab2;
  document.querySelector('[data-i="tab3"]').textContent = t.tab3;
  document.querySelector('[data-i="tab4"]').textContent = t.tab4;
  document.querySelector('[data-i="tab5"]').textContent = t.tab5;
  document.getElementById('t-label').textContent = t.label;
  document.getElementById('btn').textContent = t.btn;
  document.querySelector('[data-i="copy"]').textContent = t.copy;
  document.querySelector('[data-i="print"]').textContent = t.print;
  document.querySelector('[data-i="official"]').textContent = t.official;
  document.querySelector('[data-i="clear"]').textContent = t.clear;
  document.getElementById('t-note').innerHTML = t.note;
  document.getElementById('t-disc').textContent = t.disc;
  document.getElementById('t-hist-t').textContent = t.histT;
  document.getElementById('t-foot').textContent = t.foot;
  const ht = HOME_TXT[lang] || HOME_TXT.it;
  document.querySelector('[data-i="tab0"]').textContent = ht.tab0;
  document.querySelector('[data-i="start"]').textContent = ht.start;
  document.querySelectorAll('[data-i="demo"]').forEach(e=>e.textContent=ht.demo);
  document.querySelector('[data-i="c1t"]').textContent = ht.c1t;
  document.querySelector('[data-i="c1s"]').textContent = ht.c1s;
  document.querySelector('[data-i="c2t"]').textContent = ht.c2t;
  document.querySelector('[data-i="c2s"]').textContent = ht.c2s;
  document.querySelector('[data-i="c3t"]').textContent = ht.c3t;
  document.querySelector('[data-i="c3s"]').textContent = ht.c3s;
  document.getElementById('t-hero-t').textContent = ht.heroT;
  document.getElementById('t-hero-s').textContent = ht.heroS;
  document.getElementById('t-legend').innerHTML = ht.legend;
  document.getElementById('c-dove').innerHTML = H.dove;
  document.getElementById('c-fasi').innerHTML = H.fasi;
  document.getElementById('c-faq').innerHTML = H.faq;
  document.getElementById('c-uffici').innerHTML = H.uffici;
  document.body.classList.toggle('rtl', lang==='ar');
  const box = document.getElementById('langs'); box.innerHTML='';
  ['it','en','fr','ar','es'].forEach(l=>{const b=document.createElement('button');b.type='button';b.textContent=l.toUpperCase();if(l===lang)b.classList.add('active');b.onclick=()=>{lang=l;try{localStorage.setItem('pds-lang',l);}catch(e){}applyLang();toast(l.toUpperCase());};box.appendChild(b);});
}
document.querySelectorAll('#tabs button').forEach(b=>{b.type='button';b.onclick=()=>goTab(b.dataset.tab);});
document.querySelectorAll('[data-goto]').forEach(b=>{b.onclick=(e)=>{e.preventDefault();goTab(b.dataset.goto);};});
document.getElementById('crumb-home').onclick=(e)=>{e.preventDefault();goTab('home');};
document.getElementById('btn-start').onclick=()=>goTab('verifica');
function runDemo(){const ht=HOME_TXT[lang]||HOME_TXT.it;document.getElementById('code').value='1234567890';goTab('verifica');toast(ht.demoMsg);setTimeout(()=>document.getElementById('btn').click(),300);}
document.getElementById('btn-demo').onclick=runDemo;
document.getElementById('btn-demo2').onclick=runDemo;
function renderHist(){
  let h=[];try{h=JSON.parse(localStorage.getItem('pds-hist')||'[]');}catch(e){h=[];}
  const ul = document.getElementById('hist'); ul.innerHTML = h.length? '' : '<li>—</li>';
  h.slice(0,10).forEach(x=>{const li=document.createElement('li');const b=document.createElement('button');b.style.fontSize='11px';b.textContent='↻';b.title='Re-check';b.onclick=()=>{document.getElementById('code').value=x.code;goTab('verifica');document.getElementById('btn').click();};li.innerHTML='<code></code> — '+x.status+' — '+x.when+' ';li.querySelector('code').textContent=x.code;li.appendChild(b);ul.appendChild(li);});
}
document.getElementById('btn-clear').onclick=()=>{try{localStorage.removeItem('pds-hist');}catch(e){}renderHist();toast((HOME_TXT[lang]||HOME_TXT.it).cleared);};
function saveHist(code,status){
  let h=[];try{h=JSON.parse(localStorage.getItem('pds-hist')||'[]');}catch(e){h=[];}
  h.unshift({code,status,when:new Date().toLocaleString()});
  try{localStorage.setItem('pds-hist', JSON.stringify(h.slice(0,15)));}catch(e){}
  renderHist();
}
async function copyText(txt){
  try{await navigator.clipboard.writeText(txt);return true;}
  catch(e){const ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');document.body.removeChild(ta);return true;}catch(e2){document.body.removeChild(ta);return false;}}
}
document.getElementById('btn-copy').onclick=async()=>{const ht=HOME_TXT[lang]||HOME_TXT.it;if(!lastResult){toast(ht.noResult);return;}const ok=await copyText(lastResult);toast(ok?ht.copied:'copy failed');};
document.getElementById('btn-print').onclick=()=>window.print();
document.getElementById('btn').onclick = async ()=>{
  const t = I18N[lang] || I18N.it;
  const raw = document.getElementById('code').value.trim();
  const box = document.getElementById('result');
  const btn = document.getElementById('btn');
  const cleaned = raw.replace(/[^A-Za-z0-9]/g,'');
  if(cleaned.length!==10 && cleaned.length!==12){
    box.className='m-ok error show';
    box.innerHTML='<div class="big">⚪</div><h3>'+t.error+'</h3><div>'+t.needCode+'</div><div style="font-size:13px">Letto: '+cleaned.length+' caratteri ('+(cleaned||'vuoto')+'). N. Pratica = 10, N. Assicurata = 12.</div>';
    return;
  }
  btn.disabled=true;box.className='m-ok unknown show';box.innerHTML='<div class="big">…</div><div>'+t.checking+'</div>';
  try{
    const r = await fetch('/api/check?pratica='+encodeURIComponent(raw));
    const j = await r.json();
    let cls='unknown',title=t.unknown,msg='',icon='⚪';
    if(!j.ok){cls='error';title=t.error;msg=j.message||'Error';}
    else{cls=j.status;title=t[j.status]||t.unknown;msg=j.message_it||'';icon=cls==='ready'?'✅':cls==='processing'?'🟠':cls==='not_found'?'🔴':'⚪';}
    box.className='m-ok '+cls+' show';
    box.innerHTML='<div class="big">'+icon+'</div><h3>'+title+'</h3><div>'+msg+'</div><div style="margin-top:8px"><code>'+(j.code||cleaned.toUpperCase())+'</code></div>';
    lastResult = title+' — '+(j.code||cleaned)+' — '+msg;
    saveHist((j.code||cleaned.toUpperCase()), title);
  }catch(e){
    box.className='m-ok error show';box.innerHTML='<div class="big">⚪</div><h3>'+t.error+'</h3><div>'+String(e)+'</div>';
  }finally{btn.disabled=false;}
};
document.getElementById('code').addEventListener('keydown',e=>{if(e.key==='Enter')document.getElementById('btn').click();});
applyLang();renderHist();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body: bytes, ctype="text/html; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send(INDEX_HTML.encode("utf-8"))
        elif parsed.path == "/api/check":
            qs = urllib.parse.parse_qs(parsed.query)
            raw = (qs.get("pratica") or [""])[0]
            result = check_code(raw)
            self._send(json.dumps(result, ensure_ascii=False).encode("utf-8"), "application/json")
        elif parsed.path == "/health":
            self._send(b'{"ok": true}', "application/json")
        else:
            self._send(b"Not found", "text/plain", 404)


def main():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Permesso checker running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
