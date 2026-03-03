import fitz  # PyMuPDF
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer

french_stopwords = stopwords.words('french')



nlp = spacy.load("fr_core_news_sm")

def extraire_texte_du_pdf(fichier):
    doc = fitz.open(stream=fichier.read(), filetype="pdf")
    texte = ""
    for page in doc:
        texte += page.get_text()
    return texte

def extraire_resume_et_mots_cles(texte):
    doc = nlp(texte)
    resume = " ".join([sent.text for sent in list(doc.sents)[:3]])
    vectorizer = TfidfVectorizer(stop_words=french_stopwords, max_features=5)
    X = vectorizer.fit_transform([texte])
    mots_cles = ", ".join(vectorizer.get_feature_names_out())
    return resume, mots_cles

def classifier_domaine(texte):
    texte = texte.lower()
    if "réseau" in texte or "machine" in texte or "donnée" in texte:
        return "Informatique"
    elif "biologie" in texte or "génétique" in texte:
        return "Biologie"
    elif "santé" in texte or "médical" in texte:
        return "Santé"
    return "Autres"








