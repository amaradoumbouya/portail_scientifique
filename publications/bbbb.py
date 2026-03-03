# fichier: models.py
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User

class Publication(models.Model):
    STATUT_INDEXATION = (
        ('En attente', 'En attente'),
        ('Indexée', 'Indexée'),
        ('Rejetée', 'Rejetée')
    )

    titre = models.CharField(max_length=300, verbose_name='Titre')
    auteurs = models.ManyToManyField('Auteur', verbose_name='Auteur(s)')
    encadreurs = models.ManyToManyField('Encadreur', verbose_name='Encadreur(s)')
    type_document = models.ForeignKey('TypeDocument', on_delete=models.SET_NULL, null=True, verbose_name='Type du document')
    domaine = models.CharField(max_length=100, blank=True, verbose_name='Domaine')
    date_publication = models.DateField(verbose_name='Date de publication')
    fichier_pdf = models.FileField(upload_to='publications/', verbose_name='Fichier')
    langue = models.CharField(max_length=50, default='français', verbose_name='Langue')
    institutions_contributrices = models.ManyToManyField('Institution', related_name='publications_contribuees', verbose_name='Institution(s)')
    doi = models.CharField(max_length=100, blank=True, null=True, verbose_name='Doi')
    orcid_auteur_principal = models.CharField(max_length=100, blank=True, null=True, verbose_name='Orcid')
    statut_indexation = models.CharField(max_length=50, choices=STATUT_INDEXATION, default='En attente', verbose_name='Statut indexation')
    mots_cles = models.TextField(blank=True, verbose_name='Mots cles')
    resume = models.TextField(verbose_name='Resumé')
    date_ajout_systeme = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titre


# fichier: forms.py
from django import forms
from .models import Publication

class PublicationForm(forms.ModelForm):
    class Meta:
        model = Publication
        fields = ['titre', 'fichier_pdf', 'type_document', 'date_publication', 'langue', 'institutions_contributrices']


# fichier: nlp_tools.py
import fitz  # PyMuPDF
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

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
    vectorizer = TfidfVectorizer(stop_words='french', max_features=5)
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


# fichier: views.py
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PublicationForm
from .models import Publication
from .nlp_tools import extraire_texte_du_pdf, extraire_resume_et_mots_cles, classifier_domaine

def depot_et_indexation(request):
    if request.method == 'POST':
        form = PublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication = form.save(commit=False)
            fichier = request.FILES['fichier_pdf']
            texte = extraire_texte_du_pdf(fichier)
            resume, mots_cles = extraire_resume_et_mots_cles(texte)
            domaine = classifier_domaine(texte)

            publication.resume = resume
            publication.mots_cles = mots_cles
            publication.domaine = domaine
            publication.statut_indexation = 'Indexée'
            publication.user = request.user if request.user.is_authenticated else None
            publication.save()
            form.save_m2m()
            return redirect('publication_detail', slug=publication.slug)
    else:
        form = PublicationForm()
    return render(request, 'portail/depot_et_indexation.html', {'form': form})

def publication_detail(request, slug):
    publication = get_object_or_404(Publication, slug=slug)
    return render(request, 'portail/publication_detail.html', {'publication': publication})


# fichier: urls.py
from django.urls import path
from .views import depot_et_indexation, publication_detail

urlpatterns = [
    path('publication/nouveau/', depot_et_indexation, name='depot_et_indexation'),
    path('publication/<slug:slug>/', publication_detail, name='publication_detail'),
]


# fichier: templates/portail/depot_et_indexation.html
{% extends 'base.html' %}
{% block content %}
<h2>Soumettre une publication</h2>
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Soumettre</button>
</form>
{% endblock %}


# fichier: templates/portail/publication_detail.html
{% extends 'base.html' %}
{% block content %}
<h2>{{ publication.titre }}</h2>
<p><strong>Auteurs :</strong> {{ publication.auteurs.all|join:", " }}</p>
<p><strong>Encadreurs :</strong> {{ publication.encadreurs.all|join:", " }}</p>
<p><strong>Domaine :</strong> {{ publication.domaine }}</p>
<p><strong>Résumé :</strong> {{ publication.resume }}</p>
<p><strong>Mots-clés :</strong> {{ publication.mots_cles }}</p>
<p><strong>Date :</strong> {{ publication.date_publication }}</p>
<p><strong>Langue :</strong> {{ publication.langue }}</p>
<p><strong>Statut :</strong> {{ publication.statut_indexation }}</p>
{% endblock %}
