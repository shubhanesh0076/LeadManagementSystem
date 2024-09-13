from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
# from django.utils.translation import gettext_lazya as _
from django.utils.text import slugify 
import random,string
from django.db.models.signals import pre_save

# Create your models here.

class UserManager(BaseUserManager):
    """ Define a model manager for User model with no username field. """

    def _create_user(self, email, password=None, **extra_fields):
        """ Create and save a User with the given email and password. """
        
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """ Create and save a SuperUser with the given email and password. """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)



class User(AbstractUser):
    """ User model class. """
    
    CHOOSE_GENDER = (
        ('Male', 'M'),
        ('Female', 'F'),
        ('Other', 'O'),
        ('Prefered not to answer', 'Prefer not to answer')
    )

    
    username=models.CharField(max_length=30, default='', null=True, blank=True)
    first_name = models.CharField(max_length=20, default="", null=True, blank=True)
    last_name = models.CharField(max_length=20, default="", null=True, blank=True)
    email = models.EmailField(verbose_name='email', max_length=254, unique=True, blank=False)
    mobile_no = models.CharField(max_length=15, null=True, blank=True)
    alt_mobile_no = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=25, default="Prefered not to answer", choices=CHOOSE_GENDER, null=True, blank=True)
    nationality=models.CharField(max_length=12, default="", null=True, blank=True)
    dob=models.DateField(max_length=12, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    change_password_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    current_city = models.CharField(max_length=30, null=True, blank=True)
    slug = models.SlugField(max_length=200, null=True, blank=True)
    password=models.TextField()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] # Email & Password are required by default.
    objects = UserManager()

    def __str__(self):
        return "{0}".format(self.email)



def random_string_generator(size = 10, chars = string.ascii_lowercase + string.digits): 
    return ''.join(random.choice(chars) for _ in range(size)) 
  
def unique_slug_generator(instance, new_slug = None): 
    if new_slug is not None: 
        slug = new_slug 
    else: 
        slug = slugify(instance.first_name) 
    Klass = instance.__class__ 
    qs_exists = Klass.objects.filter(slug = slug).exists() 
      
    if qs_exists: 
        new_slug = "{slug}-{randstr}".format( 
            slug = slug, randstr = random_string_generator(size = 4)) 
              
        return unique_slug_generator(instance, new_slug = new_slug) 
    return slug 

def pre_save_receiver(sender, instance, *args, **kwargs): 
    if not instance.slug: 
       instance.slug = unique_slug_generator(instance) 
pre_save.connect(pre_save_receiver, sender = User) 