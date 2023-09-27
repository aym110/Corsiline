from django.contrib import admin
from .models import Prof,Course,Chapter,Question,Choice,Etudiant,User,Categorie,Notification,Submission,Inscription
# Register your models here.

admin.site.register(User)
admin.site.register(Prof)
admin.site.register(Etudiant)
admin.site.register(Inscription)
admin.site.register(Course)
admin.site.register(Chapter)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Categorie)
admin.site.register(Notification)
admin.site.register(Submission)