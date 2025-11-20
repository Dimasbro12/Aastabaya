from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom user model that inherits from Django's AbstractUser.
    This provides all the necessary fields and methods for authentication.
    """
    
    pass

class Data(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    data_name = models.CharField(max_length=255)
    data_description = models.TextField()
    data_image = models.ImageField(upload_to="data")
    data_view_count = models.PositiveIntegerField(default=1)
    data_created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.data_name
    
class News(models.Model):
    news_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255,blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    category_id = models.CharField(max_length=255, blank=True, null=True)
    category_name = models.CharField(max_length=255, blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    picture_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title
        
class Infographic(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    image = models.URLField(max_length=500, blank=True, null=True)
    dl = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.title

class Publication(models.Model):
    pub_id = models.CharField(unique=True)
    title = models.CharField(max_length=255, blank=True,null=True )
    image = models.URLField(max_length=500, blank=True, null=True)
    dl = models.URLField(max_length=500, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    abstract = models.TextField(blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.title

class HumanDevelopmentIndex(models.Model):
    """
    Stores the Human Development Index (IPM) for a specific location and year.
    This model is designed to hold the transposed data.
    """
    class LocationType(models.TextChoices):
        REGENCY = 'REG', 'Kabupaten/Regency'
        MUNICIPALITY = 'MUN', 'Kota/Municipality'

    location_name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=3, choices=LocationType.choices, default=LocationType.REGENCY)
    year = models.PositiveIntegerField()
    ipm_value = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.location_name} ({self.year}) - {self.ipm_value}"
    
    class Meta:
        unique_together = ('location_name', 'year')
        verbose_name = "Human Development Index (IPM)"
        verbose_name_plural = "Human Development Indices (IPM)"