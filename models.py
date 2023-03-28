from django.db import models
from django.db.models.deletion import CASCADE
from django.core.validators import RegexValidator, URLValidator
from django.db import transaction
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models.fields import CharField
import decimal
from django.db.models import Q, F, Count, ExpressionWrapper, DecimalField, Avg, Max, Min, Sum, FloatField
import datetime
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import Group, Permission
from random import randint
from django.core.exceptions import ValidationError
import re
from django.utils.translation import ugettext as _
from django.apps import apps
from django.utils import timezone
from django.db.models import When, Value, Case, BooleanField
from django_cleanup import cleanup
import random
import string
from django.core.validators import FileExtensionValidator

class CustomUserManager(UserManager):
    def get_by_natural_key(self, username):
        case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
        return self.get(**{case_insensitive_username_field: username})

class User(AbstractUser):
    #REQUIRED_FIELDS = ['email']
    objects = CustomUserManager()
    email = models.EmailField(
        verbose_name=("Email"), null=True, default=None, blank=True,
    )
    def validate_unique(self, exclude=None):
        super(User, self).validate_unique(exclude=exclude)
        qs = User.objects.filter(username__iexact=self.username)
        if qs.exists() and (qs.first().id != self.id) :
            raise ValidationError("Ce nom d'utilisateur existe déjà")
        
        if self.email :
            qs = User.objects.filter(email__iexact=self.email)
            if qs.exists() and (qs.first().id != self.id) :
                raise ValidationError("Un utilisateur est déjà enregistré avec cette adresse e-mail")

    def institution(self):
        institution_ = Institution.objects.all()
        if institution_.exists():
            institution_=institution_[0]
        else :
            institution_ = Institution.objects.create(nom='Ecole nationale Supérieure d\'Informatique', 
                                                      nom_a='المدرسة الوطنية العليا للإعلام الآلي',
                                                      sigle='ESI',
                                                      ville='Oued Smar',
                                                      ville_a='‫واد سمار‬',
                                                      adresse='BPM68 16270, OUed Smar, Alger',
                                                      tel='023939132', 
                                                      fax='023939142',
                                                      web='http://www.esi.dz',
                                                      )
            institution_.banniere.name = institution_.banniere.field.upload_to+'/banniere.png'
            institution_.logo.name = institution_.logo.field.upload_to+'/ESI_Logo.png'
            institution_.logo_bis.name = institution_.logo_bis.field.upload_to+'/Logo_ESI_talents.png'
            institution_.header.name =institution_.header.field.upload_to+'/Entete_ESI_lg.png'
            institution_.footer.name =institution_.footer.field.upload_to+'/Foot_ESI_lg.png'
            institution_.illustration_cursus.name =institution_.illustration_cursus.field.upload_to+'/etudes_esi.png'
            institution_.save()
        return institution_
        
    def nom(self):
        if self.is_enseignant():
            return self.enseignant.nom
        elif self.is_etudiant():
            return self.etudiant.nom
        elif self.has_object('Personnel'):
            return self.personnel.nom
        elif self.last_name:
            return self.last_name
        else:
            return str(self)

    def prenom(self):
        if self.is_enseignant():
            return self.enseignant.prenom
        elif self.is_etudiant():
            return self.etudiant.prenom
        elif self.has_object('Personnel'):
            return self.personnel.prenom
        elif self.first_name:
            return self.first_name
        else:
            return str(self)
    
    def annee_encours(self):
        return AnneeUniv.objects.get(encours=True)
    
    def inscription_encours_list(self):
        if self.is_etudiant():
            return Inscription.objects.filter(etudiant=self.etudiant, formation__annee_univ__encours=True)
        else:
            return Inscription.objects.none()

    def is_partenaire(self):
        group_admin=get_object_or_404(Group, name='partenaire')
        return group_admin in self.groups.all()

    def is_partenaire_only(self):
        group_admin=get_object_or_404(Group, name='partenaire')
        return (group_admin in self.groups.all()) and (self.groups.count()==1)

    '''
    def is_top_management(self):
        group_admin=get_object_or_404(Group, name='top-management')
        return group_admin in self.groups.all()
    
    def is_direction(self):
        group_admin=get_object_or_404(Group, name='direction')
        return group_admin in self.groups.all()
    
    def is_stage(self):
        group_admin=get_object_or_404(Group, name='stage')
        return group_admin in self.groups.all()
    
    def is_scolarite(self):
        group_admin=get_object_or_404(Group, name='scolarite')
        return group_admin in self.groups.all()
    
    def is_surveillance(self):
        group_admin=get_object_or_404(Group, name='surveillance')
        return group_admin in self.groups.all()
    '''

    def is_enseignant(self):
        #group_enseignant=get_object_or_404(Group, name='enseignant')
        #return group_enseignant in self.groups.all()
        return self.has_object('Enseignant')

    def is_etudiant(self):
        #group_etudiant=get_object_or_404(Group, name='etudiant')
        #return group_etudiant in self.groups.all()
        return self.has_object('Etudiant')
    '''
    def is_personnel(self):
        group_personnel=get_object_or_404(Group, name='personnel')
        return group_personnel in self.groups.all()
    '''

    def is_not_etudiant(self):
        return not self.is_etudiant()

    def is_doctorant(self):
        #group_etudiant=get_object_or_404(Group, name='etudiant')
        #return group_etudiant in self.groups.all()
        return self.has_object('Doctorant')
    
    def is_coordinateur(self, module_):
        if self.is_enseignant():
            return ((self.enseignant == module_.coordinateur) or (self.has_perm('scolar.fonctionnalite_pedagogie_gestioncoordination')))
        else:
            return self.has_perm('scolar.fonctionnalite_pedagogie_gestioncoordination')

    def is_tuteur(self, etudiant_pk):
        if self.is_enseignant():
            etudiant_=get_object_or_404(Etudiant, matricule=etudiant_pk)
            if etudiant_.tuteur == self.enseignant:
                return True
            else:
                return False
        else:
            return False
    '''
    def is_staff_only(self):
        return self.is_direction() or self.is_scolarite() or self.is_surveillance() or self.is_stage() or self.is_top_management()
         
    def is_staff_or_student_himself(self, etudiant_pk):
        if self.is_staff_only() or self.is_enseignant():
            return True
        elif self.is_etudiant():
            return (self.etudiant.matricule == etudiant_pk) 
        else :
            return False
    
    def is_staff_or_teacher_himself(self, enseignant_pk):
        if self.is_staff_only():
            return True
        elif self.is_enseignant():
            return self.enseignant.id == enseignant_pk
        else :
            return False
    '''
    def has_bloc_navigation(self, bloc):
        if self.is_superuser :
            return True
        else :
            permissions_count=Permission.objects.filter(Q(user=self)|(Q(group__user=self))).filter(codename__startswith='fonctionnalitenav_'+bloc).distinct().count()
            if permissions_count>0 :
                return True
            else :
                return False
    def has_object(self, model_name):
        if model_name=="Doctorant" :
            return Doctorant.objects.filter(Q(etudiant__user=self)|Q(enseignant__user=self)).exists()
        else :
            model=apps.get_model(app_label='scolar', model_name=model_name)
            object_=model.objects.filter(user=self).exists()
            if object_ :
                return True
            else :
                return False

    def has_perm_or_student_himself(self, permission_code, etudiant_pk):
        if self.has_perm(permission_code) :
            return True
        elif self.is_etudiant():
            return ((self.etudiant.matricule == etudiant_pk) or (self.has_perm(permission_code)))
        else :
            return False
    
    def has_perm_or_teacher_himself(self, permission_code, enseignant_pk):
        if self.has_perm(permission_code) :
            return True
        elif self.is_enseignant():
            return ((self.enseignant.id == enseignant_pk) or (self.has_perm(permission_code)))
        else :
            return False
    
    def nb_notifications_unseen(self):
        return Trace.objects.filter(cible=self, seen=False).count()
    
    def has_one_or_more_trace_as_cible(self):
        return Trace.objects.filter(cible=self).exists()
    
    def get_email(self):
        return self.email if self.email else ''
        
    def has_cycles_avec_acces_visualisation_notes(self):
        return self.cycles_avec_acces_visualisation_notes.count()
        
    def has_cycles_avec_acces_visualisation_etudiants(self):
        return self.cycles_avec_acces_visualisation_etudiants.count()
    
    def has_cycles_avec_acces_gestion_etudiants(self):
        return self.cycles_avec_acces_gestion_etudiants.count()
    
    def has_acces_visualisation_notes_programme(self, programme):
        if not programme.cycle :
            return False
        else : 
            return programme.cycle in self.cycles_avec_acces_visualisation_notes.all()
        
    def has_acces_gestion_notes_programme(self, programme):
        if not programme.cycle :
            return False
        else : 
            return programme.cycle in self.cycles_avec_acces_gestion_notes.all()
               
    def has_acces_visualisation_etudiants_programme(self, programme):
        if not programme.cycle :
            return False
        else : 
            return programme.cycle in self.cycles_avec_acces_visualisation_etudiants.all()
                
    def has_acces_gestion_etudiants_programme(self, programme):
        if not programme.cycle :
            return False
        else : 
            return programme.cycle in self.cycles_avec_acces_gestion_etudiants.all()

@cleanup.ignore                
class Institution(models.Model):
    nom_plateforme = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nom de la plateforme")
    nom = models.CharField(max_length=100, verbose_name="Nom de l'établissement")
    nom_a = models.CharField(max_length=100, default='', verbose_name="Nom de l'établissement en arabe")
    sigle = models.CharField(max_length=10, verbose_name="Sigle de l'établissement")
    adresse = models.TextField()
    ville = models.CharField(max_length=50, default='')
    ville_a = models.CharField(max_length=50, default='', verbose_name="Ville en arabe")
    wilaya_institution = models.ForeignKey('Wilaya', on_delete=models.SET_NULL, null=True, blank=True)
    tel = models.CharField(max_length=20, null=True, blank=True, validators=[RegexValidator('^[0-9\+]*$',
                               'Que des chiffres sans espaces et le + pour l\'international')])
    fax = models.CharField(max_length=20, null=True, blank=True, validators=[RegexValidator('^[0-9\+]*$',
                               'Que des chiffres sans espaces et le + pour l\'international')])
    web = models.URLField(null=True, blank=True, verbose_name="Site web")
    illustration_cursus = models.ImageField(upload_to='admin', null=True, blank=True )
    logo = models.ImageField(upload_to='admin', null=True, blank=True, verbose_name="Logo de l'établissement")
    logo_bis = models.ImageField(upload_to='admin', null=True, blank=True, verbose_name="Logo de la plateforme")
    banniere = models.ImageField(upload_to='admin', null=True, blank=True )
    header =  models.ImageField(upload_to='admin', null=True, blank=True, verbose_name="Entête des documents")
    footer =  models.ImageField(upload_to='admin', null=True, blank=True, verbose_name="Pied des documents")
    reference=models.CharField(max_length=50, null=True, blank=True, verbose_name="Référence des documents")
    identifiant_progres = models.CharField(max_length=50, null=True, blank=True)
    code_etablissement= models.CharField(max_length=50, null=True, blank=True,help_text="Veuillez insérer -code établissement- utilisé dans les fichiers de service national.")
    email_domain = models.CharField(max_length=100, null=True, blank=True, verbose_name="Domaine d'emails (exemple : institution.dz)")
    color = models.CharField(max_length=10, default="#343A40", verbose_name="Code couleur (HEX) de la plateforme (exemple : #343A40) ")
    users_direction=models.ManyToManyField('User', blank=True, verbose_name="Utilisateurs qui seront notifiés par e-mail en tant que direction", related_name='institution_direction')
    users_scolarite=models.ManyToManyField('User', blank=True, verbose_name="Utilisateurs qui seront notifiés par e-mail en tant que scolarité", related_name='institution_scolarite')
    users_stage=models.ManyToManyField('User', blank=True, verbose_name="Utilisateurs qui seront notifiés par le déroulement du processus de validation des stages de fin d'études", related_name='institution_stage')
    email_futurs_stagiaires = models.EmailField(null=True, blank=True, verbose_name="Adresse e-mail de diffusion des futurs stagiaires (qui sera notifiée par les nouveaux sujets de stage de fin d'études déposés)")
    users_theses=models.ManyToManyField('User', blank=True, verbose_name="Utilisateurs qui seront notifiés par le déroulement des processus de gestion des thèses de post-graduation", related_name='institution_theses')
    users_offres=models.ManyToManyField('User', blank=True, verbose_name="Utilisateurs qui seront notifiés par le déroulement des processus de gestion des offres (emplois, thèses, stages pratiques, etc.)", related_name='institution_offres')
    users_demandes_comptes=models.ManyToManyField('User', blank=True, verbose_name="Utilisateurs qui seront notifiés par les nouvelles demandes de compte (pour publier des offres, stages, etc.) (la fonctionnalité doit d'abord être activée)", related_name='institution_demandes_comptes')
    email_webmaster = models.EmailField(null=True, blank=True, verbose_name="Adresse e-mail du webmaster (pour notifications)")
    signature_emails=models.CharField(max_length=100, null=True, blank=True, help_text="La signature qui sera envoyée en bas de chaque mail de notification")
    activation_emails=models.BooleanField(default=True, verbose_name="Notifications par mail activées")
    activation_ddc=models.BooleanField(default=True, verbose_name="Domaines de connaissances activés")
    activation_competences=models.BooleanField(default=True, verbose_name="Ingénierie des compétences activée")
    activation_livret_competences=models.BooleanField(default=False, verbose_name="Livrets des compétences des étudiants activés (uniquement si l'ingénierie des compétences est activée)")
    activation_charges=models.BooleanField(default=True, verbose_name="Charges des enseignants activées")
    activation_google_agenda=models.BooleanField(default=True, verbose_name="Google Agenda activé")
    activation_authentification_google=models.BooleanField(default=True, verbose_name="Authentification Google (OAuth) activée")
    activation_feedback=models.BooleanField(default=True, verbose_name="Feedbacks des étudiants sur les enseignements activés")
    activation_theses=models.BooleanField(default=False, verbose_name="Thèses de post-graduation activées")
    activation_webhelp=models.BooleanField(default=False, verbose_name="Activation de la Web-Help (aide contextuelle en ligne)")
    activation_lettres_recommandation=models.BooleanField(default=True, verbose_name="Modèles de lettres de recommandation à générer par les enseignants au profit des étudiants activés")
    activation_enregistrement_etudiants=models.BooleanField(default=False, verbose_name="Demandes d'enregistrement des étudiants activées")
    activation_offres=models.BooleanField(default=False, verbose_name="Offres (emplois, thèses, stages pratiques, etc.) activées")
    activation_demandes_comptes=models.BooleanField(default=False, verbose_name="Demandes de création des comptes sur la plateforme activées (pour les personnes souhaitant déposer des offres d'emplois et/ou stages de fin d'études")
    activation_public_stages=models.BooleanField(default=False, verbose_name="Liste des stages visibles aux visiteurs")
    activation_public_projets=models.BooleanField(default=False, verbose_name="Projets de recherche visibles aux visiteurs")
    activation_public_equipesrecherche=models.BooleanField(default=False, verbose_name="Equipes de recherche visibles aux visiteurs")
    
    def has_one_or_more_cycle_dette(self):
        return Cycle.objects.filter(activation_dettes=True).exists()

    def has_one_or_more_cycle_rattrapage(self):
        return Cycle.objects.filter(activation_rattrapage=True).exists()

    def has_one_or_more_matiere_validable(self):
        return Matiere.objects.filter(validable=True).exists()
    
    def nb_enregistrements_etudiants_en_attente(self):
        return EnregistrementEtudiant.objects.filter(statut="W").count()

    def nb_offres_en_attente(self):
        return Offre.objects.filter(statut="C").count()

    def nb_offres_ouvertes(self):
        return Offre.objects.filter(statut="S").count()
    
    
    def __str__(self):
        if self.sigle :
            return f"{self.nom} {self.sigle}"
        else :
            return self.nom 

class DomaineConnaissance(models.Model):
    '''
    Cette classe sert à catégoriser les matière en domaines de connaissance globaux
    '''
    intitule=models.CharField(max_length=80)
    def __str__(self):
        return self.intitule


# Create your models here.

class Matiere(models.Model):
    '''
    La marière est l'élément de base de la formation.
    Une matière fait partie d'une Unité d'enseignement
    '''
    code=models.CharField(max_length=20)
    precision = models.CharField(max_length=5, null=True, blank=True)
    ddc=models.ForeignKey(DomaineConnaissance, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Domaine de connaissances")
    titre=models.CharField(max_length=80)
    titre_a=models.CharField(max_length=80, null=True, blank=True, verbose_name="Titre en arabe")
    titre_en=models.CharField(max_length=80, null=True, blank=True, verbose_name="Titre en anglais")
    coef=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=1.0)
    credit=models.IntegerField(blank=True, default=0)
    edition=models.CharField(max_length=5, null=True, blank=True, help_text="Par exemple l'année de l'arrêté ministériel définissant la matière")
    vh_cours=models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Volume horaire cours")
    vh_td=models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Volume horaire TD")
    vh_tp=models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Volume horaire TP")
    pre_requis=models.TextField(null=True, blank=True)
    objectifs=models.TextField(null=True, blank=True)
    contenu=models.TextField(null=True, blank=True)
    travail_perso=models.TextField(null=True, blank=True)
    bibliographie=models.TextField(null=True, blank=True)
    mode_projet=models.BooleanField(default=False, verbose_name="Mode projet : Permet d'adapter les critères de Feedback")
    pfe=models.BooleanField(default=False, verbose_name="Projet/Matière de fin d'études avec soutenance finale")
    equipe=models.BooleanField(default=False, verbose_name="Matière en équipe, avec soutenance des groupes d'étudiants")
    seminaire=models.BooleanField(default=False, verbose_name="Séminaire")
    validable=models.BooleanField(default=False, verbose_name="Matière d'un stage sans note, avec deux états : Validé, Non validé, états qui apparaitront dans les relevés de notes.")
    
    def __str__(self):
        if self.precision:
            return f"{self.code} {self.precision}"
        else:
            return self.code
        
    
class Specialite(models.Model):
    code=models.CharField(max_length=5, primary_key=True)
    intitule=models.CharField(max_length=100)
    intitule_a=models.CharField(max_length=100, null=True, blank=True, verbose_name="Intitulé arabe")
    title=models.CharField(max_length=100, null=True, blank=True, verbose_name="Intitulé anglais")
    concernee_par_pfe=models.BooleanField(default=True, verbose_name="Spécialité concernée par les stages de fin d'études (afin de l'afficher dans la liste des spécialités lors du dépôt d'un stage)")
    def __str__(self):
        return f"{self.code}: {self.intitule}"

