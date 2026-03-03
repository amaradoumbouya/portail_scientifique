from django.shortcuts import render, redirect, get_object_or_404
from portail_site.forms import CustumerUserForm
from django.contrib import messages
from accounts.models import CustumerUser
from django.contrib.auth import authenticate, login
from publications.models import Publication, PublicationLike, PublicationComment, PublicationDownload
from publications.forms import PublicationForm
from django.views.generic import TemplateView
from types_document.models import TypeDocument
from auteurs.models import Auteur
from encadreurs.models import Encadreur
from institutions.models import Institution
from django.core.paginator import Paginator
from contact_us.forms import ContactUsForm
from contact_us.models import ContactUs
from django.utils import timezone
from django.contrib.auth.decorators import login_required

# Pour les vues publicationLike, publicationComment et publicationDownload
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Envoi d'un email apres l'inscription sur le portail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Prefetch


# Pour la vue d'activation du compte apres l'inscription
from django.utils.encoding import force_str






# Fonction permettant de formater la durée en mois, jours, heures, minutes et secondes
def format_duration(seconds):
    if seconds is None:
        return None

    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)
    months = int(days // 30)

    if months >= 1:
        return f"il y a {months} mois"
    elif days >= 1:
        return f"il y a {days} jours"
    elif hours >= 1:
        return f"il y a {hours}h {minutes % 60}min"
    elif minutes >= 1:
        return f"il y a {minutes}min"
    else:
        return f"il y a {int(seconds)}s"

# La vue du tableau de bord backOffice
class DashboardTemplateView(TemplateView):
    template_name = 'back/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        def time_since(obj, attr):
            return (now - getattr(obj, attr)).total_seconds() if obj else None

        # ADMIN : Voir toutes les publications et stats globales
        if user.is_authenticated and getattr(user, "role", "") == "admin":
            context['publications'] = Publication.objects.order_by('-date_ajout_systeme')
            context['nb_publications'] = Publication.objects.count()
            context['nb_auteurs'] = Auteur.objects.count()
            context['nb_encadreurs'] = Encadreur.objects.count()
            context['nb_institutions'] = Institution.objects.count()

            # Derniers éléments
            context['time_since_last_publication'] = format_duration(time_since(
                Publication.objects.order_by('-date_ajout_systeme').first(), 'date_ajout_systeme'
            ))
            context['time_since_last_auteur'] = format_duration(time_since(
                Auteur.objects.order_by('-created_at').first(), 'created_at'
            ))
            context['time_since_last_encadreur'] = format_duration(time_since(
                Encadreur.objects.order_by('-created_at').first(), 'created_at'
            ))
            context['time_since_last_institution'] = format_duration(time_since(
                Institution.objects.order_by('-created_at').first(), 'created_at'
            ))

        # UTILISATEUR SIMPLE : Voir uniquement ses propres stats
        else:
            if not user.is_authenticated:
                return context

            context['publications'] = Publication.objects.filter(user=user).order_by('-date_ajout_systeme')
            context['nb_publications'] = context['publications'].count()
            context['nb_likes'] = PublicationLike.objects.filter(user=user).count()
            context['nb_commentaires'] = PublicationComment.objects.filter(user=user).count()
            context['nb_telechargements'] = PublicationDownload.objects.filter(user=user).count()

            context['time_since_last_publication'] = format_duration(time_since(
                context['publications'].first(), 'date_ajout_systeme'
            ))
            context['time_since_last_like'] = format_duration(time_since(
                PublicationLike.objects.filter(user=user).order_by('-liked_at').first(), 'liked_at'
            ))
            context['time_since_last_commentaire'] = format_duration(time_since(
                PublicationComment.objects.filter(user=user).order_by('-created_at').first(), 'created_at'
            ))
            context['time_since_last_telechargement'] = format_duration(time_since(
                PublicationDownload.objects.filter(user=user).order_by('-downloaded_at').first(), 'downloaded_at'
            ))

        return context

# La d'accueil
class IndexTemplateView(TemplateView):
    template_name = 'index.html'

# La vue de toutes les publications
class PublicationTemplateView(TemplateView):
    template_name = 'pages/publication.html'

# La vue publication par type
def publication_par_type_template_view(request, slug):
    type_document = get_object_or_404(TypeDocument, slug=slug)
    publications = Publication.objects.filter(type_document=type_document, statut_publication=True).order_by('-id')
    paginator = Paginator(publications, 6)  # ou 10, selon votre choix
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, "pages/publication_par_type.html", {'page_obj':page_obj, 'type_document':type_document})

# La vue Apropos
class AproposTemplateView(TemplateView):
    template_name = 'pages/a_propos.html'


