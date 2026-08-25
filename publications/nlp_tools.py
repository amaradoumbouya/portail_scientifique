import re
import string
import fitz  # PyMuPDF
import spacy
import nltk
import requests
from urllib.parse import quote
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer


# Télécharger stopwords
nltk.download('stopwords')

# Stop words français
french_stopwords = stopwords.words('french')

# Chargement modèle NLP français
nlp = spacy.load("fr_core_news_sm")

# HTTP
HTTP_TIMEOUT = 12
HTTP_HEADERS = {
    "User-Agent": "PortailScientifiqueCRICT/1.0 (indexation; mailto:admin@crict.org)",
    "Accept": "application/json",
}


# ================================
# EXTRACTION TEXTE PDF
# ================================
def extraire_texte_du_pdf(fichier):
    fichier.seek(0)
    doc = fitz.open(stream=fichier.read(), filetype="pdf")
    texte = ""
    for page in doc:
        texte += page.get_text()
    return texte


# ================================
# DETECTION LANGUE
# ================================
_LANGUES_NLTK = (
    ("français", "french"),
    ("anglais", "english"),
    ("espagnol", "spanish"),
    ("portugais", "portuguese"),
    ("allemand", "german"),
    ("italien", "italian"),
)


def detecter_langue(texte):
    """
    Détecte la langue dominante du PDF via le recouvrement
    avec les stopwords NLTK (déjà chargés pour le NLP).
    """
    if not texte or not str(texte).strip():
        return "français"

    mots = re.findall(r"[a-zà-ÿ']+", texte.lower())
    if len(mots) < 20:
        return "français"

    echantillon = mots[:500]
    scores = {}
    for libelle, nom_nltk in _LANGUES_NLTK:
        try:
            stops = set(stopwords.words(nom_nltk))
        except LookupError:
            continue
        scores[libelle] = sum(1 for mot in echantillon if mot in stops)

    if not scores:
        return "français"

    meilleure = max(scores, key=scores.get)
    if scores[meilleure] == 0:
        return "français"
    return meilleure


# ================================
# NETTOYAGE NLP
# ================================
def nettoyer_texte(texte):

    texte = texte.lower()

    # Supprimer chiffres
    texte = re.sub(r'\d+', ' ', texte)

    # Supprimer ponctuation
    texte = texte.translate(str.maketrans('', '', string.punctuation))

    # NLP
    doc = nlp(texte)

    mots_valides = []

    for token in doc:

        if (
            token.text not in french_stopwords
            and not token.is_stop
            and not token.is_punct
            and len(token.text) > 2
        ):

            mots_valides.append(token.lemma_)

    return " ".join(mots_valides)


# ================================
# EXTRACTION RESUME
# ================================
def extraire_resume(texte):
    doc = nlp(texte)
    phrases = list(doc.sents)
    resume = " ".join([phrase.text for phrase in phrases[:5]])
    return resume


# ================================
# EXTRACTION MOTS CLES
# ================================
def extraire_mots_cles(texte_nettoye):

    vectorizer = TfidfVectorizer(max_features=15)

    X = vectorizer.fit_transform([texte_nettoye])

    mots_cles = vectorizer.get_feature_names_out()

    return ", ".join(mots_cles)


