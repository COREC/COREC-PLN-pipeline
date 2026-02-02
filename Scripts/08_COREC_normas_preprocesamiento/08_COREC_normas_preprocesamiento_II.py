# -*- coding: utf-8 -*-

"""
COREC II — Normalización II (Norma 2 + 9 + 11 + 12 + 13)

Descripción
Este script aplica la fase de Normalización II a las salidas de Normalización I.
Mantiene las etiquetas de turno (I1:, E1:, etc.). Genera:
- TXT finales (Salida_TXT_normas_2)
- Log CSV de trazabilidad (Log_normas_2.csv)

Entrada
Carpeta: Preprocesamiento_linguistico/2_Salida_TXT_normas/Salida_TXT_normas_1/
Archivos: <ID_compuesto>_seg_normas_1*.txt
Codificación: UTF-8

Salida
Carpeta: Preprocesamiento_linguistico/2_Salida_TXT_normas/Salida_TXT_normas_2/
Archivos: <mismo_nombre_entrada>_normas_2.txt
Log: Preprocesamiento_linguistico/3_Logs/Log_normas_2/Log_normas_2.csv
Separador log: ;
Codificación log: UTF-8-SIG

Requisitos
- Python 3.10+
- Hunspell + diccionarios de español (REQUERIDO para Norma 2)
  En Colab:
    apt-get install -y hunspell hunspell-es libhunspell-dev
    pip install hunspell
  En local (Linux):
    instala hunspell + diccionarios es_ES del sistema y el wrapper de Python

Uso
Desde la raíz del repositorio:
python 08_COREC_normas_preprocesamiento_II.py

En Colab (opcional):
- Monta Drive (drive.mount)
- Ajusta REPO_ROOT (ver CONFIG)
- Ejecuta:
!python 08_COREC_normas_preprocesamiento_II.py
"""

import re
import csv
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Optional

# --- Colab opcional ---
try:
    from google.colab import drive  # type: ignore
    EN_COLAB = True
except Exception:
    EN_COLAB = False


# =========================
# CONFIG (EDITAR AQUÍ)
# =========================
# --- LOCAL (desde raíz del repo COREC) ---
ROOT_IN = "Preprocesamiento_linguistico/2_Salida_TXT_normas/Salida_TXT_normas_1"
OUT_DIR = "Preprocesamiento_linguistico/2_Salida_TXT_normas/Salida_TXT_normas_2"
OUT_CSV = "Preprocesamiento_linguistico/3_Logs/Log_normas_2/Log_normas_2.csv"

# --- COLAB (opcional; NO sobreescribir) ---
if EN_COLAB:
    REPO_ROOT = "/content/drive/MyDrive/COREC"
    ROOT_IN = f"{REPO_ROOT}/{ROOT_IN}"
    OUT_DIR = f"{REPO_ROOT}/Preprocesamiento_linguistico/2_Salida_TXT_normas/Salida_TXT_normas_2_test"
    OUT_CSV = f"{REPO_ROOT}/Preprocesamiento_linguistico/3_Logs/Log_normas_2/Log_normas_2_test.csv"

# --- Si quieres montar Drive, descomenta ---
# if EN_COLAB:
#     drive.mount("/content/drive")

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
Path(OUT_CSV).parent.mkdir(parents=True, exist_ok=True)


# ===========================================================
# Hunspell — REQUERIDO (Norma 2)
# ===========================================================
HUN = None
try:
    from hunspell import HunSpell  # type: ignore
    CANDIDATES = [
        ("/usr/share/hunspell/es_ES.dic", "/usr/share/hunspell/es_ES.aff"),
        ("/usr/share/hunspell/es_ANY.dic", "/usr/share/hunspell/es_ANY.aff"),
        ("/usr/share/myspell/es_ES.dic", "/usr/share/myspell/es_ES.aff"),
    ]
    for dic_path, aff_path in CANDIDATES:
        if Path(dic_path).exists() and Path(aff_path).exists():
            HUN = HunSpell(dic_path, aff_path)
            break
except Exception:
    HUN = None

if HUN is None:
    raise RuntimeError(
        "Hunspell es REQUERIDO para Norma 2 y no se encontró dic/aff.\n"
        "En Colab instala:\n"
        "  apt-get install -y hunspell hunspell-es libhunspell-dev\n"
        "  pip install hunspell\n"
        "En local: instala hunspell + diccionarios de español del sistema."
    )

