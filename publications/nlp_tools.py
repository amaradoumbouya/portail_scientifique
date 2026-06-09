import re
import string
import fitz  # PyMuPDF
import spacy
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer



# Télécharger stopwords
nltk.download('stopwords')

# Stop words français
french_stopwords = stopwords.words('french')

# Chargement modèle NLP français
nlp = spacy.load("fr_core_news_sm")



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

    texte = texte.lower()

    domaines = {

        "Informatique": [
            "intelligence artificielle",
            "machine learning",
            "deep learning",
            "réseau",
            "algorithme",
            "base de données",
            "programmation"
        ],

        "Santé": [
            "médical",
            "santé",
            "patient",
            "hôpital",
            "diagnostic"
        ],

        "Biologie": [
            "biologie",
            "génétique",
            "cellule",
            "adn"
        ],

        "Mathématiques": [
            "équation",
            "algèbre",
            "statistique",
            "probabilité"
        ]
    }

    scores = {}

    for domaine, mots in domaines.items():

        score = 0

        for mot in mots:

            if mot in texte:
                score += 1

        scores[domaine] = score

    meilleur_domaine = max(scores,key=scores.get)

    if scores[meilleur_domaine] == 0:
        return "Autres"

    return meilleur_domaine








# Ancienne version (sans reset du pointeur)
# def extraire_texte_du_pdf(fichier):
#     doc = fitz.open(stream=fichier.read(), filetype="pdf")
#     texte = ""
#     for page in doc:
#         texte += page.get_text()
#     return texte



# Avec résumé et mots clés en une seule fonction
# def extraire_resume_et_mots_cles(texte):
#     doc = nlp(texte)
#     resume = " ".join([sent.text for sent in list(doc.sents)[:3]])
#     vectorizer = TfidfVectorizer(stop_words=french_stopwords, max_features=5)
#     X = vectorizer.fit_transform([texte])
#     mots_cles = ", ".join(vectorizer.get_feature_names_out())
#     return resume, mots_cles



# Ancienne version classifier domaine (sans le nettoyage préalable)
# def classifier_domaine(texte):
#     texte = texte.lower()
#     if "réseau" in texte or "machine" in texte or "donnée" in texte:
#         return "Informatique"
#     elif "biologie" in texte or "génétique" in texte:
#         return "Biologie"
#     elif "santé" in texte or "médical" in texte:
#         return "Santé"
#     return "Autres"