# ================================
# CLASSIFICATION DOMAINE
# ================================
def classifier_domaine(texte):

    texte = (texte or "").lower()

    domaines = {
        "Informatique": [
            "intelligence artificielle", "machine learning", "deep learning",
            "apprentissage automatique", "algorithme", "programmation",
            "logiciel", "informatique", "réseau", "cyber", "données",
            "base de données", "système d'information", "hadoop", "python",
            "reconnaissance vocale", "traitement automatique",
        ],
        "Santé": [
            "médical", "santé", "patient", "hôpital", "diagnostic",
            "clinique", "épidémi", "pharmac", "thérapie", "maladie",
            "public health", "soins",
        ],
        "Biologie": [
            "biologie", "génétique", "cellule", "adn", "génom",
            "microbiolog", "écologie", "espèce", "biodiversité",
        ],
        "Mathématiques": [
            "équation", "algèbre", "statistique", "probabilité",
            "mathématique", "modélisation", "optimisation", "théorème",
        ],
        "Agronomie": [
            "agronom", "agriculture", "agricole", "culture", "sol",
            "élevage", "sécurité alimentaire", "rural",
        ],
        "Chimie": [
            "chimie", "chimique", "molécule", "catalyse", "synthèse",
            "phytochimique", "composé",
        ],
        "Physique": [
            "physique", "énergie", "optique", "mécanique", "quantique",
            "thermodynamique",
        ],
        "Sciences sociales": [
            "sociolog", "socio-économique", "anthropolog", "politique",
            "éducation", "gouvernance", "communauté",
        ],
        "Économie": [
            "économie", "économique", "marché", "finance", "développement",
            "pauvreté", "emploi",
        ],
        "Environnement": [
            "environnement", "climat", "eau", "hydrique", "pollution",
            "développement durable", "ressource", "sahel",
        ],
        "Ingénierie": [
            "génie", "ingénier", "infrastructure", "électrique",
            "civil", "industriel", "réseau électrique", "énergie renouvelable",
        ],
        "Linguistique": [
            "langue", "linguist", "poular", "soussou", "malinké",
            "traduction", "corpus",
        ],
    }

    scores = {}
    for domaine, mots in domaines.items():
        score = 0
        for mot in mots:
            if mot in texte:
                score += texte.count(mot)
        scores[domaine] = score

    meilleur_domaine = max(scores, key=scores.get)
    if scores[meilleur_domaine] == 0:
        return "Autres"
    return meilleur_domaine


def calculer_score_pertinence(texte, mots_cles, domaine):
    """Score 0–1 : longueur du texte, mots-clés extraits, domaine identifié."""
    n = len((texte or "").strip())
    score_longueur = min(n / 8000.0, 1.0) * 0.4
    nb_mots = len([m for m in (mots_cles or "").split(",") if m.strip()])
    score_mots = min(nb_mots / 15.0, 1.0) * 0.3
    score_domaine = 0.3 if domaine and domaine != "Autres" else 0.05
    return round(min(score_longueur + score_mots + score_domaine, 1.0), 2)


# ================================
# INDEXATION INTERNATIONALE (AUTO)
# Bases : Scopus | WoS | DOAJ | AJOL
# ================================

def normaliser_doi(doi):
    if not doi:
        return None
    doi = str(doi).strip()
    doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi, flags=re.I)
    return doi or None


def normaliser_issn(issn):
    if not issn:
        return None
    issn = str(issn).strip().upper().replace('–', '-').replace(' ', '')
    issn = issn.replace('ISSN', '').replace(':', '').strip()
    m = re.match(r'^(\d{4})-?(\d{3}[\dX])$', issn)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}"


def extraire_issns_du_texte(texte):
    if not texte:
        return []
    pattern = r'(?:ISSN[:\s]*)?(\d{4}[-–]\d{3}[\dXx])'
    trouves = []
    for match in re.findall(pattern, texte, flags=re.I):
        issn = normaliser_issn(match)
        if issn and issn not in trouves:
            trouves.append(issn)
    return trouves