def hun_ok(word: str) -> bool:
    w = word.strip()
    if not w:
        return False
    try:
        return bool(HUN.spell(w))
    except Exception:
        return False


# ===========================================================
# Norma 9 (APÓSTROFO) + Norma 11 (DICCIONARIO)
# ===========================================================
N9_MAP: Dict[str, str] = {
    # ---- para el ----
    "pa'l": "para el",
    "pa’l": "para el",
    "p'al": "para el",
    "p’al": "para el",
    "pal’": "para el",
    "pal'": "para el",

    # ---- para el (con espacio explícito) ----
    "pa' el": "para el",
    "pa’ el": "para el",
    "p' al": "para el",
    "p’ al": "para el",

    # ---- para un ----
    "pa' un": "para un",
    "pa’ un": "para un",

    # ---- para que ----
    "pa' que": "para que",
    "pa’ que": "para que",

    # ---- todo ----
    "to'": "todo",
    "to’": "todo",

    "pa'": "para",
    "pa’": "para",

    "p’acá": "para acá",
    "p’allá": "para allá",
    "p’alla": "para allá",
    "p’alante": "para adelante",
    "l’aspecto": "el aspecto",
    "l’azabache": "el azabache",
}

L_APOS_RE = re.compile(r"\bl[’']\s*(?P<w>\w+)", flags=re.UNICODE)


def norma9_apostrofo(text: str) -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []
    out = text

    for fo, fr in N9_MAP.items():
        if fo in out:
            start = 0
            while True:
                pos = out.find(fo, start)
                if pos == -1:
                    break
                events.append((fo, fr, "NORMA9_APLICADA"))
                start = pos + len(fo)
            out = out.replace(fo, fr)

    def repl_l(m: re.Match) -> str:
        w = m.group("w")
        w_low = w.lower()
        if w_low in {"águila", "aguila", "agua"}:
            art = "el"
        elif w_low.endswith("a"):
            art = "la"
        else:
            art = "el"
        fo = m.group(0)
        fr = f"{art} {w}"
        events.append((fo, fr, "NORMA9_L_APOSTROFO"))
        return fr

    out2 = L_APOS_RE.sub(repl_l, out)
    out2 = re.sub(r"\s{2,}", " ", out2)
    return out2, events


