from django.contrib import admin
from .models import User,News,Infographic,Publication,Data

# Register your models here.

admin.site.register(User)
admin.site.register(News)
admin.site.register(Infographic)
admin.site.register(Publication)
admin.site.register(Data)