def _http_get(url, params=None, headers=None):
    try:
        resp = requests.get(
            url,
            params=params,
            headers=headers or HTTP_HEADERS,
            timeout=HTTP_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp
    except requests.RequestException:
        return None
    return None


def enrichir_meta_depuis_doi(doi):
    """Récupère ISSN + titre de revue via Crossref à partir du DOI."""
    doi = normaliser_doi(doi)
    meta = {"issn": None, "issns": [], "nom_revue": None, "titre": None}
    if not doi:
        return meta

    resp = _http_get(f"https://api.crossref.org/works/{quote(doi)}")
    if not resp:
        return meta

    try:
        message = resp.json().get("message", {})
    except ValueError:
        return meta

    meta["titre"] = (message.get("title") or [None])[0]
    container = message.get("container-title") or []
    if container:
        meta["nom_revue"] = container[0]

    issns = []
    for raw in message.get("ISSN") or []:
        issn = normaliser_issn(raw)
        if issn and issn not in issns:
            issns.append(issn)
    meta["issns"] = issns
    meta["issn"] = issns[0] if issns else None
    return meta


def verifier_doaj(issn=None, nom_revue=None, doi=None):
    """True si la revue/article est dans DOAJ."""
    queries = []
    issn = normaliser_issn(issn)
    doi = normaliser_doi(doi)

    if issn:
        queries.append(f"https://doaj.org/api/search/journals/issn:{quote(issn)}")
    if nom_revue:
        queries.append(
            f"https://doaj.org/api/search/journals/title:{quote(nom_revue.strip())}"
        )
    if doi:
        queries.append(f"https://doaj.org/api/search/articles/doi:{quote(doi)}")

    for url in queries:
        resp = _http_get(url, params={"pageSize": 1})
        if not resp:
            continue
        try:
            data = resp.json()
        except ValueError:
            continue
        total = data.get("total")
        if total is None:
            total = len(data.get("results") or [])
        if total and int(total) > 0:
            return True
    return False


def verifier_ajol(issn=None, nom_revue=None):
    """
    True si la revue est sur African Journals Online (AJOL).
    Vérifie OpenAlex (homepage ajol.info) puis une recherche AJOL.
    """
    issn = normaliser_issn(issn)

    # OpenAlex source by ISSN
    if issn:
        resp = _http_get(
            "https://api.openalex.org/sources",
            params={"filter": f"issn:{issn}", "per_page": 5},
        )
        if resp:
            try:
                results = resp.json().get("results") or []
            except ValueError:
                results = []
            for src in results:
                homepage = (src.get("homepage_url") or "").lower()
                host = (src.get("host_organization_name") or "").lower()
                if "ajol.info" in homepage or "african journals online" in host or "ajol" in host:
                    return True

    # OpenAlex search by journal title
    if nom_revue:
        resp = _http_get(
            "https://api.openalex.org/sources",
            params={"search": nom_revue.strip(), "per_page": 10},
        )
        if resp:
            try:
                results = resp.json().get("results") or []
            except ValueError:
                results = []
            nom_l = nom_revue.strip().lower()
            for src in results:
                name = (src.get("display_name") or "").lower()
                homepage = (src.get("homepage_url") or "").lower()
                if "ajol.info" in homepage and (nom_l in name or name in nom_l):
                    return True
                if "ajol.info" in homepage and nom_l[:20] in name:
                    return True

        # Recherche HTML AJOL (signal faible mais utile)
        resp = _http_get(
            "https://www.ajol.info/index.php/index/search/search",
            params={"query": nom_revue.strip(), "searchJournal": 1},
            headers={
                **HTTP_HEADERS,
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        if resp and resp.text:
            body = resp.text.lower()
            if nom_revue.strip().lower()[:25] in body and "ajol" in body:
                # Évite les faux positifs trop larges : présence d'un lien journal
                if "/index.php/" in body and "no results" not in body:
                    return True

    return False


def _wikidata_sparql(query):
    resp = _http_get(
        "https://query.wikidata.org/sparql",
        params={"format": "json", "query": query},
        headers={
            **HTTP_HEADERS,
            "Accept": "application/sparql-results+json",
        },
    )
    if not resp:
        return []
    try:
        return resp.json().get("results", {}).get("bindings", [])
    except ValueError:
        return []


def verifier_scopus(issn=None, nom_revue=None):
    """
    True si la revue a un identifiant Scopus Source (Wikidata P7363).
    Proxie libre — Scopus API officielle est payante.
    """
    issn = normaliser_issn(issn)
    if issn:
        query = f"""
        SELECT ?item WHERE {{
          ?item wdt:P236 "{issn}" .
          ?item wdt:P7363 ?scopusId .
        }} LIMIT 1
        """
        if _wikidata_sparql(query):
            return True

    if nom_revue:
        # Recherche entité puis filtre Scopus ID
        resp = _http_get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbsearchentities",
                "search": nom_revue.strip(),
                "language": "en",
                "type": "item",
                "limit": 5,
                "format": "json",
            },
        )
        if resp:
            try:
                hits = resp.json().get("search") or []
            except ValueError:
                hits = []
            ids = " ".join(f"wd:{h['id']}" for h in hits if h.get("id"))
            if ids:
                query = f"""
                SELECT ?item WHERE {{
                  VALUES ?item {{ {ids} }}
                  ?item wdt:P7363 ?scopusId .
                }} LIMIT 1
                """
                if _wikidata_sparql(query):
                    return True
    return False


def verifier_wos(issn=None, nom_revue=None):
    """
    True si la revue est liée à Web of Science / SCIE sur Wikidata.
    Proxie libre — Clarivate MJL API n'est pas librement accessible.
    Q1047887 = Web of Science ; Q1791981 ≈ Science Citation Index Expanded.
    """
    issn = normaliser_issn(issn)
    if issn:
        query = f"""
        SELECT ?item WHERE {{
          ?item wdt:P236 "{issn}" .
          {{
            ?item wdt:P463 wd:Q1047887 .
          }} UNION {{
            ?item wdt:P463 wd:Q1791981 .
          }} UNION {{
            ?item wdt:P8379 ?wosId .
          }}
        }} LIMIT 1
        """
        if _wikidata_sparql(query):
            return True

    if nom_revue:
        resp = _http_get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "wbsearchentities",
                "search": nom_revue.strip(),
                "language": "en",
                "type": "item",
                "limit": 5,
                "format": "json",
            },
        )
        if resp:
            try:
                hits = resp.json().get("search") or []
            except ValueError:
                hits = []
            ids = " ".join(f"wd:{h['id']}" for h in hits if h.get("id"))
            if ids:
                query = f"""
                SELECT ?item WHERE {{
                  VALUES ?item {{ {ids} }}
                  {{
                    ?item wdt:P463 wd:Q1047887 .
                  }} UNION {{
                    ?item wdt:P463 wd:Q1791981 .
                  }} UNION {{
                    ?item wdt:P8379 ?wosId .
                  }}
                }} LIMIT 1
                """
                if _wikidata_sparql(query):
                    return True
    return False