N11_MAP: Dict[str, str] = {

 # --- Unificación demuletillas
    "eeh": "eh",
    "ehh": "eh",
    "mhm": "mm",
    "mh": "mm",
    "mmhm": "mm",
    "mmh": "mm",
    "mmj": "mm",
    "mjmj": "mm",
    "mmjm": "mm",
    "mmm": "mm",
    "mmajá": "ajá",
    "majám": "ajá",
    "uhm": "mm",

    # --- Variantes léxicas


    "Caponeta": "Acaponeta",
    "caponeta": "Acaponeta",
    "Dio": "Dios",
    "Prancisco": "Francisco",
    "aques": "aquellos",
    "acompeña": "acompañar",
    "albaciles": "alguaciles",
    "albaniles": "albañiles",
    "amos": "vamos",
    "ansí": "así",
    "asín": "así",
    "aiá": "allá",
    "allís": "allí",
    "bichol": "huichol",
    "bicholes": "huicholes",
    "bindicir": "bendecir",
    "ca": "acá",
    "cai": "casi",
    "castoilla": "castellano",
    "chapilote": "zapilote",
    "cemos": "hacemos",
    "ciendo": "haciendo",
    "cendo": "haciendo",
    "cimos": "hicimos",
    "com": "como",
    "comence": "comience",
    "comunida": "comunidad",
    "conpesó": "confesó",
    "costumbraban": "acostumbraban",
    "cutsillo": "cuchillo",
    "depué": "después",
    "despue": "después",
    "dicimos": "decimos",
    "dihe": "dije",
    "disde": "dice",
    "enamorao": "enamorado",
    "encalgales": "encargarles",
    "enperma": "enferma",
    "enpermeda": "enfermedad",
    "enpermedad": "enfermedad",
    "enpermo": "enfermo",
    "entoces": "entonces",
    "entoe": "entonces",
    "entonce": "entonces",
    "entós": "entonces",
    "etons": "entonces",
    "estem": "este",
    "esteem": "este",
    "estee": "este",
    "eza": "reza",
    "gonbernador": "gobernador",
    "guanador": "gobernador",
    "haiga": "haya",
    "ieva": "lleva",
    "icían": "hacían",
    "ieva": "lleva",
    "il": "el",
    "in": "un",
    "inglesia": "iglesia",
    "iinterrupción": "interrupción",
    "ire": "mire",
    "jardincinto": "jardincito",
    "jue": "fue",
    "jueices": "jueces",
    "jui": "fui",
    "juera": "fuera",
    "jultimo": "último",
    "júltimo": "último",
    "lapi": "lápiz",
    "lleaba": "llegaba",
    "lugai": "lugar",
    "luigo": "luego",
    "má": "más",
    "namás": "nada más",
    "madados": "mandados",
    "manece": "amanece",
    "manecía": "amanecía",
    "maneciste": "amaneciste",
    "máiz": "maíz",
    "mitá": "mitad",
    "nai": "nada",
    "necetamos": "necesitamos",
    "necetando": "necesitando",
    "necita": "necesita",
    "nomas": "nomás",
    "nosotro": "nosotros",
    "ntonce": "entonces",
    "onde": "donde",
    "ora": "ahora",
    "orita": "ahorita",
    "pa": "para",
    "pal": "para el",
    "pamilia": "familia",
    "pagres": "padres",
    "páctica": "práctica",
    "pladores": "bailadores",
    "preciosia": "preciosa",
    "piensaran": "pensaran",
    "pladores": "bailadores",
    "plticale": "platicarle",
    "pol": "por el",
    "poní": "ponía",
    "porma": "forma",
    "pormó": "formó",
    "pos": "pues",
    "ps": "pues",
    "pu": "pues",
    "pue": "pues",
    "pus": "pues",
    "quera": "quiera",
    "quere": "quiere",
    "radiofusora": "radiodifusora",
    "restirado": "retirado",
    "semes": "somos",
    "sotros": "nosotros",
    "stá": "está",
    "stás": "estás",
    "stámos": "estamos",
    "stába": "estaba",
    "stamos": "estamos",
    "stemos": "estamos",
    "tás": "estás",
    "talos": "palos",
    "taba": "estaba",
    "taban": "estaban",
    "tamos": "estamos",
    "tambié": "también",
    "tepahuano": "tepehuano",
    "tepehuan": "tepehuano",
    "tepehuno": "tepehuano",
    "toce": "entonces",
    "too": "todo",
    "tons": "entonces",
    "tonses": "entonces",
    "traime": "tráeme",
    "trasporte": "transporte",
    "tsostsil": "tsotsil",
    "tsotsil": "tsotsil",
    "uté": "usted",
    "uste": "usted",
    "veincinco": "veinticinco",
    "velda": "verdad",
    "verda": "verdad",
    "verdat": "verdad",
    "verdak": "verdad",
    "vinía": "venía",
    "¿verda": "¿verdad",
  }

    N11_MAP_AST: Dict[str, str] = {
    "asturianu": "asturiano",
    "acuérdome": "acuerdo me",
    "diz": "dice",
    "dizme": "dice me",
    "hai": "hay",
    "sitiu": "sitio",
    "Grao": "Grado",
    "tamién": "también",
    "enseñatelo": "enseñar te lo",
    "conócesla": "conoces la",
    "retomala": "retomar la",
    "enfadóse": "enfadó se",
    "listu": "listo",
    "cerrao": "cerrado",
    "estraña": "extraña",
    "estráñame": "extraña me",
    "coses": "cosas",
    "agacháu": "agachado",
    "levantóse": "levantó se",
    "lesionao": "lesionado",
    "fios": "hijos",
    "jubilaos": "jubilados",
    "desorientáu": "desorientado",
    "achacábalo": "achacaba lo",
    "preguntame": "preguntar me",
    "quitao": "quitado",
    "quier": "quiere",
    "parecióme": "pareció me",
    "dijéronme": "dijeron me",
    "revueltu": "revuelto",
    "esti": "este",
    "desorientáu": "desorientado",
    "agobiao": "agobiado",
    "jubilao": "jubilado",
    "esplotaran": "explotaran",
    "ruidu": "ruido",
    "tomólo": "tomó lo",
    "afectábalu":"afectaba lo",
    "acuerdaste": "acuerdas te",
    "mezclalo": "mezclar lo",
    "hablao": "hablado",
    "llamalo": "llamarlo",
    "tallao": "tallado",
    "trabayar": "trabajar",
    "piénsolo": "pienso lo",
    "aglutinalos": "aglutinarlos",
    "contabilidá": "contabilidad",
    "paisanu": "paisano",
    "vendíate": "vendía te",
    "pieces": "piezas",
    "queríala": "quería la",
    "complicáu": "complicado",
    "apretáu": "apretado",
    "Facultá": "Facultad",
    "Universidá": "Universidad",
    "salú": "salud",
    "acabase": "acabar se",
    "cachucu": "cachuco",
    "usté": "usted",
    "envede": "en vez de",
    "contestualizar": "contextualizar",
    "limitao": "limitado",
    "déjame": "deja me", 
    "mandóme": "mandó me",
    "llamao": "llamado",
    "gústanme": "gustan me",
    "préstame": "presta me",
    "facer": "hacer",
    "gatucu": "gatuco", 
    "preséntate": "presenta te",
    "gústame": "gusta me",
    "casáu": "casado",
    "préstasme": "prestas me",
    "casame": "casarme",
    "esactamente": "exactamente",
    "engurruñao": "engurruñado",
    "púseme": "puse me",
    "liao": "liado",
    "puqitín": "poquitín",
    "fae": "hace",
    "vémonos":"vemos nos", 
    "prestábanos": "prestaba nos",
    "prao": "prado",
    "tuyu": "tuyo", 
    "toa": "toda",
    "hacemelo": "hacer me lo",
    "perderíalo": "perdería lo",
    "préstesme": "prestas me",
    "apurao": "apurado",
    "neso": "en eso",
    "estoi": "estoy",
    "laos": "lados",
    "ónde": "dónde",
    "trabayando": "trabajando",
    "decítelo": "decir te lo",
    "perdístelo": "perdiste lo",
    "amestalo": "amestar lo",
    "encargao": "encargado",
    "paisanu": "paisano",
    "vendíatelo": "vendía te lo",
    "mineru": "minero",
    "dale": "dar le",
    "capacidá": "capacidad",
    "mezclase": "mezclar se",
    "faciendo": "haciendo",
    "sentáu": "sentado",
    "complicáu": "complicado",
    "nel": "en el",
    "dedicóse": "dedicó se",
    "talles": "tallas",
    "añu": "año",
    "ponelos": "poner los",
    "ponse": "pone se",
    "púsose": "puso se",
    "ponelu": "ponerlo",
    "doi": "doy",
    "nun": "no",
    "ta": "está",
    "tas": "estás",
    "esi": "ese",
    "doi": "doy",
    "tábamos": "estábamos",
    "navidá": "Navidad",
    "tabas": "estabas",
    "tando": "estando",
    "llámase": "llama se",
    "toy": "estoy",
    "tovía": "todavía",
    "pa": "para",
    "polo": "por lo",
    "mismu": "mismo",
    "lao": "lado",
    "home": "hombre",
    "espediente": "expediente",
    "cuidao": "cuidado", 
    "amigu": "amigo",
    "ensi": "así",
    "taluego": "hasta luego",
    "quies": "quieres",
    "quie": "quiere",
    "recao": "recado",
    "supermercao": "supermercado",
    "vien": "viene",
    "comprámosla": "compramos la",
    "dijéronme": "dijeron me",
    "habíase": "había se",
    "acesu": "acceso",
    "proyectu": "proyecto",
    "ponese": "poner se",
    "¿acuérdas te?": "¿acuerdas te?",
    "dedicame": "dedicar me",
    "mudámonos": "mudamos nos",
    "arroxar": "enrojar",
    "maestru": "maestro",
    "p’arroxar": "para enrojar",
    "ayuntamientu": "ayuntamiento",
    "hacelo": "hacer lo",
    "muchu": "mucho", 
    "acostumbrao": "acostumbrado", 
    "dentru": "dentro",
    "hacese": "hacerse",
    "conceyu": "concejo",
    "piquiñucu": "pequeñuco",
    "decite": "decir te",
    "arreglala": "arreglar la",
    "enséñotela": "enseño te la",
    "vaciala": "vaciar la",
    "voluntá": "voluntad",
    "forno": "horno",
    "muyeres": "mujeres",
    "vaciáronse": "vaciaron se",
    "bañu": "baño",
    "¿acuérdaste?": "¿acuerdas te?",
    "val": "vale",
    "probe": "pobre",
    "paisa": "paisano",
    "calidá": "calidad",
    "nuna": "ninguna",
    "verdá": "verdad",
    "agusto": "a gusto",
    "guapu": "guapo",
    "esagerao": "exagerado",
    "otru": "otro",
    "bai": "vas",
    "vais": "van",
    "operalo": "operar lo",
    "ingresao": "ingresado",
    "lu": "lo",
    "yáa": "ya",
    "to": "todo",
    "tolo": "todo lo",
    "toos": "todos",
    "tol": "todo el",
    "tolos": "todos los",
    "tola": "toda la",
    "toles": "todas las",
    "dau": "dado",
    "preciu": "precio",
    "vendíatelo": "vendía te lo",
    "quedábame": "quedaba me",
    "cáesme": "caes me",
    "xente": "gente",
    "liáo": "liado",
    "tará": "estará",
    "tar": "estar",
    "taré": "estaré",
    "bebu": "bebo",
    "fíos": "hijos",
    "cachu": "cacho",
    "anillu": "anillo",
    "entós": "entonces",
    "amás": "además",
    "amá s": "además",
    "tiénenlo": "tienen lo",
    "tiénen": "tienen",
    "tien": "tiene",
    "tienlo": "tiene lo",
    "tán": "están",
    "tá": "está",
    "ye": "es",
    "yes": "eres",
    "yera": "era",
    "na": "nada",
    "ná": "nada",
    "nun sé": "no sé",
    "puea": "pueda",
    "paezme": "parece me",
    "paez": "parece",
    "pallá": "para allá",
    "pola": "por la",
    "polos": "por los",
    "peles": "por las",
    "pal": "para el",
    "díxome": "dijo me",
    "dixéronme": "dijeron me",
    "dígo-te": "digo te",
    "dígote": "digo te",
    "acondicionaos": "acondicionados",
    "separaos": "separados",
    "cagon": "cago en",
}



