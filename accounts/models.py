from django.db import models
from django.utils.text import slugify
from django.contrib.auth.base_user import AbstractBaseUser,BaseUserManager

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Vous devez entrer un email')
        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, email, password=None):
        user = self.create_user(email=email,password=password)
        user.is_admin = True
        user.is_staff = True
        user.save()
        return user

class CustumerUser(AbstractBaseUser):
    ROLES = (
        ('auteur', 'Auteur'),
        ('relecteur', 'Relecteur'),
        ('visiteur', 'Visiteur'),
        ('admin', 'Administrateur'),
    )
    SEXE=(
        ('masculin','Masculin'),
        ('feminin','Féminin'),
    )
    prenoms       = models.CharField(max_length=150, blank=True, null=True, verbose_name='Prénom(s) :')
    nom           = models.CharField(max_length=150, blank=True, null=True, verbose_name='Nom :')
    slug          = models.SlugField(max_length=255, unique=True, editable=False ,blank=True, null=True,)
    adresse       = models.CharField(max_length=150, blank=True, null=True, verbose_name='Adresse :')
    email         = models.EmailField(max_length=255, unique=True, blank=False, verbose_name='Email :')
    tel           = models.CharField(max_length=150, blank=True, null=True, verbose_name='Téléphone:')
    sexe          = models.CharField(max_length=150,choices=SEXE,blank=True,null=True,verbose_name='Sexe :')
    role          = models.CharField(max_length=150, blank=True, null=True,choices=ROLES, verbose_name='Rôle :')
    photo         = models.ImageField(upload_to='accounts', blank=True, null=True, verbose_name='Photo :')
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    is_admin      = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)


    @property
    def full_name(self):
        return f"{self.prenoms} {self.nom}"
    
    def __str__(self):
        return self.full_name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            last_pk = CustumerUser.objects.order_by('pk').last()
            self.slug = slugify(self.full_name) + '-' + str(last_pk.pk + 1) if last_pk else '1'
        super(CustumerUser, self).save(*args, **kwargs)
    
    @property
    def ImageUrl(self):
        try:
            url = self.photo.url
        except:
            url = ''
        return url 
    
    
    USERNAME_FIELD = "email"
    objects = MyUserManager()
            
    def has_perm(self, perm, obj=None):
        return True
    
    def has_module_perms(self, app_label):
        return True
    