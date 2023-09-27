from django.http import HttpResponse
from django.shortcuts import redirect, render,get_object_or_404
from django.db.models import Count
from .models import Prof,Course,Chapter,Question,Choice,Categorie,Inscription,Etudiant,User,Submission
from django.http import HttpResponseRedirect
from django.views import generic
from django.urls import reverse
from decimal import Decimal

import tkinter
from tkinter import messagebox

# Create your views here.
from django.template import loader
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.

#student side

def nav(request):
    return render(request,'onlinecourse/nav.html')
def indexEtd(request):
    # View logic here
    active = None  # Initialize active with a default value of None
        
    try:
        active = request.session.get('active')
    except:
        print('wa t9eyed')  # Redirect to login if session value is not available
        
    if active is not None:
        try:
            user = User.objects.get(email=active)
            return render(request, 'etd/indexEtd.html',{'user':user})
        except:
            user=0
        
    else:
        return render(request, 'etd/indexEtd.html',{'user':0})

def coursesEtd(request):
    active = None  # Initialize active with a default value of None    
    try:
        active = request.session.get('active')
    except:
        print('wa t9eyed')  # Redirect to login if session value is not available
        
    if active is not None:
        user_id = request.session['active']
        try:
            user = Etudiant.objects.get(email=active)
            courses = Course.objects.all()
            list=[]
            for course in courses:
                ch=0
                qu=0
                ch=Chapter.objects.filter(course=course).count()
                qu=Question.objects.filter(course=course).count()
                if ch > 0 and qu > 0:
                    inscrit = check_if_enrolled(user, course)
                    nb=Inscription.objects.filter(course=course).count()
                    if inscrit:
                        termine = check_if_terminer(user, course)
                        if termine:
                            rep='termine'
                            list.append((course,rep))
                        else:    
                            rep='continue'
                            list.append((course,rep))
                    else:
                        rep="s'inscrire"
                        list.append((course,rep))
            return render(request,'etd/course_list.html',{'courses':list,'user':user})
        except:
            print(user)
    else: 
        return redirect('login')   

def is_connecte(request):
    if 'active' in request.session:
        # L'étudiant est connecté
        etudiant_id = request.session['active']
        # Faites ce que vous voulez avec l'ID de l'étudiant connecté
        return True
    else:
        # L'étudiant n'est pas connecté
        return False
def check_if_enrolled(etudiant, course):
    inscrit = False
    if etudiant.id is not None:
        # Check if user enrolled
        num_results = Inscription.objects.filter(etudiant=etudiant, course=course).count()
        if num_results > 0:
            inscrit = True
    return inscrit
def check_if_terminer(etudiant, course):
    terminer = False
    if etudiant.id is not None:
        inscription  = Inscription.objects.get(etudiant=etudiant, course=course)
        rate = inscription.rating
        if rate > -1:
            terminer = True
    return terminer


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list.html'
    context_object_name = 'course_list'
    def get_queryset(self):
        courses = Course.objects.order_by('-total_inscriptions')[:10]
        
        active = None  # Initialize active with a default value of None
        
        try:
            active = self.request.session.get('active')
        except:
            return redirect('login')  # Redirect to login if session value is not available
        
        if active is not None:
            etudiant_id = self.request.session['active']
            
            try:
                etudiant = User.objects.get(email=etudiant_id)
            except:
                return redirect('login')  # Redirect to login if user not found
            list=()
            for course in courses:
                inscrit = check_if_enrolled(etudiant, course)
                if inscrit:
                    list.append((course,1))
                else:
                    list.append((course,0))
        return list
    
class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'etd/course_detail.html'