# --- ASTURIANU: base-guion-clítico (base >= 3) + excepciones base=2 ---

RE_AST_CLIT = re.compile(
    r"\b(?P<base>(?:\w{3,}|(?:da|di)))-(?P<clit>y|ys|yos|ylo|ylu|yla|ylos|yles)\b",
    flags=re.UNICODE
)


def norma11_dicc(text: str, id_archivo: str = "") -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []

    # ===========================================================
    # ASTURIANU: activar SOLO si el archivo empieza por 014
    # ===========================================================
    AST_MODE = id_archivo.startswith("014")

    if AST_MODE:
        def repl_ast(m: re.Match) -> str:
            fo = m.group(0)
            base = m.group("base")
            clit = m.group("clit")

            if clit == "y":
                fr = f"{base} le"
            else:
                fr = f"{base} {clit}"

            events.append((fo, fr, "AST_GUION_CLIT_SPLIT"))
            return fr

        text = RE_AST_CLIT.sub(repl_ast, text)

        CLIT_MAP = {
            "ys": "les",
            "ylo": "se lo",
            "ylu": "se lo",
            "yla": "se la",
            "ylos": "se los",
            "yles": "se les",
            "se-y": "se le",
            "no-y": "no le",
            "no-yos": "no les",
            "yos": "les",
          
        }
    else:
        CLIT_MAP = {}

    def repl(m: re.Match) -> str:
        tok = m.group(0)

        # PROTECCIÓN GENERAL: si el token está pegado a ':', no aplicar N11_MAP
        i, j = m.span()
        left = text[i - 1] if i > 0 else ""
        right = text[j] if j < len(text) else ""
        if left == ":" or right == ":":
            return tok

        # clíticos (solo AST_MODE)
        if tok in CLIT_MAP:
            fr = CLIT_MAP[tok]
            events.append((tok, fr, "AST_CLIT_MAP"))
            return fr

        # diccionario general
        fr = N11_MAP.get(tok, tok)

        # diccionario asturiano SOLO en 014
        if AST_MODE:
            fr2 = N11_MAP_AST.get(tok, tok)
            if fr2 != tok:
                fr = fr2

        if fr != tok:
            events.append((tok, fr, "NORMA11_APLICADA"))
        return fr

    out = re.sub(r"\b[\w-]+\b", repl, text, flags=re.UNICODE)
    out = re.sub(r"\s{2,}", " ", out)
    return out, events