class AnneeUniv(models.Model):
    '''
    Année Universitaire qui comprend plusieurs formations
    '''
    annee_univ=models.CharField(max_length=9, unique=True, primary_key=True)
    debut=models.DateField()
    fin=models.DateField()
    encours=models.BooleanField(default=False,  blank=True)
    
    def annee_suivante(self):
        annee_univ_suivante_=int(self.annee_univ)+1
        annee_univ_suivante_pk=str(annee_univ_suivante_)
        annee_univ_, created=AnneeUniv.objects.get_or_create(annee_univ=annee_univ_suivante_pk, defaults={
                'annee_univ':annee_univ_suivante_pk,
                'debut': self.debut+datetime.timedelta(days=365),
                'fin': self.fin+datetime.timedelta(days=365),
                'encours':False
            })
        return annee_univ_

    def annee_precedente(self):
        annee_univ_precedente_=int(self.annee_univ)-1
        annee_univ_precedente_pk=str(annee_univ_precedente_)
        annee_univ_, created=AnneeUniv.objects.get_or_create(annee_univ=annee_univ_precedente_pk, defaults={
                'annee_univ':annee_univ_precedente_pk,
                'debut': self.debut+datetime.timedelta(days=-365),
                'fin': self.fin+datetime.timedelta(days=-365),
                'encours':False
            })
        return annee_univ_
    
    def __str__(self):
        return self.annee_univ

    

class Periode(models.Model):
    '''
    Ca peut être un semestre ou trimestre ou autre. 
    '''
    code=models.CharField(max_length=2, null=True, choices=(('S1','Semestre 1'),('S2', 'Semestre 2'), ('T1', 'Trimestre 1'),('T2', 'Trimestre 2'),('T3', 'Trimestre 3'), ('AN', 'Annuel')))
    ordre=models.IntegerField()
    nb_semaines=models.IntegerField(null=True, blank=True, default=15)
    session=models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.code

SEXE=(
    ('', '---'),
    ('M','Masculin'),
    ('F','Féminin'),
)

class Personnel(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nom=models.CharField(max_length=50)
    eps=models.CharField(max_length=50, null=True, blank=True)
    prenom=models.CharField(max_length=50)
    nom_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Nom en arabe")
    eps_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Eps en arabe")
    prenom_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Prénom en arabe")
    sexe=models.CharField(max_length=1, choices=SEXE, null=True, blank=True)
    tel=models.CharField(max_length=15, null=True, blank=True)
    bureau=models.CharField(max_length=10, null=True, blank=True)
    
    def get_email(self):
        return self.user.get_email() if self.user else ''
    
    def __str__(self):
        return f"{self.nom} {self.prenom}"

STATUT=(
    ('', '---'),
    ('P','Permanent'),
    ('V','Vacataire'),
    ('A','Associé'),
    ('D','Doctorant'),
)

GRADE=(
    ('', '---'),
    ('MA','Maître Assistant'),
    ('MA.B','Maître Assistant B'),
    ('MA.A','Maître Assistant A'),
    ('MC','Maître de Conférences'),
    ('MC.B','Maître de Conférences B'),
    ('MC.A','Maître de Conférences A'),
    ('PR','Professeur'),
)

SITUATION=(
    ('', '---'),
    ('A','En activité'),
    ('D','Mise en disponibilité'),
    ('T','Détachement'),
    ('M','Congé de Maladie'),
    ('I','Invalidité'),
    ('R','Retraité'),
    ('X','Départ: Mutation, Démission, ...'),
)


def validate_image(fieldfile):
        filesize = fieldfile.file.size
        megabyte_limit = 1.0
        if filesize > megabyte_limit*1024*1024:
            raise ValidationError("Max file size is %sMB" % str(megabyte_limit))  
        #verifier que le nom du fichier ne contient que des caractères qui seront acceptés par l'os
        match=re.match(r"[a-zA-Z0-9_.]+", fieldfile.name)
        if match:
            if match.group() != fieldfile.name:
                raise ValidationError("Le nom du fichier ne doit contenir que les caractères suivants: a-z A-Z 0-9 _.")
        else:
            raise ValidationError("Le nom du fichier ne doit contenir que les caractères suivants: a-z A-Z 0-9 _.")


def validate_url_list(value):
    liste_urls=value.replace('\n', '').split('\r')
    validate = URLValidator()
    for url in liste_urls :
        try :
            validate(url)
        except ValidationError as exception:
            raise ValidationError(_('Liste des URLs incorrecte, vérifiez que toutes les URLs commencent par http ou https, ainsi qu\'elles soient séparées par des sauts de ligne. Ne laissez pas de lignes vides.'))


class Enseignant(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    nom=models.CharField(max_length=50)
    eps=models.CharField(max_length=50, null=True, blank=True)
    prenom=models.CharField(max_length=50)
    nom_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Nom en arabe")
    eps_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Eps en arabe")
    prenom_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Prénom en arabe")
    sexe=models.CharField(max_length=1, choices=SEXE, null=True, blank=True)
    tel=models.CharField(max_length=15, null=True, blank=True)
    grade=models.CharField(max_length=4, choices=GRADE, null=True, blank=True)
    charge_statut=models.DecimalField(max_digits=5, decimal_places=2, default=288, blank=True)
    situation=models.CharField(max_length=1, null=True, blank=True, choices=SITUATION, default='A')
    statut=models.CharField(max_length=1, null=True, blank=True, choices = STATUT, default='P')
    bureau=models.CharField(max_length=10, null=True, blank=True)
    bal=models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Boîte aux lettres')
    edt=models.TextField(null=True,blank=True, verbose_name="Emploi du temps")
    webpage=models.URLField(null=True, blank=True)
    otp=models.CharField(max_length=6, null=True, blank=True, default='')
    photo=models.ImageField(upload_to='photos',null=True,blank=True, validators=[validate_image])
    public_profile=models.BooleanField(default=False, verbose_name='Profil public')
    bio=models.TextField(null=True,blank=True)
    publications=models.TextField(null=True,blank=True, validators=[validate_url_list], verbose_name="URLs des profils scientifiques (Google Scholar, ResearchGate, DBLP, ..), séparées par des sauts de ligne")
    date_naissance=models.DateField(null=True, blank=True,verbose_name='Date de naissance')
    date_embauche=models.DateField(null=True, blank=True,verbose_name="Date d'embauche")
    matricule=models.CharField(max_length=20, null=True, blank=True)
    organisme=models.ForeignKey('Organisme', on_delete=models.SET_NULL, null=True, blank=True, related_name='enseignants', verbose_name="Laboratoire/service/..")
    
    @transaction.atomic
    def set_otp(self):
        self.otp=str(randint(100000,999999))
        self.save(update_fields=['otp'])
        return self.otp
    
    def get_otp(self):
        return self.otp
    
    @transaction.atomic
    def check_otp(self, value):
        if self.otp=='':
            return False
        else:
            validity=(value==self.otp)
            self.otp=''
            return validity
    
    def ratio_charge_annuelle_encours(self):
        charge_list = Charge.objects.filter(realisee_par=self, annee_univ__encours=True)
        somme=0
        for charge_ in charge_list:
            if charge_.repeter_chaque_semaine:
                somme+=charge_.vh_eq_td * 15
            else:
                somme+=charge_.vh_eq_td
        return round(100,2) if self.statut=='V' else round(somme/self.charge_statut*100,2)
    
    def nb_avis(self):
        return Validation.objects.filter(pfe__groupe__isnull=True, expert=self.id).count()
    
    def nb_avis_vides(self):
        return Validation.objects.filter(pfe__groupe__isnull=True, expert=self.id, avis='X').count()

    def nb_avis_annee(self, annee):
        return Validation.objects.filter(expert=self.id, debut__year=annee).count()
    
    def nb_avis_vides_annee(self, annee):
        return Validation.objects.filter(expert=self.id, avis='X', debut__year=annee).count()
    
    def nb_encadrements(self):
        return PFE.objects.filter(groupe__section__formation__annee_univ__encours=True, coencadrants__in=[self]).count()
    
    def nb_surveillances(self):
        return SurveillanceEnseignant.objects.filter(enseignant=self, seance__activite__module__formation__annee_univ__encours=True).count()
    
    def vh_surveillances(self):
        aggregate = SurveillanceEnseignant.objects.filter(enseignant=self, seance__activite__module__formation__annee_univ__encours=True).aggregate(vh_surveillances=Sum('seance__activite__vh')) 
        return aggregate['vh_surveillances']
    
    def is_grade_magistral(self):
        return self.grade=="MC" or self.grade=="MCA" or self.grade=="PR"

    def is_doctorant(self):
        return Doctorant.objects.filter(enseignant=self).exists()
    
    def get_email(self):
        return self.user.get_email() if self.user else ''

    # vérifier si user_, un déposant de candidature, a accès au profil de l'enseignant à travers une candidature déposée pour une offre de user_
    def acces_profil_candidature(self, user_):
        try :
            return Candidature.objects.filter(offre__user=user_, offre__user__isnull=False, acces_profil=True).exists()
        except Exception :      
            return False
    
    def __str__(self):
        return f"{self.nom} {self.prenom}"
 
class Autorite(models.Model):
    intitule=models.CharField(max_length=100, verbose_name="Intitulé")
    intitule_a=models.CharField(max_length=100, null=True, blank=True, verbose_name="Intitulé arabe")
    intitule_en=models.CharField(max_length=100, null=True, blank=True, verbose_name="Intitulé anglais")
    responsable=models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True)
    titre_responsable=models.CharField(max_length=100, null=True, blank=True, verbose_name="Titre du responsable")
    titre_responsable_a=models.CharField(max_length=100, null=True, blank=True, verbose_name="Titre du responsable en arabe")
    titre_responsable_en=models.CharField(max_length=100, null=True, blank=True, verbose_name="Titre du responsable en anglais")
    signature=models.ImageField(upload_to='admin', null=True, blank=True)
    autorite=models.ForeignKey('Autorite', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Autorité mère", related_name="autorites_filles")
    
    def get_email_responsable(self):
        return self.responsable.get_email() if self.responsable else ''
    
    def __str__(self):
        if self.responsable:
            return f"{self.intitule} - Responsable : {self.responsable}"
        return self.intitule
    
        
class Cycle(models.Model):
    ordre=models.PositiveSmallIntegerField(null=True, blank=True)
    intitule=models.CharField(max_length=100)
    intitule_a=models.CharField(max_length=100, null=True, blank=True, verbose_name="Intitulé arabe")
    intitule_en=models.CharField(max_length=100, null=True, blank=True, verbose_name="Intitulé anglais")
    autorite=models.ForeignKey(Autorite, on_delete=models.SET_NULL, null=True, blank=True)
    reglement=models.FileField(upload_to='admin', null=True, blank=True)
    activation_rattrapage=models.BooleanField(default=False, verbose_name="Activation session rattrapages pour les programmes du cycle")
    activation_credits=models.BooleanField(default=False, verbose_name="Activation des crédits pour les programmes du cycle")
    activation_ues=models.BooleanField(default=False, verbose_name="Activation des unités d'enseignement (UE)s pour les programmes du cycle")
    activation_dettes=models.BooleanField(default=False, verbose_name="Activation des dettes pour les programmes du cycle")
    users_visualisation_notes=models.ManyToManyField('User', blank=True, verbose_name="Utilisateurs pouvant visualiser les notes du cycle", related_name='cycles_avec_acces_visualisation_notes')
    users_gestion_notes=models.ManyToManyField('User', blank=True, verbose_name="Utilisateurs pouvant gérer les notes du cycle", related_name='cycles_avec_acces_gestion_notes')
    users_gestion_etudiants=models.ManyToManyField('User', blank=True, verbose_name="Utilisateurs pouvant gérer les inscriptions du cycle : Modification groupes, décisions jury, observations, ..", related_name='cycles_avec_acces_gestion_etudiants')
    
    def get_email_responsable_autorite(self):
        return self.autorite.get_email_responsable() if self.autorite else ''
                
    def __str__(self):
        return self.intitule
    
class Diplome(models.Model):
    intitule=models.CharField(max_length=100)
    intitule_a=models.CharField(max_length=100, null=True, verbose_name="Intitulé en arabe")
    intitule_en=models.CharField(max_length=100, null=True, verbose_name="Intitulé en anglais", blank=True)
    domaine = models.CharField(max_length=100, null=True)
    domaine_a = models.CharField(max_length=100, null=True, blank=True, verbose_name="Domaine en arabe")
    domaine_en = models.CharField(max_length=100, null=True, blank=True, verbose_name="Domaine en anglais")
    filiere = models.CharField(max_length=100, null=True)
    filiere_a = models.CharField(max_length=100, null=True, blank=True, verbose_name="Filière en arabe")
    filiere_en = models.CharField(max_length=100, null=True, blank=True, verbose_name="Filière en anglais")
    code_filiere= models.CharField(max_length=100, null=True, blank=True,help_text="Veuillez insérer -Code de spécialité- utilisé dans les fichiers de service national.")
    code_diplome=models.CharField(max_length=100, null=True, blank=True,help_text="Veuillez insérez -Code de diplôme- utilisé dans les fichiers de service national.")
    code_cycle=models.CharField(max_length=100, null=True, blank=True,help_text="Veuillez insérez -Code de cycle- utilisé dans les fichiers de service national.")
    
    def __str__(self):
        return self.intitule
    
class Programme(models.Model):
    '''
    description statique des programmes
    '''
    code=models.CharField(max_length=18, unique=True)
    titre=models.CharField(max_length=100)
    titre_a=models.CharField(max_length=100, null=True, verbose_name="Titre en arabe")
    titre_en=models.CharField(max_length=100, null=True, verbose_name="Titre en anglais", blank=True)
    doctorat=models.BooleanField(default=False, verbose_name="Programme de post-graduation", blank=True)
    specialite=models.ForeignKey(Specialite, null=True, blank=True, on_delete=models.SET_NULL)
    description=models.TextField()
    diplome=models.ForeignKey(Diplome, on_delete=models.SET_NULL, null=True, blank=True)
    cycle=models.ForeignKey(Cycle, on_delete=models.SET_NULL, null=True, blank=False)
    #signature_par_autorite=models.BooleanField(default=False, verbose_name="Cochez si les documents liés au programme sont signés par l'autorité associée au programme, sinon ils seront signés par l'autorité associée au cycle")
    ordre=models.PositiveSmallIntegerField(null=True, blank=True)
    # si concours à la fin de ce programme car ça influt sur les décisions de jurys possibles.
    concours=models.BooleanField(default=False)
    assistant=models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True)
    fictif=models.BooleanField(default=False, verbose_name="Programme fictif (Pour ne pas l'afficher dans les feedbacks, statistiques : Cas de Stages SPE / Programmes de doctorat)")
    matiere_equipe=models.ForeignKey(Matiere, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Matière en équipe concernée par le programme fictif")
    code_serv_national=models.CharField(max_length=18, null=True, blank=True,help_text="Insérer le code niveau utilisé dans les fichiers de service national")
    programme_complementaire_master=models.BooleanField(default=False, verbose_name="Programme complémentaire de Master (Le relevé provisoire des étudiants sera différent des autres programmes)")
    
    def inclut_pfe(self):
        return Matiere.objects.filter(matiere_ues__periode__programme=self, pfe=True).exists()
    
    def inclut_pfe_only(self):
        return (self.inclut_pfe() and (Matiere.objects.filter(matiere_ues__periode__programme=self).count() == 1))
    
    def aggregate_avg_decision_jury(self):
        formation_list=Formation.objects.filter(programme=self, annee_univ__encours=False)
        aggregate={
            'admis':0,
            'admis_rattrapage':0,
            'admis_dettes':0,
            'admis_rachat':0,
            'redouble':0,
            'non_admis':0,
            'abandon':0,
            'non_inscrit':0,
            'maladie':0,
            'success':0,
            'echec':0,
            'refaire':0,
            'total':0
            }
        nb_formation=0
        for formation_ in formation_list:
            aggregate_formation=formation_.aggregate_decision_jury()
            if aggregate_formation:
                nb_formation+=1
                for key in (aggregate.keys()):
                    if key=='total':
                        aggregate['total']+=aggregate_formation['total_inscrits']
                    elif float(aggregate_formation['total_inscrits'])!=0:
                        # on calcul le purcentage pour les autres aggrégats
                        aggregate[key]+=float(aggregate_formation[key])/float(aggregate_formation['total_inscrits'])*100.00

        if nb_formation>0:
            # on calcule la moyenne
            for key in aggregate.keys():
                if key=='total':
                    aggregate[key]=int(round(aggregate[key]/nb_formation,0))
                else:
                    aggregate[key]=round(aggregate[key]/nb_formation,2)
            return aggregate
        else:
            return None

    def programme_suivant(self):
        programme_suivant_list=Programme.objects.filter(ordre=self.ordre+1, diplome=self.diplome)
        if programme_suivant_list.count()==1:
            return programme_suivant_list.get()
        else:
            programme_suivant_list=Programme.objects.filter(ordre=self.ordre+1, specialite=self.specialite, diplome=self.diplome)
            if programme_suivant_list.count()==1:
                return programme_suivant_list.get()
            else:
                return None
    
    def formation_list(self):
        return Formation.objects.filter(programme=self).order_by('-annee_univ__annee_univ')
    
    
    def __str__(self):
        return self.code
    
    def activation_rattrapage(self):
        if self.cycle and self.cycle.activation_rattrapage :
            return True
        else :
            return False

    def activation_credits(self):
        if self.cycle :
            return self.cycle.activation_credits
        else :
            return False

    def activation_ues(self):
        if self.cycle :
            return self.cycle.activation_ues
        else :
            return False
        
    def activation_dettes(self):
        if self.cycle :
            return self.cycle.activation_dettes
        else :
            return False

    def get_email_assistant(self):
        return self.assistant.get_email() if self.assistant else ''
    
    def get_email_responsable_autorite_cycle(self):
        return self.cycle.get_email_responsable_autorite() if self.cycle else ''
    
    def has_semestres(self):
        return PeriodeProgramme.objects.filter(programme=self, code__startswith='S').exists()
    
    def has_periode_annuelle_only(self):
        return ((PeriodeProgramme.objects.filter(programme=self).count()==1) and (PeriodeProgramme.objects.filter(programme=self, code='AN').exists()))
        
    
    def activation_certificat_scolarite(self):
        actif=False
        try:
            return DocumentConfig.objects.get(code="CERTIFICAT_SCOLARITE", programme=self).actif
        except Exception:
            return actif

    def activation_fiche_inscription(self):
        actif=False
        try:
            return DocumentConfig.objects.get(code="FICHE_INSCRIPTION", programme=self).actif
        except Exception:
            return actif

    def activation_releve_notes_fr(self):
        actif=False
        try:
            return DocumentConfig.objects.get(code="RELEVE_NOTES_FR", programme=self).actif
        except Exception:
            return actif
        

PERIODES = (
    ('S1', 'Semestre 1'),
    ('S2', 'Semestre 2'),
    ('S3', 'Semestre 3'),
    ('S4', 'Semestre 4'),
    ('S5', 'Semestre 5'),
    ('S6', 'Semestre 6'),
    ('S5+S6', 'Semestre 5+6'),
    ('AN', 'Annuel'),
)

class PeriodeProgramme(models.Model):
    periode=models.ForeignKey(Periode, on_delete=CASCADE)
    programme=models.ForeignKey(Programme, on_delete=CASCADE, related_name='periodes')
    # Ce code correspond à la codification du décrêt, par exemple en 2CS ce sera S3, S4, en 3CS, S5, S6
    # L'attribut code de la classe Periode correspond à la période chronologique dans l'année S1, S2, ou TR1, TR2, TR3, ...
    code = models.CharField(max_length = 10, null =True, blank=True, choices = PERIODES)
    
    def nb_matieres(self):
        somme=0
        for ue in self.ues.all():
            somme+=ue.nb_matieres()
        return somme

    def credit(self):
        somme=0
        ue_option_comptabilisee_list=[]
        for ue in self.ues.all():
            if ue.nature=='OBL':
                somme+=ue.credit()
            elif not ue.code in ue_option_comptabilisee_list:
                somme+=ue.credit()
                ue_option_comptabilisee_list.append(ue.code) 
        return somme
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['programme', 'periode'], name="periode-programme")
        ]

    def __str__(self):
        return f"{self.programme} {self.periode}"