def verifier_indexation_internationale(
    doi=None,
    nom_revue=None,
    texte_pdf=None,
    titre=None,
):
    """
    Vérifie automatiquement si la publication est reconnue dans
    Scopus, WoS, DOAJ ou AJOL.

    Retourne un dict :
      - statut: 'Acceptée' | 'Rejetée' | 'En attente'
      - bases: list[str] des bases où la revue/article a été trouvé
      - motif: str
      - issn: str|None
      - erreurs: list[str] (APIs injoignables)
    """
    doi = normaliser_doi(doi)
    nom_revue = (nom_revue or "").strip() or None

    # Enrichissement métadonnées
    meta = enrichir_meta_depuis_doi(doi) if doi else {
        "issn": None, "issns": [], "nom_revue": None, "titre": None
    }
    if not nom_revue:
        nom_revue = meta.get("nom_revue")

    issns = list(meta.get("issns") or [])
    for issn in extraire_issns_du_texte(texte_pdf or ""):
        if issn not in issns:
            issns.append(issn)
    issn_principal = issns[0] if issns else None

    bases_trouvees = []
    checks_reussis = 0  # au moins une API a répondu sans crash total
    erreurs = []

    checks = [
        ("DOAJ", lambda: verifier_doaj(issn=issn_principal, nom_revue=nom_revue, doi=doi)),
        ("AJOL", lambda: verifier_ajol(issn=issn_principal, nom_revue=nom_revue)),
        ("Scopus", lambda: verifier_scopus(issn=issn_principal, nom_revue=nom_revue)),
        ("WoS", lambda: verifier_wos(issn=issn_principal, nom_revue=nom_revue)),
    ]

    # Sans ISSN ni nom de revue ni DOI : impossible de vérifier → En attente
    if not issn_principal and not nom_revue and not doi:
        return {
            "statut": "En attente",
            "bases": [],
            "motif": (
                "Vérification d'indexation en attente : "
                "DOI, ISSN ou nom de revue manquant."
            ),
            "issn": None,
            "erreurs": [],
        }

    for nom_base, fn in checks:
        try:
            ok = bool(fn())
            checks_reussis += 1
            if ok:
                bases_trouvees.append(nom_base)
        except Exception as exc:
            erreurs.append(f"{nom_base}: {exc}")

    if bases_trouvees:
        return {
            "statut": "Acceptée",
            "bases": bases_trouvees,
            "motif": "",
            "issn": issn_principal,
            "erreurs": erreurs,
        }

    # Aucune base positive
    if checks_reussis == 0:
        # Toutes les vérifs ont échoué techniquement
        return {
            "statut": "En attente",
            "bases": [],
            "motif": (
                "Vérification d'indexation en cours : "
                "impossible de joindre les services externes "
                f"({'; '.join(erreurs) if erreurs else 'timeout/réseau'})."
            ),
            "issn": issn_principal,
            "erreurs": erreurs,
        }

    detail = (
        f"ISSN={issn_principal or '—'}, revue={nom_revue or '—'}, DOI={doi or '—'}."
    )
    return {
        "statut": "Rejetée",
        "bases": [],
        "motif": (
            "Publication non reconnue dans Scopus, Web of Science (WoS), "
            f"DOAJ ni AJOL. {detail}"
        ),
        "issn": issn_principal,
        "erreurs": erreurs,
    }