# ===========================================================
# LISTA EXACTA (coincidencia literal)
# ===========================================================
EXACT_MAP: Dict[str, str] = {
    "tocó: o": "tocó",
    "ciclopase: os": "ciclopaseos",
    "tocó: o": "tocó",
    "ella: siempre": "ella siempre",
    "mese: s": "meses",
    "si: n": "sin",
    "po: ios": "poios",
    "pesteni:che": "pesteniche",
    "deplu: ma": "depluma",
    "po: pollos": "pollos",
    "po: pollo": "pollo",
    "con: pa: sas": "con pasas",
    "ense: ncios": "ensencios",
    "toa: ias": "toaias",
    "encie: nso": "encienso",
    "Medellí: n": "Medellín",
    "la: s": "las",
    "bacha: ta": "bachata",
    "la: rgos": "largos",
    "zanque: ra": "zanquera",
    "trabaja: r": "trabajar",
    "traba: jo: s": "trabajos",
    "a: la": "a la",
    " no se: no": "no se",
    "a:la": "a la",
    "se:no": "se no",
    "unos:": "unos",
    "ci: nco ": "cinco",
    "no: rte": "norte",
    "entoce:": "entonces",
}



PH_PREFIX = "<<<EXACT_FIX_"
PH_SUFFIX = ">>>"