# La vue de contact
def contact_us_template_view(request):
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            contact = form.save()
            email = contact.email

            # Envoi de l'email de réception
            subject = "Portail Scientifique: Votre message a bien été reçu"
            message = f"""
            Bonjour M/Mme {contact.nom_complet},
            Merci de nous avoir contactés. Nous avons bien reçu votre message et vous répondrons dans les plus brefs délais.

            Cordialement,
            L’équipe Techniqque du CRICT(Centre de Recherche en Informatique et Cyber-Technologie)
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            messages.success(request, "Message reçu avec succès. Un mail de confirmation vous a été envoyé.")
            form = ContactUsForm()
        else:
            messages.error(request, "Une erreur est survenue. Veuillez vérifier les informations.")
    else:
        form = ContactUsForm()

    return render(request, "pages/contact.html", {"form": form})


# La vue d'inscription au portail scientifique
def inscriptionTemplateView(request):
    if request.method == 'POST':
        form = CustumerUserForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            password1 = data['password1']
            password2 = data['password2']

            if password1 != password2:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
            else:
                new_custumer = CustumerUser.objects.create(
                    prenoms=data['prenoms'],
                    nom=data['nom'],
                    adresse=data['adresse'],
                    email=data['email'],
                    tel=data['tel'],
                    sexe=data['sexe'],
                    is_active=False,  # important
                )
                new_custumer.set_password(password1)
                new_custumer.save()

                # Envoi de l’email d’activation
                current_site = get_current_site(request)
                mail_subject = 'Activation de votre compte'
                uid = urlsafe_base64_encode(force_bytes(new_custumer.pk))
                token = default_token_generator.make_token(new_custumer)
                activation_link = reverse('portail_site:activation', kwargs={'uidb64': uid, 'token': token})
                activation_url = f"http://{current_site.domain}{activation_link}"

                message = render_to_string('emails/activation_email.html', {
                    'user': new_custumer,
                    'activation_url': activation_url,
                })

                send_mail(
                    mail_subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [new_custumer.email],
                    fail_silently=False,
                )

                messages.success(request, "Inscription réussie. Veuillez vérifier votre email pour activer votre compte.")
                return redirect('portail_site:connexion')
        else:
            messages.error(request, "Formulaire invalide.")
    else:
        form = CustumerUserForm()

    return render(request, 'pages/inscription.html', {'form': form})




# La vue d'activation du compte au portail
def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustumerUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustumerUser.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter.")
        return redirect('portail_site:connexion')
    else:
        messages.error(request, "Le lien d’activation est invalide ou a expiré.")
        return redirect('portail_site:inscription')




# La vue de connexion au portail 
def user_login_view(request, *args, **kwargs):
    
    if request.method == 'POST':
        
        email = request.POST.get('email')
        
        password = request.POST.get('password')
        
        user = CustumerUser.objects.filter(email=email)
        
        if user.exists():
            
            if user.first().is_active:
                
                user = authenticate(request, email=email, password=password)
                
                if user is not None:
                    
                    login(request, user)
                    
                    messages.success(request, 'Vous êtes connectés.')
                    
                else:
                    messages.error(request, "Le nom d'utilisateur ou le mot de passe est incorrecte.")
                    
            else:
                messages.error(request, "Votre compte n'est pas encore activé. Veuillez vérifier votre boite de reception email.")
                
        else:
            messages.error(request, "Le nom d'utilisateur ou le mot de passe est incorrecte.")
            
        return redirect('portail_site:dashboard')  
         
    return render(request, 'registration/login.html', {})



# La vue du profil_user
class MonprofilTemplateView(TemplateView):
    template_name = 'pages/mon_profil.html'



# La vue de toutes les publications_user
class MespublicationsTemplateView(TemplateView):
    template_name = 'pages/mes_publications.html'


# La vue de publication_user
@login_required
def depot_publication(request):

    if not request.user.role:

        return render(request, 'pages/profil_auteur.html')

    if request.method == 'POST':

        form = PublicationForm(request.POST, request.FILES)

        if form.is_valid():

            publication = form.save()

            form.save_m2m()  # sauvegarde les auteurs

            return redirect('dashboard')
    else:

        form = PublicationForm()

    return render(request, 'pages/depot_publication.html', {'form': form})



# La vue des messages_user
class MessagesTemplateView(TemplateView):
    template_name = 'pages/messages.html'


# L vue des notifications_user
class NotificationsTemplateView(TemplateView):
    template_name = 'pages/notifications.html'



# Detail_d'une_publication
def detail_publication_template(request, slug):
    publication = get_object_or_404(Publication, slug=slug)
    publications_categorie = Publication.objects.filter(domaine=publication.domaine).exclude(id=publication.id).order_by('-id')[:10]
    comments = publication.comments.order_by('-id')[:5]
    return render(request, 'pages/detail_publication.html', {'publication': publication, 'publications_categorie': publications_categorie, 'comments': comments,
    })


# Informations sur l'auteur
def detail_auteur_template_view(request, slug):
    auteur = get_object_or_404(Auteur, slug=slug)
    publications = Publication.objects.filter(auteurs__in=[auteur]).order_by('-id')[:10]
    return render(request, 'pages/detail_auteur.html', {'auteur': auteur, 'publications': publications,})



# Informations sur l'encadreur
def detail_encadreur_template_view(request, slug):
    encadreur = get_object_or_404(Encadreur, slug=slug)
    publications = Publication.objects.filter(encadreurs__in=[encadreur]).order_by('-id')[:10]
    return render(request, 'pages/detail_encadreur.html', {'encadreur': encadreur, 'publications': publications,})




# La vue de like d'une publication
@require_POST
@login_required
def like_publication(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    like, created = PublicationLike.objects.get_or_create(publication=publication, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({
        'liked': liked,
        'like_count': publication.likes.count()
    })


# La vue de commentaire d'une publication
@require_POST
@login_required
def comment_publication(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    content = request.POST.get('content')
    comment = PublicationComment.objects.create(publication=publication, user=request.user, contenu=content)
    return JsonResponse({
        'user': request.user.full_name(),
        'content': comment.contenu,
        'created_at': comment.created_at.strftime('%d/%m/%Y %H:%M')
    })

# La vue de téléchargement d'une publication
@require_POST
def download_publication(request, pk):
    publication = get_object_or_404(Publication, pk=pk)
    user = request.user if request.user.is_authenticated else None
    ip = request.META.get('REMOTE_ADDR')
    PublicationDownload.objects.create(publication=publication, user=user, ip_address=ip)
    return JsonResponse({'status': 'ok'})