CAT_UE = (
    ('F','UE Fondamentale'),
    ('M','UE Méthodologique'),
    ('T','UE Transversale'),
    ('D','UE Découverte'),
)

class UE(models.Model):
    '''
    Un programme est composé de plusieurs UE
    '''
    '''
    Une UE obligatoire figure nécessairement dans tous les relevés de note
    Une UE optionnelle est composée de matières au choix dans la limite du nombre de crédits alloués à l'UE
    Donc plusieurs instances de l'UE sont créées en fonction des choix
    C'est dans Formation qui est l'instance temporelle de Programme qu'on fixe la liste des options retenues pour la promotion
    Puis dans le groupe on précise les UE spécifique à une option
    '''
    NATURES = (
        ('OBL','Obligatoire'),
        ('OPT','Optionnelle'),
    )
    code=models.CharField(max_length=8)
    code_a=models.CharField(max_length=20, null=True, blank=True, verbose_name="Code en arabe (uniquement pour le relevé de notes en arabe)")
    type=models.CharField(max_length=1, choices=CAT_UE)
    nature=models.CharField(max_length=3, choices=NATURES, null=True)
    matieres=models.ManyToManyField(Matiere, blank=True, related_name='matiere_ues')
    periode=models.ForeignKey(PeriodeProgramme, on_delete=CASCADE, null=True, blank=True, related_name='ues')
    coefold=models.IntegerField(null=True)
    
    def nb_matieres(self):
        return self.matieres.all().count()
    
    def coef(self):
        somme=0
        for matiere in self.matieres.all():
            somme+=matiere.coef
        return somme
    
    def credit(self):
        somme=0
        for matiere in self.matieres.all():
            somme+=matiere.credit
        return somme

    def __str__(self):
        list_matieres = " ".join([matiere.code for matiere in self.matieres.all()])
        return f"{self.code} {self.periode} {list_matieres}"

# DECISIONS_JURY=(
#     ('C','En cours'),
#     ('A','Admis'),
#     ('AR','Admis avec Rachat'),
#     ('R','Redouble'),
#     ('F','Abandon'),
#     ('M','Maladie'),
#     ('N','Non Admis'),
#     ('X','Non Inscrit'),
# )

 
class Formation(models.Model):
    '''
    Formation correspond à un pallier ou spécialité
    '''
    programme=models.ForeignKey(Programme, on_delete=CASCADE)
    annee_univ=models.ForeignKey(AnneeUniv, on_delete=CASCADE)
    archive=models.BooleanField(default=False)
    moyenne_passage=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=10.0)
    
    
    def pv_existe(self, periode_):
        if PV.objects.filter(formation=self.id, annuel=True):
            return True
        else:
            return PV.objects.filter(formation=self.id, periode=periode_).count() > 0
        
    def pv_final_existe(self):
        return PV.objects.filter(formation=self.id, annuel=True, signature=True).count() > 0

    def inscriptions_actives(self):
        return Inscription.objects.filter(formation=self).exclude(Q(inscription_periodes__groupe__isnull=True)|Q(decision_jury='X')|Q(decision_jury__startswith='F')|Q(decision_jury__startswith='M'))

    def inscriptions_pour_deliberations(self):
        return Inscription.objects.filter(formation=self).exclude(Q(inscription_periodes__groupe__isnull=True)|Q(decision_jury='X')|Q(decision_jury='FT'))

    def inscriptions_pour_deliberations_sans_conges(self):
        return self.inscriptions_pour_deliberations().exclude(decision_jury__startswith='M')

    def inscriptions_encours(self):
        return Inscription.objects.filter(formation=self, decision_jury='C')
    
    def pre_inscriptions(self):
        return Inscription.objects.filter(formation=self).filter(Q(decision_jury='X')|Q(decision_jury='C'))
    
    def aggregate_decision_jury(self):
        inscription_list=Inscription.objects.filter(formation=self)
        admis_count=Count('decision_jury', filter=Q(decision_jury='A')|Q(decision_jury='AC'))
        admis_f_count=Count('decision_jury',filter=(Q(etudiant__sexe='F')&(Q(decision_jury='AC')|Q(decision_jury='A'))))
        admisrachat_f_count=Count('decision_jury',filter=(Q(etudiant__sexe='F')&(Q(decision_jury='AR')|Q(decision_jury='CR'))))
        admis_G_count=Count('decision_jury',filter=(Q(etudiant__sexe='M')&(Q(decision_jury='AC')|Q(decision_jury='A'))))
        admisrachat_G_count=Count('decision_jury',filter=(Q(etudiant__sexe='M')&(Q(decision_jury='AR')|Q(decision_jury='CR'))))       
        admis_rattrapage_count=Count('decision_jury', filter=Q(decision_jury='SR'))        
        admis_dettes_count=Count('decision_jury', filter=Q(decision_jury='AD'))
        admis_rachat_count=Count('decision_jury', filter=Q(decision_jury='AR')|Q(decision_jury='CR'))
        encours_count=Count('decision_jury', filter=Q(decision_jury='C'))
        non_admis_count=Count('decision_jury', filter=Q(decision_jury='N'))
        redouble_count=Count('decision_jury', filter=Q(decision_jury='R')| Q(decision_jury='AJ')| Q(decision_jury='P'))
        abandon_count=Count('decision_jury', filter=Q(decision_jury='F'))
        maladie_count=Count('decision_jury', filter=Q(decision_jury__startswith='M'))
        #non_inscrit_count=Count('decision_jury', filter=Q(decision_jury='X')|Q(groupe__isnull=True))
        non_inscrit_count=Count('decision_jury', filter=Q(decision_jury='X'))
        total_count=Count('decision_jury', filter=Q(decision_jury='A') |Q(decision_jury='AC') | Q(decision_jury='AR') | Q(decision_jury='SR') | Q(decision_jury='AD') | Q(decision_jury='CR') | Q(decision_jury='C')| Q(decision_jury__startswith='F')| Q(decision_jury__startswith='M')| Q(decision_jury='R')| Q(decision_jury='N')| Q(decision_jury='AJ')| Q(decision_jury='P')|Q(decision_jury='X'))
        inscrits_count=Count('decision_jury', filter=Q(decision_jury='A') |Q(decision_jury='AC') | Q(decision_jury='AR') | Q(decision_jury='SR') | Q(decision_jury='AD') | Q(decision_jury='CR') | Q(decision_jury='C')| Q(decision_jury='F')| Q(decision_jury__startswith='M')| Q(decision_jury='R')| Q(decision_jury='N')| Q(decision_jury='AJ')| Q(decision_jury='P'))
        transfert_count=Count('decision_jury',filter=Q(decision_jury='FT')|Q(decision_jury='AC')|Q(decision_jury='CR'))
        if inscription_list.exists():
            aggregate_data=inscription_list.values('formation').annotate(
                admis=admis_count).annotate(
                admis_rattrapage=admis_rattrapage_count).annotate(                
                admis_dettes=admis_dettes_count).annotate(
                admis_rachat=admis_rachat_count).annotate(
                admis_fille=admis_f_count).annotate(
                admisrachat_fille=admisrachat_f_count).annotate(
                admis_garcon=admis_G_count).annotate(
                admisrachat_garcon=admisrachat_G_count).annotate(                           
                encours=encours_count).annotate(
                non_admis=non_admis_count).annotate(
                redouble=redouble_count).annotate(
                abandon=abandon_count).annotate(
                maladie=maladie_count).annotate(
                non_inscrit=non_inscrit_count).annotate(
                total=total_count).annotate(
                success=admis_count+admis_rachat_count).annotate(
                echec=abandon_count+non_admis_count).annotate(
                total_inscrits=inscrits_count).annotate(
                transfert=transfert_count).annotate(
                sortants=transfert_count+non_inscrit_count).annotate(
                scolarise=encours_count+ admis_count+admis_rachat_count+non_admis_count+redouble_count).annotate(
                maladie_abandon=maladie_count+abandon_count).annotate(
                redouble_nonadmis=non_admis_count+redouble_count).annotate(                         
                refaire=redouble_count+maladie_count)                             
                 
        else:
            return None
        return aggregate_data[0]

    
    def formation_sup_annee_suivante(self):
        #annee_courante=AnneeUniv.objects.get(annee_univ=self.annee_univ)
        annee_suivante_=self.annee_univ.annee_suivante()
        #programme_courant=Programme.objects.get(id=self.programme)
        programme_suivant_=self.programme.programme_suivant()
        if programme_suivant_:
            formation_sup_annee_suivante_, created=Formation.objects.get_or_create(annee_univ=annee_suivante_, programme=programme_suivant_, defaults={
                    'annee_univ':annee_suivante_,
                    'programme':programme_suivant_,
                    'archive':False
                })
            return formation_sup_annee_suivante_
        else:
            return None

    def formation_idem_annee_suivante(self):
        #annee_courante=AnneeUniv.objects.get(annee_univ=self.annee_univ)
        annee_suivante_=self.annee_univ.annee_suivante()
        formation_idem_annee_suivante_, created=Formation.objects.get_or_create(annee_univ=annee_suivante_, programme=self.programme, defaults={
                'annee_univ':annee_suivante_,
                'programme':self.programme,
                'archive':False
            })
        return formation_idem_annee_suivante_
    
    def matiere_pfe(self):
        matiere_qs=Matiere.objects.filter(pfe=True, module__formation=self).distinct()
        if matiere_qs.exists() and matiere_qs.count() == 1 :
            return matiere_qs.first()
        else :
            return None
            
    def activation_rattrapage(self):
        return self.programme.activation_rattrapage()

    def activation_credits(self):
        return self.programme.activation_credits()

    def activation_ues(self):
        return self.programme.activation_ues()
    
    def activation_dettes(self):
        return self.programme.activation_dettes()
    
    def marquer_entree_rattrapage_resultats(self):
        if self.activation_rattrapage() :
            Resultat.objects.filter(inscription__formation=self, inscription__proposition_decision_jury="DR", module__isnull=False, entree_rattrapage=False, module__formation=self).annotate(
              inferieur=Case(
                  When(moy_post_delib__lt=F('module__seuil_rattrapage'), then=Value(True)),
                  default=Value(False),
                  output_field=BooleanField()
               )).filter(inferieur=True).update(entree_rattrapage=True)
        return
         
    def dettes_total_count(self):
        return Resultat.objects.filter(inscription__formation=self, dette=True).count()
    
    def dettes_en_attente_count(self):
        return Resultat.objects.filter(inscription__formation=self, dette=True, etat_dette='X').count()
        
    def dettes_en_cours_count(self):
        return Resultat.objects.filter(inscription__formation=self, dette=True, etat_dette='C').count()
    
    def dettes_terminees_count(self):
        return Resultat.objects.filter(inscription__formation=self, dette=True, etat_dette='T').count()

    def has_semestres(self):
        return self.programme.has_semestres()

    def has_periode_annuelle_only(self):
        return self.programme.has_periode_annuelle_only()
    
        
    def __str__(self):
        return f"{self.programme} {self.annee_univ}"
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['programme', 'annee_univ'], name="programme-annee_univ")
        ]

class PeriodeFormation(models.Model):
    formation = models.ForeignKey(Formation, on_delete=CASCADE, null=True, blank=True, related_name='periodes')
    periode = models.ForeignKey(Periode, on_delete=CASCADE, null=True, blank=True)
    session = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return f"{self.formation} {self.periode.code} {self.session}"
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['formation', 'periode'], name="formation-periode")
        ]

class PV(models.Model):
    formation=models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True)
    content=models.TextField()
    annuel=models.BooleanField(default=False)
    periode=models.ForeignKey(Periode, on_delete=models.SET_NULL, null=True, blank=True)
    tri_rang=models.BooleanField(default=True)
    photo=models.BooleanField(default=True)
    anonyme=models.BooleanField(default=False)
    note_eliminatoire=models.BooleanField(default=True)
    moy_ue=models.BooleanField(default=False)
    rang=models.BooleanField(default=True)
    signature=models.BooleanField(default=True)
    reserve=models.BooleanField(default=False)
    post_rattrapage=models.BooleanField(default=False)
    date=models.DateField(null=True, blank=True)
    xlsx=models.FileField(upload_to='files/pvs', null=True, blank=True) 

    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['formation', 'annuel', 'periode', 'tri_rang', 'photo', 'anonyme', 'note_eliminatoire', 'rang','signature', 'post_rattrapage'], name="pv_config")
        ]
    def __str__(self):
        pv = f"PV {self.formation}"
        if not self.annuel:
            pv+=' '+str(self.periode)
        if self.tri_rang:
            pv+=' Rang'
        if self.note_eliminatoire:
            pv+=' NE'
        if self.photo:
            pv+=' Photos'
        if self.signature:
            pv+=' Sig'
        if self.post_rattrapage:
            pv+=' Post-Rattrapage'
        if self.anonyme:
            pv+=' Anonyme'
        return pv
    

class Module(models.Model):
    '''
    Il s'agit d'une instance d'une matière dans une formation
    '''
    matiere=models.ForeignKey(Matiere, on_delete=CASCADE)
    formation=models.ForeignKey(Formation, on_delete=CASCADE, related_name='modules')
    periode=models.ForeignKey(PeriodeProgramme, on_delete=models.SET_NULL, null=True, blank=True)
    # TODO on doit pas cascader delete de periode sinon on perd la base en un click
    coordinateur=models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True)
    note_eliminatoire=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=5.0)
    ponderation_moy=models.DecimalField(max_digits=3, decimal_places=2, default=0, blank=True, verbose_name="Pondération Moy Session Normale (de 0.00 à 1.00)")
    ponderation_moy_rattrapage=models.DecimalField(max_digits=3, decimal_places=2, default=0, blank=True, verbose_name="Pondération Moy Session Rattrapage (de 0.00 à 1.00)")
    activation_max_moy_normale_et_rattrapage=models.BooleanField(default=True, verbose_name="Comptabilisation du maximum entre la moyenne normale et la moyenne de rattrapage")
    seuil_rattrapage=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=10.0)
    
    def pv_existe(self):
        return self.formation.pv_existe(self.periode.periode)
    
    def calcul_note_eliminatoire(self):
        # on considère les résultats de tous les étudiants qui suivent la formation
        # on exclut du calcul les malades et abandons
        resultat_list=Resultat.objects.filter(inscription__formation=self.formation, module=self).exclude(inscription__decision_jury__startswith='M').exclude(inscription__decision_jury__startswith='F').exclude(inscription__decision_jury='X').exclude(inscription__groupe__isnull=True)
        if resultat_list.exists():
            resultat_avg=resultat_list.values('module').annotate(moyenne=Avg('moy')).get()
            note_eliminatoire=round(resultat_avg['moyenne']*decimal.Decimal(0.60),2)
        else:
            note_eliminatoire=round(decimal.Decimal(5.0),2)
        if note_eliminatoire>=decimal.Decimal(10.0):
            note_eliminatoire=round(decimal.Decimal(9.99),2)
        elif note_eliminatoire<decimal.Decimal(5.0):
            note_eliminatoire=round(decimal.Decimal(5.0),2)
            
        return note_eliminatoire

    def nb_absences(self, etudiant_):
        nb = AbsenceEtudiant.objects.filter(etudiant=etudiant_, seance__activite__module=self).count()
        return nb
    
    def nb_etudiants_avec_ne(self):
        return Resultat.objects.filter(inscription__formation=self.formation, module=self, moy__lt=self.note_eliminatoire).exclude(inscription__decision_jury__startswith='M').exclude(inscription__decision_jury__startswith='F').exclude(inscription__decision_jury='X').exclude(inscription__groupe__isnull=True).count()

    def nb_etudiants_avec_ne_calculee(self):
        return Resultat.objects.filter(inscription__formation=self.formation, module=self, moy__lt=self.calcul_note_eliminatoire()).exclude(inscription__decision_jury__startswith='M').exclude(inscription__decision_jury__startswith='F').exclude(inscription__decision_jury='X').exclude(inscription__groupe__isnull=True).count()

    def moy(self):
        aggregate=Resultat.objects.filter(inscription__formation=self.formation, module=self
                                        ).exclude(inscription__decision_jury__startswith='M'
                                        ).exclude(inscription__decision_jury__startswith='F'
                                        ).exclude(inscription__decision_jury='X'
                                        ).aggregate(moy=Avg('moy'))
        if aggregate['moy']:
            return round(aggregate['moy'],2)
        else:
            return 0
    
    def somme_ponderation(self):
        if self.evaluations.filter(ponderation__isnull=False).exists():
            aggregate=self.evaluations.all().aggregate(somme=Sum('ponderation'))
            return round(aggregate['somme'],2)
        else:
            return 0
    
    def activation_rattrapage(self):
        return self.formation.activation_rattrapage()
    
    def activation_dettes(self):
        return self.formation.activation_dettes()
    
    def get_email_coordinateur(self):
        return self.coordinateur.get_email() if self.coordinateur else ''
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['matiere', 'formation', 'periode'], name="matiere-formation")
        ]
        indexes = [
            models.Index(fields=['formation', 'periode'])
        ]
        
    def __str__(self):
        # to f fomrmat
        return f"{self.formation} {self.matiere} {self.periode}"
    