def _apply_exact_placeholders(text: str) -> Tuple[str, Dict[str, str], List[Tuple[str, str]]]:
    keys = sorted(EXACT_MAP.keys(), key=len, reverse=True)
    ph_to_value: Dict[str, str] = {}
    found_pairs: List[Tuple[str, str]] = []
    out = text
    idx = 0
    for k in keys:
        start = 0
        while True:
            pos = out.find(k, start)
            if pos == -1:
                break
            ph = f"{PH_PREFIX}{idx}{PH_SUFFIX}"
            idx += 1
            ph_to_value[ph] = EXACT_MAP[k]
            found_pairs.append((k, EXACT_MAP[k]))
            out = out[:pos] + ph + out[pos + len(k):]
            start = pos + len(ph)
    return out, ph_to_value, found_pairs


def _restore_exact_placeholders(text: str, ph_to_value: Dict[str, str]) -> str:
    out = text
    for ph, val in ph_to_value.items():
        out = out.replace(ph, val)
    return out


# ===========================================================
# 1 UD = 1 línea etiquetada
# ===========================================================
LABEL_RE = re.compile(
    r"""^\s*
    (?P<label>(?:INF|ENT|E|I)(?:[0-9]+|(?:\.[A-Za-z0-9]+))*)
    \s*:\s*
    (?P<rest>.*)$
    """,
    flags=re.VERBOSE
)

JOIN_RE = re.compile(r"(?P<a>\w+):(?P<sp>\s+)(?P<b>\w+)", flags=re.UNICODE)
COMPACT_COLON_RE = re.compile(r"(?P<a>\w+):(?P<b>\w+)", flags=re.UNICODE)
ADJ_COLON_RE = re.compile(r"(?<=\w):|:(?=\w)", flags=re.UNICODE)
WORD_RE = re.compile(r"\b\w+\b", flags=re.UNICODE)
FORMA_ORIG_RE = re.compile(
    r"(?:\w+:\s*\w+|\w+:\w+|:\w+|\w+:)",
    flags=re.UNICODE
)

LEADING_DOT_NUM_RE = re.compile(r"^\s*\.\s*\d+\.\s*")

RIGHT_FRAGS = {
    "z", "s", "r",
    "ja", "sa", "llo", "mos", "tas",
    "mbos",
    "rbas", "nes", "lla", "cas", "rse",
    "ndo",
    "da", "rgos",
}

STOP_LEFT = {
    "y",
    "que", "pero", "hasta", "de", "en", "la", "lo", "un", "una",
    "eh", "ya", "si", "no", "por", "con", "como"
}

NO_JOIN_RIGHT_1 = {"a", "y", "e", "o", "u"}
YES_JOIN_RIGHT_1 = {"s", "r", "z"}
ALLOW_1x1 = {("e", "s"), ("i", "r")}

COLON_AS_SPACE_RE = re.compile(r"(?<=\w):(?=\w)", flags=re.UNICODE)


def build_observed_words_from_text(text: str) -> Set[str]:
    tmp = COLON_AS_SPACE_RE.sub(" ", text)
    tmp = ADJ_COLON_RE.sub("", tmp)
    return {w.lower() for w in WORD_RE.findall(tmp)}


def should_join_spaced(a: str, b: str, observed: Set[str]) -> bool:
    a_l = a.lower()
    b_l = b.lower()
    ab = (a + b).lower()

    if (a_l, b_l) in ALLOW_1x1:
        return True
    if a_l in STOP_LEFT:
        return False

    if hun_ok(ab):
        return True

    if len(a) == 1:
        if a_l in {"a", "e", "i", "o", "u"} and len(b) >= 3 and ab in observed:
            return True
        return False

    if len(b) == 1:
        if b_l in NO_JOIN_RIGHT_1:
            return False
        if b_l in YES_JOIN_RIGHT_1:
            return True
        return False

    if b_l in RIGHT_FRAGS:
        if b_l == "da":
            return len(a) >= 4
        if b_l == "ndo":
            return len(a) >= 3
        return True

    return ab in observed


