from django.db import models

# Create your models here.
class User(models.Model):  
    email = models.EmailField()
    password = models.CharField(max_length=255)
    role=models.CharField(max_length=20,choices=[('etd','etd'),('prof','prof')],default='etd')
    


class Etudiant(User):
    nom = models.CharField(max_length=50,default='Aucun')
    prenom = models.CharField(max_length=50,default='Aucun')
    telephone=models.CharField(max_length=10,null=True,blank=True,default='Aucun')
    linkedin=models.CharField(max_length=100,null=True,blank=True,default='Aucun')
    twitter=models.CharField(max_length=100,null=True,blank=True,default='Aucun')
    sexe=models.CharField(max_length=20,choices=[('Femme','Femme'),('Homme','Homme')],default='Homme')
    photo=models.ImageField(upload_to='photo/etds/%y/%m/%d',default='photo/etds/default_user.jpg')
    LEVEL_CHOICES = [
        ('sans bac', 'sans bac'),
        ('bac', 'bac'),
        ('bac+2', 'bac+2'),
        ('bac+3', 'bac+3'),
        ('bac+5', 'bac+5'),
    ]
    NiveauEtude = models.CharField(max_length=10, null=False,choices=LEVEL_CHOICES,default='bac')
    def __str__(self):
        return self.nom
    
class Prof(User):
    nom = models.CharField(max_length=50,default='Aucun')
    prenom = models.CharField(max_length=50,default='Aucun')
    telephone=models.CharField(max_length=10,null=True,blank=True,default='Aucun')
    linkedin=models.CharField(max_length=100,null=True,blank=True,default='Aucun')
    twitter=models.CharField(max_length=100,null=True,blank=True,default='Aucun')
    sexe=models.CharField(max_length=20,choices=[('Femme','Femme'),('Homme','Homme')],default='Homme')
    photo=models.ImageField(upload_to='photo/profs/%y/%m/%d',default='photo/profs/default_user.jpg')
    bio=models.TextField()
    def __str__(self):
        return self.nom
    
class Categorie(models.Model):
    CATEGORIE_CHOICES=[
        ('Informatique','Informatique'),
        ('Business','Business'),
        ('Droit','Droit'),
        ('Appretissange des langues','Appretissange des langues'),
    ]
    nom = models.CharField(max_length=255,choices=CATEGORIE_CHOICES,default='Informatique')
    photo=models.ImageField(upload_to='photo/categories/%y/%m/%d',default='photo/categories/default_cours.png')  
    def __str__(self):
        return self.nom

class Course(models.Model):
    titre=models.CharField(max_length=50)
    categorie=models.ForeignKey(Categorie,on_delete=models.PROTECT,null=True)
    datePub=models.DateField(auto_now_add=True)    
    description=models.TextField()
    fichier=models.FileField(upload_to="support//%y/%m/%d",null=True,default=None)
    photo=models.ImageField(upload_to='photo/cours/%y/%m/%d',default='photo/cours/default_cours.png')
    prof=models.ForeignKey(Prof,on_delete=models.PROTECT,null=True)
    nombreEtds = models.IntegerField(editable=True,default=0)
    nombreChaps = models.IntegerField(editable=True,default=0)
    nombreQues = models.IntegerField(editable=True,default=0)
    avgRate = models.DecimalField(max_digits=5,decimal_places=2,editable=False,default=0)
    def __str__(self):
        return self.titre

class Question(models.Model):
    text=models.TextField()
    note=models.IntegerField(default=1)
    course=models.ForeignKey(Course,on_delete=models.PROTECT,null=True)    
    def __str__(self):
        return self.text 
    def is_get_score(self, selected_ids):
        all_answers = self.choice_set.filter(correct=True).count()
        selected_correct = self.choice_set.filter(correct=True, id__in=selected_ids).count()
        if all_answers == selected_correct:
            return True
        else:
            return False
    
class Choice(models.Model):
    text=models.TextField()
    correct=models.BooleanField()
    question=models.ForeignKey(Question,on_delete=models.PROTECT,null=True)    
    def __str__(self):
        return self.text 
    
class Chapter(models.Model):
    titre=models.CharField(max_length=50)
    description=models.TextField()
    video=models.FileField(upload_to='video/cours/%y/%m/%d',verbose_name='contenu')
    course=models.ForeignKey(Course,on_delete=models.PROTECT,null=True)
    def __str__(self):
        return self.titre
    
class Inscription(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    date_inscription = models.DateField(auto_now_add=True)
    rating = models.IntegerField(null=True,blank=True,default=-1)
    comment = models.TextField(null=True,blank=True,default="Aucun")
    score=models.DecimalField(max_digits=5,decimal_places=2,default=-1)
    def __str__(self):
        return self.course.titre

class Submission(models.Model):
   inscription = models.ForeignKey(Inscription, on_delete=models.PROTECT)
   choices = models.ManyToManyField(Choice)
   

class Notification(models.Model):
    titre = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    prof = models.ForeignKey(Prof, on_delete=models.PROTECT)
    def __str__(self):
        return self.titre