class Evaluation(models.Model):
    '''
    On définit ici les évlautaions prévues dans un module
    '''
    TYPES_EVAL=(
        ('CF','Contrôle Final'),
        ('CFR','Contrôle Final Rattrapage'),
        ('CI','Contrôle Intérmédiaire'),
        ('INT','Interrogation'),
        ('TP','Travail Pratique'),
        ('TH','Contrôle Théorique'),
        ('TPR','Travail Pratique Rattrapage'),
        ('THR','Contrôle Théorique Rattrapage'),
        ('CC','Contrôle Continu'),
        ('EMD1','EMD1'),
        ('EMD2','EMD2'),
        ('EMD3','EMD3'),
        ('EMDR','EMD Rattrapage'),
        ('Equipe','Evaluation d\'une équipe'),
        ('Rapporteur','PFE: Evaluation du rapport'),
        ('Jury','PFE: Evaluation du jury'),
        ('Encadreur','PFE: Evaluation de l\'encadreur'),
        ('Rapport','Master: Evaluation du rapport'),
        ('Soutenance','Master: Evaluation de l\'oral'),
        ('Poster','Master: Evaluation du Poster'),
        ('EQP_Objectifs','Evaluation des objectifs d\'une matière d\'équipe'),
        ('EQP_Rapport','Evaluation du rapport d\'une matière d\'équipe'),
        ('EQP_Presentation','Evaluation de la présentation d\'une matière d\'équipe'),
        ('EQP_Qsts_Reps','Evaluation des réponses aux questions d\'une matière d\'équipe'),
        
    )
    type=models.CharField(max_length=20,choices=TYPES_EVAL)
    ponderation=models.DecimalField(max_digits=6, decimal_places=5, default=0, verbose_name="Pondération")
    ponderation_rattrapage=models.DecimalField(max_digits=6, decimal_places=5, default=0, blank=True)
    module=models.ForeignKey(Module,on_delete=CASCADE, related_name='evaluations')
    
    def __str__(self):
        return f"{self.type} {self.module}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['type', 'module'], name="eval-module")
    ]

    
class Section(models.Model):
    '''
    Section de cours. Une formation est organisée en sections
    '''
    CODES_SEC=(
        ('A','Section A'),
        ('B','Section B'),
        ('C','Section C'),
        ('D','Section D'),
        ('E','Section E'),
        ('F','Section F'),
        ('G','Section G'),
        ('H','Section H'),
        ('I','Section I'),
        ('J','Section J'),
        ('K','Section K'),
        ('L','Section L'),
        
    )
    code=models.CharField(max_length=1,null=True,choices=CODES_SEC)
    formation=models.ForeignKey(Formation, on_delete=CASCADE, null=True, related_name='sections')

    def taille(self):
        somme=0
        for groupe_ in self.groupes.all().exclude(code__isnull=True):
            somme+=groupe_.inscrits.all().count()
        return somme

    def __str__(self):
        return f"{self.formation.programme.code} Section {self.code}"

CODES_GRP=(
    ('G00','Groupe 00'),
    ('G01','Groupe 01'),
    ('G02','Groupe 02'),
    ('G03','Groupe 03'),
    ('G04','Groupe 04'),
    ('G05','Groupe 05'),
    ('G06','Groupe 06'),
    ('G07','Groupe 07'),
    ('G08','Groupe 08'),
    ('G09','Groupe 09'),
    ('G10','Groupe 10'),
    ('G11','Groupe 11'),
    ('G12','Groupe 12'),
)
    

class Groupe(models.Model):
    '''
    Groupe de TD ou TP
    UN groupe appartient à une section
    Un groupe particulier est créé automatiquement pour représenter une section et qui porte un code null
    '''
    code=models.CharField(max_length=10,null=True)
    section=models.ForeignKey(Section, on_delete=CASCADE, null=True, related_name='groupes')
    option=models.ManyToManyField(UE, blank=True)
    edt=models.TextField(null=True,blank=True, default='Agenda Empty')

    def gCal(self):
        # L'agenda correspondant à un groupe doit porter comme nom/code:
        # code programme (1CP, 2SL, ....) section (A, B, C, ...) et code groupe si c'est un groupe (G01, G02, ...)
        gCalCode = self.section.formation.programme.code+' '+self.section.code
        if self.code:
            gCalCode+=' '+self.code
        try:
            gCal_=GoogleCalendar.objects.get(code=gCalCode)
        except Exception:
            return None
        return gCal_
     
    def taille(self):
        if self.code:
            aggregate=InscriptionPeriode.objects.filter(groupe=self).exclude(Q(inscription__decision_jury__startswith='F')|Q(inscription__decision_jury__startswith='M')|Q(inscription__decision_jury='X')).values('periodepgm__periode__code').annotate(taille=Count('inscription')).order_by('periodepgm__periode__code')
            #return self.inscrits.all().count()
            return aggregate
        else:
            aggregate=InscriptionPeriode.objects.filter(groupe__section=self.section).exclude(Q(inscription__decision_jury__startswith='F')|Q(inscription__decision_jury__startswith='M')|Q(inscription__decision_jury='X')).values('periodepgm__periode__code').annotate(taille=Count('inscription')).order_by('periodepgm__periode__code')
#             somme={}
#             for groupe_ in self.section.groupes.all().exclude(code__isnull=True):
#                 somme+=groupe_.inscrits.all().count()
#             return somme
            return aggregate

    def is_pfe(self):
        if PFE.objects.filter(groupe=self).exists() :
            return True
        else :
            return False
 
    
    def is_equipe(self):
        if PFE.objects.filter(groupe=self).exists() :
            if Equipe.objects.filter(pfe=self.pfe).exists() :
                return True
            else :
                return False
        else :
            return False
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code', 'section'], name="groupe-section")
        ]

    def __str__(self):
        if self.code:
            if self.is_pfe() :
                return f"{self.section.formation.programme.code} {self.code}"
            else :
                return f"{self.section.formation.programme.code} {self.section.code} {self.code}"
        else:
            return str(self.section)

class ModulesSuivis(models.Model):
    SAISIE_ETAT=(
        ('N','Pas encore'),
        ('C','En cours'),
        ('T','Terminé'),
    )

    module=models.ForeignKey(Module, on_delete=CASCADE, related_name='groupes_suivis')
    groupe=models.ForeignKey(Groupe, on_delete=CASCADE, related_name='modules_suivis')
    saisie_notes=models.CharField(max_length=1, choices= SAISIE_ETAT, default='N')
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['module', 'groupe'], name="module-groupe")
        ]
        indexes = [
            models.Index(fields = ['module', 'groupe'])
        ]
        
    def __str__(self):
        return f"{self.module} {self.groupe}"

TYPES_ACT=(
    ('C','Cours'),
    ('TD','Travail Dirigé'),
    ('TP','Travail Pratique'),
    ('P','Projet'),
    ('E_CI','Contrôle Intermédiaire'),
    ('E_CF','Contrôle Final'),
    ('E_CR','Contrôle de Remplacement'),
    ('E_In','Interrogation'),
    ('E_TP','Test TP'),
    ('PFE_Enc', 'Encadrement PFE'),
    ('PFE_Sout','Soutenance PFE'),
    ('Mem_Enc', 'Encadrement Master'),
    ('Mem_Sout','Soutenance Master'),
    ('EQP_Sout','Soutenance Equipe Matière'),
)

TYPES_ACT_EXAM=(
    ('E_CI','Contrôle Intermédiaire'),
    ('E_CF','Contrôle Final'),
    ('E_CR','Contrôle de Remplacement'),
    ('E_In','Interrogation'),
    ('E_TP','Test TP'),
)

class Activite(models.Model):
    '''
    Il y a plusieurs activités dans un module comme un cours + TD + TP ...
    '''
    type=models.CharField(max_length=10,choices=TYPES_ACT)
    module=models.ForeignKey(Module, on_delete=CASCADE)
    cible=models.ManyToManyField(Groupe, blank=True, related_name='activites')
    assuree_par=models.ManyToManyField(Enseignant, related_name='enseignants')
    vh=models.DecimalField(max_digits=4, decimal_places=2, null=True, verbose_name="Volume horaire")
    repeter_chaque_semaine=models.BooleanField(default=True)
    repartir_entre_intervenants=models.BooleanField(default=False)
    
    def inscrits_activite(self):
        inscrits_activite_list=[]
        for groupe_ in self.cible.all():
            for resultat_ in Resultat.objects.filter(module=self.module, 
                                                    acquis=False,
                                                    resultat_ue__inscription_periode__groupe=groupe_).exclude(
                                                        Q(inscription__decision_jury__startswith='F')|
                                                        Q(inscription__decision_jury__startswith='M')|
                                                        Q(inscription__decision_jury__startswith='X')
                                                        ):
                inscrits_activite_list.append(resultat_.inscription)
        return inscrits_activite_list
    
    def nb_etudiants(self):
        return len(self.inscrits_activite())
    
    def vh_par_enseignant(self):
        # calcul du volume horaire
        nb_intervenants=self.assuree_par.count()
        if nb_intervenants>0:
            if self.repartir_entre_intervenants:
                vh_=self.vh/nb_intervenants
            else:
                vh_=self.vh
        else:
            vh_=0.0
        return round(vh_,2)
    
    def vh_eq_td_par_enseignant(self):
        # calcul du volume horaire
        vh_=self.vh_par_enseignant()
        if self.type=='C':
            vh_=vh_*decimal.Decimal(1.5)
        return round(vh_,2)
            
        
    class Meta:
        indexes = [
            models.Index(fields=['module'])
        ]
    
    def __str__(self):
        cible_str = " + ".join(str(groupe) for groupe in self.cible.all())
        return f"{dict(TYPES_ACT)[self.type]}: {self.module.matiere.code} + {cible_str}"

TYPE_CHARGE=(
    ('E','Enseignement'),
    ('C','Encadrement'),
    ('J','Jury'),
    ('S','Surveillance'),
    ('A','Responsabilite Administrative'),
    ('M','Mission'),
    ('R','Réunion'),
)

class ActiviteChargeConfig(models.Model):
    categorie=models.CharField(max_length=5, choices=TYPE_CHARGE, null=True )
    type=models.CharField(max_length=10)
    titre=models.CharField(max_length=50, null=True)
    vh=models.DecimalField(max_digits=5, decimal_places=2, default=0)
    vh_eq_td=models.DecimalField(max_digits=5, decimal_places=2, default=0)
    repeter_chaque_semaine=models.BooleanField(default=True)
    repartir_entre_intervenants=models.BooleanField(default=False)
    def __str__(self):
        return f"{dict(TYPE_CHARGE)[self.categorie]} {self.titre}"
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['type'], name="activite-charge_config")
        ]
    
class Charge(models.Model):
    '''
        Charge d'un enseignant issue de ses activités d'enseignement, encadrement, administration, surveillance, missions, etc.
    '''
    type=models.CharField(max_length=1, choices=TYPE_CHARGE)
    activite=models.ForeignKey(Activite, on_delete=CASCADE, null=True, blank=True)
    obs=models.CharField(max_length=50, null=True, blank=True)
    vh=models.DecimalField(max_digits=5, decimal_places=2, default=0)
    vh_eq_td=models.DecimalField(max_digits=5, decimal_places=2, default=0)
    annee_univ=models.ForeignKey(AnneeUniv, on_delete=models.SET_NULL, null=True)
    periode = models.ForeignKey(Periode, on_delete=models.SET_NULL, null=True)
    realisee_par=models.ForeignKey(Enseignant, on_delete=CASCADE, related_name='charges')
    cree_par=models.ForeignKey(Enseignant, on_delete=CASCADE, null=True, blank=True)
    repeter_chaque_semaine=models.BooleanField(default=False, null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['activite', 'realisee_par'], name="activite-enseignant")
        ]
        indexes = [
            models.Index(fields=['realisee_par'])
        ]

    def __str__(self):
        if self.activite:
            return f"{self.type} {self.activite} {self.vh_eq_td}"
        else:
            return f"{self.type} {self.obs} {self.vh_eq_td}"


class Pays(models.Model):
    code=models.CharField(max_length=2, primary_key=True)
    nom=models.CharField(max_length=50)
    def __str__(self):
        return self.nom

class Wilaya(models.Model):
    code=models.CharField(max_length=2, primary_key=True)
    nom=models.CharField(max_length=50)
    def __str__(self):
        return f"{self.code} {self.nom}"

class Commune(models.Model):
    code_postal=models.CharField(max_length=5, primary_key=True)
    nom=models.CharField(max_length=50)
    wilaya=models.ForeignKey(Wilaya, on_delete=models.SET_NULL, null=True, related_name='communes')
    def __str__(self):
        return f"{self.code_postal} {self.nom}"
   
Serie_bac=(
    ('', '---'),
    ('Sciences Experimentales','N03'),
    ('Mathematiques','N04'),    
    ('Techniques Mathematiques','N05'),
) 

#Remarque : A chaque fois qu'un nouveau modèle est créé et pointant vers le modèle Etudiant, il faut que la méthode matricule_update du modèle Etudiant puisse mettre à jour le nouveau modèle ajouté vers le nouvel objet étudiant créé
#C'est car le matricule d'un étudiant est une clé primaire il n'est pas possible de la modifier
#Donc on passe par une duplication de l'objet Etudiant et le changement des liens des objets pointant vers l'étudiant via la méthode matricule_update
#Le cleanup ignore est car si on change de matricule à l'étudiant, il est supprimé puis recréé ce qui supprime tous ses fichiers; On ignore donc le cleanup pour le modèle étudiant
@cleanup.ignore
class Etudiant(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, error_messages={
            'unique': (
                "Un étudiant associé à cet utilisateur existe déjà."),
        },)
    matricule=models.CharField(max_length=20,primary_key=True, error_messages={
            'unique': (
                "Un étudiant avec ce matricule existe déjà."),
        },)
    nom=models.CharField(max_length=50)
    prenom=models.CharField(max_length=50)
    sexe=models.CharField(max_length=1, choices=SEXE, null=True, blank=True)
    date_naissance=models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    lieu_naissance=models.CharField(max_length=100, null=True, blank=True)
    wilaya_naissance=models.ForeignKey(Wilaya, on_delete=models.SET_NULL, null=True, blank=True)
    wilaya_residence=models.ForeignKey(Wilaya, on_delete=models.SET_NULL, null=True, blank=True, related_name='origines')
    commune_residence=models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    interne=models.BooleanField(default=False, null=True, blank=True)
    residence_univ=models.TextField(null=True, blank=True)
    addresse_principale=models.TextField(null=True, blank=True)
    nom_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Nom en arabe")
    prenom_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Prénom en arabe")
    lieu_naissance_a=models.CharField(max_length=100, null=True, blank=True, verbose_name="Lieu de naissance en arabe")
    photo=models.ImageField(upload_to='photos',null=True,blank=True)
    activite_extra=models.TextField(null=True, blank=True)
    tuteur=models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True)    
    github=models.URLField(null=True, blank=True)
    linkdin=models.URLField(null=True, blank=True)
    public_profile=models.BooleanField(default=False)   
    tel=models.CharField(max_length=15, null=True, blank=True)
    numero_securite_sociale=models.CharField(max_length=15, validators=[RegexValidator('^[0-9\+]*$',
                               'Que des chiffres sans espaces')], null=True, blank=True)
    nom_mere=models.CharField(max_length=50, null=True, blank=True, verbose_name="Nom de la mère")       
    nom_mere_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Nom de la mère en arabe")
    prenom_mere=models.CharField(max_length=50, null=True, blank=True, verbose_name="Prénom de la mère")
    prenom_mere_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Prénom de la mère en arabe")
    fonction_mere=models.CharField(max_length=50, null=True, blank=True, verbose_name="Fonction de la mère")
    prenom_pere=models.CharField(max_length=50, null=True, blank=True, verbose_name="Prénom du père")
    prenom_pere_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Prénom du père en arabe")
    fonction_pere=models.CharField(max_length=50, null=True, blank=True, verbose_name="Fonction du père")
    tel_parents=models.CharField(max_length=15, null=True, blank=True)
    annee_bac=models.CharField(max_length=10, null=True, blank=True)
    n_inscription_bac=models.CharField(max_length=20,null=True, blank=True, verbose_name="Numéro d'inscription au bac")    
    moyenne_bac=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=0)
    serie_bac=models.CharField(max_length=50, choices=Serie_bac, null=True, blank=True)    
    lycee_bac=models.CharField(max_length=100, null=True, blank=True)
    matricule_progres=models.CharField(max_length=50,null=True,blank=True)
    livret_competences=models.FileField(upload_to='files/livrets', null=True, blank=True) 
    livret_last_upload=models.DateTimeField(null=True, blank=True)
    #def rang_max(self): 