# ===========================================================
# DATA STRUCT
# ===========================================================
@dataclass
class LogRow:
    id_archivo: str
    id_ud: str
    linea_n: int
    hablante: str
    rol: str
    norma_id: int
    fenomeno: str
    forma_original: str
    forma_resultante: str
    accion: str
    contexto: str


def rol_from_label(label: str) -> str:
    lab = label.upper()
    if lab.startswith("E") or lab.startswith("ENT"):
        return "ENTREVISTADOR"
    return "INFORMANTE"


def iter_txt_files(root: str) -> List[Path]:
    rootp = Path(root)
    if rootp.is_file() and rootp.suffix.lower() == ".txt":
        return [rootp]
    return sorted([p for p in rootp.rglob("*.txt") if p.is_file()])


# ===========================================================
# Norma 2 ESTRICTA
# ===========================================================
def apply_norma2(ud_text: str, observed: Set[str]) -> str:
    out_parts = []
    last = 0
    for m in JOIN_RE.finditer(ud_text):
        a = m.group("a")
        b = m.group("b")
        if should_join_spaced(a, b, observed):
            out_parts.append(ud_text[last:m.start()])
            out_parts.append(f"{a}{b}")
            last = m.end()
    out_parts.append(ud_text[last:])
    text_after_join = "".join(out_parts)

    def repl_compact(m: re.Match) -> str:
        a = m.group("a")
        b = m.group("b")
        a_l = a.lower()
        b_l = b.lower()
        ab = (a + b).lower()

        if a_l == "y" and b_l == "y":
            return a

        if a_l == "y":
            return a + " " + b

        if (a_l, b_l) in ALLOW_1x1:
            return a + b
        if hun_ok(ab) or ab in observed:
            return a + b
        return a + " " + b

    text_after_compact = COMPACT_COLON_RE.sub(repl_compact, text_after_join)

    # Impedir que "y:para" acabe como "ypara" al borrar ":" después
    text_after_compact = re.sub(r"\by\s*:\s*(?=\w)", "y ", text_after_compact, flags=re.UNICODE)
    # (extra seguro) impedir "a:la" -> "ala"
    text_after_compact = re.sub(r"\ba\s*:\s*(?=\w)", "a ", text_after_compact, flags=re.UNICODE)

    normalized = ADJ_COLON_RE.sub("", text_after_compact)
    return normalized


def extract_pairs_all_colon(contexto_in: str, observed: Set[str]) -> List[Tuple[str, str, str]]:
    triples: List[Tuple[str, str, str]] = []
    for m in FORMA_ORIG_RE.finditer(contexto_in):
        fo = m.group(0).strip()
        fr = apply_norma2(fo, observed).strip()
        if not fr:
            continue
        accion = "NORMA2_APLICADA" if fr != fo else "NORMA2_NO_APLICADA"
        triples.append((fo, fr, accion))
    return triples