def inscrit(request, course_id):
    active = None  # Initialize active with a default value of None
        
    try:
        active = request.session.get('active')
    except:
        return redirect('login')  # Redirect to login if session value is not available
        
    if active is not None:
        etudiant_id = request.session['active']
        try:
            etudiant = Etudiant.objects.get(email=etudiant_id)
        except:
            return redirect('login')
        course = get_object_or_404(Course, pk=course_id)
        inscrit = check_if_enrolled(etudiant, course)
        if not inscrit:
            # Create an enrollment
            Inscription.objects.create(etudiant=etudiant,course=course)
            course.nombreEtds+=1
            course.save()
    else:
        return render(request, 'prof/login.html')

    return render(request,'etd/course_detail.html',{'user':etudiant,'course':course})



def submit(request,course_id):
    active = None  # Initialize active with a default value of None
        
    try:
        active = request.session.get('active')
    except:
        return redirect('login')  # Redirect to login if session value is not available
        
    if active is not None:
        etudiant_id = request.session['active']
        try:
            etudiant = Etudiant.objects.get(email=etudiant_id)
        except:
            return redirect('login')
        course = get_object_or_404(Course, pk=course_id)
        inscription = Inscription.objects.get(etudiant=etudiant, course=course)
        submission = Submission.objects.create(inscription=inscription)
        answers = extract_answers(request)
        submission.choices.set(answers)
        submission.save()
        return HttpResponseRedirect(reverse(
                viewname='show_exam_result',
                args=(course.id, submission.id,)
                ))
    else:
        return redirect('login')



def extract_answers(request):
    submitted_anwsers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_anwsers.append(choice_id)
    return submitted_anwsers


def show_exam_result(request, course_id, submission_id):
    try:
        active = request.session.get('active')
    except:
        return redirect('login')  # Redirect to login if session value is not available
        
    if active is not None:
        
        try:
            etudiant = Etudiant.objects.get(email=active)
        except:
            return redirect('login')
        course = get_object_or_404(Course,pk=course_id)
        inscrit = check_if_enrolled(etudiant,course)
        submission = get_object_or_404(Submission,pk=submission_id)
        choices = submission.choices.all()
        total_mark, mark = 0, 0
        for question in Question.objects.filter(course=course):
            total_mark += question.note
            if question.is_get_score(choices):
                mark += 1
        print('wselt')
        i=Inscription.objects.get(etudiant=etudiant,course=course)
        note=round((mark/total_mark)*100,2)
        i.score=note
        print("votre score est :::::::::::: ",i.score)
        i.save()
        return render(request,'etd/exam_result.html',
        {"course":course, "choices":choices,"mark":mark,"user":etudiant, 
            "submission": submission,
            "note": note})
    else:
        return redirect('login')


def desinscrit(request, course_id):
    # Vérifier si l'utilisateur est connecté
    print('5edam')
    if 'active' not in request.session:
        return redirect('login')  # Rediriger vers la page de connexion si la session n'est pas disponible
    etudiant_id = request.session['active']
    try:
        etudiant = Etudiant.objects.get(email=etudiant_id)
    except Etudiant.DoesNotExist:
        return redirect('login')  # Rediriger vers la page de connexion si l'étudiant n'existe pas 
    course = get_object_or_404(Course, pk=course_id)
    # Vérifier si l'étudiant est inscrit au cours
    inscrit = check_if_enrolled(etudiant, course)
    if inscrit:
        # Supprimer l'inscription
        i=Inscription.objects.get(etudiant=etudiant,course=course)
        subs=Submission.objects.filter(inscription=i)
        for s in subs:
            s.delete()
        i.delete()
    course.nombreEtds-=1
    course.save()
     
    return redirect('coursesEtd')
      


def profilEtd(request):
    active = None  # Initialize active with a default value of None  
    try:
        active = request.session.get('active')
    except:
        return redirect('login')  # Redirect to login if session value is not available
        
    if active is not None:
        etudiant_id = request.session['active']
        etd=Etudiant.objects.get(email=active)
        if request.method == 'POST':
            old=request.POST['oldpwd']
            new=request.POST['newpwd']
            if old == 0:
                referer = request.META.get('HTTP_REFERER')
                return redirect(referer)
            else:
                etd.password=new
                etd.save()
                return render(request,'etd/profil_etudiant.html',{'mod_pwd': True})
        try:
            etudiant = Etudiant.objects.get(email=etudiant_id)
        except:
            return redirect('login')
    else:
        return render(request, 'prof/login.html')
    return render(request,'etd/profil_etudiant.html',{'etudiant':etudiant})


