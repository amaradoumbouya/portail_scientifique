from django.db import models
from django.utils.text import slugify
from institutions.models import Institution
from django.db.models.signals import post_save
from django.dispatch import receiver 
from django.utils.crypto import get_random_string
import random
from django.conf import settings
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser,BaseUserManager

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("l'email est obligatoire")
        
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        user = self.create_user(email=email, password=password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user

class CustumerUser(AbstractBaseUser, PermissionsMixin):
    SEXE = (
        ('Masculin', 'Masculin'),
        ('Féminin', 'Féminin'),
    )
    prenoms       = models.CharField(max_length=150, verbose_name='Prénom(s) :')
    nom           = models.CharField(max_length=150, verbose_name='Nom :')
    sexe          = models.CharField(max_length=150,choices=SEXE, blank=True,null=True,verbose_name='Sexe :')
    email         = models.EmailField(max_length=255, unique=True, db_index=True, verbose_name='Email :')
    tel           = models.CharField(max_length=20,unique=True, verbose_name='Téléphone :')
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    slug          = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True,)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)


    @property
    def full_name(self):
        return f"{self.prenoms} {self.nom}"
    
    def __str__(self):
        return self.full_name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.full_name) + '-' + get_random_string(5)
        super(CustumerUser, self).save(*args, **kwargs)
    


    USERNAME_FIELD = "email"
    objects = MyUserManager()
            
    def has_perm(self, perm, obj=None):
        return self.is_staff
    
    

class UserProfile(models.Model):
    ROLES = (
        ('masterant', 'Masterant'),
        ('doctorant', 'Doctorant'),
        ('encadreur', 'Encadreur'),
        ('enseignant', 'Enseignant'),
        ('enseignant chercheur', 'Enseignant chercheur'),
        ('responsable institution', "Responsable d'institution"),
        ('admin', 'Administrateur'),
    )
    GRADE = (
        ('Assistant', 'Assistant'),
        ('Maître assistant', 'Maître assistant'),
        ('Maître de conférences', 'Maître de conférences'),
        ('Professeur', 'Professeur'),
        ('Autre', 'Autre'),
    )
    SPECIALITE = (
        ('Informatique', 'Informatique'),
        ('Biologie', 'Biologie'),
        ('Chimie', 'Chimie'),
        ('Physique', 'Physique'),
        ('Mathématiques', 'Mathématiques'),
        ('Médecine', 'Médecine'),
        ('Autre', 'Autre'),
    )
    user                   = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    profil_inc             = models.CharField(max_length=25, unique=True, editable=False, blank=True, null=True)
    adresse                = models.CharField(max_length=150, blank=True, null=True, verbose_name='Adresse :')
    institution            = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Institution :')
    fonction_poste         = models.CharField(max_length=150, blank=True, null=True, verbose_name='Fonction/postale :')
    grade                  = models.CharField(max_length=150, blank=True, null=True, choices=GRADE, verbose_name='Grade :')
    specialite             = models.CharField(max_length=150, blank=True, null=True, choices=SPECIALITE, verbose_name='Spécialité :')
    orcid                  = models.CharField(max_length=150, blank=True, null=True, verbose_name='ORCID :')
    role                   = models.CharField(max_length=150, blank=True, null=True, choices=ROLES, verbose_name='Rôle :')
    photo                  = models.ImageField(upload_to='accounts', blank=True, null=True, verbose_name='Photo :')
    reseau_social_facebook = models.URLField(blank=True, null=True, verbose_name= "Facebook")
    reseau_social_twitter  = models.URLField(blank=True, null=True, verbose_name= "Twitter")
    reseau_social_linkedin = models.URLField(blank=True, null=True, verbose_name= "LinkedIn")
    reseau_social_youtube  = models.URLField(blank=True, null=True, verbose_name= "YouTube")
    slug                   = models.SlugField(max_length=255, unique=True, editable=False)
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"Profil de {self.user.full_name}|{self.profil_inc}"
    
    def generate_profil_inc(self):
        prefix = "INC"

        # compteur basé sur le nombre d'utilisateurs
        count = UserProfile.objects.count() + 1

        part1 = str(count).zfill(4)
        part2 = str(random.randint(1000, 9999))
        part3 = str(random.randint(1000, 9999))

        return f"{prefix}-{part1}-{part2}-{part3}"


    def save(self, *args, **kwargs):

        if not self.profil_inc:
            self.profil_inc = self.generate_profil_inc()

        if not self.slug:
            self.slug = slugify(self.user.email) + '-' + get_random_string(5)
        super(UserProfile, self).save(*args, **kwargs)


    
    @property
    def ImageUrl(self):
        try:
            url = self.photo.url
        except Exception:
            url = ''
        return url 
    

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class User_biography(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='biographie')
    biographie = models.TextField(blank=True, null=True, verbose_name='Biographie :')
    is_published = models.BooleanField(default=False, verbose_name='Publié :')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Biographie de {self.user}"