#         aggregate=Etudiant.objects.filter(matricule=self.matricule).aggregate(rang_max=Max('inscriptions__rang'))
#         return aggregate['rang_max']
#     def annee_encours(self):
#         return self.inscriptions.all().get(formation__programme__encours=True).values('formation__programme')
    def inscriptions_encours(self):
        return Inscription.objects.filter(etudiant=self, formation__annee_univ__encours=True)
    
    def nb_depots_stages(self):
        return PFE.objects.filter(groupe__isnull=True, reserve_pour__etudiant__in=[self]).count()
    
    def eligible_pfe(self):
        eligible_=False
        for inscription_ in self.inscriptions_encours():
            ordre_programmes_pfe=Programme.objects.filter(periodes__ues__matieres__pfe__in=[True]).distinct().values_list('ordre', flat=True)
            for ordre in ordre_programmes_pfe :
                if inscription_.formation.programme.ordre >= ordre-1:
                    return True
        return eligible_
    
    def is_doctorant(self):
        return Doctorant.objects.filter(etudiant=self).exists()
        
    def ranking_agrege_de_plusieurs_modules(self, modules):     
        aggregate_etudiant = Resultat.objects.filter(module__in=modules, inscription__etudiant=self).aggregate(somme_moy=Sum(ExpressionWrapper(F('moy')*F('module__matiere__coef'), output_field=FloatField())), somme_coef=Sum('module__matiere__coef')) 
        etudiants_annotes_moy_agregee=Etudiant.objects.filter(inscriptions__resultats__module__in=modules).distinct().annotate(somme_moy=Sum(ExpressionWrapper(F('inscriptions__resultats__moy')*F('inscriptions__resultats__module__matiere__coef'), output_field=FloatField()), filter=Q(inscriptions__resultats__module__in=modules))).annotate(somme_coef=Sum('inscriptions__resultats__module__matiere__coef', filter=Q(inscriptions__resultats__module__in=modules))).annotate(moy_agregee=ExpressionWrapper(F('somme_moy')/F('somme_coef'), output_field=FloatField()))     
        moy_agregee_etudiant= decimal.Decimal(aggregate_etudiant['somme_moy'])  / aggregate_etudiant['somme_coef'] 
        aggregate={}
        aggregate['ranking'] = etudiants_annotes_moy_agregee.filter(moy_agregee__gt=moy_agregee_etudiant).count()+1
        aggregate['moy_agregee']=moy_agregee_etudiant
        aggregate['nb_inscrits_dont_la_moy_agregee_est_superieure_a_dix']=etudiants_annotes_moy_agregee.filter(moy_agregee__gte=10.0).count()
        return aggregate

    def ects_agrege_de_plusieurs_modules(self, modules): 
        if (modules.count()==1):
            resultat_etudiant = Resultat.objects.get(module__in=modules, inscription__etudiant=self)
            ects=resultat_etudiant.calcul_ects()
        else:
            rang_et_moy=self.ranking_agrege_de_plusieurs_modules(modules)
            rang=rang_et_moy['ranking']
            moy=rang_et_moy['moy_agregee']
            ects='F'
            if moy < 10.0:
                ects='F' 
            else:
                nb_inscrits_plusieurs_modules=rang_et_moy['nb_inscrits_dont_la_moy_agregee_est_superieure_a_dix']
                if  rang <= nb_inscrits_plusieurs_modules * decimal.Decimal(0.10):
                    ects='A'
                elif rang <= nb_inscrits_plusieurs_modules * decimal.Decimal(0.10 + 0.25):
                    ects='B'
                elif rang <= nb_inscrits_plusieurs_modules * decimal.Decimal(0.10 + 0.25 + 0.30):
                    ects='C'
                elif rang <= nb_inscrits_plusieurs_modules * decimal.Decimal(0.10 + 0.25 + 0.30 + 0.25):
                    ects='D'
                else :
                    ects='E'
                
        return ects  

    def get_email(self):
        return self.user.get_email() if self.user else '' 
    
    # Cette méthode met à jour le matricule d'un étudiant. 
    #A chaque fois qu'un nouveau modèle est créé et pointant vers le modèle Etudiant, il faut que cette méthode puisse mettre à jour le modèle vers le nouvel objet étudiant créé
    #C'est car le matricule est une clé primaire il n'est pas possible de la modifier
    #Donc on passe par une duplication de l'objet Etudiant et le changement des liens des objets pointant vers l'étudiant
    @transaction.atomic
    def matricule_update(self, matricule):
        try :
            etudiant_=self
            user_=etudiant_.user
            ancien_matricule=etudiant_.matricule
            if matricule :
                nouveau_matricule=str(matricule).strip()
                if nouveau_matricule != self.matricule :
                    if not Etudiant.objects.filter(matricule=nouveau_matricule).exists() :
                        etudiant_.user=None
                        etudiant_.matricule=nouveau_matricule
                        etudiant_.save()
                        ancien_etudiant=Etudiant.objects.get(matricule=ancien_matricule)
                        Inscription.objects.filter(etudiant=ancien_etudiant).update(etudiant=etudiant_)
                        Doctorant.objects.filter(etudiant=ancien_etudiant).update(etudiant=etudiant_)
                        AbsenceEtudiant.objects.filter(etudiant=ancien_etudiant).update(etudiant=etudiant_)
                        ancien_etudiant.delete()
                        etudiant_.user=user_
                        etudiant_.save()
                    else :
                        return None
                else :
                    return None
            else :
                return None
        except Exception :
            raise Exception
        else : 
            return etudiant_
        
    # vérifier si user_, un déposant de candidature, a accès au profil de l'étudiant à travers une candidature déposée pour une offre de user_
    def acces_profil_candidature(self, user_):
        try :
            return Candidature.objects.filter(offre__user=user_, offre__user__isnull=False, acces_profil=True).exists()
        except Exception :      
            return False
    
    
    def __str__(self):
        return f"{self.matricule} {self.nom} {self.prenom}"

def char_range(nb_chars):
    return list(string.ascii_uppercase[:nb_chars])

class Salle(models.Model):
    code= models.CharField(max_length=50)
    version = models.CharField(max_length=50, default='v0')
    calendarId= models.CharField(max_length=100, null=True, blank=True)
    nb_lignes= models.PositiveSmallIntegerField(default=0)
    nb_colonnes= models.PositiveSmallIntegerField(default=0)
    
    def capacite(self):
        return self.places.filter(disponible=True).count()
    
    def capacite_max(self):
        return self.nb_lignes * self.nb_colonnes

    def place_disponible_list(self):
        
        return self.places.filter(disponible=True).order_by('code')
    
    def ligne_list(self):
        return range(1, self.nb_lignes+1)
    
    def colonne_list(self):
        return char_range(self.nb_colonnes)
    
    def __str__(self):
        return f"{self.code}{self.version}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code', 'version'], name="salle-code-version")
        ]
    
class Place(models.Model):
    code = models.CharField(max_length=3, null=False, blank=False)
    disponible = models.BooleanField(default=True)
    salle = models.ForeignKey(Salle, on_delete=CASCADE, related_name='places')
    num_ligne = models.PositiveSmallIntegerField(default=0)
    num_colonne = models.CharField(max_length=1, null=True, blank=True)
    
    def __str__(self):
        return f"{self.salle}({self.code})"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['salle','code'], name="salle-place")
        ]
        constraints = [
            models.UniqueConstraint(fields=['salle','num_ligne','num_colonne'], name="salle-num_ligne-num_colonne")
        ]
        indexes = [models.Index(fields=['salle','code'])]
     
class Seance(models.Model):
    '''
    Instance d'une activité durant le semestre
    '''
    date=models.DateField()
    heure_debut=models.TimeField(null=True, blank=True)
    heure_fin=models.TimeField(null=True, blank=True)
    salles=models.ManyToManyField(Salle, blank=True)
    activite=models.ForeignKey(Activite, on_delete=CASCADE)
    rattrapage=models.BooleanField(default=False)
    
    def capacite_reservee(self):
        somme=0
        for salle_ in self.salles.all():
            somme += salle_.capacite()
        return somme
    
    def nb_places_reservees_salle(self):
        capacite_salle_={}
        for salle_ in self.salles.all():
            capacite_salle_[salle_.code]= ReservationPlaceEtudiant.objects.filter(seance=self, place__salle=salle_).count()
        return capacite_salle_
    
    def surveillance_par_salle(self):
        surveillants_salle_={}
        for salle_ in self.salles.all().order_by('code'):
            surveillants_salle_[salle_.code] = SurveillanceEnseignant.objects.filter(seance=self, salle=salle_).order_by('enseignant__nom')
        return surveillants_salle_
    
    def __str__(self):
        
        return f"{dict(TYPES_ACT)[self.activite.type]} {self.activite.module} {self.date.day}/{self.date.month}/{self.date.year}{' R' if self.rattrapage else ''}"

    def get_absolute_url(self):
        return reverse('seance_detail', kwargs={'seance_pk': self.pk})

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['activite', 'date', 'heure_debut', 'heure_fin'], name="seance")
        ]

class AbsenceEtudiant(models.Model):
    '''
    Permet de stocker les absences et leurs justifications
    '''
    etudiant=models.ForeignKey(Etudiant, on_delete=CASCADE, null=True, blank=True)
    seance=models.ForeignKey(Seance, on_delete=CASCADE, null=True, blank=True)
    justif=models.BooleanField(default=False)
    motif=models.TextField(max_length=50, null=True, blank=True)
    date_justif=models.DateField(null=True, blank=True)  
    
    def nb_absences(self):
        aggregate = AbsenceEtudiant.objects.filter(etudiant=self.etudiant, seance__activite__module=self.seance.activite.module).aggregate(nb_absences=Count('etudiant'))
        return aggregate['nb_absences']
    

    def __str__(self):
        return f"{self.etudiant} {self.seance}"
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['etudiant', 'seance'], name="etudiant-seance")
        ]

class AbsenceEnseignant(models.Model):
    '''
    Permet de stocker les absences et leurs justifications
    '''
    enseignant=models.ForeignKey(Enseignant, on_delete=models.CASCADE, null=True, blank=True)
    seance=models.ForeignKey(Seance, on_delete=CASCADE, null=True, blank=True)
    justif=models.BooleanField(default=False)
    date_justif=models.DateField(null=True, blank=True)
    motif=models.TextField(max_length=50, null=True, blank=True)
    seance_remplacement=models.ForeignKey(Seance, on_delete=CASCADE, null=True, blank=True, related_name='remplacement')

    def nb_absences(self):
        aggregate = AbsenceEnseignant.objects.filter(enseignant=self.enseignant, seance__activite__module=self.seance.activite.module).aggregate(nb_absences=Count('enseignant'))
        return aggregate['nb_absences']
    
    def __str__(self):
        return f"{self.enseignant} {self.seance}"
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['enseignant', 'seance'], name="enseignant-seance")
        ]
    
MENTION=(
    ('T','Très Bien'),
    ('B','Bien'),
    ('A','Assez Bien'),
    ('P','Passable'),
    ('F', 'Ajournement'),
    ('X', 'Non concerné')
)

DECISIONS_JURY=(
    ('C','Inscrit'),
    ('A','Admis'),
    ('AR','Admis avec Rachat'),
    ('DR','Rattrapage'),
    ('SR','Admis avec Rattrapage'),
    ('AD','Admis avec Dettes'),
    ('AC','Admis au Concours'),
    ('CR','Admis au Concours avec Rachat'),
    ('R','Redouble'),
    ('AJ','Ajournement'),
    ('P','Prolongation'),
    ('F','Abandon'),
    ('FD','Défaillant'),
    ('FT','Transfert'),
    ('M', 'Maladie'),
    ('M1', 'Congé académique (année blanche) pour raisons médicales'),
    ('M2', 'Congé académique (année blanche) pour raisons personnelles'),
    ('M3', 'Congé académique (année blanche) pour raisons personnelles (Covid 19)'),
    ('M4', 'Congé académique (année blanche) pour raisons familiales'),
    ('M5', 'Congé académique'),
    ('N','Non Admis'),
    ('X','Non Inscrit'),
)

OPTIONS_DEPOT=(
    (1,'Oui'),
    (2,'Oui avec des corrections à faire'),
    (3,'Non'),
)

class Soutenance(models.Model):
    groupe = models.OneToOneField(Groupe, on_delete=CASCADE, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    depot_biblio = models.SmallIntegerField(default=3, choices=OPTIONS_DEPOT)
    president = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, related_name='president')
    rapporteur = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, related_name='rapporteur')
    examinateur = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, related_name='examinateur')
    coencadrant = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, related_name='coencadrant')
    assesseur1 = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, related_name='assesseur1')
    assesseur2 = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, related_name='assesseur2')
    invite1 = models.CharField(max_length=100, null=True, blank=True)
    invite2 = models.CharField(max_length=100, null=True, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['groupe'], name="groupe-soutenance")
        ]
    
    def __str__(self):
        return f"{self.groupe} : {self.date}"
    
class Inscription(models.Model):
    etudiant=models.ForeignKey(Etudiant, on_delete=CASCADE, related_name='inscriptions')
    formation=models.ForeignKey(Formation,on_delete=CASCADE)
    groupe=models.ForeignKey(Groupe, null=True, blank=True, on_delete=models.SET_NULL, related_name='inscrits')
    moy=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=0)
    moy_ra=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=0)
    #moy_post_delib=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=0)
    rang=models.PositiveSmallIntegerField(null=True, blank=True, default=0)
    decision_jury=models.CharField(max_length=2,choices=DECISIONS_JURY, null=True, blank=True, default='X')
    # proposition decision_jury qui ne soit pas vue par les étudiants, avant confirmation déliberations
    proposition_decision_jury=models.CharField(max_length=2,choices=DECISIONS_JURY, null=True, blank=True, default='X')
    observation=models.CharField(max_length=100,null=True, blank=True) 
    mention = models.CharField(max_length=2, choices=MENTION, null=True, blank=True, default='X')
    quittance = models.ImageField(upload_to='quittances', null=True, blank=True )

    def nb_modules_a_rattraper(self):
        if self.formation.activation_rattrapage() :
            return Resultat.objects.filter(inscription=self, module__isnull=False, entree_rattrapage=False, module__formation=self.formation, module__formation__isnull=False).annotate(
              inferieur=Case(
                  When(moy_post_delib__lt=F('module__seuil_rattrapage'), then=Value(True)),
                  default=Value(False),
                  output_field=BooleanField()
               )).filter(inferieur=True).count()
        else :
            return 0
    
    def credits_obtenus(self):
        somme=0
        if self.moy_post_delib() >= 10:
            for periode in self.inscription_periodes.all():
                for resultat_ue in periode.resultat_ues.all():
                    for resultat in resultat_ue.resultat_matieres.all():
                        if resultat.moy_post_delib >=resultat.module.note_eliminatoire:
                            somme+=resultat.module.matiere.credit
        else:
            for periode in self.inscription_periodes.all():
                somme+=periode.credits_obtenus()
        return somme
    
    def credits_cursus(self):
        somme=self.credits_obtenus()
        for inscription in Inscription.objects.filter(Q(etudiant=self.etudiant)& 
                                                      Q(formation__programme__ordre__lt=self.formation.programme.ordre)&
                                                      (Q(decision_jury='A')|Q(decision_jury='AR')|Q(decision_jury='SR')|Q(decision_jury='AD'))):
            somme+=inscription.credits_obtenus()
        return somme
    
    def ects_credits(self):
        #cette méthode est obsolète, utiliser credits_obtenus conforme à la réglementation en vigueur
        somme=0
        for periode in self.inscription_periodes.all():
            somme+=periode.ects_credits()
        return somme

    def ects_cursus(self):
        #cette méthode est obsolète, utiliser credits_cursus conforme à la réglementation en vigueur
        somme=self.ects_credits()
        for inscription in Inscription.objects.filter(Q(etudiant=self.etudiant)& 
                                                      Q(formation__programme__ordre__lt=self.formation.programme.ordre)&
                                                      (Q(decision_jury='A')|Q(decision_jury='AR')|Q(decision_jury='SR')|Q(decision_jury='AD'))):
            somme+=inscription.ects_credits()
        return somme
    
    def nb_inscrits(self):
        return self.formation.inscriptions_pour_deliberations().count()
    
    def nb_ne(self):
        nb_ne=0
        for periode in self.inscription_periodes.all():
            nb_ne+=periode.nb_ne()
        return nb_ne
    
    def reset_moy(self):
        self.moy=0.0
        return self.save(update_fields=['moy'])   
    
    def moyenne(self):
        if (self.moy == 0) :
            moy=0
            coef_sum=0
            for inscription_periode in self.inscription_periodes.all():
                for resultat_ue in inscription_periode.resultat_ues.all():
                    moy += resultat_ue.moyenne() * resultat_ue.ue.coef()
                    coef_sum += resultat_ue.ue.coef()
            if coef_sum>0:
                return round(decimal.Decimal(moy / coef_sum),2)
            else:
                return decimal.Decimal(0.0)
        else :
            return self.moy
    
    def moyenne_post_delib(self):
        if self.moy_ra==0:
            moy=0
            coef_sum=0
            for inscription_periode in self.inscription_periodes.all():
                for resultat_ue in inscription_periode.resultat_ues.all():
                    moy += resultat_ue.moyenne_post_delib() * resultat_ue.ue.coef()
                    coef_sum += resultat_ue.ue.coef()
            if coef_sum>0:
                return round(decimal.Decimal(moy / coef_sum),2)
            else:
                return decimal.Decimal(0.0)
        else:
            return self.moy_ra

    def moyenne_finale(self):
        if self.moyenne() < self.moyenne_post_delib() :
            return self.moyenne_post_delib()
        else :
            return self.moyenne()
    
    def reset_moy_ra(self):
        self.moy_ra=0.0
        return self.save(update_fields=['moy_ra']) 

    def moy_post_delib(self):
        # Cette méthode est similaire à la précédente et a été introduite pour garder le code qui se base sur 
        # l'attribut moy_post_delib supprimé
        return self.moyenne_post_delib()
    
    def ranking(self):
        aggregate = Inscription.objects.filter(formation=self.formation, moy__gt=self.moy).exclude(Q(groupe__isnull=True)|Q(decision_jury='X')|Q(decision_jury='FT')).aggregate(ranking=Count('moy'))
        return aggregate['ranking'] + 1

    def moy_globale(self):
        aggregate = Inscription.objects.filter(
                Q(etudiant=self.etudiant) & 
                Q(formation__programme__diplome=self.formation.programme.diplome) &
                Q(formation__programme__ordre__lte=self.formation.programme.ordre) &
                (Q(decision_jury='A')|Q(decision_jury='AR')|Q(decision_jury='SR')|Q(decision_jury='AD'))
            ).aggregate(moy_generale=Avg('moy'))
        if aggregate['moy_generale']:
            return round(aggregate['moy_generale'],2)
        else:
            return 0.0
    
    def ranking_global(self):
        list_inscrits = self.formation.inscriptions_pour_deliberations()
        list_moyennes_globales=[]
        for inscrit in list_inscrits:
            list_moyennes_globales.append(inscrit.moy_globale())
        list_moyennes_globales.sort(reverse=True)
            
        return list_moyennes_globales.index(self.moy_globale()) + 1
    
    def annee_diplome(self):
        diplome_=self.formation.programme.diplome
        ordre_programme_list=Programme.objects.filter(diplome=diplome_).values_list('ordre', flat=True).distinct().order_by('ordre')
        annee_encours=int(self.formation.annee_univ.annee_univ)
        annees_restantes=ordre_programme_list.count()-self.formation.programme.ordre
        if annees_restantes<0:
            annees_restantes=0
        return str(annee_encours+annees_restantes+1)
    
    def refait_en_dette(self):
        inscription_periodes=InscriptionPeriode.objects.filter(inscription=self)
        for inscription_periode in inscription_periodes :
            if inscription_periode.refait_en_dette() :
                return True
        return False
    
    def moyenne_finale_dette(self):
        moy=decimal.Decimal(0.0)
        coef_sum=0
        inscription_periodes=InscriptionPeriode.objects.filter(inscription=self)
        for inscription_periode in inscription_periodes :
            coef_sum += 1
            if inscription_periode.refait_en_dette() :
                moy = moy + decimal.Decimal(inscription_periode.moyenne_finale_dette())
            else :
                moy = moy + decimal.Decimal(inscription_periode.moyenne_finale())
        return round(decimal.Decimal(moy/coef_sum),2)    
    
    def is_inscrit(self):
        return (self.decision_jury == 'C')

    def somme_credits_seminaires(self):
        somme=0
        for seminaire in self.seminaires_suivis.all():
            somme+=seminaire.matiere.credit
        return somme
    
    def all_periodes(self):
        return PeriodeProgramme.objects.filter(programme=self.formation.programme)
    
    def is_admis(self):
        return (self.decision_jury == 'A') or (self.decision_jury == 'AC') or (self.decision_jury == 'AR') or (self.decision_jury == 'SR') or (self.decision_jury == 'AD') or (self.decision_jury == 'CR')
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['etudiant', 'formation'], name="etudiant-formation")
        ]
    
    def __str__(self):
        return f"{self.etudiant} {self.formation}"