# ===========================================================
# MAIN
# ===========================================================
def main():
    files = iter_txt_files(ROOT_IN)
    if not files:
        raise FileNotFoundError(f"No se encontraron .txt en: {ROOT_IN}")

    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: List[LogRow] = []

    observed_global: Set[str] = set()
    for fp in files:
        t = fp.read_text(encoding="utf-8", errors="replace")
        observed_global |= build_observed_words_from_text(t)

    for fp in files:
        id_archivo = fp.name
        ud_counter = 0
        linea_n = 0
        out_lines: List[str] = []

        with fp.open("r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n")
                m = LABEL_RE.match(line)
                if not m:
                    continue

                linea_n += 1
                ud_counter += 1
                id_ud = f"UD{ud_counter:05d}"

                label = m.group("label")
                hablante = label
                rol = rol_from_label(label)
                contexto = m.group("rest")
                if contexto.startswith(". TL"):
                    contexto = contexto[4:].lstrip()
                else:
                    contexto = contexto.lstrip()
                contexto = LEADING_DOT_NUM_RE.sub("", contexto)

                contexto_ph, ph_to_value, exact_pairs = _apply_exact_placeholders(contexto)

                contexto_norm = apply_norma2(contexto_ph, observed_global)
                contexto_norm = _restore_exact_placeholders(contexto_norm, ph_to_value)

                # aplicar 9 y 11 DESPUÉS de la 2 + LOG acorde
                contexto_norm, ev9 = norma9_apostrofo(contexto_norm)
                for fo, fr, accion in ev9:
                    rows.append(LogRow(
                        id_archivo=id_archivo, id_ud=id_ud, linea_n=linea_n,
                        hablante=hablante, rol=rol,
                        norma_id=9, fenomeno="APOSTROFO",
                        forma_original=fo, forma_resultante=fr,
                        accion=accion, contexto=contexto
                    ))

                contexto_norm, ev11 = norma11_dicc(contexto_norm, id_archivo=id_archivo)
                for fo, fr, accion in ev11:
                    rows.append(LogRow(
                        id_archivo=id_archivo, id_ud=id_ud, linea_n=linea_n,
                        hablante=hablante, rol=rol,
                        norma_id=11, fenomeno="NORMALIZACION_LEXICA",
                        forma_original=fo, forma_resultante=fr,
                        accion=accion, contexto=contexto
                    ))

                # --- post-proceso final (tokens aislados) + LOG (NORMA 12) ---
                POST_MAP = {"sese": "se se", "síes": "sí es", "eses": "es es"}
                for fo, fr in POST_MAP.items():
                    pat = re.compile(rf"\b{re.escape(fo)}\b", flags=re.UNICODE)
                    if pat.search(contexto_norm):
                        contexto_norm = pat.sub(fr, contexto_norm)
                        rows.append(LogRow(
                            id_archivo=id_archivo, id_ud=id_ud, linea_n=linea_n,
                            hablante=hablante, rol=rol,
                            norma_id=12, fenomeno="POST_TOKEN_FIX",
                            forma_original=fo, forma_resultante=fr,
                            accion="NORMA12_APLICADA", contexto=contexto
                        ))

                # --- NORMA 13: anonimización SOLO x -> ⟦ANON_X⟧ (solo token suelto) ---
                def _anon_x_repl(m: re.Match) -> str:
                    tok = m.group(0)  # siempre "x"
                    fr = "⟦ANON_X⟧"
                    rows.append(LogRow(
                        id_archivo=id_archivo, id_ud=id_ud, linea_n=linea_n,
                        hablante=hablante, rol=rol,
                        norma_id=13, fenomeno="ANONIMIZACION",
                        forma_original=tok, forma_resultante=fr,
                        accion="NORMA13_APLICADA", contexto=contexto
                    ))
                    return fr

                contexto_norm = re.sub(r"(?<!\w)x(?!\w)", _anon_x_repl, contexto_norm, flags=re.UNICODE)

                out_lines.append(contexto_norm)


                triples = extract_pairs_all_colon(contexto, observed_global)
                for fo, fr, accion in triples:
                    rows.append(LogRow(
                        id_archivo=id_archivo, id_ud=id_ud, linea_n=linea_n,
                        hablante=hablante, rol=rol,
                        norma_id=2, fenomeno="ALARGAMIENTO_DOS_PUNTOS",
                        forma_original=fo, forma_resultante=fr,
                        accion=accion, contexto=contexto
                    ))

                for fo, fr in exact_pairs:
                    rows.append(LogRow(
                        id_archivo=id_archivo, id_ud=id_ud, linea_n=linea_n,
                        hablante=hablante, rol=rol,
                        norma_id=2, fenomeno="LISTA_EXACTA",
                        forma_original=fo, forma_resultante=fr,
                        accion="LISTA_EXACTA_APLICADA", contexto=contexto
                    ))

        (out_dir / f"{fp.stem}_normas_2{fp.suffix}").write_text("\n".join(out_lines), encoding="utf-8")


    rows.sort(key=lambda r: (r.id_archivo, r.id_ud, r.linea_n, r.norma_id))

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([
            "id_archivo", "id_ud", "linea_n", "hablante", "rol",
            "norma_id", "fenomeno", "forma_original", "forma_resultante",
            "accion", "contexto"
        ])
        for r in rows:
            w.writerow([
                r.id_archivo, r.id_ud, r.linea_n, r.hablante, r.rol,
                r.norma_id, r.fenomeno, r.forma_original, r.forma_resultante,
                r.accion, r.contexto
            ])

    print("OK")
    print(f"- TXT normalizados en: {OUT_DIR}")
    print(f"- LOG CSV en:         {OUT_CSV}")
    print(f"- Archivos .txt:      {len(files)}")
    print(f"- Filas log:          {len(rows)}")


if __name__ == "__main__":
    main()