class User_emploi(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emploi')
    nom_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nom de l'institution :")
    ville_emploi = models.CharField(max_length=150, blank=True, null=True, verbose_name="Ville de l'emploi :")
    region_emploi = models.CharField(max_length=150, blank=True, null=True, verbose_name="Région de l'emploi :")
    pays_emploi = models.CharField(max_length=150, blank=True, null=True, verbose_name="Pays de l'emploi :")
    departement_emploi = models.CharField(max_length=150, blank=True, null=True, verbose_name='Département :')
    poste_occupe = models.CharField(max_length=150, blank=True, null=True, verbose_name='Poste occupé :')
    date_debut_emploi = models.DateField(blank=True, null=True, verbose_name='Date de début :')
    date_fin_emploi = models.DateField(blank=True, null=True, verbose_name='Date de fin :')
    is_published = models.BooleanField(default=False, verbose_name='Publié :')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Emploi de {self.user}"

class User_etude_academique(models.Model):
    TYPE_FORMATION = (
        ('Academique', 'Académique'),
        ('Attestation', 'Attestation'),
        ('Certification', 'Certification'),
        ('Professionnelle', 'Professionnelle'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='etude_academique')
    type_formation = models.CharField(max_length=150, blank=True, null=True, choices=TYPE_FORMATION, verbose_name='Type de formation :')
    nom_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nom de l'institution :")
    ville_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Ville de l'institution :")
    region_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Région de l'institution :")
    pays_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Pays de l'institution :")
    departement_etude = models.CharField(max_length=150, blank=True, null=True, verbose_name='Département :')
    diplome_obtenu = models.CharField(max_length=150, blank=True, null=True, verbose_name='Diplôme obtenu :')
    date_debut_etude = models.DateField(blank=True, null=True, verbose_name='Date de début :')
    date_fin_etude = models.DateField(blank=True, null=True, verbose_name='Date de fin :')
    is_published = models.BooleanField(default=False, verbose_name='Publié :')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Etude académique de {self.user}"

class User_experience_professionnelle(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='experience_professionnelle')
    nom_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nom de l'institution :")
    poste_occupe = models.CharField(max_length=150, blank=True, null=True, verbose_name='Poste occupé :')
    date_debut_experience = models.DateField(blank=True, null=True, verbose_name='Date de début :')
    date_fin_experience = models.DateField(blank=True, null=True, verbose_name='Date de fin :')
    is_published = models.BooleanField(default=False, verbose_name='Publié :')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Expérience professionnelle de {self.user}"

class User_travaux_recherche(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='travaux_recherche')
    nom_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Nom de l'institution :")
    ville_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Ville de l'institution :")
    region_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Région de l'institution :")
    pays_institution = models.CharField(max_length=150, blank=True, null=True, verbose_name="Pays de l'institution :")
    departement_recherche = models.CharField(max_length=150, blank=True, null=True, verbose_name='Département de recherche :')
    poste_occupe = models.CharField(max_length=150, blank=True, null=True, verbose_name='Poste occupé :')
    titre_domaine_recherche = models.CharField(max_length=150, blank=True, null=True, verbose_name='Titre/Domaine :')
    date_de_debut_travaux = models.DateField(blank=True, null=True, verbose_name='Date de début :')
    date_de_fin_travaux = models.DateField(blank=True, null=True, verbose_name='Date de fin :')
    is_published = models.BooleanField(default=False, verbose_name='Publié :')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Travaux de recherche de {self.user}"