class ResidenceUniv(models.Model):
    nom = models.CharField(max_length=50)
    adresse = models.TextField()
    tel = models.CharField(max_length=15, validators=[RegexValidator('^[0-9\+]*$',
                               'Que des chiffres sans espaces et le + pour l\'international')])
    wilaya = models.ForeignKey(Wilaya, on_delete=CASCADE)
    commune = models.ForeignKey(Commune, on_delete=CASCADE)

    def __str__(self):
        return self.nom

# pour ne pas supprimer une quittance du dossier une fois sa préinscription supprimée
@cleanup.ignore
class Preinscription(models.Model):
    
    inscription = models.OneToOneField(Inscription, on_delete=models.CASCADE)
    wilaya_residence=models.ForeignKey(Wilaya, on_delete=models.CASCADE, null=True, blank=True)
    commune_residence=models.ForeignKey(Commune, on_delete=models.CASCADE, null=True, blank=True)
    interne=models.BooleanField(default=False, null=True, blank=True)
    residence_univ=models.ForeignKey(ResidenceUniv, on_delete=models.SET_NULL, null=True, blank=True)
    adresse_principale=models.TextField(null=True, blank=True)
    photo=models.ImageField(upload_to='tmp',null=True,blank=True, validators=[validate_image])
    quittance=models.ImageField(upload_to='tmp',null=True,blank=True, validators=[validate_image])
    tel=models.CharField(max_length=15, validators=[RegexValidator('^[0-9\+]*$',
                               'Que des chiffres sans espaces et le + pour l\'international')], null=True, blank=True)
    numero_securite_sociale=models.CharField(max_length=15, validators=[RegexValidator('^[0-9\+]*$',
                               'Que des chiffres sans espaces')], null=True, blank=True)

    def __str__(self):
        return str(self.inscription)


    # i need to delete the temp uploaded file from the file system when i delete this model      
    # from the database
#     def delete(self, using=None):
#         # i ensure that the database record is deleted first before deleting the uploaded 
#         # file from the filesystem.
#         super(Preinscription, self).delete(using)
#         self.photo.close()
#         #self.photo.storage.delete(name_photo)
#         self.photo.delete()
#         self.quittance.close()
#         #self.quittance.storage.delete(name_quittance)    
#         self.quittance.delete()
   
class ReservationPlaceEtudiant(models.Model):
    inscription = models.ForeignKey(Inscription, on_delete=CASCADE)
    seance = models.ForeignKey(Seance, on_delete=CASCADE)
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['inscription', 'seance'], name="reservation_place_etudiant"),
            models.UniqueConstraint(fields=['seance', 'place'], name="seance_place")
        ]
    
    def __str__(self):
        return f"{self.inscription} : {self.seance.activite.module.matiere.code} --> {self.place.salle.code} ({self.place})"

class SurveillanceEnseignant(models.Model):
    enseignant = models.ForeignKey(Enseignant, on_delete=CASCADE)
    seance = models.ForeignKey(Seance, on_delete=CASCADE)
    salle = models.ForeignKey(Salle, on_delete=CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['enseignant', 'seance'], name="surveillance_enseignant")
        ]
    
    def __str__(self):
        return f"{self.enseignant} : {self.seance} --> {self.salle.code}"

    
class InscriptionPeriode(models.Model):
    inscription=models.ForeignKey(Inscription, on_delete=CASCADE, related_name='inscription_periodes')
    # TODO supprimer cet attribut et le remplacer par periodepgm qui suit
    periode=models.ForeignKey(Periode, on_delete=models.SET_NULL, null=True, blank=True)
    periodepgm=models.ForeignKey(PeriodeProgramme, on_delete=CASCADE, null=True, blank=True)
    groupe=models.ForeignKey(Groupe, on_delete=models.SET_NULL, null=True, blank=True, related_name='inscrits_periode')
    moy=models.DecimalField(max_digits=4, decimal_places=2, default=0)
    moy_importee=models.DecimalField(max_digits=4, decimal_places=2, default=0)
    moy_post_delib_importee=models.DecimalField(max_digits=4, decimal_places=2, default=0)
    is_moy_importee=models.BooleanField(default=False)
    ne=models.PositiveSmallIntegerField(default=0)
    rang=models.PositiveSmallIntegerField(null=True, blank=True, default=0)
    
    def pv_existe(self):
        return self.inscription.formation.pv_existe(self.periodepgm.periode)

    def pv_final_existe(self):
        if PV.objects.filter(formation=self.inscription.formation, annuel=True):
            return True
        else:
            return PV.objects.filter(formation=self.inscription.formation, periode=self.periodepgm.periode, signature=True).count() > 0

    
    def nb_matieres(self):
        cpt=0
        for ue in self.resultat_ues.all():
            cpt+= ue.resultat_matieres.all().count()
        return cpt
    
    def nb_ne_parmis_matieres(self, matieres_moyenne):
        #Filtrer matieres_moyenne pour ne garder que les matières suivies par le groupe durant ce semestre, car on peut avoir le même module suivi durant le second semestre
        matieres_suivies_moyenne=[]
        for module_suivi_ in self.groupe.modules_suivis.filter(module__periode=self.periodepgm, module__matiere__code__in=matieres_moyenne):
            matieres_suivies_moyenne.append(module_suivi_.module.matiere.code)
        aggregate=Resultat.objects.filter(inscription=self.inscription, module__matiere__code__in=matieres_suivies_moyenne).aggregate(ne=Count('inscription', filter=Q(moy_post_delib__lt=ExpressionWrapper(F('module__note_eliminatoire'), output_field=DecimalField()))))
        return aggregate['ne']

    def nb_ne(self):
        nb_=0
        for ue_ in self.resultat_ues.all():
            for resultat_ in ue_.resultat_matieres.all():
                if resultat_.moy_post_delib:
                    if resultat_.moy_post_delib < resultat_.module.note_eliminatoire:
                        nb_+=1
                else:
                    nb_+=1 
        return nb_

    def moyenne(self):
        if self.is_moy_importee :
            return self.moy_importee
        moy=0
        coef_sum=0
        for resultat_ue in self.resultat_ues.all():
            moy += resultat_ue.moyenne() * resultat_ue.ue.coef()
            coef_sum += resultat_ue.ue.coef()
        if coef_sum!=0:
            return round(decimal.Decimal(moy / coef_sum),2)
        else:
            return decimal.Decimal(0.0)

    def moyenne_post_delib(self):
        if self.is_moy_importee or self.moy_post_delib_importee :
            return self.moy_post_delib_importee
        moy=0
        coef_sum=0
        for resultat_ue in self.resultat_ues.all():
            moy += resultat_ue.moyenne_post_delib() * resultat_ue.ue.coef()
            coef_sum += resultat_ue.ue.coef()
        if coef_sum!=0:
            return round(decimal.Decimal(moy / coef_sum),2)
        else:
            return decimal.Decimal(0.0)

    def moy_post_delib(self):
        # Cette méthode est similaire à la précédente et a été introduite pour garder le code qui se base sur 
        # l'attribut moy_post_delib supprimé
        return self.moyenne_post_delib()

    def moyenne_provisoire(self):
        if self.is_moy_importee :
            return self.moy_importee
        moy=0
        coef_sum=0
        for resultat_ue in self.resultat_ues.all():
            # on ne compte que les matières suivies dans le semestre prévu dans le programme
            coef = resultat_ue.coef_provisoire()
            moy += resultat_ue.moyenne_provisoire() * coef
            coef_sum += coef
        if coef_sum != 0:
            return round(decimal.Decimal(moy / coef_sum),2)
        else :
            return decimal.Decimal(0.0)


    def ranking(self):
        aggregate = InscriptionPeriode.objects.filter(inscription__formation=self.inscription.formation, periodepgm=self.periodepgm, moy__gt=self.moy).exclude(Q(groupe__isnull=True)|Q(inscription__decision_jury='X')|Q(inscription__decision_jury='FT')).aggregate(ranking=Count('moy'))
        return aggregate['ranking'] + 1

    def credits_requis(self):
        somme=0
        for ue in self.resultat_ues.all():
            somme+=ue.credits_requis()
        return somme   
        
    def credits_obtenus(self):
        somme=0
        if self.moy_post_delib() >= 10 or self.moy_importee >=10:
            for resultat_ue in self.resultat_ues.all():
                for resultat in resultat_ue.resultat_matieres.all():
                    if resultat.moy_post_delib>=resultat.module.note_eliminatoire:
                        somme+=resultat.module.matiere.credit
        else:
            for resultat_ue in self.resultat_ues.all():
                somme+=resultat_ue.credits_obtenus()
        return somme

    def ects_credits(self):
        somme=0
        for resultat_ue in self.resultat_ues.all():
            for resultat in resultat_ue.resultat_matieres.all():
                somme+=resultat.ects_credits()
        return somme

    def moyenne_finale(self):
        if self.moyenne() < self.moyenne_post_delib() :
            return self.moyenne_post_delib()
        else :
            return self.moyenne()
    
    def refait_en_dette(self):
        resultat_ues=ResultatUE.objects.filter(inscription_periode=self)
        for resultat_ue in resultat_ues :
            if resultat_ue.refait_en_dette() :
                return True
        return False
    
    def moyenne_finale_dette(self):
        moy=decimal.Decimal(0.0)
        coef_sum=0
        resultat_ues=ResultatUE.objects.filter(inscription_periode=self)
        for resultat_ue in resultat_ues :
            coef_sum += resultat_ue.ue.coef()
            if resultat_ue.refait_en_dette() :
                moy = moy + decimal.Decimal(resultat_ue.moyenne_finale_dette()) * resultat_ue.ue.coef()
            else :
                moy = moy + decimal.Decimal(resultat_ue.moyenne_finale()) * resultat_ue.ue.coef()
        return round(decimal.Decimal(moy/coef_sum),2)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['inscription', 'periode'], name="inscription-periode")
        ]
    
    def __str__(self):
        return f"{self.inscription} {self.periodepgm}"

class ResultatUE(models.Model):
    ue=models.ForeignKey(UE, on_delete=models.SET_NULL, null=True, blank=True)
    inscription_periode=models.ForeignKey(InscriptionPeriode, on_delete=CASCADE, related_name='resultat_ues')
    #TODO à supprimer c'est un champ qu'on recalcule au besoin
    moy=models.DecimalField(max_digits=4, decimal_places=2, default=0)
    #moy_post_delib=models.DecimalField(max_digits=4, decimal_places=2, default=0)
    
    def credits_requis(self):
        somme=0
        for matiere in self.ue.matieres.all():
            somme+=matiere.credit
        return somme   
        
    def credits_obtenus(self):
        somme=0

        if self.moy_post_delib() >= 10:
            
            for resultat in self.resultat_matieres.all():
                if resultat.moy_post_delib>=resultat.module.note_eliminatoire:
                    somme+=resultat.module.matiere.credit
        else:
            for resultat in self.resultat_matieres.all():
                somme+=resultat.credits_obtenus()
        return somme

    def moyenne(self):
        moy=0
        coef_sum=0
        for resultat in self.resultat_matieres.all():
            if not resultat.entree_rattrapage :
                if resultat.moy:
                    moy = moy + resultat.moy * resultat.module.matiere.coef
            else :
                if resultat.module.activation_max_moy_normale_et_rattrapage :
                    moy = moy + max(resultat.moy_rattrapage, resultat.moy) * resultat.module.matiere.coef
                else :
                    moy = moy + (resultat.moy * resultat.module.ponderation_moy + resultat.moy_rattrapage * resultat.module.ponderation_moy_rattrapage) * resultat.module.matiere.coef
            coef_sum = coef_sum + resultat.module.matiere.coef
        if coef_sum != 0:
            return round(decimal.Decimal(moy / coef_sum),2)
        else:
            return decimal.Decimal(0.0)

    def moyenne_post_delib(self):
        moy=0
        coef_sum=0
        for resultat in self.resultat_matieres.all():
            if resultat.moy_post_delib:
                moy = moy + resultat.moy_post_delib * resultat.module.matiere.coef
            coef_sum = coef_sum + resultat.module.matiere.coef
        if coef_sum != 0:
            return round(decimal.Decimal(moy / coef_sum),2)
        else:
            return decimal.Decimal(0.0)
    
    def moy_post_delib(self):
        # Cette méthode est similaire à la précédente et a été introduite pour garder le code qui se base sur 
        # l'attribut moy_post_delib supprimé
        return self.moyenne_post_delib()
        
    def moyenne_provisoire(self):
        moy=0
        coef_sum=0
        for resultat in self.resultat_matieres.all():
            if resultat.module.periode == self.inscription_periode.periodepgm:
                # module suivi au semestre prévu dans le programme
                moy += resultat.moy * resultat.module.matiere.coef
                coef_sum += resultat.module.matiere.coef
        if coef_sum!=0:
            return round(decimal.Decimal(moy / coef_sum),2)
        else:
            return decimal.Decimal(0.0)
        
    def coef_provisoire(self):
        coef_sum=0
        for resultat in self.resultat_matieres.all():
            if resultat.module.periode == self.inscription_periode.periodepgm:
                # module suivi au semestre prévu dans le programme
                coef_sum += resultat.module.matiere.coef
        return coef_sum
    
    def moyenne_finale(self):
        if self.moyenne() < self.moyenne_post_delib() :
            return self.moyenne_post_delib()
        else :
            return self.moyenne()
            
    def refait_en_dette(self):
        resultats=Resultat.objects.filter(resultat_ue=self)
        for resultat in resultats :
            if resultat.refait_en_dette() :
                return True
        return False
    
    def moyenne_finale_dette(self):
        moy=decimal.Decimal(0.0)
        coef_sum=0
        resultats=Resultat.objects.filter(resultat_ue=self)
        for resultat in resultats :
            coef_sum += resultat.module.matiere.coef
            if resultat.refait_en_dette() :
                moy = moy + decimal.Decimal(resultat.moyenne_finale_dette()) * resultat.module.matiere.coef
            else :
                moy = moy + decimal.Decimal(resultat.moyenne_finale()) * resultat.module.matiere.coef
        return round(moy/coef_sum,2)
            
    def __str__(self):
        return f"{self.ue} {self.inscription_periode}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ue', 'inscription_periode'], name="ue-inscription-periode")
        ]
    
STATUT_DETTE=(
    ('X','Non commencée'),
    ('C','En cours'),
    ('T','Terminée'),
)
    
class Resultat(models.Model):
    '''
    Résultats d'un module pour un étudiant
    '''
    ECTS=(
        ('A','Excellent: 10%'),
        ('B','Très bien: 25%'),
        ('C','Bien: 30%'),
        ('D','Satisfaisant; 25%'),
        ('E','Passable: 10%'),
        ('Fx','Insuffisant'),
        ('F','Insuffisant'),
    )

    module=models.ForeignKey(Module, on_delete=CASCADE, null=True, blank=True)
    inscription=models.ForeignKey(Inscription, on_delete=CASCADE, null=True, blank=True, related_name='resultats')
    
    moy=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=0)
    moy_rattrapage=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=0)
    # cet attribut devrait disparaître vu que calcul_ects se base sur moy_post_delib
    moy_post_delib=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=0)
    ects=models.CharField(max_length=2, choices = ECTS, default='F', null=True, blank=True)
    # TODO à supprimer on garde uniquement esct_post_delib
    #ects_post_delib=models.CharField(max_length=2, choices = ECTS, default = 'F', null=True, blank=True)
    # pour gérer les redoublants avec des modules acquis, pour éviter de les faire apparaître sur les listes de présence
    acquis=models.BooleanField(default=False)
    entree_rattrapage=models.BooleanField(default=False)
    resultat_ue=models.ForeignKey(ResultatUE, on_delete=CASCADE, null=True, blank=True, related_name='resultat_matieres')
    dette=models.BooleanField(default=False)
    etat_dette=models.CharField(max_length=2, choices = STATUT_DETTE, default='X', null=True, blank=True)
    ancien_resultat=models.ForeignKey('Resultat', on_delete=models.SET_NULL, null=True, blank=True, related_name='nouveaux_resultats')
    resultat_en_cours=models.ForeignKey('Resultat', on_delete=models.SET_NULL, null=True, blank=True, related_name='ancien_resultat_du_resultat_en_cours')
    
    def credits_obtenus(self):
        if self.moy >= 10:
            return self.module.matiere.credit
        else:
            return 0
        
    def ects_credits(self):
        # cette méthode est obsolète, il faut considérer credits_obtenus qui reflète la réglementation en vigueur
        if self.moy >= self.module.note_eliminatoire:
            return self.module.matiere.credit
        else:
            return 0


    def coef_provisoire(self):
        if self.module.periode == self.resultat_ue.inscription_periode.periodepgm:
            return self.module.matiere.coef
        else:
            return 0
                
    def ranking(self):
        aggregate = Resultat.objects.filter(module=self.module, moy__gt=self.moy).aggregate(ranking=Count('moy'))
        return aggregate['ranking'] + 1
    
    def moyenne(self):
        moy=0
        for note in self.notes.all():
            moy += note.note * note.evaluation.ponderation
        return round(moy,2)

    def moyenne_rattrapage(self):
        moy_rattrapage=0
        for note in self.notes.all():
            moy_rattrapage += note.note * note.evaluation.ponderation_rattrapage
        return round(moy_rattrapage,2)
    
    def moyenne_finale(self):
        if not self.entree_rattrapage :
            return self.moy
        else :
            if self.module.activation_max_moy_normale_et_rattrapage :
                return max(self.moy_rattrapage, self.moy)
            else :
                return round(self.moy * self.module.ponderation_moy + self.moy_rattrapage * self.module.ponderation_moy_rattrapage,2)
        
    
    def rachete(self):
        if not self.entree_rattrapage :
            return (self.moy < self.moy_post_delib)
        else :
            if self.module.activation_max_moy_normale_et_rattrapage :
                return (max(self.moy_rattrapage, self.moy) < self.moy_post_delib)
            else :
                return ((self.moy * self.module.ponderation_moy + self.moy_rattrapage * self.module.ponderation_moy_rattrapage) < self.moy_post_delib)
        
        
    def activation_rattrapage(self):
        return self.module.activation_rattrapage()

    def activation_dettes(self):
        return self.module.activation_dettes()

    def calcul_ects(self):
        ects='F'
        # affecter ECTS=F si non acquis
        if not self.moy_post_delib:
            ects='F'
        elif self.moy_post_delib < self.module.note_eliminatoire:
            ects='F'
        elif self.moy_post_delib >= self.module.note_eliminatoire and self.moy_post_delib < 10.0:
            #mdoule non acquis avec une moyenne > note éliminatoire
            #ects='Fx'
            ects='F' # on garde F pour tout echec car la note > note_eliminatoire risque d'être trop faible pour avoir Fx
        else:
            # mettre ECST à jour selon ranking dans le module
            nb_inscrits_module=Resultat.objects.filter(module=self.module, moy_post_delib__gte=10.0).count()
            rang=self.ranking()
            if  rang <= nb_inscrits_module * decimal.Decimal(0.10):
                ects='A'
            elif rang <= nb_inscrits_module * decimal.Decimal(0.10 + 0.25):
                ects='B'
            elif rang <= nb_inscrits_module * decimal.Decimal(0.10 + 0.25 + 0.30):
                ects='C'
            elif rang <= nb_inscrits_module * decimal.Decimal(0.10 + 0.25 + 0.30 + 0.25):
                ects='D'
            else :
                ects='E'
        return ects
                    
    def nouveaux_resultats_dette(self):
        return Resultat.objects.filter(ancien_resultat=self).order_by('module__formation__annee_univ__annee_univ')
    
    def refait_en_dette(self):
        return (self.dette and self.etat_dette=='T' and self.resultat_en_cours)
    
    def moyenne_finale_dette(self):
        return self.resultat_en_cours.moyenne_finale()

    def __str__(self):
        return f"{self.inscription.etudiant} {self.module}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['inscription', 'module'], name="inscription-module")
        ]
    
    