def modProfilEtd(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        etd=Etudiant.objects.get(email=active)
        if request.method == 'POST':
            nom=request.POST.get('nom')
            prenom=request.POST.get('prenom')
            telephone=request.POST.get('tel')
            linkedin=request.POST.get('linkedin')
            twitter=request.POST.get('twitter')
            sexe=request.POST.get('sexe')
            niv=request.POST.get('niv')
            try: 
                photo=request.FILES['photo']
            except:
                photo=None
            
            if etd.nom != nom:
                etd.nom=nom
            if etd.prenom != prenom:
                etd.prenom=prenom
            if etd.telephone != telephone:
                etd.telephone=telephone
            if etd.linkedin != linkedin:
                etd.linkedin=linkedin
            if etd.twitter != twitter:
                etd.twitter=twitter
            if etd.sexe != sexe:
                etd.sexe=sexe
            if etd.NiveauEtude != niv:
                etd.NiveauEtude=niv
            
            if photo is not None:
                etd.photo=photo
           
            etd.save()
            return render(request,'etd/modProfilEtd.html',{'profil_mod':True}) 
        else:
            return render(request,'etd/modProfilEtd.html',{'etd':etd})  

    else:
        return redirect('login')
        
def rate(request, course_id):
  context = {}
  if request.method == "POST":
    if 'active' not in request.session:
        return redirect('login')  # Rediriger vers la page de connexion si la session n'est pas disponible
    etudiant_id = request.session['active']
    try:
        etudiant = Etudiant.objects.get(email=etudiant_id)
    except Etudiant.DoesNotExist:
        return redirect('login')  # Rediriger vers la page de connexion si l'étudiant n'existe pas 
    rate = request.POST['rate']
    try:
        cmt = request.POST['cmt']
    except:
        cmt=None
  
    course = get_object_or_404(Course, pk=course_id)
    # Vérifier si l'étudiant est inscrit au cours
    inscrit = check_if_enrolled(etudiant, course)
    
    if inscrit:
        # Supprimer l'inscription
        inscrire = Inscription.objects.get(etudiant=etudiant, course=course)
        # Mettre à jour le nombre total d'inscriptions du cours
        if cmt is not None:
            inscrire.comment=cmt
        inscrire.rating = rate
        inscrire.save()
        allins=Inscription.objects.exclude(rating=-1)
        s=0
        nb=0
        for i in allins:
            s=s+i.rating
            nb+=1
        course.avgRate=round(s/nb,2)
        course.save()

    return redirect('coursesEtd')
    


#*******************************************************************************************************

#Prof side

def index(request):


    try:
        catg_by_cours = Course.objects.values('categorie').annotate(total=Count('id'))
    except:
        catg_by_cours=0
    if catg_by_cours != 0:
        for cat in catg_by_cours:
            c=Categorie.objects.get(id=cat['categorie'])
            cat['categorie']=c
    
    try:
        pop_cours = Inscription.objects.values('course').annotate(total=Count('id')).order_by('-total')
    except:
        pop_cours=0
    if pop_cours != 0:
        for pop in pop_cours:
            p=Course.objects.get(id=pop['course'])
            pop['course']=p
    
    comments = Inscription.objects.exclude(comment="Aucun")

    try:
        active=request.session.get('active')
    except:
        active=None
    
    if active is None:
        return render(request,'index.html',{'catg_cours':catg_by_cours,'pop_cours':pop_cours,'utl':0,'comments':comments})
    else:
        u=User.objects.filter(email=active).first()
        return render(request,'index.html',{'catg_cours':catg_by_cours,'pop_cours':pop_cours,'utl':u,'comments':comments})
        

   
    
def about(request):
    try:
        active=request.session.get('active')
    except:
        active=None
    
    if active is None:
        return render(request,'about.html',{'utl':0})
    else:
        active=request.session.get('active')
        user=User.objects.filter(email=active).first()
        return render(request,'about.html',{'utl':user})

def contact(request):
    try:
        active=request.session.get('active')
    except:
        active=None
    
    if active==None:
        return render(request,'contact.html',{'user':None})
    else:

        try:
            user=User.objects.filter(email=active).first()

            return render(request,'contact.html',{'utl':user})
        except:
            user=None
      
        return render(request,'contact.html',{'utl':0})

def contactUs(request):
    try:
        active=request.session.get('active')
    except:
        return redirect('login')
    return render(request,'prof/contactPr.html')
def contactEtd(request):
    try:
        active=request.session.get('active')
    except:
        return redirect('login')
    return render(request,'etd/contactEtd.html')

def team(request):
    try:
        active=request.session.get('active')
    except:
        active=None
    
    if active==None:
        return render(request,'team.html',{'user':None})
    else:

        try:
            user=User.objects.filter(email=active).first()
            return render(request,'team.html',{'utl':user})
        except:
            user=None
     
            user=None
        return render(request,'team.html',{'utl':0})
def error(request):
    try:
        active=request.session.get('active')
    except:
        active=None
    
    if active==None:
        return render(request,'404.html',{'user':None})
    else:

        try:
            user=User.objects.filter(email=active).first()

        except:
            user=None
       
        return render(request,'404.html',{'user':user})
def courses(request):
    try:
        catg_by_cours = Course.objects.values('categorie').annotate(total=Count('id'))
    except:
        catg_by_cours=0
    if catg_by_cours != 0:
        for cat in catg_by_cours:
            c=Categorie.objects.get(id=cat['categorie'])
            cat['categorie']=c
    
    try:
        #pop_cours = Inscription.objects.values('course').annotate(total=Count('id')).order_by('-total')
        pop_cours = Course.objects.all().order_by('-nombreEtds')
    except:
        pop_cours=0
    #if pop_cours != 0:
    #    for pop in pop_cours:
    #        p=Course.objects.get(id=pop['course'])
    #        pop['course']=p
    try:
        active=request.session.get('active')
    except:
        active=None
    
    if active==None:
        return render(request,'courses.html',{'catg_cours':catg_by_cours,'pop_cours':pop_cours,'user':None})
    else:

        try:
            user=User.objects.filter(email=active).first()
            return render(request,'courses.html',{'catg_cours':catg_by_cours,'pop_cours':pop_cours,'utl':user})
        except:
            user=None
        
        return render(request,'courses.html',{'catg_cours':catg_by_cours,'pop_cours':pop_cours,'utl':0})

def profil(request):
    try:
        active=request.session.get('active')
        prof=get_object_or_404(Prof,email=active)
        cours=Course.objects.filter(prof=prof)
        cours_count=Course.objects.filter(prof=prof).count()
        if request.method == 'POST':
            old=request.POST['oldpwd']
            new=request.POST['newpwd']
            if old == 0:
                referer = request.META.get('HTTP_REFERER')
                return redirect(referer)
            else:
                user=get_object_or_404(User,email=active)
                user.password=new
                prof.password=new
                user.save()
                prof.save()
                return render(request,'prof/prof_profil2.html',{'mod_pwd': True})



        if len(cours)>0:
            return render(request,'prof/prof_profil2.html',{'teacher': prof,'cours':cours,'cours_count':cours_count})
        else:
            return render(request,'prof/prof_profil2.html',{'teacher': prof,'cours':0})
        

    except:
        return redirect('login')
        
def testNav(request):
    return render(request,'header.html')



def logout(request):
    del request.session['active']
    return redirect('login')


def login(request):
    context={}
    if request.method == 'POST':
        try:
            user=User.objects.filter(email=request.POST.get('email'),password=request.POST.get('mdp')).first()
            if user.role == 'etd':
                request.session['active']=user.email
                return redirect('coursesEtd')
            else:
                request.session['active']=user.email
                return redirect('homeProf')
        except:
            user=0
        user=0
        if user==0:
            context['message'] = "Compte n'existe pas"
            return render(request, 'prof/login.html', context)
        
        
        #return render(request,'etd/login.html',{'error':True})
    return render(request,'prof/login.html')
 
def signup(request):
    context = {}
    if request.method == 'POST':
        print('hhh')
        # Check if user exists
        
        nom = request.POST['nom']
        prenom = request.POST['prenom']
        email = request.POST['email']
        try:
            telephone=request.POST.get('tel')
        except:
            telephone=""
        try:
            linkedin=request.POST.get('linkedin')

        except:
            linkedin=""
        try:
            twitter=request.POST.get('twitter')
        except:
            twitter=""

        sexe=request.POST.get('sexe')
        role = request.POST.get('user_role')
        try: 
                photo=request.FILES['photo']
        except:
                photo=None
        password = request.POST['mdp']
        user_exist = False
        try:
            User.objects.get(email=email)
            user_exist = True
        except:
            logger.error("New user")
        

        if not user_exist:
            print("LETSS GOOOO")
            User.objects.create(email=email,password=password,role=role)
            if role == "etd":
               niveau = request.POST['niv']
               if photo is None:
                    Etudiant.objects.create(nom=nom,prenom=prenom,email=email,password=password,telephone=telephone,linkedin=linkedin,twitter=twitter,sexe=sexe,NiveauEtude=niveau)
               else:
                    Etudiant.objects.create(nom=nom,prenom=prenom,email=email,password=password,photo=photo,telephone=telephone,linkedin=linkedin,twitter=twitter,sexe=sexe,NiveauEtude=niveau)
               return redirect('login')
            else:
                bio = request.POST['bio']
                if photo is None:
                    Prof.objects.create(nom=nom,prenom=prenom,email=email,password=password,telephone=telephone,linkedin=linkedin,twitter=twitter,sexe=sexe,bio=bio)
                else:
                    Prof.objects.create(nom=nom,prenom=prenom,email=email,password=password,photo=photo,telephone=telephone,linkedin=linkedin,twitter=twitter,sexe=sexe,bio=bio)
                return redirect('login')
        else:
            context['message'] = "Email déja utilisé"
            return render(request, 'prof/signup.html', context)
    else:
        return render(request,'prof/signup.html',context)

def homeProf(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        
        prof=Prof.objects.get(email=active)
        cours=Course.objects.filter(prof=prof)
        course_chapter_counts = []
        inscription=Inscription.objects.filter(course__in=cours)
        etds=inscription.values_list('etudiant',flat=True)
        dic={}
        for e in etds:
            if e in dic:
                dic[e]=dic[e]+1
            else:
                dic[e]=1
        listEtd=[]
        for idE,nbCours in dic.items():
            student=Etudiant.objects.get(id=idE)
            listEtd.append((student,nbCours))

        for course in cours:
            chapter_count = Chapter.objects.filter(course=course).count()
            course_chapter_counts.append((course, chapter_count))
        if len(cours) == 0 and len(listEtd) != 0 :
            return render(request,'prof/homeProf.html',{'courses':0,'students':listEtd,'teacher':prof})
        elif len(listEtd) == 0 and len(cours) != 0:
            return render(request,'prof/homeProf.html',{'courses':course_chapter_counts,'students':0,'teacher':prof})
        elif len(cours) == 0 and len(listEtd) == 0:
            return render(request,'prof/homeProf.html',{'courses':0,'students':0,'teacher':prof})
        else:
           return render(request,'prof/homeProf.html',{'courses':course_chapter_counts,'students':listEtd,'teacher':prof}) 
    else:
        return redirect('login')
  
#Course functions

def ajoutCours(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        cat=Categorie.objects.all()
        if request.method == 'POST':
            t=request.POST.get('titre')
            d=request.POST.get('desc')
            c=request.POST.get('cat')
            cc=Categorie.objects.get(id=c)
            f=request.FILES['support']
            i=request.FILES['image']
            p=Prof.objects.get(email=active)
            cours=Course(titre=t,categorie=cc,description=d,fichier=f,photo=i,prof=p)
            cours.save()
            return render(request,'prof/ajoutCours.html',{'course_added':True,'course_id':cours.id}) 
        else:
            return render(request,'prof/ajoutCours.html',{'categories':cat}) 

    else:
        return redirect('login')

def ajoutChapitre(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        course_id=request.GET.get('course_id')
        if request.method == 'POST':
            t=request.POST.get('titre')
            d=request.POST.get('desc')
            v=request.FILES['contenu']
            c=Course.objects.get(id=course_id)
            chapitre=Chapter(titre=t,description=d,video=v,course=c)
            chapitre.save()
            c.nombreChaps+=1
            c.save()
            return render(request,'prof/ajoutChapitre.html',{'chapter_added':True,'course_id':course_id}) 
        else:
            return render(request,'prof/ajoutChapitre.html',{'course_id':course_id}) 

    else:
        return redirect('login')

def ajoutQuestion(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        if request.method == 'POST':
            
            course_id=request.GET.get('course_id')
            c=Course.objects.get(id=course_id)
            ques=request.POST.get('ques')
            question=Question(text=ques,course=c)
            question.save()
            c.nombreQues+=1
            c.save()
            ch1=request.POST.get('choix1')
            cor1=request.POST.get('cor1')
            if cor1=="Correct":
                test=True
            else:
                test=False
            choix1=Choice(text=ch1,correct=test,question=question)
            choix1.save()

            ch2=request.POST.get('choix2')
            cor2=request.POST.get('cor2')
            if cor2=="Correct":
                test=True
            else:
                test=False
            choix2=Choice(text=ch2,correct=test,question=question)
            choix2.save()

            ch3=request.POST.get('choix3')
            cor3=request.POST.get('cor3')
            if cor3=="Correct":
                test=True
            else:
                test=False
            choix3=Choice(text=ch3,correct=test,question=question)
            choix3.save()

            ch4=request.POST.get('choix4')
            cor4=request.POST.get('cor4')
            if cor4=="Correct":
                test=True
            else:
                test=False
            choix4=Choice(text=ch4,correct=test,question=question)
            choix4.save()

            return render(request,'prof/ajoutQuestion.html',{'question_added':True,'course_id':course_id}) 
        else:
            return render(request,'prof/ajoutQuestion.html') 

    else:
        return redirect('login')


def afficherQuestion(request):
    ques_id=request.GET.get('ques_id')
    try:
        ques=Question.objects.get(id=ques_id)
    except:
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer)
    
    try:
        choix=Choice.objects.filter(question=ques)
    except:
        choix=None
    
    choix_num=[]
    if len(choix):
        nb=1
        for choice in choix:
            choix_num.append((choice,nb))
            nb+=1
        return render(request,'prof/course_question.html',{'question':ques,'choix':choix_num})
    else:
        return render(request,'prof/course_question.html',{'choix':0})



def delQuestion(request):
    ques_id=request.GET.get('ques_id')
    ques = get_object_or_404(Question, id=ques_id)
    Choice.objects.filter(question=ques).delete()
    ques.course.nombreQues=-1
    ques.course.save()
    
    ques.delete()
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer)

def delAllQuestions(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        course_id=request.GET.get('course_id')
        course=Course.objects.get(id=course_id)
        questions=Question.objects.filter(course=course)
        for question in questions:
            Choice.objects.filter(question=question).delete()
        questions.delete()
        course.nombreQues=0
        course.save()
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer)

    else:
        return redirect('login')

def modQuestion(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        ques_id=request.GET.get('ques_id')
        course_id=request.GET.get('course_id')
        ques=Question.objects.get(id=ques_id)
        choices=Choice.objects.filter(question=ques)
        if request.method == 'POST':
            question=request.POST.get('ques')
            if ques.text != question:
                ques.text=question
          
            ques.save()


            ch1=request.POST.get('choix1')
            cor1=request.POST.get('cor1')
            idch1=request.POST.get('idCh1')
            print('$$$$$$$$$$$$$$$$$$$$$$$ = >',idch1)
            if cor1=="Correct":
                test=True
            else:
                test=False
            choix1=Choice.objects.get(id=idch1)
            if choix1.text != ch1:
                choix1.text=ch1
            if choix1.correct != test:
                choix1.correct=test
            choix1.save()

            ch2=request.POST.get('choix2')
            cor2=request.POST.get('cor2')
            idch2=request.POST.get('idCh2')
            if cor2=="Correct":
                test=True
            else:
                test=False
            choix2=Choice.objects.get(id=idch2)
            if choix2.text != ch2:
                choix2.text=ch2
            if choix2.correct != test:
                choix2.correct=test
            choix2.save()

            ch3=request.POST.get('choix3')
            cor3=request.POST.get('cor3')
            idch3=request.POST.get('idCh3')
            if cor3=="Correct":
                test=True
            else:
                test=False
            choix3=Choice.objects.get(id=idch3)
            if choix3.text != ch3:
                choix3.text=ch3
            if choix3.correct != test:
                choix3.correct=test
            choix3.save()

            ch4=request.POST.get('choix4')
            cor4=request.POST.get('cor4')
            idch4=request.POST.get('idCh4')
            if cor4=="Correct":
                test=True
            else:
                test=False
            choix4=Choice.objects.get(id=idch4)
            if choix4.text != ch4:
                choix4.text=ch4
            if choix4.correct != test:
                choix4.correct=test
            choix4.save()


            
            return render(request,'prof/modQuestion.html',{'question_mod':True,'course_id':course_id}) 
        else:
            return render(request,'prof/modQuestion.html',{'question':ques,'choice1':choices[0],'choice2':choices[1],'choice3':choices[2],'choice4':choices[3]})  

    else:
        return redirect('login')

def afficherCourse(request):
    try:
        course_id=request.GET.get('course_id')
        course=Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        redirect('login')
    
    chap=Chapter.objects.filter(course=course)
    ques=Question.objects.filter(course=course)
    etds=Inscription.objects.filter(course=course)
    course.nombreEtds=etds.count()
    course.nombreQues=Question.objects.filter(course=course).count()
    course.save()
    nbE=0
    if len(chap)==0:
        chap_num=0
    else:
        nb=1
        chap_num=[]
        for chapitre in chap:
            chap_num.append((chapitre,nb))
            nb+=1
    if len(ques)==0:
        ques_num=0
    else:
        nb=1
        ques_num=[]
        for question in ques:
            ques_num.append((question,nb))
            nb+=1
    

    return render(request,'prof/prof_course.html',{'course':course,'chapters':chap_num,'questions':ques_num,'etds':etds,'nbE':nbE})



def delCourse(request):
    course_id=request.GET.get('course_id')
    course = get_object_or_404(Course, id=course_id)
    Chapter.objects.filter(course=course).delete()
    questions=Question.objects.filter(course=course)
    insc=Inscription.objects.filter(course=course)
    for ques in questions:
        Choice.objects.filter(question=ques).delete()
    insc.delete()
    questions.delete()
    course.delete()
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer)


def delChapitre(request):
    id=request.GET.get('chap_id')
    ch=Chapter.objects.get(id=id)
    ch.course.nombreChaps-=1
    ch.course.save()
    ch.delete()
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer)

def modChapitre(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        chap_id=request.GET.get('chap_id')
        chap=Chapter.objects.get(id=chap_id)
        if request.method == 'POST':
            t=request.POST.get('titre')
            d=request.POST.get('desc')
            try:
                v=request.FILES['contenu'] 
            except:
                v=None
            
            if chap.titre != t:
                chap.titre=t
            if chap.description != d:
                chap.description=d
            if v is not None:
                chap.video=v
    
            chap.save()
            return render(request,'prof/modChapter.html',{'chap_mod':True}) 
        else:
            return render(request,'prof/modChapter.html',{'chapter':chap})  

    else:
        return redirect('login')


def afficherChapitre(request):
    chap_id=request.GET.get('chap_id')
    try:
        chap=Chapter.objects.get(id=chap_id)
    except:
        redirect('homeProf')
    return render(request,'prof/course_chapter.html',{'chapitre':chap})

def modCourse(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        cat=Categorie.objects.all()
        course_id=request.GET.get('course_id')
        cours=Course.objects.get(id=course_id)
        if request.method == 'POST':
            t=request.POST.get('titre')
            d=request.POST.get('desc')
            c=request.POST.get('cat')
            cc=Categorie.objects.get(id=c)
            try:
                f=request.FILES['support'] 
            except:
                f=None
            try:
                i=request.FILES['image']
            except:
                i=None
            if cours.titre != t:
                cours.titre=t
            if cours.description != d:
                cours.description=d
            if cours.categorie != cc:
                cours.categorie=cc
            if f is not None:
                cours.fichier=f
            if i is not None:
                cours.photo=i
            cours.save()
            return render(request,'prof/modCourse.html',{'course_mod':True}) 
        else:
            return render(request,'prof/modCourse.html',{'course':cours,'cat':cat})  

    else:
        return redirect('login')



def delAllCourses(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        p=Prof.objects.get(email=active)
        courses=Course.objects.filter(prof=p)
        for course in courses:
            Chapter.objects.filter(course=course).delete()
            questions=Question.objects.filter(course=course)
            insc=Inscription.objects.filter(course=course)
            for ques in questions:
                Choice.objects.filter(question=ques).delete()
            insc.delete()
            questions.delete()
        
        courses.delete()
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer)
    else:
        return redirect('login')

def delAllChapters(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        course_id=request.GET.get('course_id')
        c=Course.objects.get(id=course_id)
        Chapter.objects.filter(course=c).delete()
        c.nombreChaps=0
        c.save()
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer)

    else:
        return redirect('login')

def modProfil(request):
    try:
        active=request.session.get('active')
    except:
        redirect('login')
    if active is not None:
        prof=Prof.objects.get(email=active)
        if request.method == 'POST':
            nom=request.POST.get('nom')
            prenom=request.POST.get('prenom')
            telephone=request.POST.get('tel')
            linkedin=request.POST.get('linkedin')
            twitter=request.POST.get('twitter')
            sexe=request.POST.get('sexe')
            bio=request.POST.get('bio')
            try: 
                photo=request.FILES['photo']
            except:
                photo=None
            
            if prof.nom != nom:
                prof.nom=nom
            if prof.prenom != prenom:
                prof.prenom=prenom
            if prof.telephone != telephone:
                prof.telephone=telephone
            if prof.linkedin != linkedin:
                prof.linkedin=linkedin
            if prof.twitter != twitter:
                prof.twitter=twitter
            if prof.sexe != sexe:
                prof.sexe=sexe
            if prof.bio != bio:
                prof.bio=bio
            
            if photo is not None:
                prof.photo=photo
           
            prof.save()
            return render(request,'prof/modProfil.html',{'profil_mod':True}) 
        else:
            return render(request,'prof/modProfil.html',{'prof':prof})  

    else:
        return redirect('login')