class Note(models.Model):
    '''
    Une note correspondant à une évaluation prévue dans un module
    '''
    note=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=0)
    note_post_delib=models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=0)
    evaluation=models.ForeignKey(Evaluation, on_delete=CASCADE, null=True, blank=True)
    resultat=models.ForeignKey(Resultat, on_delete=CASCADE, null=True, blank=True, related_name='notes')
    def __str__(self):
        return f"{self.resultat} {self.evaluation} {self.note}"
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['evaluation', 'resultat'], name="evaluation-resultat")
        ]

class GoogleCalendar(models.Model):
    code = models.CharField(max_length=20)
    calendarId = models.CharField(max_length=100)

    def __str__(self):
        return self.code
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code'], name="gcal-code")
        ]
    
TYPE_ORGANISME=(
    ('R','Laboratoire / Centre de Recherche'),
    ('E', 'Entreprise'),
    ('A','Administration'),
)

NATURE_ORGANISME=(
    ('P','Publique'),
    ('PR', 'Privée'),
    ('M','Mixte'),
)

STATUT_ORGANISME=(
    ('SPA','Société Par Actions'),
    ('SARL', 'Société Anonyme à Résponsabilité Limitée'),
    ('EURL','Entreprise Unanime à Résponsabilité Limitée'),
)

TAILLE_ORGANISME=(
    ('10','Moins de 10 salariés'),
    ('100', 'Entre 10 et 100 salariés'),
    ('500','Entre 100 et 500 salariés'),
    ('1000','Plus de 500 salariés'),
)

SECTEUR_ORGANISME=(
    ('S','Services'),
    ('C', 'Commercial'),
    ('I','Industriel'),
)

class Organisme(models.Model):
    sigle = models.CharField(max_length=50, primary_key=True, validators=[RegexValidator('^[A-Z_\-\&\@\ 0-9]+$',
                               'Saisir en majuscule')])
    nom = models.CharField(max_length=200)
    adresse = models.TextField(null=True, blank=True)
    pays=models.ForeignKey(Pays, on_delete=CASCADE, default='DZ')
    type=models.CharField(max_length=2, choices=TYPE_ORGANISME)
    nature=models.CharField(max_length=2, choices=NATURE_ORGANISME, null=True, blank=True)
    statut=models.CharField(max_length=5, choices=STATUT_ORGANISME, null=True, blank=True)
    taille=models.CharField(max_length=5, choices=TAILLE_ORGANISME, null=True, blank=True) 
    secteur=models.CharField(max_length=2, choices=SECTEUR_ORGANISME, null=True, blank=True)
    interne=models.BooleanField(default=False, verbose_name="Organisme interne au sein de l'établissement (laboratoire, service, ..)")
    
    def __str__(self):
        return f"{self.sigle} : {self.nom}"

#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['sigle'], name="sigle-organisme"),
#         ]
    
STATUT_VALIDATION=(
    ('C', 'Contrôle - Non visible'),
    ('S', 'Soumis - Visible'),
    ('W', 'Validation en cours'),
    ('RR', 'Révision Requise'),
    ('RT', 'Révision Terminée'),
    ('LR', 'Levée de Réserve'),
    ('V', 'Validé'),
    ('N', 'Rejeté'),
)

TYPE_STAGE=(
        ('P', 'PFE: Projet de fin d\'études'),
        ('M', 'Master'),
        ('D', 'Doctorat')
    )
OPTION_MOYENS=(
        ('ESI','A la charge de l\'école'),
        ('ORG','A la charge de l\'organisme d\'accueil')
    )
class PFE(models.Model):
    type = models.CharField(max_length=2, choices=TYPE_STAGE, default='P')
    specialites = models.ManyToManyField(Specialite)
    organisme = models.ForeignKey(Organisme, on_delete=models.SET_NULL, null=True)
    groupe = models.OneToOneField(Groupe, on_delete=models.SET_NULL, null=True, blank=True)
    coencadrants = models.ManyToManyField(Enseignant, blank=True, related_name='pfes')
    promoteur = models.TextField(max_length=100, null=True)
    email_promoteur = models.EmailField(null=True)
    tel_promoteur = models.CharField(max_length=20, null=True, blank=True, validators=[RegexValidator('^[0-9\+]*$',
                               'Que des chiffres sans espaces et le + pour l\'international')])
    intitule = models.TextField(null=True)
    resume = models.TextField(null=True)
    keywords = models.TextField(null=True)
    objectifs = models.TextField(null=True)
    resultats_attendus = models.TextField(null=True)
    antecedents = models.TextField(null=True, blank=True)
    moyens_informatiques = models.CharField(max_length=3, choices=OPTION_MOYENS, null=True, blank=True)
    echeancier = models.TextField(null=True)
    bibliographie = models.TextField(null=True, blank=True)
    statut_validation = models.CharField(max_length=2, choices=STATUT_VALIDATION, default='C')
    reponse_aux_experts = models.TextField(null=True, blank=True)
    reserve_pour = models.ManyToManyField(Inscription, related_name='reservations_pfe')
    projet_recherche = models.CharField(max_length=200, null=True, blank=True)
    # cet attribut sert à bloquer les notifications après la validation du sujet suite à de nouvelles modifications
    notification = models.BooleanField(default=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['groupe'], name="groupe-pfe"),
        ]
        
    def nb_avis(self):
        return Validation.objects.filter(pfe=self.id).exclude(avis='X').count()

    def nb_avis_favorables(self) :
        return Validation.objects.filter(pfe=self, avis="V").count()
    
    def nb_avis_favorables_avec_reserves_mineures(self) :
        return Validation.objects.filter(pfe=self, avis="SR").count()
    
    def nb_avis_favorables_avec_reserves_majeures(self) :
        return Validation.objects.filter(pfe=self, avis="MR").count()
    
    def nb_avis_defavorables(self) :
        return Validation.objects.filter(pfe=self, avis="N").count()
    
    def nb_avis_non_renseignes(self) :
        return Validation.objects.filter(pfe=self, avis="X").count()
    
    def get_these(self):
        these_qs= These.objects.filter(sujet=self)
        if these_qs.exists() :
            return these_qs.first()
        else :
            return These.objects.none()
    
    def __str__(self):
        if self.intitule:
            return f"{self.id}: {self.intitule}"
        return str(self.id)

OPTIONS_VALIDATION=(
    ('V', 'Avis favorable'),
    ('SR', 'Avis favorable avec réserves mineures'),
    ('MR', 'Avis favorable avec réserves majeures'),
    ('N', 'Avis défavorable'),
    ('X','Non Renseigné'),
)

class Validation(models.Model):
    pfe = models.ForeignKey(PFE, on_delete=CASCADE, related_name='validations')
    expert = models.ForeignKey(Enseignant, on_delete=CASCADE)
    avis = models.CharField(max_length=2, choices=OPTIONS_VALIDATION, default='X')
    commentaire=models.TextField(null=True, blank=True)
    debut=models.DateField(null=True, blank=True)
    fin=models.DateField(null=True)
    
    def __str__(self):
        return f"{self.pfe} - {self.expert} - {dict(OPTIONS_VALIDATION).get(self.avis)}"
#     class Meta:
#         constraints = [
#             models.UniqueConstraint(fields=['pfe','expert', 'avis'], name="pfe-expert-avis")
#         ]
 
class Equipe(models.Model):

    pfe=models.OneToOneField(PFE, on_delete=CASCADE, related_name='equipe', null=True)
    inscriptions=models.ManyToManyField(Inscription, related_name='equipes')
        
    def __str__(self):
        return " - ".join(str(i) for i in [self.pfe.intitule, *self.inscriptions.all()])

class Question(models.Model):
    code=models.CharField(max_length=3, primary_key=True)
    intitule=models.CharField(max_length=80)   
    projet_na=models.BooleanField(default=False)
    cours_na=models.BooleanField(default=False)         
    def __str__(self):
        return f"{self.code} : {self.intitule}"

class Feedback(models.Model):
    
    module=models.ForeignKey(Module, on_delete=CASCADE, related_name='feedbacks')
    inscription=models.ForeignKey(Inscription, on_delete=CASCADE, null=True, blank=True)
    comment=models.TextField(null=True, blank=True)
    show=models.BooleanField(default=True)
    def __str__(self):
#         if self.resultat:
#             return str(self.module.matiere.code) +' by '+str(self.resultat.etudiant)
#         else : 
        return f"{self.module.matiere.code} by anonymous"

class Reponse(models.Model):
    REPONSE=(
        ('++','Tout à fait d\'accord'),
        ('+','D\'accord'),
        ('-','Pas d\'accord'),
        ('--','En total désaccord'),
    )
    feedback=models.ForeignKey(Feedback, on_delete=CASCADE, related_name='reponses')
    question=models.ForeignKey(Question, on_delete=CASCADE)
    reponse=models.CharField(max_length=2, choices=REPONSE)
    def __str__(self):
        return f"{self.question} {self.feedback}"

class CompetenceFamily(models.Model):
    code=models.CharField(max_length=5, primary_key = True)
    intitule = models.CharField(max_length = 120)
    def __str__(self):
        return f"{self.code} : {self.intitule}"

class Competence(models.Model):
    code = models.CharField(max_length = 10)
    competence_family = models.ForeignKey(CompetenceFamily, on_delete = CASCADE, null = True, related_name='competences')
    intitule = models.CharField(max_length = 160)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code', 'competence_family'], name="competence-competence-family")
        ]
    def __str__(self):
        return f"{self.code} : {self.intitule}"

class CompetenceElement(models.Model):

    TYPE=(
        ('MOD','Modélisation'),
        ('MET','Méthodologie'),
        ('TEC','Technique'),
        ('OPE','Opérationnel'),        
    )

    code = models.CharField(max_length = 10)
    competence = models.ForeignKey(Competence, on_delete=CASCADE, null=True, related_name='competence_elements')
    intitule = models.CharField(max_length = 160)
    type = models.CharField(max_length = 5, choices = TYPE)
    objectif = models.TextField(null=True, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code', 'competence'], name="competence-element-competence")
        ]
    def __str__(self):
        return f"{self.code} : {self.intitule}"
    
class MatiereCompetenceElement(models.Model):
    NIVEAU=(
        ('B','Base'),
        ('I','Intermédiaire'),
        ('A','Avancé'),
    )
    matiere = models.ForeignKey(Matiere, on_delete=CASCADE, null=True)
    competence_element = models.ForeignKey(CompetenceElement, on_delete=CASCADE, null=True, related_name='competence_elements')
    niveau = models.CharField(max_length = 1, choices = NIVEAU)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['matiere', 'competence_element'], name="matiere-competence-element")
        ]
        
        indexes = [models.Index(fields=['matiere','competence_element'])]
        
    def __str__(self):
        return f"{self.matiere} : {self.competence_element}"
    
class Semainier(models.Model):
    SEMAINE=(
        (1, 'Semaine 1'),
        (2, 'Semaine 2'),
        (3, 'Semaine 3'),
        (4, 'Semaine 4'),
        (5, 'Semaine 5'),
        (6, 'Semaine 6'),
        (7, 'Semaine 7'),
        (8, 'Semaine 8'),
        (9, 'Semaine 9'),
        (10, 'Semaine 10'),
        (11, 'Semaine 11'),
        (12, 'Semaine 12'),
        (13, 'Semaine 13'),
        (14, 'Semaine 14'),
        (15, 'Semaine 15')
    )    
    module=models.ForeignKey(Module, on_delete=CASCADE)
    semaine=models.PositiveSmallIntegerField(choices=SEMAINE)
    activite_cours=models.CharField(max_length=255, null=True, blank=True)
    activite_dirigee=models.TextField(null=True, blank=True)
    observation=models.CharField(max_length=255, null=True, blank=True)
    objectifs=models.CharField(max_length=255, null=True, blank=True)
    matiere_competence_element=models.ForeignKey(MatiereCompetenceElement, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['module', 'semaine'], name="module-semaine")
        ]
    def __str__(self):
        return f"{self.module.matiere.code} : {self.semaine}"
    
class EvaluationCompetenceElement(models.Model):
    evaluation=models.ForeignKey(Evaluation, on_delete=CASCADE, related_name='competence_elements')
    competence_element=models.ForeignKey(CompetenceElement, on_delete=CASCADE)
    commune_au_groupe=models.BooleanField(default=False)
    ponderation=models.DecimalField(max_digits=4, decimal_places=2, default=0)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['evaluation', 'competence_element'], name="evaluation_competence_element")
        ]
    def __str__(self):
        return f"{self.evaluation.type} : {self.competence_element.intitule}"

class NoteCompetenceElement(models.Model):
    evaluation_competence_element=models.ForeignKey(EvaluationCompetenceElement, on_delete=CASCADE, null=True, blank=True)
    note_globale=models.ForeignKey(Note, on_delete=CASCADE, null=True, blank=True) #Note globale à laquelle contribue cette note d'un élément de compétence
    valeur=models.DecimalField(max_digits=6, decimal_places=4, default=0) # pour obtenir les points attribués: valeur * eval_competence_element.ponderation * 20
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['evaluation_competence_element','note_globale'], name="evaluation_competence_element_note_globale")
        ]

NOTES_PAR_DEFAUT=(
    ('A', 18),
    ('B', 15),
    ('C', 13),
    ('D', 10),
    ('E', 8),
    ('F', 5),
)    

class CompetenceEvalConfig(models.Model):  
    evaluation=models.OneToOneField(Evaluation, on_delete=CASCADE, null=True, related_name='competence_eval_config')
    A=models.DecimalField(max_digits=4, decimal_places=2, default=dict(NOTES_PAR_DEFAUT).get('A'))
    B=models.DecimalField(max_digits=4, decimal_places=2, default=dict(NOTES_PAR_DEFAUT).get('B'))
    C=models.DecimalField(max_digits=4, decimal_places=2, default=dict(NOTES_PAR_DEFAUT).get('C'))
    D=models.DecimalField(max_digits=4, decimal_places=2, default=dict(NOTES_PAR_DEFAUT).get('D'))
    E=models.DecimalField(max_digits=4, decimal_places=2, default=dict(NOTES_PAR_DEFAUT).get('E'))
    F=models.DecimalField(max_digits=4, decimal_places=2, default=dict(NOTES_PAR_DEFAUT).get('F'))
    def __str__(self):
        return str(self.evaluation)
    
class Trace(models.Model):
    source=models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_faites')
    source_text=models.CharField(max_length=255, null=True, blank=True)
    cible=models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_recues')
    cible_text=models.CharField(max_length=255, null=True, blank=True)
    action=models.TextField()
    date_time= models.DateTimeField(default=timezone.now)
    seen=models.BooleanField(default=False, verbose_name="Vu par la cible")

    def is_seen_then_toggle(self):
        was_seen_before=self.seen
        if not was_seen_before :
            self.seen=True
            self.save(update_fields=['seen'])
        return was_seen_before

class Doctorant(models.Model):
    etudiant = models.OneToOneField(Etudiant, on_delete=models.SET_NULL, null=True, blank=True)
    enseignant = models.OneToOneField(Enseignant, on_delete=models.SET_NULL, null=True, blank=True)
    organisme=models.ForeignKey(Organisme, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctorants')

    def __str__(self):
        if self.enseignant :
            return f"{self.enseignant.nom} {self.enseignant.prenom}"
        if self.etudiant :
            return f"{self.etudiant.nom} {self.etudiant.prenom}"
        return "-"
    
    def nom(self):
        if self.enseignant :
            return self.enseignant.nom
        if self.etudiant :
            return self.etudiant.nom
        return "-"

    def prenom(self):
        if self.enseignant :
            return str(self.enseignant.prenom)
        if self.etudiant :
            return str(self.etudiant.prenom)
        return "-"
    
    def user(self):
        if self.enseignant :
            if self.enseignant.user :
                return self.enseignant.user
        if self.etudiant :
            if self.etudiant.user :
                return self.etudiant.user
        return User.objects.none()
    
    def annee_inscription(self):
        if self.etudiant :
            inscriptions_qs=Inscription.objects.filter(etudiant=self.etudiant, formation__programme__doctorat=True).order_by('-formation__programme__ordre')
            if inscriptions_qs.exists() :
                return str(inscriptions_qs.first().formation)
        return "/"
    
    def somme_credits_seminaires(self):
        somme=0
        if self.etudiant:
            inscriptions_qs=Inscription.objects.filter(etudiant=self.etudiant, formation__programme__doctorat=True)
            for inscription in inscriptions_qs:
                somme=somme+inscription.somme_credits_seminaires()
        return somme


TYPE_PROJET=(
        ('PRFU', 'Projet de Recherche en Formation Universitaire'),
        ('PNR', 'Projet National de Recherche'),
        ('TASSILI', 'TASSILI : Coopération Algérie/France'),
        ('Autre', 'Autre')
    )
          
class Projet(models.Model):
    code = models.CharField(null=True, blank=True, max_length=50)
    type=models.CharField(max_length=20,choices=TYPE_PROJET, blank=True)
    titre = models.CharField(null=True, max_length=300)
    chef = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, related_name='projets_en_chef')
    chef_externe=models.CharField(max_length=200, null=True, blank=True, verbose_name="Chef externe (s'il y a lieu)")
    membres =models.ManyToManyField(Enseignant, blank=True, related_name='projets_en_membre', verbose_name="Membres enseignants")
    membres_doctorants=models.ManyToManyField(Doctorant, blank=True, related_name='projets_en_membre', verbose_name="Membres doctorants")
    membres_externes=models.TextField(null=True,blank=True, verbose_name="Membres externes")
    organisme=models.ForeignKey('Organisme', on_delete=models.SET_NULL, null=True, blank=True, related_name='projets')
    annee_debut=models.ForeignKey(AnneeUniv ,related_name='projets_commences' , null= True, blank=True, on_delete=models.SET_NULL)
    annee_fin=models.ForeignKey(AnneeUniv ,related_name='projets_termines' , null= True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return str(self.titre)

class These(models.Model):
    sujet = models.OneToOneField(PFE,null= True, blank=True, on_delete= models.SET_NULL)
    directeur = models.ForeignKey(Enseignant, related_name='directions',on_delete= models.SET_NULL, null = True, blank = True)
    directeur_externe=models.CharField(max_length=300, null=True, blank=True)
    codirecteur = models.ForeignKey(Enseignant,related_name='codirections' , null= True, blank=True, on_delete=models.SET_NULL)
    codirecteur_externe=models.CharField(max_length=300, null=True, blank=True)
    doctorant = models.OneToOneField(Doctorant, related_name='these' , null= True, blank=True, on_delete=models.SET_NULL)
    annee_univ=models.ForeignKey(AnneeUniv ,related_name='theses' , null= True, blank=True, on_delete=models.SET_NULL)
    projet=models.ForeignKey(Projet, related_name='theses',on_delete= models.SET_NULL, null = True, blank = True)
    
    def __str__(self):
        if self.sujet :
            return f"{self.id} {self.sujet.intitule}"
        return f"{self.id} : None"
'''        
class ChoixThese(models.Model):
    
    doctorant = models.ForeignKey(Doctorant, on_delete=models.SET_NULL, null=True)    
    sujet = models.ForeignKey(These,on_delete=models.SET_NULL, null=True)
    preference = models.IntegerField( default=0, null=True)
    
    def __str__(self):
        return self.doctorant # + '    ' + self.sujet
'''
       
class OptionCritere(models.Model):
    ordre=models.IntegerField(null=True)
    option=models.CharField(max_length=100, null=True, blank=False)
    
    def __str__(self):
        return str(self.option)

class Critere(models.Model):
    ordre=models.IntegerField(null=True)
    critere=models.CharField(max_length=500, null=True, blank=False, verbose_name="Enoncé du critère")
    options= models.ManyToManyField(OptionCritere, blank=True)
    programmes= models.ManyToManyField(Programme, blank=True)
    commentaire=models.BooleanField(default=True, verbose_name="Possibilité d'introduire un commentaire au critère")

    def __str__(self):
        return str(self.critere)

DECISIONS_1=(
        ('N', 'Avancement normal'),
        ('E', 'Encouragement'),
        ('W1', 'Avertissement 1'),
        ('W2', 'Avertissement 2'),
        ('AJ', 'Ajournement'),
        ('D', 'Défavorable'),
    )

DECISIONS_FINALES=(
        ('F', 'Favorable'),
        ('FR', 'Favorable avec réserves'),
        ('D', 'Défavorable'),
    )

class EtatAvancement(models.Model):
    inscription = models.ForeignKey(Inscription, null=True, on_delete=CASCADE, related_name="etat_avancement")
    jury = models.ManyToManyField(Enseignant, blank=True, related_name='etats_avancements_en_jury')
    avis_directeur=models.TextField(null=True, verbose_name="Avis du directeur de thèse")
    final=models.BooleanField(default=False)
    decision_1=models.CharField(max_length=20,choices=DECISIONS_1, null=True)
    decision_finale=models.CharField(max_length=20,choices=DECISIONS_FINALES, null=True)

#    class Meta:
#        constraints = [
#            models.UniqueConstraint(fields=['inscription'], name="inscription-etat_avancement")
#        ]
    
    def these(self):
        if self.inscription and self.inscription.etudiant and Doctorant.objects.filter(etudiant=self.inscription.etudiant).exists() and These.objects.filter(doctorant=self.inscription.etudiant.doctorant).exists() :
            try :
                these_=get_object_or_404(These, id=self.inscription.etudiant.doctorant.these.id)
                return these_
            except These.DoesNotExist :
                return None
        return None
        
        
    def __str__(self):
        return f"Etat Avancement : {self.inscription}"


class EvaluationCritere(models.Model):
    etat_avancement=models.ForeignKey(EtatAvancement, on_delete=CASCADE)
    critere=models.ForeignKey(Critere, on_delete=CASCADE)
    options=models.ManyToManyField(OptionCritere, blank=True, related_name='evaluations_criteres')
    commentaire=models.TextField()
    
#    class Meta:
#        constraints = [
#            models.UniqueConstraint(fields=['etat_avancement', 'critere'], name="etat_avancement-critere")
#        ]
    

class SeminaireSuivi(models.Model):
    inscriptions = models.ManyToManyField(Inscription, blank=True, related_name="seminaires_suivis")
    matiere = models.ForeignKey(Matiere, null=True, on_delete=models.SET_NULL, related_name="matiere")  
    animateur_interne =models.ForeignKey(Enseignant, null=True, blank=True, on_delete= models.SET_NULL, related_name="seminaire_animateur")
    animateur_externe=models.CharField(max_length=30,null=True,blank=True)
    date=models.DateField(null=True,blank=True,)
    annee_univ=models.ForeignKey(AnneeUniv, null= True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Seminaire suivi {self.annee_univ} {self.matiere}"


# En cas d'ajout d'un nouveau document, indiquer son type, son nom puis sa catégorie entre "Programme", "Enseignant" et "Diplome". 
# Les DocumentConfig de la catégorie programme sont créés autant de fois que par programmme.
# Les DocumentConfig de la catégorie Diplome sont créés autant de fois que par diplôme.
# Les DocumentConfig de la catégorie Enseignant ne sont créés qu'une seule fois de manière globale (pour les tous les enseignants)
DOCUMENTS=(
        ("ATTESTATION_ETUDES_FR", ("Attestation des études en français", "Programme")),
        ("ATTESTATION_ETUDES_EN", ("Attestation des études en anglais (Situation Certificate)", "Programme")),
        ("ATTESTATION_FONCTION", ("Attestation de fonction", "Enseignant")),
        ("ATTESTATION_REINTEGRATION", ("Attestation de réintégration (document non signé)", "Programme")),
        ("ATTESTATION_SOUTENANCES", ("Attestation de soutenances", "Enseignant")),
        ("ATTESTATION_ENCADREMENTS", ("Attestation d'encadrements", "Enseignant")),
        ("ATTESTATION_EXPERTISES_PFE", ("Attestation d'expertises de PFE", "Enseignant")),
        ("CERTIFICAT_CONGES", ("Certificat congé académique", "Programme")),
        ("CERTIFICAT_NON_OBJECTION", ("Certification de non objection", "Programme")),
        ("CERTIFICAT_SCOLARITE", ("Certificat de scolarité 3L-TRILINGUE (Arabe, Français, Anglais)", "Programme")),
        ("CERTIFICAT_SCOLARITE_2L", ("Certificat de scolarité 2L-BILINGUE (Arabe, Français)", "Programme")),
        ("FICHE_INSCRIPTION", ("Fiche d'inscription (document non signé)", "Programme")),
        ("RELEVE_NOTES_FR", ("Relevé de notes en français (inclut le relevé de notes interactif où il est possible de réinitialiser les notes, il sera masqué si ce document est désactivé)", "Programme")),
        ("RELEVE_NOTES_EN", ("Relevé de notes en anglais", "Programme")),
        ("RELEVE_NOTES_AR", ("Relevé de notes en arabe", "Programme")),
        ("RELEVE_NOTES_ECTS", ("Relevé de notes ECTS", "Programme")),
        ("RELEVE_NOTES_PROVISOIRE", ("Relevés de notes provisoires", "Programme")),
        ("LISTE_MATIERES", ("Syllabus des matières (non signé et sans entête)", "Programme")),
        ("RELEVE_SEMINAIRES", ("Relevé des séminaires", "Programme")),
        ("RELEVE_NOTES_GLOBAL", ("Relevé de notes global par diplôme (document non signé)", "Diplome")),
        ("ATTESTATION_BON_CONDUITE", ("Attestation de bon conduite en arabe (Certificat de bon conduite)", "Programme")),      
    )

class DocumentConfig(models.Model):
    code=CharField(max_length=100)
    actif=models.BooleanField(default=False)
    programme=models.ForeignKey(Programme, on_delete=CASCADE, null=True, blank=True)
    diplome=models.ForeignKey(Diplome, on_delete=CASCADE, null=True, blank=True)
    autorite=models.ForeignKey(Autorite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Autorité", related_name="documents_signes")
    autorite_entete=models.ForeignKey(Autorite, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Autorité affichée dans l'entête du document", related_name="documents_en_entete")
    
    def type(self):
        return dict(DOCUMENTS)[self.code][1]
        
    def __str__(self):
        doc = dict(DOCUMENTS)[self.code][0]
        if self.programme :
            return f"{doc} {self.programme}"
        if self.diplome :
            return f"{doc} {self.diplome}"
        return doc
        
class Poste(models.Model):
    inscription = models.OneToOneField(Inscription, on_delete=CASCADE, unique=True, error_messages={
            'unique': (
                "Un poste est déjà associé à cette inscription"),
        },)
    specialite=models.ForeignKey(Specialite, null=True, blank=True, on_delete=models.SET_NULL)   
    organisme = models.ForeignKey(Organisme, on_delete=models.SET_NULL, null=True)
    responsable = models.ForeignKey(Enseignant, related_name='postes_en_responsable',on_delete= models.SET_NULL, null = True, blank = True)
    responsable_ext=models.CharField(max_length=300, null=True, blank=True, verbose_name="Responsable ext")

    def __str__(self):
        return f"{self.inscription} {self.specialite} {self.organisme}"


STATUT_ENREGISTREMENT=(
        ('W','En attente'),
        ('V','Validé'),
        ('R','Rejeté')
    )

@cleanup.ignore
class EnregistrementEtudiant(models.Model):
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Date et heure")
    statut = models.CharField(max_length=1, choices=STATUT_ENREGISTREMENT, null=True, blank=True, default='W')
    message = models.TextField(default='', blank=True, verbose_name="Message à transmettre à l'utilisateur")
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(null=True, verbose_name="Adresse e-mail")
    nom=models.CharField(max_length=50)
    prenom=models.CharField(max_length=50)
    sexe=models.CharField(max_length=1, choices=SEXE, null=True, blank=True)
    date_naissance=models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    lieu_naissance=models.CharField(max_length=100, null=True, blank=True, verbose_name="Lieu de naissance")
    wilaya_naissance=models.ForeignKey(Wilaya, on_delete=models.SET_NULL, null=True, blank=True, related_name="wilaya_naissance_enregistrements")
    wilaya_residence=models.ForeignKey(Wilaya, on_delete=models.SET_NULL, null=True, blank=True, related_name='origines_enregistrements')
    commune_residence=models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True)
    interne=models.BooleanField(default=False, null=True, blank=True, verbose_name="Interne dans une cité universitaire")
    residence_univ=models.TextField(null=True, blank=True, verbose_name="Nom de la cité universitaire si vous êtes interne")
    addresse_principale=models.TextField(null=True, blank=True, verbose_name="Adresse principale")
    programme=models.ForeignKey(Programme, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Actuellement scolarisé en")
    nom_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Nom en arabe")
    prenom_a=models.CharField(max_length=50, null=True, blank=True, verbose_name="Prénom en arabe")
    lieu_naissance_a=models.CharField(max_length=100, null=True, blank=True, verbose_name="Lieu de naissance en arabe")
    photo=models.ImageField(upload_to='photos',null=True,blank=True, verbose_name="Photo d'identité scannée (taille maximale 1 MO)") 
    tel=models.CharField(max_length=15, null=True, blank=True, verbose_name="Numéro de téléphone", validators=[RegexValidator('^[0-9\+]*$',
                               'Que des chiffres sans espaces et le + pour l\'international')])
    numero_securite_sociale=models.CharField(max_length=15, validators=[RegexValidator('^[0-9\+]*$',
                               'Que des chiffres sans espaces')], null=True, blank=True)

    def __str__(self):
        return f"{self.email} {self.nom} {self.prenom}"


class EquipeRecherche(models.Model):
    code = models.CharField(null=True, blank=True, max_length=50, verbose_name="Code/Sigle")
    nom = models.CharField(null=True, max_length=300)
    responsable = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipes_en_responsable')
    responsable_externe=models.CharField(max_length=200, null=True, blank=True, verbose_name="Responsable externe (s'il y a lieu)")
    membres =models.ManyToManyField(Enseignant, blank=True, related_name='equipes_en_membre')
    membres_doctorants=models.ManyToManyField(Doctorant, blank=True, related_name='equipes_en_membre', verbose_name="Membres doctorants")
    membres_externes=models.TextField(null=True,blank=True, verbose_name="Membres externes")
    organisme=models.ForeignKey('Organisme', on_delete=models.SET_NULL, null=True, blank=True, related_name='equipes')
    description = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.code} {self.nom}"    

TYPE_OFFRE=(
        ("EMPLOI", "Offre d'emploi"),
        ("THESE", "Offre de thèse"),
        ("SP", "Offre de stage pratique"),
        ("AUTRE", "Autre")
    )
STATUT_OFFRE=(
    ('C', 'Offre en attente de vérification par un administrateur'),
    ('S', 'Offre ouverte - Prête à recevoir des candidatures'),
    ('T', 'Offre fermée - Il n\'est plus possible de postuler à cette candidature'),
    ('N', 'Offre rejetée par un administrateur'),
)

def file_size(value):
    limit = 10 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('Fichier trop lourd. Le maximum est de 10 Méga-octets par fichier.')
    
class Offre(models.Model):
    user=models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='offres', verbose_name="Offre déposée par")
    emetteur = models.TextField(max_length=200, null=True, verbose_name="Émetteur réel de l'offre")
    type = models.CharField(max_length=20, choices=TYPE_OFFRE, default='EMPLOI', null=True, blank=True)
    intitule = models.TextField(null=True, verbose_name="Intitulé de l'offre")
    specialites = models.ManyToManyField(Specialite, verbose_name="Spécialités ciblées")
    organisme = models.ForeignKey(Organisme, on_delete=models.SET_NULL, null=True, blank=True)
    date=models.DateField(null=True, blank=True,verbose_name='Date de dépôt')
    description = models.TextField(null=True, verbose_name="Description détaillée de l'offre")
    fichier1 = models.FileField(upload_to='files/offres', null=True, blank=True, verbose_name="Pièce jointe 1 (facultatif)", validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']), file_size])
    fichier2 = models.FileField(upload_to='files/offres', null=True, blank=True, verbose_name="Pièce jointe 2 (facultatif)", validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']), file_size])
    fichier3 = models.FileField(upload_to='files/offres', null=True, blank=True, verbose_name="Pièce jointe 3 (facultatif)", validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']), file_size])
    statut = models.CharField(max_length=2, choices=STATUT_OFFRE, default='C')
    notification = models.BooleanField(default=True, verbose_name="Notifier le déposant par e-mail de la validation de l'offre ainsi que pour chaque nouvelle candidature")
    activation_candidatures = models.BooleanField(default=True, verbose_name="Activation de l'espace de candidature pour cette offre (les utilisateurs pourront candidater directement sur la plateforme)")

    def nb_candidatures(self):
        return Candidature.objects.filter(offre=self).count()
    def __str__(self):
        return f"{dict(TYPE_OFFRE)[self.type]} : {self.intitule}" 
 
def candidature_file_name(instance, filename):
    random_string=''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return "files/candidatures/"+random_string+'/'+str(filename)
   
class Candidature(models.Model):
    user=models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='candidatures', verbose_name="Candidat")
    nom=models.CharField(max_length=50, null=True)
    prenom=models.CharField(max_length=50, null=True, verbose_name="Prénom(s)")
    offre = models.ForeignKey(Offre, on_delete=CASCADE, null=True)
    reponse=models.TextField(null=True, verbose_name="Pourquoi moi ?")
    competences=models.TextField(null=True, verbose_name="Mes compétences que j'estime adéquates à l'offre")
    motivations=models.TextField(null=True, verbose_name="Mes motivations")
    cv = models.FileField(upload_to=candidature_file_name, null=True, blank=True, verbose_name="CV (facultatif)", validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']), file_size])
    fichier1 = models.FileField(upload_to=candidature_file_name, null=True, blank=True, verbose_name="Autre pièce jointe (facultatif)", validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']), file_size])
    date_time= models.DateTimeField(default=timezone.now, verbose_name="Date et heure")
    last_edit= models.DateTimeField(null=True, blank=True, verbose_name="Dernière modification")
    acces_profil=models.BooleanField(default=False, verbose_name="Accorder l'accès à mon profil à l'utilisateur ayant déposé l'offre (parcours, activités et photo uniquement)")
    
    def __str__(self):
        return f"{self.user} : {self.offre}"
