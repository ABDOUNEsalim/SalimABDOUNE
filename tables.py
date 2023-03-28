import django_tables2 as tables

import django_filters
from django_filters.widgets import BooleanWidget
 from scolar.models import User, DomaineConnaissance, Matiere, MatiereCompetenceElement, Specialite, AnneeUniv, Periode, Enseignant, Departement, Diplome, Programme, PeriodeProgramme, UE, Formation, Module, Evaluation, \
     Section, Groupe, PFE, ModulesSuivis, Activite, Charge, Etudiant, Seance, AbsenceEtudiant, Soutenance, Inscription, InscriptionPeriode, ResultatUE, Resultat, Note,  Question, Feedback, Reponse, Competence, CompetenceElement, \
     CompetenceFamily, Semainier, EvaluationCompetenceElement, AbsenceEnseignant ,

from crispy_forms.layout import Layout, Submit, Div, Field
from crispy_forms.helper import FormHelper
from django.utils.html import format_html
from django import forms
import datetime
from bootstrap_datepicker_plus import DatePickerInput
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django_select2.forms import ModelSelect2Widget

from django_tables2 import A
from scolar.admin import settings
import pytz

def get_institution():
    institution_ = Institution.objects.all()
    if institution_.exists():
        return institution_[0]
    else :
        raise Exception

class MatiereTable(tables.Table):
    code = tables.LinkColumn('matiere_detail', args=[tables.A('pk')])
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
                <a href="{% url "matiere_update" pk=record.id %}" > {% icon "pencil-alt" %} </a>\
                <a href="{% url "matiere_delete" pk=record.id %}" > {% icon "trash" %} </a>\
            {% endif %}'
    edit= tables.TemplateColumn(action, orderable=False)
    
    def render_titre(self,value,record):
        html=""
        if record.seminaire :
            html+="<strong><span style='border:2px solid black; padding:5px;'>Séminaire</span></strong><br><br>"
        html+=record.titre
            
        return format_html(html)

    def render_coef(self,value,record):
        try:
            if decimal.Decimal(value) == int(value) :
                return int(value)
            else :
                return value
        except Exception:
            return value
        
            
    class Meta:
        model = Matiere
        fields=('code','precision', 'titre', 'ddc','credit','coef','edition', 'vh_cours', 'vh_td', 'vh_tp')        
        template_name = "django_tables2/bootstrap4.html"
        row_attrs = { "style": lambda record: "background-color: #f5f5f5;" if record.seminaire else "background-color: #ffffff;" } 

class MatiereFilter(django_filters.FilterSet):
    code= django_filters.CharFilter(field_name='code', lookup_expr='icontains', label = 'Code')
    ddc = django_filters.ModelChoiceFilter(field_name='ddc', queryset = DomaineConnaissance.objects.all().order_by('intitule'), empty_label ='Domaine', label ='Domaine')
    titre = django_filters.CharFilter(field_name='titre', lookup_expr='icontains', label = 'Mot clé dans Titre')
    contenu = django_filters.CharFilter(field_name='contenu', lookup_expr='icontains', label = 'Mot clé dans Description')
    programme = django_filters.ModelChoiceFilter(distinct=True, field_name='matiere_ues__periode__programme', queryset = Programme.objects.all().order_by('ordre'), empty_label ='Programme')    
    
    class Meta:
        model = Matiere
        fields = ('code', 'ddc','titre', 'contenu', 'programme',)


class ActiviteFilter(django_filters.FilterSet):
    annee_univ=django_filters.ModelChoiceFilter(field_name='module__formation__annee_univ', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label="Année Universitaire", empty_label="Année Universitaire")
    type=django_filters.ChoiceFilter(field_name='type', choices=TYPES_ACT, label="Type d'activité", empty_label="Type d'activité")
    semestre = django_filters.ModelChoiceFilter(field_name='module__periode__periode', queryset = Periode.objects.all().order_by('code'), label ='Période', empty_label='Période')
    
    class Meta:
        model = Activite
        fields = ('annee_univ', 'type','semestre')
        
        
        
class ActiviteTable(tables.Table):
    cible=tables.Column()
    def render_cible(self,value,record):
        cible_=''
        for groupe in value.all():
            if record.module.matiere.pfe:
                cible_=cible_+' '+str(groupe)+' : '+str([inscription_.etudiant.nom +' '+ inscription_.etudiant.prenom for inscription_ in groupe.inscrits.all()])
            else: 
                cible_=cible_+' '+str(groupe)
        return format_html("<b>{}</b>",cible_)
    action= '{% if not record.module.matiere.pfe and not record.module.formation.programme.matiere_equipe %}\
                {% for groupe in record.cible.all %}\
                    {% if groupe.code %}\
                        <a href="{% url "absencesform" activite_pk=record.id groupe_pk=groupe.id %}" class="btn btn-danger">{{ groupe.code }} </a>\
                    {% else %}\
                        {% for groupe_section in groupe.section.groupes.all %}\
                            {% if groupe_section.code %}\
                                <a href="{% url "absencesform" activite_pk=record.id groupe_pk=groupe_section.id  %}" class="btn btn-danger">{{ groupe_section.code }}</a>\
                            {% endif %}\
                        {% endfor %}\
                    {% endif %}\
                {% endfor %}\
            {% endif %}'
                
    absences   = tables.TemplateColumn(action, orderable=False)

    action= '{% if not record.module.matiere.pfe and not record.module.formation.programme.matiere_equipe %}\
                <a href="{% url "assiduite" activite_pk=record.id %}" class="btn btn-danger"> Assiduite</a>\
            {% endif %}'
    gestion_assiduite   = tables.TemplateColumn(action, orderable=False)
    action= '{% for groupe in record.cible.all %}\
                {% if groupe.code %}\
                    <a href="{% url "note_list" matiere_pk=record.module.matiere.id groupe_pk=groupe.id %}" class="btn btn-info">{{ groupe.code }} </a>\
                {% else %}\
                    {% for groupe_section in groupe.section.groupes.all %}\
                        {% if groupe_section.code %}\
                            <a href="{% url "note_list" matiere_pk=record.module.matiere.id groupe_pk=groupe_section.id %}" class="btn btn-info">{{ groupe_section.code }}</a>\
                        {% endif %}\
                    {% endfor %}\
                {% endif %}\
            {% endfor %}'
                
    notes   = tables.TemplateColumn(action, orderable=False)
    action= '{% load icons %}\
            <a href="{% url "feedback_module_detail" module_pk=record.module.id %}">{% icon "chart-bar" %}</a>'
    feedback   = tables.TemplateColumn(action, orderable=False)
    class Meta:
        model= Activite
        fields = ['module__formation__annee_univ', 'type', 'module__matiere__code', 'vh', 'cible']
        template_name= "django_tables2/bootstrap4.html"
        
class EncadrementsTable(tables.Table):
    cible__pfe__intitule=tables.Column(empty_values=())
    etudiants =tables.Column(empty_values=(), orderable=False)
    def render_etudiants(self,value,record):
        etudiants_=''
        groupe_=record.cible.all().first()
        str_to_return='Code : '+ str(groupe_)
        for inscription_ in groupe_.inscrits.all() :
            if inscription_.etudiant.public_profile or self.request.user.has_perm('scolar.fonctionnalitenav_etudiants_annuairecomplet'): 
                 str_to_return=str_to_return+'<br><a href='+reverse('etudiant_detail',kwargs={'pk': inscription_.etudiant.matricule})+'>- '+inscription_.etudiant.nom +' '+ inscription_.etudiant.prenom+'</a>'
            else :
                str_to_return=str_to_return+'<br>- '+inscription_.etudiant.nom +' '+ inscription_.etudiant.prenom
        return format_html("<b>{}</b>",mark_safe(str_to_return))           
    def render_cible__pfe__intitule(self,value,record):
        try :
            pfe_=get_object_or_404(PFE, groupe=record.cible.all().first())
            if self.request.user.is_authenticated :
                return format_html("<a href='{0}' target='_blank'><b>{1}</b></a>",reverse('pfe_detail',kwargs={'pk': pfe_.id}),pfe_.intitule)
            else :
                return format_html("<b>{}</b>",pfe_.intitule)
        except Exception:
            return ''
        
    class Meta:
        model= Activite
        fields = ['module__formation__annee_univ', 'cible__pfe__intitule', 'etudiants']
        template_name= "django_tables2/bootstrap4.html"


class EncadrementsAttestationTable(tables.Table):
    cible__pfe__intitule=tables.Column(empty_values=(), verbose_name="Intitulé")
    etudiants =tables.Column(empty_values=(), orderable=False)
    module__formation__annee_univ =tables.Column(empty_values=(), orderable=False, verbose_name="Année universitaire")
            
    def render_etudiants(self,value,record):
        etudiants_=''
        groupe_=record.cible.all().first()
        str_to_return='Code : '+ str(groupe_)
        for inscription_ in groupe_.inscrits.all() :            
                str_to_return=str_to_return+' - '+inscription_.etudiant.nom +' '+ inscription_.etudiant.prenom
        return format_html("{}",str_to_return)           
    def render_cible__pfe__intitule(self,value,record):
        try :
            pfe_=get_object_or_404(PFE, groupe=record.cible.all().first())      
            return format_html("{}",pfe_.intitule)
        except Exception:
            return ''
        
    class Meta:
        model= Activite
        fields = ['module__formation__annee_univ', 'cible__pfe__intitule', 'etudiants']
        template_name= "django_tables2/bootstrap4.html"
        
class SoutenancesAttestationTable(tables.Table):
    cible__pfe__intitule=tables.Column(empty_values=(), verbose_name="Intitulé")
    etudiants =tables.Column(empty_values=(), orderable=False)
    module__formation__annee_univ =tables.Column(empty_values=(), orderable=False, verbose_name="Année universitaire")
    role=tables.Column(empty_values=(), orderable=False, verbose_name="Rôle")

    def __init__(self, *args, **kwargs):
        temp_enseignant = kwargs.pop("enseignant")
        super(SoutenancesAttestationTable, self).__init__(*args, **kwargs)
        self.enseignant=temp_enseignant
            
    def render_etudiants(self,value,record):
        groupe_=record.cible.all().first()
        str_to_return='Code : '+ str(groupe_)
        for inscription_ in groupe_.inscrits.all() :            
                str_to_return=str_to_return+' - '+inscription_.etudiant.nom +' '+ inscription_.etudiant.prenom
        return format_html("{}",str_to_return)
        
    def render_cible__pfe__intitule(self,value,record):
        try :
            pfe_=get_object_or_404(PFE, groupe=record.cible.all().first())      
            return format_html("{}",pfe_.intitule)
        except Exception:
            return ''
        
    def render_role(self, value, record):
        try :
            role_=''
            soutenance_=get_object_or_404(Soutenance, groupe=record.cible.all().first())
            if soutenance_.president == self.enseignant :
                role_=role_+' Président'
            if soutenance_.rapporteur == self.enseignant :
                role_=role_+' Rapporteur'
            if soutenance_.examinateur == self.enseignant :
                role_=role_+' Examinateur'
            if soutenance_.coencadrant == self.enseignant :
                role_=role_+' Coencadrant'
            if soutenance_.assesseur1 == self.enseignant :
                role_=role_+' Assesseur1'
            if soutenance_.assesseur2 == self.enseignant :
                role_=role_+' Assesseur2'  
            return role_    
        except Exception:
            return ''            
    class Meta:
        model= Activite
        fields = ['module__formation__annee_univ', 'cible__pfe__intitule', 'etudiants']
        template_name= "django_tables2/bootstrap4.html"
        
class ExpertisesPFEAttestationTable(tables.Table):
    intitule=tables.Column(empty_values=(), verbose_name="Intitulé")
    annee_expertise=tables.Column(empty_values=(), verbose_name="Année d'expertise")
            
    class Meta:
        model= PFE
        fields = ['id', 'intitule', 'annee_expertise']
        template_name= "django_tables2/bootstrap4.html"

    def __init__(self, *args, **kwargs):
        temp_enseignant = kwargs.pop("enseignant")
        super(ExpertisesPFEAttestationTable, self).__init__(*args, **kwargs)
        self.enseignant=temp_enseignant
        
    def render_annee_expertise(self,value,record):
        pfe_=record
        expertise_qs=Validation.objects.filter(pfe=record, expert=self.enseignant).order_by('-id')
        if expertise_qs.exists() :
            last_expertise=expertise_qs.first()
            date_=last_expertise.debut
            return str(date_.year)
        else :
            return ''
        

class InscriptionTable(tables.Table):
    action='{% load dictionary %}\
            {% for periode_ in record.inscription_periodes.all|dictsort:"periodepgm.periode.code" %}\
                <strong>{{ periode_.periodepgm.periode.code }} : </strong> {{ periode_.groupe.code }}<br>\
            {% endfor %}'

    groupe   = tables.TemplateColumn(action, orderable=False)
    
    action='<a href="{% url "etudiant_inscription_list" etudiant_pk=record.etudiant.matricule %}" class="btn btn-info"> Inscriptions </a>'

    detail   = tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model= Inscription
        fields = ('etudiant__matricule', 'etudiant__nom', 'etudiant__nom_a','etudiant__prenom', 'etudiant__prenom_a', 'formation__programme')
        template_name= "django_tables2/bootstrap4.html"
        

class InscriptionFilter(django_filters.FilterSet):
    etudiant = django_filters.CharFilter(field_name='etudiant__nom', lookup_expr='icontains', label='Nom de l\'étudiant')
    programme = django_filters.ModelChoiceFilter(field_name='formation__programme', queryset=Programme.objects.all().order_by('ordre'), label='Année d\'étude', empty_label='Année d\'étude')
    groupe = django_filters.ModelChoiceFilter(field_name='groupe', queryset=Groupe.objects.filter(section__formation__annee_univ__encours=True).exclude(code__isnull=True).order_by('section__formation__programme__ordre', 'code'), label='Groupe', empty_label='Groupe')
    class Meta:
        model = Inscription
        fields = ('etudiant', 'programme', 'groupe')
        

class ValidationTable(tables.Table):
    link='{% load icons %}\
            {% if user.is_enseignant %}\
                {% if user.enseignant == record.expert %}\
                    {% if record.pfe.statut_validation != "V" and record.pfe.statut_validation != "N" %}\
                        {% if record.avis == "X" %}\
                            <a href="{% url "validation_update" pk=record.id pfe_pk=record.pfe.id %}" > {% icon "pencil-alt" %} </a>\
                        {% endif %}\
                    {% endif %}\
                {% endif %}\
            {% endif %}'
                    
    action = tables.TemplateColumn(link, orderable=False)
    link='{% load icons %}\
            <a href="{% url "validation_delete" pk=record.id pfe_pk=record.pfe.id %}" > {% icon "trash" %} </a>'
    edit = tables.TemplateColumn(link, orderable=False)
    
    def render_pfe__id(self,value,record):
        these_qs=These.objects.filter(sujet__id=record.pfe.id)
        these_=None
        if these_qs.exists() :
            these_=these_qs.first()
        if these_ : 
            return these_.id
        else :
            return record.pfe.id

    def render_debut(self,value,record):
        try :
            return value.strftime("%d/%m/%Y")
        except Exception:
            return ''  

    def render_fin(self,value,record):
        try :
            return value.strftime("%d/%m/%Y")
        except Exception:
            return ''  
            
    class Meta:
        model= Validation
        fields = ('pfe__id', 'pfe__type', 'pfe__intitule', 'pfe__organisme', 'expert', 'debut', 'fin', 'avis', 'commentaire')
        template_name= "django_tables2/bootstrap4.html"
        row_attrs = { "style": lambda record: "background-color: #37D263;" if record.avis == 'V' 
                                        else "background-color: #DB7E7A;" if record.avis == 'N'
                                        else "background-color: #ACD992;" if record.avis == 'SR'
                                        else "background-color: #DECD23;" if record.avis == 'MR'
                                        else "background-color: ##FFFFFF;"}

class PFETable(tables.Table):
    nb_avis=tables.Column(orderable=False)
    action='{% load icons usergroup %}\
            <a href="{% url "pfe_detail" pk=record.id %}" > {% icon "eye" %} </a>\
            {% if user.is_authenticated %}\
                <a href="{% url "pfe_fiche_pdf" pfe_pk=record.id %}" > {% icon "file-pdf" %} </a>\
                {% if record.statut_validation == "C" or record.statut_validation == "RR" or  record.statut_validation == "S" or  record.statut_validation == "N" %}\
                    {% if user.is_enseignant %}\
                        {% if request.user.enseignant in record.coencadrants.all %}\
                            <a href="{% url "pfe_update" pk=record.id %}" class="btn btn-warning"  > Réviser </a> \
                            <a href="{% url "pfe_demande_suppression_confirmation" pk=record.id %}" class="btn btn-danger"  > Demander la suppression </a>\
                        {% endif %}\
                    {% endif %}\
                    {% if user.is_etudiant and not user.is_enseignant %}\
                        {% for inscription in user.etudiant.inscriptions_encours %}\
                            {% if inscription in record.reserve_pour.all %}\
                                <a href="{% url "pfe_update" pk=record.id %}" class="btn btn-warning"  > Réviser </a> \
                                <a href="{% url "pfe_demande_suppression_confirmation" pk=record.id %}" class="btn btn-danger"  > Demander la suppression </a>\
                            {% endif %}\
                        {% endfor %}\
                    {% endif %}\
                    {% if user.is_partenaire %}\
                        {% if request.user.email|upper == record.email_promoteur|upper %}\
                            <a href="{% url "pfe_update" pk=record.id %}" class="btn btn-warning"  > Réviser </a> \
                            <a href="{% url "pfe_demande_suppression_confirmation" pk=record.id %}" class="btn btn-danger"  > Demander la suppression </a>\
                        {% endif %}\
                    {% endif %}\
                {% elif record.statut_validation == "V" or record.statut_validation == "W" %}\
                    {% if user.is_enseignant and request.user.enseignant in record.coencadrants.all and not record.groupe or user.is_partenaire and request.user.email|upper == record.email_promoteur|upper and not record.groupe %}\
                            <a href="{% url "pfe_update" pk=record.id %}" class="btn btn-warning"  > Affectation </a> \
                            {% if record.statut_validation == "V" %}\
                                <a href="{% url "pfe_demande_suppression_confirmation" pk=record.id %}" class="btn btn-danger"  > Demander la suppression </a>\
                            {% endif %}\
                    {% endif %}\
                {% endif %}\
            {% endif %}'
                
            
    detail   = tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            <a href="{% url "pfe_update" pk=record.id %}" > {% icon "pencil-alt" %}</a>\
            <a href="{% url "pfe_delete" pk=record.id %}" > {% icon "trash" %}</a>'
            
    edit   = tables.TemplateColumn(action, orderable=False)
    
    
    class Meta:
        model= PFE
        fields = ('id', 'groupe__section__formation__annee_univ__annee_univ', 'type', 'reserve_pour', 'intitule', 'organisme__sigle', 'coencadrants', 'email_promoteur', 'nb_avis', 'statut_validation')
        template_name= "django_tables2/bootstrap4.html"
        row_attrs = { "style": lambda record: "background-color: #e6e6e6;" if record.reserve_pour.count() > 0 
                                        else "background-color: #66ff33;"}
        

class PFEFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(label ='Mots-clés (titre, description, ..)', method='keyword_lookup')
    pays = django_filters.ModelChoiceFilter(field_name='organisme__pays', queryset=Pays.objects.all().order_by('nom'), label='Pays', empty_label='Pays')
    organisme = django_filters.ModelChoiceFilter(field_name='organisme', queryset=Organisme.objects.all().order_by('sigle'), label='Organisme', empty_label='Organisme')
    type = django_filters.ChoiceFilter(field_name='type', choices=set(TYPE_STAGE) ^ set((('D', 'Doctorat'),)), label='Type', empty_label='Type')
    statut_validation = django_filters.ChoiceFilter(field_name='statut_validation', choices=STATUT_VALIDATION, label='Etat Validation', empty_label='Etat Validation')
    annee_universitaire = django_filters.ModelChoiceFilter(field_name='groupe__section__formation__annee_univ', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label='Année Universitaire', empty_label='Année Univ')
    groupe = django_filters.CharFilter(field_name='groupe__code', lookup_expr='icontains', label='Groupe')
    nom_prenoms = django_filters.CharFilter(label ='Nom/prénom(s) étudiant', method='nom_prenoms_lookup')
    encadrant_promoteur = django_filters.CharFilter(label ='Encadrant/Promoteur', method='encadrant_promoteur_lookup')
    specialite= django_filters.ModelChoiceFilter(field_name='specialites', queryset=Specialite.objects.all().order_by('code'), label='Spécialité', empty_label='Spécialité')
    
    class Meta:
        model = PFE
        fields = ('annee_universitaire', 'groupe', 'id', 'keyword', 'nom_prenoms', 'encadrant_promoteur', 'type', 'specialite', 'keyword', 'pays', 'statut_validation',)
        
        
    def nom_prenoms_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=PFE.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(reserve_pour__etudiant__nom__icontains=value_)|Q(reserve_pour__etudiant__prenom__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(reserve_pour__etudiant__nom__icontains=value_)|Q(reserve_pour__etudiant__prenom__icontains=value_)).distinct())
        return qs_
        
    def encadrant_promoteur_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=PFE.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(coencadrants__nom__icontains=value_)|Q(coencadrants__prenom__icontains=value_)|Q(promoteur__icontains=value_)|Q(email_promoteur__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(coencadrants__nom__icontains=value_)|Q(coencadrants__prenom__icontains=value_)|Q(promoteur__icontains=value_)|Q(email_promoteur__icontains=value_)).distinct())
        return qs_

    def keyword_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=PFE.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(intitule__icontains=value_)|Q(resume__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(intitule__icontains=value_)|Q(resume__icontains=value_)).distinct())
        return qs_
        
class OrganismeTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "organisme_update" pk=record.sigle %}" > {% icon "pencil-alt" %}</a>\
            <a href="{% url "organisme_delete" pk=record.sigle %}" > {% icon "trash" %}</a>'
            
    edit   = tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model= Organisme
        fields = ['sigle', 'nom', 'adresse', 'pays', 'type', 'secteur', 'taille']
        template_name= "django_tables2/bootstrap4.html"
        

class OrganismeFilter(django_filters.FilterSet):
    sigle = django_filters.CharFilter(field_name='sigle', lookup_expr='icontains', label='Sigle')
    nom = django_filters.CharFilter(field_name='nom', lookup_expr='icontains', label='Nom')
    pays = django_filters.ModelChoiceFilter(field_name='pays', queryset=Pays.objects.all().order_by('nom'), label='Pays', empty_label='Pays')
    type = django_filters.ChoiceFilter(field_name='type', choices=TYPE_ORGANISME, label='Type', empty_label='Type')
    secteur = django_filters.ChoiceFilter(field_name='secteur', choices=SECTEUR_ORGANISME, label='Secteur', empty_label='Secteur d\'activité')

    class Meta:
        model = Organisme
        fields = ['sigle', 'nom', 'pays', 'type', 'secteur']
        

class ExamenTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "examen_update" seance_pk=record.id %}" class="btn btn-danger"> {% icon "pencil-alt" %} Examen </a>\
            <a href="{% url "placer_surveillants_update" seance_pk=record.id %}" class="btn btn-warning"> {% icon "pencil-alt" %} Surveillants </a>\
            <a href="{% url "pv_examen_list" seance_pk=record.id %} " target="_blank" > PV {% icon "file-pdf" %}</a>\
            <a href="{% url "examen_delete" pk=record.activite.id %}"> {% icon "trash" %}</a>'

            
             
    edit   = tables.TemplateColumn(action, orderable=False)
    date = tables.DateTimeColumn(format ='d/m/Y')
    heure_debut = tables.TimeColumn(format='H:i')
    heure_fin = tables.TimeColumn(format='H:i')
    class Meta:
        model= Seance
        fields = ['activite__type', 'activite__module', 'date', 'heure_debut', 'heure_fin', 'salles']
        template_name= "django_tables2/bootstrap4.html"
        
class SurveillancesEnseignantFilter(django_filters.FilterSet):
    annee_univ = django_filters.ModelChoiceFilter(field_name='activite__module__formation__annee_univ', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label='Année Universitaire', empty_label='Année Univ')
    semestre = django_filters.ModelChoiceFilter(field_name='activite__module__periode__periode', queryset=Periode.objects.all().order_by('code'), label='Période', empty_label='Période')
    formation = django_filters.ModelChoiceFilter(field_name='activite__module__formation', queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'), label='Formation', empty_label='Formation')
    type = django_filters.ChoiceFilter(field_name='activite__type', choices=TYPES_ACT, label='Type', empty_label='Type')
    matiere = django_filters.CharFilter(field_name='activite__module__matiere__code', lookup_expr='icontains', label='Matière')
    
    class Meta:
        model = Seance
        fields = ['annee_univ', 'semestre', 'formation', 'type', 'matiere']


class ExamenFilter(django_filters.FilterSet):
    annee_univ = django_filters.ModelChoiceFilter(field_name='activite__module__formation__annee_univ', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label='Année Universitaire', empty_label='Année Univ')
    semestre = django_filters.ModelChoiceFilter(field_name='activite__module__periode__periode', queryset=Periode.objects.all().order_by('code'), label='Période', empty_label='Période')
    formation = django_filters.ModelChoiceFilter(field_name='activite__module__formation', queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'), label='Formation', empty_label='Formation')
    type = django_filters.ChoiceFilter(field_name='activite__type', choices=TYPES_ACT, label='Type', empty_label='Type')
    matiere = django_filters.CharFilter(field_name='activite__module__matiere__code', lookup_expr='icontains', label='Matière')
    surveillant = django_filters.ModelChoiceFilter(field_name='activite__assuree_par', queryset=Enseignant.objects.all().order_by('nom'), label='Surveillant', empty_label='Surveillant')

    class Meta:
        model = Seance
        fields = ['annee_univ', 'semestre', 'formation', 'type', 'matiere', 'surveillant']
        

class SalleTable(tables.Table):
    
    action='{% load icons %}\
            <a href="{% url "salle_update" pk=record.id %} " target="_blank" > {% icon "pencil-alt" %}</a>\
            <a href="{% url "salle_copy" salle_pk=record.id %} " target="_blank" > {% icon "copy" %}</a>\
            <a href="{% url "salle_delete" pk=record.id %}"> {% icon "trash" %}</a>'

    edit   = tables.TemplateColumn(action, orderable=False)
    class Meta:
        model= Salle
        fields = ['code', 'version', 'calendarId', 'capacite', 'capacite_max']
        template_name= "django_tables2/bootstrap4.html"
        

class SalleFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(field_name='code', lookup_expr='icontains', label='Code Salle')

    class Meta:
        model = Salle
        fields = ['code']

class PlaceEtudiantTable(tables.Table):
    
    action='{% load icons %}\
            <a href="{% url "place_etudiant_update" pk=record.id %}"> {% icon "pencil-alt" %}</a>'

    edit   = tables.TemplateColumn(action, orderable=False)
    seance__date = tables.DateTimeColumn(format='d/m/Y')
    seance__heure_debut = tables.DateTimeColumn(format='H:i')
    seance__heure_fin = tables.DateTimeColumn(format='H:i')
    
    class Meta:
        model= ReservationPlaceEtudiant
        fields = ['seance__activite__type', 'seance__activite__module__matiere', 'inscription__etudiant', 'seance__date', 'seance__heure_debut', 'seance__heure_fin', 'place']
        template_name= "django_tables2/bootstrap4.html"
        

class PlaceEtudiantFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(field_name='inscription__etudiant__nom', lookup_expr='icontains', label='Nom Etudiant')
    formation = django_filters.ModelChoiceFilter(field_name='seance__activite__module__formation__programme', queryset = Programme.objects.all().order_by('ordre'), label = 'Formation', empty_label='Formation')
    matiere = django_filters.ModelChoiceFilter(field_name='seance__activite__module__matiere', queryset = Matiere.objects.all().order_by('code'), label = 'Matière', empty_label='Matière')
    type_examen=django_filters.ChoiceFilter(field_name='seance__activite__type', choices=TYPES_ACT_EXAM, label="Type d'examen", empty_label="Type d'examen")
    date_examen = django_filters.DateFilter(field_name='seance__date', label ='Date de l\'examen', widget=DatePickerInput(format='%m/%d/%Y'), initial=datetime.date.today())
 
    class Meta:
        model = ReservationPlaceEtudiant
        fields = ['nom', 'formation', 'matiere', 'type_examen', 'date_examen']
        

class SurveillanceTable(tables.Table):
    
    action='{% load icons %}\
            <a href="{% url "placer_surveillants_update" seance_pk=record.seance.id %}"> {% icon "pencil-alt" %}</a>'

    edit   = tables.TemplateColumn(action, orderable=False)
    seance__date=tables.DateTimeColumn(format ='d/m/Y')
    seance__heure_debut=tables.DateTimeColumn(format ='H:i')
    seance__heure_fin=tables.DateTimeColumn(format ='H:i')
    
    class Meta:
        model= SurveillanceEnseignant
        fields = ['enseignant', 'seance__date', 'seance__heure_debut', 'seance__heure_fin', 'seance__activite__module__formation__programme', 'seance__activite__module__matiere', 'salle__code']
        template_name= "django_tables2/bootstrap4.html"
        

class SurveillanceFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(field_name='enseignant__nom', lookup_expr='icontains', label='Nom Enseignant')
    formation = django_filters.ModelChoiceFilter(field_name='seance__activite__module__formation__programme', queryset = Programme.objects.all().order_by('ordre'), label = 'Formation', empty_label='Formation')
    matiere = django_filters.ModelChoiceFilter(field_name='seance__activite__module__matiere', queryset = Matiere.objects.all().order_by('code'), label = 'Matière', empty_label='Matière')
    type_examen=django_filters.ChoiceFilter(field_name='seance__activite__type', choices=TYPES_ACT_EXAM, label="Type d'examen", empty_label="Type d'examen")
    date_examen = django_filters.DateFilter(field_name='seance__date', label ='Date de l\'examen', widget=DatePickerInput(format='%m/%d/%Y'), initial=datetime.date.today())
 
    class Meta:
        model = SurveillanceEnseignant
        fields = ['nom', 'formation', 'matiere', 'type_examen', 'date_examen']
        

class InscriptionGroupeTable(tables.Table):
    etudiant__photo=tables.Column()
    def render_etudiant__photo(self,value,record):
        return format_html("<img src='{}' width='80'>",value.url)
    
    action= '{% load icons %}\
            <a href="{% url "etudiant_detail" pk=record.etudiant.matricule %}" > {% icon "eye" %}</a> '
    detail   = tables.TemplateColumn(action, orderable=False)

    action= '{% load icons %}\
            {% if perms.scolar.fonctionnalite_etudiants_gestion %}\
                <a href="{% url "inscription_update" pk=record.id %}" > {% icon "pencil-alt" %}</a>\
            {% endif %}'
    edit   = tables.TemplateColumn(action, orderable=False)
    class Meta:
        model= Inscription
        fields = ('etudiant__matricule', 'etudiant__nom', 'etudiant__nom_a','etudiant__prenom', 'etudiant__prenom_a',)
        template_name= "django_tables2/bootstrap4.html"

class EvaluationCompetenceElementTable(tables.Table):
    action= '{% load icons %}\
            <a href="{% url "evaluation_competence_element_update" pk=record.id evaluation_pk=record.evaluation.id %}">{% icon "pencil-alt" %}</a>\
            <a href="{% url "evaluation_competence_element_delete" pk=record.id evaluation_pk=record.evaluation.id %}">{% icon "trash" %}</a>'
    actions   = tables.TemplateColumn(action, orderable=False)
    class Meta:
        model= EvaluationCompetenceElement
        fields = ['competence_element', 'ponderation', 'commune_au_groupe']
        template_name= "django_tables2/bootstrap4.html"
        


class AbsenceEtudiantFilter(django_filters.FilterSet):
    nom_prenoms = django_filters.CharFilter(label ='Nom et/ou prénom(s)', method='nom_prenoms_lookup')
    module = django_filters.ModelChoiceFilter(field_name='seance__activite__module', queryset = Module.objects.filter(formation__annee_univ__encours=True).order_by('formation__programme__ordre', 'formation__programme__code', 'periode__periode__code', 'matiere__code'), label = 'Module', empty_label='Module')
    groupe = django_filters.ModelChoiceFilter(field_name='seance__activite__cible', queryset = Groupe.objects.filter(section__formation__annee_univ__encours=True).order_by('section__formation__programme__ordre'), label = 'Groupe', empty_label='Groupe')
    enseignant = django_filters.ModelChoiceFilter(field_name='seance__activite__assuree_par', queryset = Enseignant.objects.all().order_by('nom'), label = 'Enseignant', empty_label='Enseignant')
    date_absence = django_filters.DateFilter(field_name='seance__date', label ='Date de l\'absence', widget=DatePickerInput(format='%m/%d/%Y'), initial=datetime.date.today())
    justif = django_filters.BooleanFilter(field_name='justif',label ='Justifiée' )
    class Meta:
        model = AbsenceEtudiant
        fields = ('nom_prenoms', 'module', 'groupe', 'enseignant', 'date_absence', 'justif')
    def nom_prenoms_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=Etudiant.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(etudiant__nom__icontains=value_)|Q(etudiant__prenom__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(etudiant__nom__icontains=value_)|Q(etudiant__prenom__icontains=value_)).distinct())
        return qs_    
        
class AbsenceEtudiantTable(tables.Table):
    seance__activite__cible=tables.Column()
    def render_seance__activite__cible(self,value,record):
        cible_=''
        for groupe in value.all():
            cible_=cible_+' '+str(groupe)
        return format_html("<b>{}</b>",cible_)
    action= '{% load icons %}\
            {% if perms.scolar.fonctionnalite_etudiants_justificationabsences or is_assuree_par_enseignant %}\
                <a href="{% url "absence_update" pk=record.id %}"> {% icon "pencil-alt" %} </a>\
            {% endif %}\
            {% if perms.scolar.fonctionnalite_etudiants_justificationabsences or is_assuree_par_enseignant %}\
                <a href="{% url "absence_etudiant_delete" pk=record.id activite_pk=record.seance.activite.id seance_pk=record.seance.id %}"> {% icon "trash" %} </a>\
            {% endif %}'
    actions   = tables.TemplateColumn(action, orderable=False)
    class Meta:
        model= AbsenceEtudiant
        fields = ('etudiant', 'seance', 'seance__activite__cible', 'justif', 'motif')
        template_name= "django_tables2/bootstrap4.html"
        

class AbsenceEnseignantFilter(django_filters.FilterSet):
    enseignant = django_filters.CharFilter(field_name='enseignant__nom', lookup_expr='icontains', label ='Nom enseignant')
    formation = django_filters.ModelChoiceFilter(field_name='seance__activite__module__formation', queryset = Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'), label = 'Formation', empty_label='Formation')
    justif = django_filters.BooleanFilter(field_name='justif',label ='Justifiée' )
    class Meta:
        model = AbsenceEnseignant
        fields = ['enseignant', 'formation', 'justif']
        
class EnseignementsTable(tables.Table):
    types=tables.Column(empty_values=(), orderable=False)
    matiere__code=(tables.Column(empty_values=()))
    
    def render_matiere__code(self, value, record):
        return format_html("<a href='{0}'target='_blank'><b>{1}</b></a>",reverse('matiere_detail',kwargs={'pk': record.matiere.id}),value) 
            
    def render_types(self,value,record):
        types_= ''
        activite_list=Activite.objects.filter(module__matiere=record.matiere, module__formation__annee_univ=record.formation.annee_univ, assuree_par=record.enseignant).filter(Q(type='C')|Q(type='TD')|Q(type='TP')|Q(type='P')).order_by('type')
        type_list=[]
        for activite_ in activite_list:   
            if not activite_.type in type_list :
                type_list.append(activite_.type)          
        for type_ in type_list :
            types_= types_+' | '+str(dict(TYPES_ACT)[type_])
        return format_html("<b>{}</b>",types_)
    class Meta:
        model = Module
        fields = ['formation__annee_univ','matiere__code','matiere__titre']
        template_name= "django_tables2/bootstrap4.html"     
        
class AbsenceEnseignantTable(tables.Table):
    seance__activite__cible=tables.Column()
    def render_seance__activite__cible(self,value,record):
        cible_=''
        for groupe in value.all():
            cible_=cible_+' '+str(groupe)
        return format_html("<b>{}</b>",cible_)
    action= '{% load icons%}\
            {% if perms.scolar.fonctionnalite_planification_gestionseances or module_assure_par_enseignant %}\
                <a href="{% url "seance_rattrapage_create" activite_pk=record.seance.activite.id %}" class="btn btn-primary"> Rattrapage </a>\
            {% endif %}\
            {% if perms.scolar.fonctionnalite_enseignants_justificationabsences %}\
                <a href="{% url "absence_enseignant_update" pk=record.id %}" class="btn btn-warning"> Modifier </a>\
            {% endif %}'
    edit   = tables.TemplateColumn(action, orderable=False)
    class Meta:
        model= AbsenceEnseignant
        fields = ('enseignant', 'seance', 'seance__activite__cible', 'justif', 'motif')
        template_name= "django_tables2/bootstrap4.html"
        

        
        
        
class InscriptionEtudiantTable(tables.Table):
    rang=tables.Column()
    def render_rang(self,value,record):
        if record.formation.programme.doctorat :
            return '—'
        else :
            return format_html("{} / <b>{}</b>",str(value), str(record.nb_inscrits()))
    
    action= '{% load icons dictionary %}\
                {% if user.is_etudiant %}\
                    {% if record.etudiant == user.etudiant %}\
                        {% if "FICHE_INSCRIPTION"|document_programme_actif:record.formation.programme %}\
                            {% if record.decision_jury != "X" %}\
                                <a href="{% url "fiche_inscription_pdf" inscription_pk=record.id %}">Fiche {% icon "file-pdf" %}</a>\
                            {% endif %}\
                        {% endif %}\
                        {% if "RELEVE_NOTES_FR"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes" inscription_pk=record.id %}">Notes</a>\
                        {% endif %}\
                        {% if "RELEVE_NOTES_ECTS"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_ects" inscription_pk=record.id %}">ECTS</a>\
                        {% endif %}\
                        {% if record.formation.programme.doctorat and "RELEVE_SEMINAIRES"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_seminaires" inscription_pk=record.id %}">Séminaires</a>\
                        {% endif %}\
                    {% else %}\
                        {% if perms.scolar.fonctionnalite_etudiants_documents %}\
                            {% if "FICHE_INSCRIPTION"|document_programme_actif:record.formation.programme %}\
                                <a href="{% url "fiche_inscription_pdf" inscription_pk=record.id %}">Fiche {% icon "file-pdf" %}</a>\
                            {% endif %}\
                        {% endif %}\
                        {% if perms.scolar.fonctionnalite_etudiants_visualisationnotesprofil %}\
                            {% if "RELEVE_NOTES_FR"|document_programme_actif:record.formation.programme %}\
                                <a href="{% url "releve_notes" inscription_pk=record.id %}">Notes</a>\
                            {% endif %}\
                            {% if "RELEVE_NOTES_ECTS"|document_programme_actif:record.formation.programme %}\
                                <a href="{% url "releve_ects" inscription_pk=record.id %}">ECTS</a>\
                            {% endif %}\
                        {% endif %}\
                        {% if perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsdoctorants and record.formation.programme.doctorat and "RELEVE_SEMINAIRES"|document_programme_actif:record.formation.programme or perms.scolar.fonctionnalite_etudiants_visualisationnotesprofil and record.formation.programme.doctorat and "RELEVE_SEMINAIRES"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_seminaires" inscription_pk=record.id %}">Séminaires</a>\
                        {% endif %}\
                    {% endif %}\
                {% else %}\
                    {% if perms.scolar.fonctionnalite_etudiants_documents %}\
                            {% if "FICHE_INSCRIPTION"|document_programme_actif:record.formation.programme %}\
                                <a href="{% url "fiche_inscription_pdf" inscription_pk=record.id %}">Fiche {% icon "file-pdf" %}</a>\
                            {% endif %}\
                    {% endif %}\
                    {% if perms.scolar.fonctionnalite_etudiants_visualisationnotesprofil %}\
                        {% if "RELEVE_NOTES_FR"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes" inscription_pk=record.id %}">Notes</a>\
                        {% endif %}\
                        {% if "RELEVE_NOTES_ECTS"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_ects" inscription_pk=record.id %}">ECTS</a>\
                        {% endif %}\
                    {% endif %}\
                    {% if perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsdoctorants and record.formation.programme.doctorat and "RELEVE_SEMINAIRES"|document_programme_actif:record.formation.programme or perms.scolar.fonctionnalite_etudiants_visualisationnotesprofil and record.formation.programme.doctorat and "RELEVE_SEMINAIRES"|document_programme_actif:record.formation.programme  %}\
                        <a href="{% url "releve_seminaires" inscription_pk=record.id %}">Séminaires</a>\
                    {% endif %}\
                {% endif %}'
    detail   = tables.TemplateColumn(action, orderable=False)
    action= '{% load icons dictionary %}\
            {% if not record.formation.programme.doctorat %}\
                {% if perms.scolar.fonctionnalite_etudiants_gestion or request.user|has_acces_gestion_etudiants_programme:record.formation.programme %}\
                    <a href="{% url "inscription_update" pk=record.id %}">{% icon "pencil-alt" %}</a>\
                {% endif %}\
                {% if perms.scolar.fonctionnalite_etudiants_gestion %}\
                    <a href="{% url "inscription_delete" pk=record.id etudiant_pk=record.etudiant.matricule %}">{% icon "trash" %}</a>\
                {% endif %}\
            {% else %}\
                {% if perms.scolar.fonctionnalite_postgraduation_gestiondoctorants %}\
                    <a href="{% url "inscription_update" pk=record.id %}">{% icon "pencil-alt" %}</a>\
                {% endif %}\
                {% if perms.scolar.fonctionnalite_postgraduation_gestiondoctorants %}\
                    <a href="{% url "inscription_delete" pk=record.id etudiant_pk=record.etudiant.matricule %}">{% icon "trash" %}</a>\
                {% endif %}\
            {% endif %}'
    edit   = tables.TemplateColumn(action, orderable=False)

    def render_moy(self, value, record):
        if record.formation.programme.doctorat :
            return '—'
        else :
            return value
    
    
    class Meta:
        model= Inscription
        fields = ('formation', 'moy', 'rang',  'decision_jury','observation', )
        template_name= "django_tables2/bootstrap4.html"

class InscriptionEtudiantDocumentsTable(tables.Table):
    action= '{% load usergroup dictionary %}\
            {% if record.decision_jury != "X" %}\
                {% if record.formation.programme.inclut_pfe and record.decision_jury == "A" %}\
                    {% if perms.scolar.fonctionnalite_etudiants_documents or is_etudiant_himself %}\
                        {% if "RELEVE_NOTES_FR"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-info">Relevé</a> \
                        {% endif %}\
                        {% if "RELEVE_NOTES_EN"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes_english_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-info">Transcript</a> \
                        {% endif %}\
                        {% if "RELEVE_NOTES_AR"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes_arabe_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-info">كشف النقاط</a> \
                        {% endif %}\
                    {% endif %}\
                    {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes and "RELEVE_NOTES_FR"|document_programme_actif:record.formation.programme %}\
                        <a href="{% url "releve_notes_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-info">Relevé-S</a>\
                    {% endif %}\
                    {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes and "RELEVE_NOTES_EN"|document_programme_actif:record.formation.programme %}\
                        <a href="{% url "releve_notes_english_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-info">Transcript-S</a> \
                    {% endif %}\
                    {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes and "RELEVE_NOTES_AR"|document_programme_actif:record.formation.programme %}\
                        <a href="{% url "releve_notes_arabe_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-info">كشف النقاط -S</a> \
                    {% endif %}\
                {% elif record.formation.archive %}\
                    {% if perms.scolar.fonctionnalite_etudiants_documents or is_etudiant_himself %}\
                        {% if "RELEVE_NOTES_FR"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-info">Relevé</a>\
                        {% endif %}\
                        {% if "RELEVE_NOTES_EN"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes_english_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-info">Transcript</a>\
                        {% endif %}\
                        {% if "RELEVE_NOTES_AR"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes_arabe_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-info">كشف النقاط</a> \
                        {% endif %}\
                    {% endif %}\
                    {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes %}\
                        {% if "RELEVE_NOTES_FR"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-info">Relevé-S</a>\
                        {% endif %}\
                        {% if "RELEVE_NOTES_EN"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes_english_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-info">Transcript-S</a>\
                        {% endif %}\
                        {% if "RELEVE_NOTES_AR"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "releve_notes_arabe_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-info">كشف النقاط -S</a> \
                        {% endif %}\
                    {% endif %}\
                    {% if record.formation.pv_final_existe %}\
                        {% if perms.scolar.fonctionnalite_etudiants_documents or is_etudiant_himself %}\
                            {% if "RELEVE_NOTES_ECTS"|document_programme_actif:record.formation.programme %}\
                                <a href="{% url "releve_ects_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-info">ECTS</a>\
                            {% endif %}\
                        {% endif %}\
                        {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes %}\
                            {% if "RELEVE_NOTES_ECTS"|document_programme_actif:record.formation.programme %}\
                                <a href="{% url "releve_ects_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-info">ECTS-S </a>\
                            {% endif %}\
                        {% endif %}\
                    {% endif %}\
                {% else %}\
                    {% if "RELEVE_NOTES_PROVISOIRE"|document_programme_actif:record.formation.programme %}\
                        {% for periode in record.inscription_periodes.all %}\
                            {% if periode.pv_final_existe %}\
                                {% if perms.scolar.fonctionnalite_etudiants_documents or is_etudiant_himself %}\
                                    <a href="{% url "releve_notes_provisoire_pdf" inscription_pk=record.id periode_pk=periode.periodepgm.id signature=1 %}" class="btn btn-info">RP. {{periode.periodepgm.code}}</a>\
                                {% endif %}\
                            {% endif %}\
                            {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes %}\
                                <a href="{% url "releve_notes_provisoire_pdf" inscription_pk=record.id periode_pk=periode.periodepgm.id signature=0 %}" class="btn btn-info">RP. {{periode.periodepgm.code}}-S </a>\
                            {% endif %}\
                        {% endfor %}\
                    {% endif %}\
                {% endif %}\
                {% if record.decision_jury != "F" and not record.decision_jury|startswith:"M" and record.decision_jury != "X" %}\
                    {% if "CERTIFICAT_SCOLARITE"|document_programme_actif:record.formation.programme %}\
                        {% if perms.scolar.fonctionnalite_etudiants_documents or perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsdoctorants and record.formation.programme.doctorat or is_etudiant_himself %}\
                            <a href="{% url "certificat_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-success">Cert3Lx4</a>\
                        {% endif %}\
                        {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes or perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsnonsignesdoctorants and record.formation.programme.doctorat %}\
                             <a href="{% url "certificat_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-success">Cert3Lx4-S</a>\
                        {% endif %}\
                    {% endif %}\
                    {% if "CERTIFICAT_SCOLARITE_2L"|document_programme_actif:record.formation.programme %}\
                        {% if perms.scolar.fonctionnalite_etudiants_documents or perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsdoctorants and record.formation.programme.doctorat or is_etudiant_himself %}\
                            <a href="{% url "certificat_2l_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-success">Cert2L</a>\
                        {% endif %}\
                        {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes or perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsnonsignesdoctorants and record.formation.programme.doctorat %}\
                             <a href="{% url "certificat_2l_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-success">Cert2L-S</a>\
                        {% endif %}\
                    {% endif %}\
                {% endif %}\
                {% if record.decision_jury|startswith:"M" %}\
                    {% if perms.scolar.fonctionnalite_etudiants_documents or perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsdoctorants or is_etudiant_himself %}\
                        {% if "CERTIFICAT_CONGES"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "certificat_conges_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-success">CertAcad</a>\
                        {% endif %}\
                    {% endif %}\
                    {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes or perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsnonsignesdoctorants and record.formation.programme.doctorat %}\
                        {% if "CERTIFICAT_CONGES"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "certificat_conges_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-success">CertAcad-S</a>\
                        {% endif %}\
                        {% if "ATTESTATION_REINTEGRATION"|document_programme_actif:record.formation.programme %}\
                            <a href="{% url "attestation_reintegration_pdf" inscription_pk=record.id %}" class="btn btn-success">Réintégration</a>\
                        {% endif %}\
                    {% endif %}\
                {% endif %}\
                {% if "LISTE_MATIERES"|document_programme_actif:record.formation.programme %}\
                    <a href="{% url "matiere_detail_list_pdf" programme_pk=record.formation.programme.id %}" class="btn btn-info">Syllabus</a>\
                {% endif %}\
            {% else %}\
                {% if perms.scolar.fonctionnalite_etudiants_documents or perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsdoctorants and record.formation.programme.doctorat %}\
                    {% if "CERTIFICAT_SCOLARITE"|document_programme_actif:record.formation.programme %}\
                        <a href="{% url "certificat_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-success">Cert3Lx4</a>\
                    {% endif %}\
                {% endif %}\
                {% if perms.scolar.fonctionnalite_etudiants_documentsnonsignes or perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsnonsignesdoctorants and record.formation.programme.doctorat %}\
                    {% if "CERTIFICAT_SCOLARITE"|document_programme_actif:record.formation.programme %}\
                        <a href="{% url "certificat_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-success">Cert3Lx4-S</a>\
                    {% endif %}\
                {% endif %}\
            {% endif %}\
            {% if record.formation.programme.doctorat and "RELEVE_SEMINAIRES"|document_programme_actif:record.formation.programme and perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsdoctorants or record.formation.programme.doctorat and "RELEVE_SEMINAIRES"|document_programme_actif:record.formation.programme and is_etudiant_himself %}\
                <a href="{% url "releve_seminaires_pdf" inscription_pk=record.id signature=1 %}" class="btn btn-info">Séminaires</a>\
            {% endif %}\
            {% if record.formation.programme.doctorat and "RELEVE_SEMINAIRES"|document_programme_actif:record.formation.programme and perms.scolar.fonctionnalite_postgraduation_visualisationdocumentsnonsignesdoctorants %}\
                <a href="{% url "releve_seminaires_pdf" inscription_pk=record.id signature=0 %}" class="btn btn-info">Séminaires-S</a>\
            {% endif %}\
            '
                    #<a href="{% url "certificat_old_pdf" inscription_pk=record.id %}" class="btn btn-success">Cert. 2L</a>\
    detail   = tables.TemplateColumn(action, orderable=False)
    class Meta:
        model= Inscription
        fields = ('formation', 'moy', 'rang', 'decision_jury', 'observation', )
        template_name= "django_tables2/bootstrap4.html"
      

class ActiviteChargeConfigTable(tables.Table):
    
    action= '{% load icons %}\
            {% if perms.scolar.fonctionnalite_enseignants_gestioncharges %}\
                <a href="{% url "activite_charge_config_update" record.id %}">{% icon "pencil-alt" %}</a>\
            {% endif %}\
            {% if perms.scolar.fonctionnalite_enseignants_gestioncharges %}\
                <a href="{% url "activite_charge_config_delete" record.id %}">{% icon "trash" %}</a>\
            {% endif %}'

    edit   = tables.TemplateColumn(action, orderable=False)
    class Meta:
        model= ActiviteChargeConfig
        fields = ('categorie', 'type', 'titre', 'vh', 'vh_eq_td',  'repeter_chaque_semaine', 'repartir_entre_intervenants')
        template_name= "django_tables2/bootstrap4.html"
        
class ActiviteEtudiantTable(tables.Table):
    module=tables.Column()
    def render_module(self, value, record):
        link='<a href="/scolar/module_detail/'+str(value.id)+'">'+str(value.matiere.code)+'</a>'
        return format_html(link)
    assuree_par=tables.Column()
    def render_assuree_par(self,value,record):
        enseignant_list=''
        for enseignant in value.all():
            enseignant_list+=' '+str(enseignant)
        return format_html("<b>{}</b>",enseignant_list)
    
    action= '<a href="{% url "etudiant_module_absences" etudiant_pk=request.user.etudiant.matricule  module_pk=record.module.id %}" class="btn btn-danger" role="button"> Absences</a>\
             <a href="{% url "etudiant_module_notes" etudiant_pk=request.user.etudiant.matricule matiere_pk=record.module.matiere.id %}" class="btn btn-primary" role="button">Notes</a>'
    detail   = tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model= Activite
        fields=('type','module','vh','assuree_par')
        template_name= "django_tables2/bootstrap4.html"


def matieres(request):
    if request is None:
        return Matiere.objects.all().order_by('code')
    inscriptions_encours=request.user.etudiant.inscriptions_encours()
    resultats= Resultat.objects.filter(ancien_resultat__isnull=True, inscription__in=inscriptions_encours).values('module__matiere__id').order_by('module__periode__periode', 'module__matiere__code')
    return Matiere.objects.filter(id__in=resultats)
     
class ActiviteEtudiantFilter(django_filters.FilterSet):
    periode = django_filters.ModelChoiceFilter(field_name='module__periode__periode', queryset=Periode.objects.all().order_by('ordre'), label='Période', empty_label='Période')
    type=django_filters.ChoiceFilter(field_name='type', choices=TYPES_ACT, label="Type d'activité", empty_label="Type d'activité")
    matiere = django_filters.ModelChoiceFilter(field_name='module__matiere', queryset=matieres, label='Matière', empty_label='Matière')

    class Meta:
        model = Activite
        fields = ('periode', 'type','matiere')
           
class MatiereCompetenceElementTable(tables.Table):
    action = '{% load icons %}\
        {% if perms.scolar.fonctionnalite_pedagogie_gestioncompetences %}\
            <a href="{% url "matiere_competence_element_update" pk=record.id matiere_pk=record.matiere.id %}"> {% icon "pencil-alt" %} </a>\
        {% endif %}\
        {% if perms.scolar.fonctionnalite_pedagogie_gestioncompetences %}\
            <a href="{% url "matiere_competence_element_delete" pk=record.id matiere_pk=record.matiere.id %}"> {% icon "trash" %} </a>\
        {% endif %}'

    edit= tables.TemplateColumn(action, orderable=False)

    class Meta:
        model= MatiereCompetenceElement
        fields = ('matiere__code', 'matiere__titre', 'competence_element__code', 'competence_element__intitule', 'competence_element__objectif', 'niveau')
        template_name= "django_tables2/bootstrap4.html"


class CompetenceFamilyTable(tables.Table):
    action = '{% load icons %}\
        <a href="{% url "competence_list" competence_family_pk=record.code %}"> {% icon "eye" %} </a>'

    detail= tables.TemplateColumn(action, orderable=False)

    action = '{% load icons %}\
        {% if perms.scolar.fonctionnalite_pedagogie_gestioncompetences %}\
            <a href="{% url "competence_family_update" pk=record.code %}"> {% icon "pencil-alt" %} </a>\
        {% endif %}\
        {% if perms.scolar.fonctionnalite_pedagogie_gestioncompetences %}\
            <a href="{% url "competence_family_delete" pk=record.code %}"> {% icon "trash" %} </a>\
        {% endif %}'

    edit= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = CompetenceFamily
        template_name= "django_tables2/bootstrap4.html"

class CompetenceTable(tables.Table):
    action = '{% load icons %}\
        <a href="{% url "competence_element_list" competence_pk=record.id %}"> {% icon "eye" %} </a>'

    detail = tables.TemplateColumn(action, orderable=False)

    action = '{% load icons %}\
        {% if perms.scolar.fonctionnalite_pedagogie_gestioncompetences %}\
            <a href="{% url "competence_update" pk=record.id competence_family_pk=record.competence_family.code %}"> {% icon "pencil-alt" %} </a>\
        {% endif %}\
        {% if perms.scolar.fonctionnalite_pedagogie_gestioncompetences %}\
            <a href="{% url "competence_delete" pk=record.id competence_family_pk=record.competence_family.code %}"> {% icon "trash" %} </a>\
        {% endif %}'

    edit= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Competence
        fields = ['code', 'intitule']
        template_name= "django_tables2/bootstrap4.html"

class CompetenceElementTable(tables.Table):
    action = '{% load icons %}\
        {% if perms.scolar.fonctionnalite_pedagogie_gestioncompetences %}\
            <a href="{% url "competence_element_update" pk=record.id competence_pk=record.competence.id %}"> {% icon "pencil-alt" %} </a>\
        {% endif %}\
        {% if perms.scolar.fonctionnalite_pedagogie_gestioncompetences %}\
            <a href="{% url "competence_element_delete" pk=record.id competence_pk=record.competence.id %}"> {% icon "trash" %} </a>\
        {% endif %}'

    edit= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = CompetenceElement
        fields = ['code', 'intitule', 'type', 'objectif']
        template_name= "django_tables2/bootstrap4.html"

class PVTable(tables.Table):
    action = '{% load icons %}\
        <a href="{% url "pv_detail" pk=record.id %}" target="_blank"> {% icon "eye" %} </a>\
        {% if record.xlsx %} <a href="{{ record.xlsx.url }}"> {% icon "file-excel" %} </a>{% endif %}'

    detail= tables.TemplateColumn(action, orderable=False)
    action = '{% load icons %}\
        <a href="{% url "pv_delete" pk=record.id %}"> {% icon "trash" %} </a>'
    edit= tables.TemplateColumn(action, orderable=False)
    date=tables.DateTimeColumn(format ='d/m/Y')
    class Meta:
        model = PV
        fields = ['date', 'annuel', 'periode', 'note_eliminatoire', 'moy_ue', 'rang', 'tri_rang', 'photo', 'signature', 'anonyme', 'reserve', 'post_rattrapage']
        template_name= "django_tables2/bootstrap4.html"

class DiplomeTable(tables.Table):
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
                <a href="{% url "diplome_update" pk=record.id %}" > {% icon "pencil-alt" %} </a>\
            {% endif %}\
            {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
                <a href="{% url "diplome_delete" pk=record.id %}" > {% icon "trash" %} </a>\
            {% endif %}'
                  
    edit= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Diplome
        fields = ['intitule',]
        template_name= "django_tables2/bootstrap4.html"

class CycleTable(tables.Table):
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
                <a href="{% url "cycle_update" pk=record.id %}" > {% icon "pencil-alt" %} </a>\
            {% endif %}\
            {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
                <a href="{% url "cycle_delete" pk=record.id %}" > {% icon "trash" %} </a>\
            {% endif %}'
                  
    edit= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Cycle
        fields = ['intitule', 'intitule_a', 'autorite']
        template_name= "django_tables2/bootstrap4.html"

class AutoriteTable(tables.Table):
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalite_configurationetablissement_modification %}\
                <a href="{% url "autorite_update" pk=record.id %}" > {% icon "pencil-alt" %} </a>\
            {% endif %}\
            {% if perms.scolar.fonctionnalite_configurationetablissement_modification %}\
                <a href="{% url "autorite_delete" pk=record.id %}" > {% icon "trash" %} </a>\
            {% endif %}'
                  
    edit= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Autorite
        fields = ['intitule', 'intitule_a', 'intitule_en', 'responsable', 'titre_responsable', 'titre_responsable_a', 'titre_responsable_en', 'autorite']
        template_name= "django_tables2/bootstrap4.html"

class SpecialiteTable(tables.Table):
    action = '{% load icons %}\
        {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
            <a href="{% url "specialite_update" pk=record.code %}"> {% icon "pencil-alt" %} </a>\
            <a href="{% url "specialite_delete" pk=record.code %}"> {% icon "trash" %} </a>\
        {% endif %}'
    edit= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Specialite
        exclude=['concernee_par_pfe']
        template_name= "django_tables2/bootstrap4.html"

class PeriodeTable(tables.Table):
    action = '{% load icons %}\
        {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
            <a href="{% url "periode_update" pk=record.id %}"> {% icon "pencil-alt" %} </a>\
            <a href="{% url "periode_delete" pk=record.id %}"> {% icon "trash" %} </a>\
        {% endif %}'
    edit= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Periode
        fields=('code', 'session', 'ordre', 'nb_semaines')
        template_name= "django_tables2/bootstrap4.html"

class ProgrammeTable(tables.Table):
    action = '{% load icons %}\
            <a href="{% url "programme_detail" pk=record.id %}" > {% icon "eye" %} </a>'
    detail= tables.TemplateColumn(action, orderable=False)
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
                <a href="{% url "programme_update" pk=record.id %}" > {% icon "pencil-alt" %} </a>\
            {% endif %}'
    edit= tables.TemplateColumn(action, orderable=False)

    class Meta:
        model = Programme
        fields = ('code', 'titre', 'cycle', 'specialite', 'diplome', 'assistant__user__email')
        template_name= "django_tables2/bootstrap4.html"


class FormationTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "section_list" formation_pk=record.id %}" class="btn btn-link"> Sections </a> '
    detail=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            <a href="{% url "export_inscriptions" formation_pk=record.id %}" > Liste Inscrits {% icon "file-excel" %} </a> '
    Inscrits=tables.TemplateColumn(action, orderable=False)    
    action='{% load icons %}\
            {% if perms.scolar.fonctionnalite_planification_gestionformations %}\
                <a href="{% url "formation_delete" pk=record.id annee_univ_pk=record.annee_univ %}"> {% icon "trash" %} </a>\
            {% endif %}\
            {% if perms.scolar.fonctionnalite_planification_gestionformations %}\
                <a href="{% url "formation_archive_toggle" formation_pk=record.id %}" data-toggle="tooltip" data-placement="bottom" title="Archiver/Désarchiver"> {% icon "database" %} </a>\
            {% endif %}'
    edit=tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model = Formation
        fields=('programme','annee_univ', 'archive')
        template_name= "django_tables2/bootstrap4.html"

class PreinscriptionTable(tables.Table):
#     quittance=tables.Column()
#     def render_quittance(self,value,record):
#         return format_html("<img src='{}' width='300'>",value.url)

    action='{% load icons %}\
            <a href="{% url "validation_preinscription" inscription_pk=record.inscription.id %}" class="btn btn-warning"> Vérifier </a> '
    edit=tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model = Preinscription
        fields=('inscription__formation','inscription__etudiant', 'inscription__formation__programme__assistant')
        template_name= "django_tables2/bootstrap4.html"

class PreinscriptionFilter(django_filters.FilterSet):
    cycle = django_filters.ModelChoiceFilter(field_name='inscription__formation__programme__cycle', queryset=Cycle.objects.all().order_by('ordre'), label='Cycle', empty_label='Cycle')
    
    class Meta:
        model = Preinscription
        fields = ('cycle',)

class ResidenceUnivTable(tables.Table):
    
    class Meta:
        model = ResidenceUniv
        fields=('nom','adresse', 'wilaya', 'commune', 'tel')
        template_name= "django_tables2/bootstrap4.html"

        
class DeliberationFormationTable(tables.Table):
    action='{% load icons usergroup %}\
            <a href="{% url "deliberation_detail" formation_pk=record.id %}"> Délibérer </a>'
    detail=tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Formation
        fields=('annee_univ','programme',)
        template_name= "django_tables2/bootstrap4.html"

class PlanificationTable(tables.Table):
    action='{% for periode in record.programme.periodes.all %}\
                <a href="{% url "planification_update" formation_pk=record.id periode_pk=periode.id %}" class="btn btn-primary"> {{ periode.periode.code }} </a>\
            {% endfor %}'
    detail=tables.TemplateColumn(action, orderable=False)

    class Meta:
        model = Formation
        fields = ('programme','annee_univ')
        template_name= "django_tables2/bootstrap4.html"

class FormationFilter(django_filters.FilterSet):
    annee_univ = django_filters.ModelChoiceFilter(field_name='annee_univ', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label='Année Universitaire', empty_label='Année Universitaire')
    programme = django_filters.ModelChoiceFilter(field_name='programme', queryset=Programme.objects.all().order_by('ordre'), label='Programme', empty_label='Programme')
    class Meta:
        model = Formation
        fields = ('annee_univ', 'programme')

        

class EtudiantTable(tables.Table):
    action='{% load dictionary %}\
            {% for inscription_ in record.inscriptions_encours %}\
                {% for periode_ in inscription_.inscription_periodes.all|dictsort:"periodepgm.periode.code" %}\
                    <strong>{{ periode_.periodepgm.periode.code }} : {% if not periode_.groupe.is_pfe %}{{ periode_.groupe.section.code }} {% endif %}</strong>{{ periode_.groupe.code }}<br>\
                {% endfor %}\
            {% endfor %}'

    groupe   = tables.TemplateColumn(action, orderable=False)
    
    photo=tables.Column()
    def render_photo(self,value,record):
        return format_html("<img src='{}' width='80'>",value.url)

    action= '<a href="{% url "etudiant_detail" pk=record.matricule %}" class="btn btn-info" role="button"> Détail</a>'
    detail=tables.TemplateColumn(action, orderable=False)
    date_naissance = tables.DateTimeColumn(format ='d/m/Y')

    class Meta:
        model = Etudiant
        fields = ('matricule', 'nom', 'nom_a', 'prenom', 'prenom_a', 'date_naissance', 'user__email', 'tel')
        template_name= "django_tables2/bootstrap4.html"

class EtudiantFilter(django_filters.FilterSet):
    matricule = django_filters.CharFilter(field_name='matricule', lookup_expr='icontains', label ='Matricule')
    nom_prenoms = django_filters.CharFilter(label ='Nom et/ou prénom(s)', method='nom_prenoms_lookup')
    rang_min = django_filters.NumberFilter(field_name='rang_min', lookup_expr='lte', label='Rang <')
    programme = django_filters.ModelChoiceFilter(field_name='inscriptions__formation', queryset=Formation.objects.all().order_by('-annee_univ__annee_univ','programme__ordre'), label='Formation', empty_label='Formation')
    class Meta:
        model = Etudiant
        fields = ('matricule', 'nom_prenoms','rang_min', 'programme')
        
    def nom_prenoms_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=Etudiant.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(nom__icontains=value_)|Q(prenom__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(nom__icontains=value_)|Q(prenom__icontains=value_)).distinct())
        return qs_
        

class PVEnseignantTable(tables.Table):
    action = '{% load icons %}\
        <a href="{% url "pv_detail" pk=record.id %}" target="_blank"> {% icon "eye" %} </a>'

    detail= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = PV
        fields = ['formation', 'annuel', 'periode', 'photo']
        template_name= "django_tables2/bootstrap4.html"

class PVFilter(django_filters.FilterSet):
    annee_univ = django_filters.ModelChoiceFilter(field_name='formation__annee_univ', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label='Année Universitaire', empty_label='Année Universitaire')
    programme = django_filters.ModelChoiceFilter(field_name='formation__programme', queryset=Programme.objects.all().order_by('ordre'), label='Programme', empty_label='Programme')
    periode = django_filters.ModelChoiceFilter(field_name='periode', queryset=Periode.objects.all().order_by('ordre'), label='Période', empty_label='Période')
    
    class Meta:
        model = PV
        fields = ('annee_univ', 'programme', 'periode',)

        



    
class EnseignantTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "enseignant_edt" enseignant_pk=record.id %}" > {% icon "calendar-check" %} </a>'
    edt=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            {% if perms.scolar.fonctionnalite_enseignants_gestion %}\
                <a href="{% url "enseignant_update" pk=record.id %}"> {% icon "pencil-alt" %} </a>\
            {% endif %}'
    edit=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            {% if perms.scolar.fonctionnalite_enseignants_suppression %}\
                <a href="{% url "enseignant_delete" pk=record.id %}"> {% icon "trash" %} </a>\
            {% endif %}'
    admin=tables.TemplateColumn(action, orderable=False)
    photo=tables.Column()
    def render_photo(self,value,record):
        return format_html("<img src='{}' width='80'>",value.url)
    action= '<a href="{% url "enseignant_detail" pk=record.id %}" class="btn btn-info" role="button"> Détail</a>'
    detail=tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Enseignant
        fields = ('nom', 'eps', 'prenom', 'grade', 'situation', 'tel', 'user__email', 'bureau', 'bal')
        template_name= "django_tables2/bootstrap4.html"
        
        
class EnseignantFilter(django_filters.FilterSet):
    nom_prenoms = django_filters.CharFilter(label ='Nom et/ou prénom(s)', method='nom_prenoms_lookup')
    grade = django_filters.ChoiceFilter(field_name='grade', choices=GRADE, label="Grade", empty_label="Grade")
    statut = django_filters.ChoiceFilter(field_name='statut', choices=STATUT, label="Statut", empty_label="Statut")
    situation = django_filters.ChoiceFilter(field_name='situation', choices=SITUATION, label="Situation", empty_label="Situation")
    class Meta:
        model = Enseignant
        fields = ('nom_prenoms', 'grade', 'situation', 'statut')

    def nom_prenoms_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=Enseignant.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(nom__icontains=value_)|Q(prenom__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(nom__icontains=value_)|Q(prenom__icontains=value_)).distinct())
        return qs_

class ChargeEnseignantTable(tables.Table):
    action= '{% load icons %}\
            {% if perms.scolar.fonctionnalite_enseignants_gestioncharges %}\
                <a href="{% url "charge_enseignant_update" pk=record.id %}" > {% icon "pencil-alt" %}</a>\
            {% endif %}\
            {% if perms.scolar.fonctionnalite_enseignants_gestioncharges %}\
                <a href="{% url "charge_enseignant_delete" enseignant_pk=record.realisee_par.id pk=record.id %}" > {% icon "trash" %}</a>\
            {% endif %}'
            
    edit=tables.TemplateColumn(action, orderable=False)

    class Meta:
        model = Charge
        fields = ('periode', 'type', 'activite', 'obs', 'vh', 'vh_eq_td', 'cree_par', 'repeter_chaque_semaine')
        template_name= "django_tables2/bootstrap4.html"

class SectionTable(tables.Table):
    action='{% load icons %}\
            {% if record.formation.programme.matiere_equipe %}\
                {% for periode_ in record.formation.programme.periodes.all %}\
                     <a href="{% url "equipe_list" formation_pk=record.formation.id periode_pk=periode_.id %}" class="btn btn-link"> Equipes {{ record.formation.programme.matiere_equipe.code }} {{ periode_.code }} </a>\
                {% endfor %}\
            {% else %}\
                <a href="{% url "groupe_list" section_pk=record.id %}" class="btn btn-link"> Groupes </a>\
            {% endif %}'
    detail=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            {% if perms.scolar.fonctionnalite_planification_gestionformations %}\
                <a href="{% url "section_delete" pk=record.id formation_pk=record.formation.id %}"> {%  icon "trash" %} </a>\
            {% endif %}'
    edit=tables.TemplateColumn(action, orderable=False)

    class Meta:
        model = Section
        fields=('code', 'formation', 'taille')
        template_name= "django_tables2/bootstrap4.html"

class GroupeTable(tables.Table):
    action='{% load icons %}\
            {% for periode_ in record.section.formation.programme.periodes.all %}\
                {% if record.code %}\
                    <a href="{% url "etudiant_groupe_list" groupe_pk=record.id periode_pk=periode_.id %}"> {{ periode_.periode.code }} {% icon "user-friends" %} </a>\
                {% endif %}\
            {% endfor %}'
    detail=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            {% if record.code %}\
                {% if perms.scolar.fonctionnalite_planification_gestionformations and not record.section.formation.programme.matiere_equipe %}\
                    <a href="{% url "groupe_update" pk=record.id section_pk=record.section.id %}"> {% icon "pencil-alt" %} </a> \
                {% endif %}\
                {% if record.section.formation.programme.matiere_equipe %}\
                    <a href="{% url "equipe_delete" pk=record.id formation_pk=record.section.formation.id periode_pk=periode_pk %}"> {% icon "trash" %} </a>\
                {% elif perms.scolar.fonctionnalite_planification_gestionformations %}\
                    <a href="{% url "groupe_delete" pk=record.id section_pk=record.section.id %}"> {% icon "trash" %} </a>\
                {% endif %}\
            {% endif %}'
    edit=tables.TemplateColumn(action, orderable=False)

    taille=tables.Column(orderable=False)
    def render_taille(self,value,record):
        taille_periode_list=''
        if record.section.formation.programme.matiere_equipe :
            for periode_ in record.section.formation.programme.periodes.all() :
                taille_periode_list+=str(periode_.code)+' : '+str(record.pfe.equipe.inscriptions.all().count())
        else :
            for item in value:
                taille_periode_list+=item['periodepgm__periode__code']+' : '+str(item['taille'])+" "
        return format_html("{}", taille_periode_list)

    option=tables.Column()
    def render_option(self,value,record):
        ue_list=''
        for ue in value.all():
            ue_list+=str(ue)+'   '
        return format_html("{}",ue_list)

    class Meta:
        model = Groupe
        fields=('code', 'section','option', 'taille')
        template_name= "django_tables2/bootstrap4.html"

class GroupeAllTable(tables.Table):
    action='{% load icons %}\
            {% for periode_ in record.section.formation.programme.periodes.all %}\
                {% if record.code %}\
                    <a href="{% url "etudiant_groupe_list" groupe_pk=record.id periode_pk=periode_.id %}"> {{ periode_.periode.code }} {% icon "user-friends" %} </a>\
                {% endif %}\
            {% endfor %}'
    detail=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            {% for periode_ in record.section.formation.programme.periodes.all %}\
                {% if record.code and not record.section.formation.programme.matiere_equipe %}\
                    <a href="{% url "groupe_list_export" groupe_pk=record.id periode_pk=periode_.id %}" class="btn btn-success"> {{ periode_.periode.code }} {% icon "file-export" %} </a>\
                {% endif %}\
            {% endfor %}'
    listes=tables.TemplateColumn(action, orderable=False)
    
    option=tables.Column()
    def render_option(self,value,record):
        ue_list=''
        for ue in value.all():
            ue_list+=str(ue)+'   '
        return format_html("{}",ue_list)
    
    taille=tables.Column(orderable=False)
    def render_taille(self,value,record):
        taille_periode_list=''
        for item in value:
            taille_periode_list+=item['periodepgm__periode__code']+' : '+str(item['taille'])+" "
        return format_html("{}", taille_periode_list)
    
    class Meta:
        model = Groupe
        fields=('section__formation__programme','section','code', 'option','taille')
        template_name= "django_tables2/bootstrap4.html"

class GroupeAllFilter(django_filters.FilterSet):
    programme = django_filters.ModelChoiceFilter(field_name='section__formation__programme', queryset=Programme.objects.all().order_by('ordre'), label ='Formation', empty_label='Formation')

    class Meta:
        model = Groupe
        fields = ('programme',)
        

class NotesFormationTable(tables.Table):
    action='{% load icons dictionary %}\
            {% if record.programme.fictif and record.programme.matiere_equipe is not None %}\
                {% for periode in record.programme.periodes.all %}\
                    <a href="{% url "notes_formation_detail" formation_pk=record.id periode_pk=periode.id %}" class="btn btn-primary"> Notes {{periode.periode.code}} </a>\
                {% endfor %}\
                <a href="{% url "export_equipes" formation_pk=record.id %}" class="btn btn-success"> Liste {{ record.programme.matiere_equipe.code }} {% icon "file-excel" %} </a>\
            {% else %}\
                {% for periode in record.programme.periodes.all %}\
                        <a href="{% url "notes_formation_detail" formation_pk=record.id periode_pk=periode.id %}" class="btn btn-primary"> Notes {{periode.periode.code}} </a>\
                {% endfor %}\
                {% if record.programme.inclut_pfe and perms.scolar.fonctionnalitenav_stages_exportationstages or record.programme.inclut_pfe and request.user|has_acces_visualisation_notes_programme:record.programme %}\
                    <a href="{% url "export_etudiant_pfe_list" formation_pk=record.id %}" class="btn btn-info"> Liste PFE {% icon "file-excel" %} </a>\
                {% endif %}\
            {% endif %}  '         
    detail=tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Formation
        exclude = ['id']
        template_name= "django_tables2/bootstrap4.html"


class ProgresFormationTable(tables.Table):
    action='{% load icons dictionary %}\
            {% if not record.programme.fictif %}\
                {% for periode in record.programme.periodes.all %}\
                        <a href="{% url "export_notes_progres_full" formation_pk=record.id periode_pk=periode.id %}" class="btn btn-primary"> Fichier {{periode.periode.code}} {% icon "file-excel" %}  </a>\
                {% endfor %}\
            {% endif %}  '         
    detail=tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Formation
        exclude = ['id']
        template_name= "django_tables2/bootstrap4.html"


class TutoratTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "etudiant_detail" pk=record.etudiant.matricule %}"> {% icon "eye" %} </a>'
    detail=tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Inscription
        fields = ('etudiant', 'formation__programme')
        template_name= "django_tables2/bootstrap4.html"

class ModuleTable(tables.Table):
    action='<a href="{% url "module_detail" pk=record.id %}" class="btn btn-primary"> Coordination </a>'
    coordonner=tables.TemplateColumn(action, orderable=False)
    action='<a href="{% url "notes_formation_coordinateur_detail" formation_pk=record.formation.id periode_pk=record.periode.id module_pk=record.id %}" class="btn btn-success"> Notes </a>'
    notes=tables.TemplateColumn(action, orderable=False)
    
    formule_='Moy = \
                {% for eval_ in record.evaluations.all %}\
                    {% if forloop.first %}\
                        {{ eval_.ponderation.normalize}} x {{eval_.type}}\
                    {% else %}\
                        + {{ eval_.ponderation.normalize}} x {{eval_.type}}\
                    {% endif %}\
                {% endfor %}\
                {% if record.activation_rattrapage %}\
                    <br>Moy Rattrapage = \
                    {% for eval_ in record.evaluations.all %}\
                        {% if forloop.first %}\
                            {{ eval_.ponderation_rattrapage.normalize}} x {{eval_.type}}\
                        {% else %}\
                            + {{ eval_.ponderation_rattrapage.normalize}} x {{eval_.type}}\
                        {% endif %}\
                    {% endfor %}\
                {% endif %}\
                '
    formule=tables.TemplateColumn(formule_, orderable=False)

    class Meta:
        model = Module
        fields = ('matiere', 'periode')
        template_name= "django_tables2/bootstrap4.html"

class ModuleFeedbackTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "feedback_module_detail" module_pk=record.id %}" > {% icon "chart-bar" %} </a> '
    detail=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            {% if perms.scolar.fonctionnalite_pedagogie_validationfeedbacks %}\
                <a href="{% url "feedback_list" module_pk=record.id %}" > {% icon "pencil-alt" %} </a> \
            {% endif %}\
            {% if perms.scolar.fonctionnalite_pedagogie_importationfeedbacks %}\
                <a href="{% url "import_feedback_module" module_pk=record.id %}" > {% icon "upload" %} </a>\
            {% endif %}'
    edit=tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model = Module
        fields = ['formation', 'periode', 'matiere']
        template_name= "django_tables2/bootstrap4.html"

class ModuleFilter(django_filters.FilterSet):
    matiere = django_filters.CharFilter(distinct=True, field_name='matiere__code', lookup_expr='icontains', label='Matière')
    formation = django_filters.ModelChoiceFilter(field_name='formation__programme', queryset=Programme.objects.all().order_by('ordre'), label='Formation', empty_label='Formation')
    annee_univ = django_filters.ModelChoiceFilter(field_name='formation__annee_univ', queryset=AnneeUniv.objects.all().order_by('annee_univ'), label='Année Universitaire', empty_label='Année Universitaire')
    periode = django_filters.ModelChoiceFilter(field_name='periode__periode', queryset=Periode.objects.all().order_by('ordre'), label='Période', empty_label='Période')
    class Meta:
        model = Module
        fields = ('matiere', 'formation', 'annee_univ', 'periode')


class CoordinationModuleFilter(django_filters.FilterSet):
    matiere = django_filters.CharFilter(distinct=True, field_name='matiere__code', lookup_expr='icontains', label='Matière')
    formation = django_filters.ModelChoiceFilter(field_name='formation__programme', queryset=Programme.objects.all().order_by('ordre'), label='Formation', empty_label='Formation')
    periode = django_filters.ModelChoiceFilter(field_name='periode__periode', queryset=Periode.objects.all().order_by('ordre'), label='Période', empty_label='Période')
    class Meta:
        model = Module
        fields = ('matiere', 'formation', 'periode')



class SemainierTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "semainier_update" pk=record.id module_pk=record.module.id %}"> {% icon "pencil-alt" %} </a>\
            <a href="{% url "semainier_delete" pk=record.id module_pk=record.module.id %}"> {% icon "trash" %} </a>'
    actions=tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Semainier
        fields = ('semaine', 'activite_cours', 'activite_dirigee', 'observation', 'objectifs', 'matiere_competence_element__competence_element__intitule')
        template_name= "django_tables2/bootstrap4.html"

class FeedbackTable(tables.Table):
    action='{% load icons %}\
            {% if perms.scolar.fonctionnalite_pedagogie_validationfeedbacks %}\
                <a href="{% url "feedback_update" pk=record.id module_pk=record.module.id %}" > {% icon "pencil-alt" %} </a>\
            {% endif %}'
            
    edit=tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = Feedback
        fields=('comment','show')
        template_name= "django_tables2/bootstrap4.html"

class EvaluationTable(tables.Table):
    action='{% if is_coordinateur %}\
                <a href="{% url "evaluation_delete" pk=record.id module_pk=record.module.id %}" class="btn btn-danger"> Supprimer </a>  \
            {% endif %}\
            {% if is_coordinateur %}\
                <a href="{% url "evaluation_update" pk=record.id module_pk=record.module.id %}" class="btn btn-warning"> Modifier </a>\
            {% endif %}'
    actions=tables.TemplateColumn(action, orderable=False)

    def render_ponderation(self,value,record):
        return value.normalize()
    
    def render_ponderation_rattrapage(self,value,record):
        return value.normalize()
    
    class Meta:
        model = Evaluation
        fields = ('type', 'ponderation', 'ponderation_rattrapage')
        template_name= "django_tables2/bootstrap4.html"

class ExportTable(tables.Table):  
    action='{% load icons %}\
            <a href="{% url "export_serv_national_list" annee_univ_pk=record.annee_univ %}" > Liste {% icon "file-excel" %} </a> '
    Service_National=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            <a href="{% url "export_maladie_list" annee_univ_pk=record.annee_univ %}" > Liste {% icon "file-excel" %} </a> '
    Maladie=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            <a href="{% url "export_sortants_list" annee_univ_pk=record.annee_univ %}" > Liste {% icon "file-excel" %} </a> '
    Sortants=tables.TemplateColumn(action, orderable=False)
     
    class Meta:        
        model = AnneeUniv
        fields=('annee_univ', 'encours')
        template_name= "django_tables2/bootstrap4.html"
        
class AnneeUnivTable(tables.Table):
    action = '{% load icons %}\
            <a href="{% url "formation_list" annee_univ_pk=record.annee_univ %}" class="btn btn-link" role="button"> Formations </a> '
    detail= tables.TemplateColumn(action, orderable=False)
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalite_planification_gestionformations%}\
                <a href="{% url "anneeuniv_update" pk=record.annee_univ %}"> {% icon "pencil-alt" %} </a>\
            {% endif %}'
    edit= tables.TemplateColumn(action, orderable=False)

    class Meta:
        model = AnneeUniv
        template_name= "django_tables2/bootstrap4.html"
                
class SeanceTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "seance_update" activite_pk=record.activite.id pk=record.id %}">{% icon "pencil-alt" %}</a>\
            <a href="{% url "seance_delete" activite_pk=record.activite.id pk=record.id %}">{% icon "trash" %}</a>\
            <a href="{% url "absence_seance_list" seance_pk=record.id activite_pk=record.activite.id %}">{% icon "eye" %}</a>'
    actions=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            {% for groupe in record.activite.cible.all %}\
                {% if groupe.code %}\
                    <a href="{% url "absencesform" activite_pk=record.activite.id groupe_pk=groupe.id %}" class="btn btn-danger">{{ groupe.code }}</a>\
                {% else %}\
                    {% for groupe_section in groupe.section.groupes.all %}\
                        {% if groupe_section.code %}\
                            <a href="{% url "absencesform" activite_pk=record.activite.id groupe_pk=groupe_section.id %}" class="btn btn-danger">{{ groupe_section.code }}</a>\
                        {% endif %}\
                    {% endfor %}\
                {% endif %}\
            {% endfor%}'
    absences=tables.TemplateColumn(action, orderable=False)
        
    class Meta:
        model=Seance
        template_name="django_tables2/bootstrap4.html"

class TraceTable(tables.Table):
    source_text=tables.Column(empty_values=(), verbose_name="Nom Source")
    source__username=tables.Column(empty_values=(), verbose_name="Utilisateur Source")
    action=tables.TemplateColumn('{{record.action|urlize|linebreaks}}', verbose_name="Action")
    cible_text=tables.Column(empty_values=(), verbose_name="Nom Cible")
    cible__username=tables.Column(empty_values=(), verbose_name="Utilisateur Cible")
    date_time=tables.Column(empty_values=(), verbose_name="Date et heure")
    link='{% load icons %}\
            <a href="{% url "trace_delete" pk=record.id %}" > {% icon "trash" %} </a>'
    edit = tables.TemplateColumn(link, orderable=False)

    def render_source__username(self,value,record):
        return value if value else format_html("<strong>Inexistant</strong>")
    
    def render_cible__username(self,value,record):
        return value if value else format_html("<strong>Inexistant</strong>")
        
    class Meta:
        model = Trace
        fields=('id', 'source_text', 'source__username', 'action', 'cible_text', 'cible__username', 'date_time', 'seen') 
        template_name= "django_tables2/bootstrap4.html"

class TraceFilter(django_filters.FilterSet):
    nom_prenoms_source = django_filters.CharFilter(label ='Nom/prénom(s) source', method='nom_prenoms_source_lookup')
    source = django_filters.ModelChoiceFilter(widget=ModelSelect2Widget(model=User, search_fields=['username__icontains', 'email__icontains',], attrs={'style':'width:250px', 'data-placeholder':"Utilisateur Source"}), queryset=User.objects.all())
    action=django_filters.CharFilter(lookup_expr='icontains', label='Mot clé dans l\'action')
    nom_prenoms_cible = django_filters.CharFilter(label ='Nom/prénom(s) cible', method='nom_prenoms_cible_lookup')
    cible = django_filters.ModelChoiceFilter(widget=ModelSelect2Widget(model=User, search_fields=['username__icontains', 'email__icontains',], attrs={'style':'width:250px;', 'data-placeholder':"Utilisateur Cible"}), queryset=User.objects.all())

    def nom_prenoms_source_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=Trace.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(source_text__icontains=value_).distinct()
            else :    
                qs_=(qs_ & queryset.filter(source_text__icontains=value_).distinct())
        return qs_

    def nom_prenoms_cible_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=Trace.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(cible_text__icontains=value_).distinct()
            else :    
                qs_=(qs_ & queryset.filter(cible_text__icontains=value_).distinct())
        return qs_
        
    class Meta:
        model = Trace
        fields = ('id', 'nom_prenoms_source','source', 'action', 'nom_prenoms_cible', 'cible') 


class NotificationsTable(tables.Table):
    #source_text=tables.Column(empty_values=(), verbose_name="Intervenant")
    action=tables.TemplateColumn('{{record.action|urlize|linebreaks}}', verbose_name="Notification")
    date_time=tables.Column(empty_values=(), verbose_name="Date et heure")

    class Meta:
        model = Trace
        fields=('action', 'date_time') 
        template_name= "django_tables2/bootstrap4.html"    
        row_attrs = { "style": lambda record: "background-color: #FFFF80;" if not record.is_seen_then_toggle() else "background-color: #ffffff;" } 

class UserTable(tables.Table):
    nom=tables.Column(empty_values=(), orderable=False)
    prenom=tables.Column(empty_values=(), orderable=False)
    username=tables.Column(verbose_name="Nom d'utilisateur")
    email=tables.Column(empty_values=(), verbose_name="Email")
    groups=tables.Column(orderable=False, empty_values=(), verbose_name="Rôles")
    action='{% load icons %}\
            <a href="{% url "user_update" pk=record.id %}" > {% icon "pencil-alt" %}</a>\
            <a href="{% url "user_delete" pk=record.id %}" > {% icon "trash" %}</a>'
            
    edit   = tables.TemplateColumn(action, orderable=False)
    
    def render_groups(self,value,record):
        string=""
        for group_ in record.groups.all():
            string = string + " "+str(group_)
        return string
    
    class Meta:
        model = User
        fields=('username','email', 'nom', 'prenom', 'groups') 
        template_name= "django_tables2/bootstrap4.html" 
       
class DoctorantTable(tables.Table):       
    photo=tables.Column(empty_values=(), orderable=False)
    nom=tables.Column(empty_values=())
    prenom=tables.Column(empty_values=())
    these__sujet__intitule=tables.Column(verbose_name="Thèse")
    these__directeur=tables.Column(verbose_name="Directeur de thèse")
    annees_inscription=tables.Column(orderable=False, empty_values=(), verbose_name="Dernière année d'inscription")
    organisme__sigle = tables.Column(verbose_name="Organisme")
    
    def render_photo(self,value,record):
        if record.enseignant :
            if record.enseignant.photo :
                return format_html("<img src='{}' width='80'>",record.enseignant.photo.url)
        if record.etudiant :
            if record.etudiant.photo :
                return format_html("<img src='{}' width='80'>",record.etudiant.photo.url)
        return ''
    
    def render_nom(self,value,record):
        if record.enseignant :
            if record.enseignant.nom :
                return record.enseignant.nom
        if record.etudiant :
            if record.etudiant.nom :
                return record.etudiant.nom
        return ''
    
    def render_prenom(self,value,record):
        if record.enseignant :
            if record.enseignant.prenom :
                return record.enseignant.prenom
        if record.etudiant :
            if record.etudiant.prenom :
                return record.etudiant.prenom
        return ''
    
    def render_annees_inscription(self,value,record):
        return format_html("<center><strong>"+str(record.annee_inscription())+"</strong></center>")
    
    action= '{% if record.etudiant %}<a href="{% url "etudiant_detail" pk=record.etudiant.matricule %}" class="btn btn-info" role="button"> Profil étudiant</a>{% endif %} \
    {% if record.enseignant %}<a href="{% url "enseignant_detail" pk=record.enseignant.id %}" class="btn btn-danger" role="button"> Profil enseignant</a>{% endif %}'
    detail=tables.TemplateColumn(action, orderable=False)
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalite_postgraduation_gestiondoctorants %}\
                <a href="{% url "doctorant_update" doctorant_pk=record.id %}" > {% icon "pencil-alt" %}</a> \
                <a href="{% url "doctorant_delete" pk=record.id %}" > {% icon "trash" %}</a>\
            {% endif %}'
    edit=tables.TemplateColumn(action, orderable=False)
           
    class Meta:
        model = Doctorant
        fields = ('nom', 'prenom', 'organisme__sigle', 'these__sujet__intitule', 'these__directeur', 'annees_inscription', 'photo')
        template_name= "django_tables2/bootstrap4.html"                   
           
class DoctorantFilter(django_filters.FilterSet):
    etudiant__matricule = django_filters.CharFilter(field_name='etudiant__matricule', lookup_expr='iexact', label ='Matricule étudiant')
    organisme = django_filters.ModelChoiceFilter(field_name='organisme',queryset = Organisme.objects.filter(interne=True), label ='Affiliation', empty_label='Affiliation')
    nom_prenoms = django_filters.CharFilter(label ='Nom/prénom(s) doctorant', method='nom_prenoms_lookup')
    specialite = django_filters.ModelChoiceFilter(label ="Spécialité", empty_label="Spécialite", queryset=Specialite.objects.filter(programme__doctorat=True).distinct(), method='specialite_lookup')

    def specialite_lookup(self, queryset, name, value):
        qs_=Doctorant.objects.none()
        if not qs_ :
            qs_=queryset.filter(etudiant__inscriptions__formation__programme__specialite__in=[value]).distinct()
        else :    
            qs_=(qs_ & queryset.filter(etudiant__inscriptions__formation__programme__specialite__in=[value]).distinct())
        return qs_
    
    def nom_prenoms_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=Doctorant.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(etudiant__nom__icontains=value_)|Q(enseignant__nom__icontains=value_)|Q(etudiant__prenom__icontains=value_)|Q(enseignant__prenom__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(etudiant__nom__icontains=value_)|Q(enseignant__nom__icontains=value_)|Q(etudiant__prenom__icontains=value_)|Q(enseignant__prenom__icontains=value_)).distinct())
        return qs_
    
    class Meta:
        model = Doctorant
        fields = ('etudiant__matricule', 'nom_prenoms','organisme', 'specialite') 

class TheseFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(field_name='sujet__resume', lookup_expr='icontains', label='Mot Clé dans la description')
    statut_validation = django_filters.ChoiceFilter(field_name='sujet__statut_validation', choices=STATUT_VALIDATION, label='Etat Validation', empty_label='Etat Validation')
    annee_universitaire = django_filters.ModelChoiceFilter(field_name='annee_univ', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label='Année Universitaire', empty_label='Année Univ')
    organisme = django_filters.ModelChoiceFilter(label ='Organisme', empty_label='Organisme', queryset=Organisme.objects.filter(interne=True), method='organisme_lookup')    
    
    def organisme_lookup(self, queryset, name, value):
        organisme_=value
        return These.objects.filter(Q(directeur__organisme=organisme_)|Q(codirecteur__organisme=organisme_)|Q(doctorant__organisme=organisme_))
    
    class Meta:
        model = These
        fields = ('id', 'annee_universitaire', 'statut_validation',)

class TheseTable(tables.Table):
    nb_avis=tables.Column(empty_values=(), orderable=False)
    codirecteur=tables.Column(empty_values=())
    directeur=tables.Column(empty_values=())
    action='{% load icons usergroup %}\
            <a href="{% url "these_detail" pk=record.id %}" > {% icon "eye" %} </a>\
            {% if user.is_authenticated %}\
                {% if record.sujet.statut_validation == "RR" or  record.sujet.statut_validation == "S" or  record.sujet.statut_validation == "N" %}\
                    {% if user.is_enseignant %}\
                        {% if request.user.enseignant == record.directeur or request.user.enseignant == record.codirecteur %}\
                            <a href="{% url "these_update" these_pk=record.id %}" class="btn btn-warning"  > Réviser </a>\
                        {% endif %}\
                    {% endif %}\
                {% elif record.sujet.statut_validation == "V" %}\
                    <a href="{% url "these_fiche_pdf" these_pk=record.id %}" > {% icon "file-pdf" %} </a>\
                {% endif %}\
            {% endif %}'
                
            
    detail   = tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            <a href="{% url "these_update" these_pk=record.id %}" > {% icon "pencil-alt" %}</a>\
            <a href="{% url "these_delete" pk=record.id %}" > {% icon "trash" %}</a>'
            
    edit   = tables.TemplateColumn(action, orderable=False)

    def render_nb_avis(self,value,record):
        if record.sujet :
            return record.sujet.nb_avis()
        else :
            return '/'

    def render_directeur(self,value,record):
        if record.directeur :
            if record.directeur.organisme :
                return format_html("<strong>"+record.directeur.organisme.sigle +"</strong> - "+str(record.directeur))
            else :
                return str(record.directeur)
        elif record.directeur_externe :
            return format_html("<strong>Externe </strong>- "+str(record.directeur_externe))
        else :
            return '/'

    def render_codirecteur(self,value,record):
        if record.codirecteur :
            if record.codirecteur.organisme :
                return format_html("<strong>"+record.codirecteur.organisme.sigle +"</strong> - "+str(record.codirecteur))
            else :
                return str(record.codirecteur)
        elif record.codirecteur_externe :
            return format_html("<strong>Externe </strong>- "+str(record.codirecteur_externe))
        else :
            return '/'  
        

    def render_doctorant(self,value,record):
        if record.doctorant :
            if record.doctorant.organisme :
                return format_html("<strong>"+record.doctorant.organisme.sigle +"</strong> - "+str(record.doctorant))
            else :
                return str(record.doctorant)
        else :
            return '/'  
    class Meta:
        model= These
        fields = ('id', 'annee_univ', 'sujet__intitule', 'directeur', 'codirecteur', 'doctorant', 'nb_avis', 'sujet__statut_validation')
        template_name= "django_tables2/bootstrap4.html"
        row_attrs = { "style": lambda record: "background-color: #e6e6e6;" if record.doctorant
                                        else "background-color: #66ff33;"}

class ProjetFilter(django_filters.FilterSet):
    annee_debut=django_filters.ModelChoiceFilter(field_name='annee_debut__annee_univ', lookup_expr='gte', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label="Min année début", empty_label="Min année début")
    annee_fin=django_filters.ModelChoiceFilter(field_name='annee_fin__annee_univ', lookup_expr='lte', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label="Max année fin", empty_label="Max année fin")
    titre = django_filters.CharFilter(field_name='titre', lookup_expr='icontains', label='Titre')
    type=django_filters.ChoiceFilter(field_name='type', choices=TYPE_PROJET, label="Type", empty_label="Type")
    organisme = django_filters.ModelChoiceFilter(field_name='organisme', empty_label='Organisme', queryset=Organisme.objects.filter(interne=True))        
    
    class Meta:
        model = Projet
        fields = ['type', 'organisme', 'annee_debut', 'annee_fin', 'titre']

class ProjetTable(tables.Table):
    action='{% load icons usergroup %}\
            <a href="{% url "projet_detail" pk=record.id %}" > {% icon "eye" %} </a>'
   
    detail   = tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            <a href="{% url "projet_update" pk=record.id %}" > {% icon "pencil-alt" %}</a>\
            <a href="{% url "projet_delete" pk=record.id %}" > {% icon "trash" %}</a>'
            
    edit   = tables.TemplateColumn(action, orderable=False)
    organisme__sigle   = tables.Column(orderable=False, verbose_name="Organisme")
    chef = tables.Column(empty_values=(), orderable=False, verbose_name="Chef")
    membres   = tables.Column(orderable=False, verbose_name="Membres")

    def render_chef(self,value,record):
        if record.chef :
            return str(record.chef)
        if record.chef_externe :
            return str(record.chef_externe)
        return "—"
    
    def render_membres(self,value,record):
        membres=""
        cpt=0
        for membre in record.membres.all() :
            cpt=cpt+1
            membres= membres + "<strong>"+str(cpt)+")</strong> "+str(membre) + '<br>'
        for membre in record.membres_doctorants.all() :
            cpt=cpt+1
            membres= membres + "<strong>"+str(cpt)+")</strong> "+str(membre) + '<br>'
    
        if record.membres_externes :
            liste_membres=record.membres_externes.replace('\n', '').split('\r')
            for membre in liste_membres :
                cpt=cpt+1
                membres= membres + "<strong>"+str(cpt)+")</strong> "+str(membre) + '<br>'

        return format_html(membres)
    
    def render_type(self,value,record):
        return str(record.type)
            
    class Meta:
        model= Projet
        fields=['code', 'type', 'titre', 'annee_debut', 'chef', 'membres', 'organisme__sigle']
        template_name= "django_tables2/bootstrap4.html"
        

class ProjetsEnseignantTable(tables.Table):
    role=tables.Column(empty_values=(), orderable=False, verbose_name="Rôle")
    titre=tables.Column(empty_values=(), orderable=False)
    action='{% load icons %}\
            {% if perms.scolar.fonctionnalite_postgraduation_gestionprojetsrecherche or request.user.enseignant and record.chef == request.user.enseignant %}\
                <a href="{% url "projet_update" pk=record.id %}"> {% icon "pencil-alt" %}</a>\
            {% endif %}'
    edit=tables.TemplateColumn(action, orderable=False)
    
    def __init__(self, *args, **kwargs):
        temp_enseignant = kwargs.pop("enseignant")
        super(ProjetsEnseignantTable, self).__init__(*args, **kwargs)
        self.enseignant=temp_enseignant
              
    def render_type(self,value,record):
        return str(record.type)

    def render_role(self, value, record):
        try :
            role_=''
            if record.chef == self.enseignant :
                role_='Chef du projet'
            elif self.enseignant in record.membres.all() :
                role_='Membre'
            return role_
        except Exception:
            return ''
        
    def render_titre(self,value,record):
        try :
            if get_institution().activation_public_projets or (self.request.user.is_authenticated and self.request.user.has_perm_or_teacher_himself('scolar.fonctionnalitenav_postgraduation_visualisationprojetsrecherche', self.enseignant.id)) :
                return format_html("<a href='{0}' target='_blank'><b>{1}</b></a>",reverse('projet_detail',kwargs={'pk': record.id}),record.titre)
            else :
                return format_html("<b>{}</b>",record.titre)
        except Exception:
            return ''

    class Meta:
        model= Projet
        fields = ['type', 'titre', 'annee_debut', 'annee_fin']
        template_name= "django_tables2/bootstrap4.html"
        
class CritereTable(tables.Table):  
    action= '{% load icons %}\
            {% if perms.scolar.fonctionnalite_postgraduation_gestioncriteres %}\
                <a href="{% url "critere_update" record.id %}">{% icon "pencil-alt" %}</a>\
                <a href="{% url "critere_delete" record.id %}">{% icon "trash" %}</a>\
            {% endif %}'
    edit   = tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model = Critere
        fields =('ordre','critere', 'options', 'programmes', 'commentaire')
        template_name= "django_tables2/bootstrap4.html"
        
class OptionCritereTable(tables.Table):
    action= '{% load icons %}\
            {% if perms.scolar.fonctionnalite_postgraduation_gestioncriteres %}\
                <a href="{% url "option_critere_update" record.id %}">{% icon "pencil-alt" %}</a>\
                <a href="{% url "option_critere_delete" record.id %}">{% icon "trash" %}</a>\
            {% endif %}'
    edit   = tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model = OptionCritere
        fields =('ordre','option')
        template_name= "django_tables2/bootstrap4.html" 
        
class FormationDoctoratTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "etat_avancement_list" formation_pk=record.id %}" class="btn btn-link"> États d\'avancement </a> '
    detail=tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model = Formation
        fields=('programme','annee_univ', 'archive')
        template_name= "django_tables2/bootstrap4.html"
        
class InscriptionDoctoratAvancementTable(tables.Table):
    annee_inscription=tables.Column(empty_values=(), orderable=False, verbose_name="Année d'inscription")
    decision_jury=tables.Column(empty_values=(), orderable=False, verbose_name="État d'inscription")
    etat_avancement=tables.Column(empty_values=(), orderable=False, verbose_name="État d'avancement")
    these=tables.Column(empty_values=(), orderable=False, verbose_name="Thèse")
    directeur_these=tables.Column(empty_values=(), orderable=False, verbose_name="Directeur de thèse")
    decision_labo=tables.Column(empty_values=(), orderable=False, verbose_name="Décision 1")
    decision_finale=tables.Column(empty_values=(), orderable=False, verbose_name="Décision finale")
        
    def render_annee_inscription(self,value,record):
        try :
            return format_html("<b>{}</b>",str(record.formation))
        except Exception:
            return '' 

    def render_etat_avancement(self,value,record):
        try :
            etat_avancement_qs=EtatAvancement.objects.filter(inscription__id=record.id)
            etat_avancement_=None
            html_code=""
            if etat_avancement_qs.exists() :
                etat_avancement_=etat_avancement_qs.first()
                these_=etat_avancement_.these()
                if not these_ :
                    return "Aucune thèse"
            if self.request.user.has_perm('scolar.fonctionnalite_postgraduation_gestionavancementdoctorants'):
                if etat_avancement_ :
                    html_code= html_code + "<a href='"+reverse('etat_avancement_update_jury', kwargs={'inscription_pk' : record.id })+"' class='btn btn-danger' role='button'> Modifier jury </a> "
                    html_code= html_code + "<a href='"+reverse('evaluation_etat_avancement', kwargs={'pk' : etat_avancement_.id })+"' class='btn btn-info' role='button'> Évaluer </a> "
                else :
                    html_code=html_code + "<a href='"+reverse('etat_avancement_create', kwargs={'inscription_pk' : record.id })+"' class='btn btn-info' role='button'> Nouveau </a>"
            
            if etat_avancement_ : 
                if not etat_avancement_.final :
                    if self.request.user.is_enseignant() and ((self.request.user.enseignant in etat_avancement_.jury.all()) or (self.request.user.enseignant == etat_avancement_.these().directeur)) :
                        html_code= html_code + "<a href='"+reverse('evaluation_etat_avancement', kwargs={'pk' : etat_avancement_.id })+"' class='btn btn-info' role='button'> Évaluer </a> "
                        if self.request.user.enseignant in etat_avancement_.jury.all() :
                            html_code=html_code + "<span> (Jury) </span>"
                        if self.request.user.enseignant == etat_avancement_.these().directeur :
                            html_code=html_code + "<span> (Avis Directeur de thèse)  </span>"
                else :
                    html_code=html_code + "<a href='"+reverse('evaluation_etat_avancement_pdf', kwargs={'pk' : etat_avancement_.id })+"' class='btn btn-success' role='button'> PV </a>"
                    
            else : 
                html_code=html_code+" Aucune évaluation créée" 
            return format_html(html_code)
        except Exception :
            return "Erreur"
        
    def render_these(self,value,record):
        try :
            these_=record.etudiant.doctorant.these
            return str(these_)
        except Exception :
            return ""

    def render_directeur_these(self,value,record):
        try :
            these_=record.etudiant.doctorant.these
            return str(these_.directeur)
        except Exception :
            return ""
    
    def render_decision_labo(self,value,record):
        try :
            etat_avancement_qs=EtatAvancement.objects.filter(inscription__id=record.id)
            etat_avancement_=None
            html_code="/"
            if etat_avancement_qs.exists() :
                etat_avancement_=etat_avancement_qs.first()
                decision=dict(DECISIONS_1).get(etat_avancement_.decision_1) if etat_avancement_.decision_1 else "/  "
                html_code=decision
                if self.request.user.has_perm('scolar.fonctionnalite_postgraduation_decisionslabos') :
                    html_code=html_code+"<a href='"+reverse('etat_avancement_decision_labo_update', kwargs={'pk' : etat_avancement_.id })+"' class='btn btn-info' role='button'> Modifier </a>"
            return format_html(html_code)
        except Exception :
            raise Exception
            return ""
        
    def render_decision_finale(self,value,record):
        try :
            etat_avancement_qs=EtatAvancement.objects.filter(inscription__id=record.id)
            etat_avancement_=None
            html_code="/"
            if etat_avancement_qs.exists() :
                etat_avancement_=etat_avancement_qs.first()
                decision=dict(DECISIONS_FINALES).get(etat_avancement_.decision_finale) if etat_avancement_.decision_finale else "/  "
                html_code=decision
                if self.request.user.has_perm('scolar.fonctionnalite_postgraduation_decisionsfinales') :
                    html_code=html_code+"<a href='"+reverse('etat_avancement_decision_finale_update', kwargs={'pk' : etat_avancement_.id })+"' class='btn btn-info' role='button'> Modifier </a>"
            return format_html(html_code)
        except Exception :
            raise Exception
            return ""
        
        
    
        
    class Meta:
        model = Inscription
        fields=('formation','etudiant', 'these', 'directeur_these', 'annee_inscription', 'decision_jury', 'decision_labo', 'decision_finale', 'etat_avancement')
        template_name= "django_tables2/bootstrap4.html" 
        

class SeminairesFilter(django_filters.FilterSet):
    annee_univ = django_filters.ModelChoiceFilter(field_name='annee_univ', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label='Année Universitaire', empty_label='Année Univ')
    organisme = django_filters.ModelChoiceFilter(field_name='inscriptions__etudiant__doctorant__organisme',queryset = Organisme.objects.filter(interne=True), label ="Affiliation d'au moins un des doctorants", empty_label="Affiliation d'au moins un des doctorants")
    # specialite = django_filters.ModelChoiceFilter(field_name='inscriptions__formation__programme__specialite',queryset = Specialite.objects.filter(programme__doctorat=True).distinct(), label ="Spécialité d'au moins un des doctorants", empty_label="Spécialité d'au moins un des doctorants")
    specialite = django_filters.ModelChoiceFilter(label ="Spécialité d'au moins un des doctorants", empty_label="Spécialite d'au moins un des doctorants", queryset=Specialite.objects.filter(programme__doctorat=True).distinct(), method='specialite_lookup')
    nom_prenoms = django_filters.CharFilter(label ='Nom/prénom(s) doctorant', method='nom_prenoms_lookup')

    def specialite_lookup(self, queryset, name, value):
        qs_=SeminaireSuivi.objects.none()
        if not qs_ :
            qs_=queryset.filter(inscriptions__formation__programme__specialite__in=[value]).distinct()
        else :    
            qs_=(qs_ & queryset.filter(inscriptions__formation__programme__specialite__in=[value]).distinct())
        return qs_
        
        
    def nom_prenoms_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=SeminaireSuivi.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(inscriptions__etudiant__nom__icontains=value_)|Q(inscriptions__etudiant__prenom__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(inscriptions__etudiant__nom__icontains=value_)|Q(inscriptions__etudiant__prenom__icontains=value_)).distinct())
        return qs_

    
    class Meta:
        model= SeminaireSuivi
        fields=['annee_univ','nom_prenoms', 'organisme', 'specialite']   
             
class SeminairesTable(tables.Table):
    animateur=tables.Column(empty_values=())

    def render_animateur(self,value,record):
        if record.animateur_interne :
            return str(record.animateur_interne)
        elif record.animateur_externe :
            return format_html("<strong>Externe </strong>- "+str(record.animateur_externe))
        else :
            return '/'
    def render_inscriptions(self,value,record):
        if record.inscriptions.all() :
            inscriptions=""
            for inscription_ in record.inscriptions.all() :
                inscriptions=inscriptions+"<strong>- </strong>"+str(inscription_)+"<br>"
            return format_html(inscriptions)     
        else :
            return '/'
    
    action= '{% load icons %}\
             {% if perms.scolar.fonctionnalite_postgraduation_visualisationseminaires %}\
            <a href=" {% url "detail_seminaire" pk=record.id %}" > {% icon "eye" %}</a> \
            {% endif %}'   
    detail   = tables.TemplateColumn(action, orderable=False) 
    
    action= '{% load icons %}\
             {% if perms.scolar.fonctionnalite_postgraduation_gestionseminaires %}\
            <a href="{% url "seminaire_update" seminaire_pk=record.id %} " > {% icon "pencil-alt" %}</a>\
            <a href="{% url "seminaire_delete" pk=record.id %} " > {% icon "trash" %}</a>\
            {% endif %}'  
    edit   = tables.TemplateColumn(action, orderable=False) 
    class Meta:
        model = SeminaireSuivi
        fields=('annee_univ','inscriptions','matiere__titre','animateur','matiere__credit')
        template_name= "django_tables2/bootstrap4.html"
        

class DomaineConnaissanceTable(tables.Table):
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
                <a href="{% url "ddc_update" pk=record.id %}" > {% icon "pencil-alt" %} </a>\
            {% endif %}\
            {% if perms.scolar.fonctionnalitenav_pedagogie_gestionprogrammes %}\
                <a href="{% url "ddc_delete" pk=record.id %}" > {% icon "trash" %} </a>\
            {% endif %}'
                  
    edit= tables.TemplateColumn(action, orderable=False)
    class Meta:
        model = DomaineConnaissance
        fields = ['intitule',]
        template_name= "django_tables2/bootstrap4.html"

class PosteTable(tables.Table):
    action= '{% load icons %}\
            {% if perms.scolar.fonctionnalite_postes_gestion %}\
                <a href="{% url "poste_update" record.id %}">{% icon "pencil-alt" %}</a>\
                <a href="{% url "poste_delete" record.id %}">{% icon "trash" %}</a>\
            {% endif %}'
    edit   = tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model = Poste
        fields =('inscription','specialite', 'organisme', 'responsable', 'responsable_ext')
        template_name= "django_tables2/bootstrap4.html"

class PosteFilter(django_filters.FilterSet):
    organisme = django_filters.ModelChoiceFilter(field_name='organisme', queryset=Organisme.objects.all().order_by('sigle'), label='Organisme', empty_label='Organisme')
    specialite= django_filters.ModelChoiceFilter(field_name='specialite', queryset=Specialite.objects.all().order_by('code'), label='Spécialité', empty_label='Spécialité')    
    nom_prenoms = django_filters.CharFilter(label ='Nom/prénom(s) étudiant', method='nom_prenoms_lookup')

    def nom_prenoms_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=Poste.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(inscription__etudiant__nom__icontains=value_)|Q(inscription__etudiant__prenom__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(inscription__etudiant__nom__icontains=value_)|Q(inscription__etudiant__prenom__icontains=value_)).distinct())
        return qs_
    
    class Meta:
        model = Poste
        fields = ('nom_prenoms', 'organisme', 'specialite')

class ProgrammeDetteTable(tables.Table):
    action = '{% load icons %}\
                <a href="{% url "dette_list" programme_pk=record.id %}" class="btn btn-info" > {% icon "list" %} Liste des dettes </a>'
    detail= tables.TemplateColumn(action, orderable=False) 
    tableau="<table>\
        <tr><th>Année</th><th>En attente</th><th>En cours</th><th>Terminées</th><th>Total</th></tr>\
        {% for formation in record.formation_list.all %}<tr><td>{{ formation.annee_univ }}</td><td>{{ formation.dettes_en_attente_count }}</td><td>{{ formation.dettes_en_cours_count }}</td><td>{{ formation.dettes_terminees_count }}</td><td>{{ formation.dettes_total_count }}</td></tr>{% endfor %}\
        </table>"
     
    statistiques = tables.TemplateColumn(tableau, orderable=False) 
    
    
    class Meta:
        model = Programme
        fields = ('code', 'titre', 'statistiques', 'detail')
        template_name= "django_tables2/bootstrap4.html"

class DetteTable(tables.Table):
#     quittance=tables.Column()
#     def render_quittance(self,value,record):
#         return format_html("<img src='{}' width='300'>",value.url)

    action='{% load icons %}\
            <a href="{% url "dette_update" pk=record.id %}" class="btn btn-warning"> Modifier </a> '
    edit=tables.TemplateColumn(action, orderable=False)

    colonne="<table><tr><th>Moy</th>{% if record.activation_rattrapage %}<th>MoyRattrapage</th>{% endif %}<th>MoyFinale</th></tr><tr><td>{{ record.moy }}</td>{% if record.activation_rattrapage %}<td>{{ record.moy_rattrapage }}</td>{% endif %}<td>{{ record.moyenne_finale }}</td></tr></table>"
    ancienne_moyenne = tables.TemplateColumn(colonne, orderable=False)

    colonne="{% load icons %}<table><tr><th></th><th>Moy</th>{% if record.activation_rattrapage %}<th>MoyRattrapage</th>{% endif %}<th>MoyFinale</th></tr>{% for resultat in record.nouveaux_resultats_dette %}<tr><td>{{ resultat.module }} <a href=\"{% url \"resultat_dette_delete\" pk=resultat.id %}\" > {% icon \"trash\" %} </a></td><td>{{ resultat.moy }}</td>{% if record.activation_rattrapage %}<td>{{ resultat.moy_rattrapage }}</td>{% endif %}<td>{{ resultat.moyenne_finale }}</td></tr>{% endfor %}</table>"
    nouvelle_moyenne = tables.TemplateColumn(colonne, orderable=False)
    
    class Meta:
        model = Resultat
        fields=('inscription__formation__annee_univ', 'inscription__etudiant', 'module', 'etat_dette', 'ancienne_moyenne', 'nouvelle_moyenne')
        template_name= "django_tables2/bootstrap4.html"

class DetteFilter(django_filters.FilterSet):
    annee_univ=django_filters.ModelChoiceFilter(field_name='inscription__formation__annee_univ', queryset=AnneeUniv.objects.all().order_by('-annee_univ'), label="Année Universitaire", empty_label="Année Universitaire")
    nom_prenoms = django_filters.CharFilter(label ='Nom/prénom(s) étudiant', method='nom_prenoms_lookup')
    etat_dette=django_filters.ChoiceFilter(field_name='etat_dette', choices=STATUT_DETTE, label="Etat de la dette", empty_label="Etat de la dette")
    matiere = django_filters.CharFilter(field_name='module__matiere__code', lookup_expr='icontains', label='Matière')
    
    def nom_prenoms_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=PFE.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(inscription__etudiant__nom__icontains=value_)|Q(inscription__etudiant__prenom__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(inscription__etudiant__nom__icontains=value_)|Q(inscription__etudiant__prenom__icontains=value_)).distinct())
        return qs_    

    class Meta:
        model = Resultat
        fields = ('annee_univ', 'nom_prenoms', 'etat_dette', 'matiere')


class UserFilter(django_filters.FilterSet):
    username = django_filters.ModelChoiceFilter(widget=ModelSelect2Widget(model=User, search_fields=['username__icontains', 'email__icontains', 'first_name__icontains', 'last_name__icontains'], attrs={'style':'width:300px', 'data-placeholder':"Recherche d'un utilisateur"}), queryset=User.objects.all())
    
    class Meta:
        model = User
        fields = ('username',)
        
class PersonnelTable(tables.Table):
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalite_configurationetablissement_modification %}\
                <a href="{% url "personnel_update" pk=record.id %}" > {% icon "pencil-alt" %} </a>\
                <a href="{% url "personnel_delete" pk=record.id %}" > {% icon "trash" %} </a>\
            {% endif %}'
    edit= tables.TemplateColumn(action, orderable=False)
    user =tables.Column(empty_values=(), orderable=False, verbose_name="Utilisateur")
    
    class Meta:
        model = Personnel
        fields=('user', 'nom','eps', 'prenom', 'nom_a', 'eps_a', 'prenom_a', 'sexe', 'tel', 'bureau',)
        template_name= "django_tables2/bootstrap4.html"
        
class PaysTable(tables.Table):
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalite_configurationetablissement_modification %}\
                <a href="{% url "pays_update" pk=record.code %}" > {% icon "pencil-alt" %} </a>\
                <a href="{% url "pays_delete" pk=record.code %}" > {% icon "trash" %} </a>\
            {% endif %}'
    edit= tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model = Pays
        fields=('code', 'nom',)
        template_name= "django_tables2/bootstrap4.html"

class WilayaTable(tables.Table):
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalite_configurationetablissement_modification %}\
                <a href="{% url "wilaya_update" pk=record.code %}" > {% icon "pencil-alt" %} </a>\
                <a href="{% url "wilaya_delete" pk=record.code %}" > {% icon "trash" %} </a>\
            {% endif %}'
    edit= tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model =Wilaya
        fields=('code', 'nom',)
        template_name= "django_tables2/bootstrap4.html"
        
class CommuneTable(tables.Table):
    action = '{% load icons %}\
            {% if perms.scolar.fonctionnalite_configurationetablissement_modification %}\
                <a href="{% url "commune_update" pk=record.code_postal %}" > {% icon "pencil-alt" %} </a>\
                <a href="{% url "commune_delete" pk=record.code_postal %}" > {% icon "trash" %} </a>\
            {% endif %}'
    edit= tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model =Commune
        fields=('code_postal', 'nom', 'wilaya')
        template_name= "django_tables2/bootstrap4.html"
        
class EnregistrementEtudiantTable(tables.Table):
    action='{% load icons %}\
            <a href="{% url "enregistrement_etudiant_update" enregistrement_etudiant_pk=record.id %}"> {% icon "pencil-alt" %} </a>'
    traitement=tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            <a href="{% url "enregistrement_etudiant_delete" pk=record.id %}"> {% icon "trash" %} </a>'
    suppression=tables.TemplateColumn(action, orderable=False)
    
    class Meta:
        model = EnregistrementEtudiant
        fields = ('user', 'nom', 'prenom', 'programme', 'statut', 'created_at',)
        template_name= "django_tables2/bootstrap4.html"

class EnregistrementEtudiantFilter(django_filters.FilterSet):
    nom_prenoms = django_filters.CharFilter(label ='Nom et/ou prénom(s)', method='nom_prenoms_lookup')
    programme = django_filters.ModelChoiceFilter(field_name='programme', queryset=Programme.objects.all().order_by('ordre'), label='Programme', empty_label='Programme')
    statut = django_filters.ChoiceFilter(field_name='statut', choices=STATUT_ENREGISTREMENT, label="Statut", empty_label="Statut")
    class Meta:
        model = EnregistrementEtudiant
        fields = ('nom_prenoms', 'programme', 'statut')
        
    def nom_prenoms_lookup(self, queryset, name, value):
        all_values=value.split()
        qs_=EnregistrementEtudiant.objects.none()
        for value_ in all_values :
            if not qs_ :
                qs_=queryset.filter(Q(nom__icontains=value_)|Q(prenom__icontains=value_)).distinct()
            else :    
                qs_=(qs_ & queryset.filter(Q(nom__icontains=value_)|Q(prenom__icontains=value_)).distinct())
        return qs_



class EquipeRechercheFilter(django_filters.FilterSet):
    organisme = django_filters.ModelChoiceFilter(field_name='organisme', empty_label='Organisme', queryset=Organisme.objects.filter(interne=True))        
    
    class Meta:
        model = EquipeRecherche
        fields = ['organisme',]

class EquipeRechercheTable(tables.Table):
    action='{% load icons usergroup %}\
            <a href="{% url "equiperecherche_detail" pk=record.id %}" > {% icon "eye" %} </a>'
   
    detail   = tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            <a href="{% url "equiperecherche_update" pk=record.id %}" > {% icon "pencil-alt" %}</a>\
            <a href="{% url "equiperecherche_delete" pk=record.id %}" > {% icon "trash" %}</a>'
            
    edit   = tables.TemplateColumn(action, orderable=False)
    organisme__sigle   = tables.Column(orderable=False, verbose_name="Organisme")
    responsable = tables.Column(empty_values=(), orderable=False, verbose_name="Responsable")
    membres   = tables.Column(orderable=False, verbose_name="Membres")

    def render_responsable(self,value,record):
        if record.responsable :
            return str(record.responsable)
        if record.responsable_externe :
            return str(record.responsable_externe)
        return "—"
    
    def render_membres(self,value,record):
        membres=""
        cpt=0
        for membre in record.membres.all() :
            cpt=cpt+1
            membres= membres + "<strong>"+str(cpt)+")</strong> "+str(membre) + '<br>'
        for membre in record.membres_doctorants.all() :
            cpt=cpt+1
            membres= membres + "<strong>"+str(cpt)+")</strong> "+str(membre) + '<br>'
    
        if record.membres_externes :
            liste_membres=record.membres_externes.replace('\n', '').split('\r')
            for membre in liste_membres :
                cpt=cpt+1
                membres= membres + "<strong>"+str(cpt)+")</strong> "+str(membre) + '<br>'

        return format_html(membres)
    
    def render_type(self,value,record):
        return str(record.type)
            
    class Meta:
        model= EquipeRecherche
        fields=['code', 'nom', 'responsable', 'membres', 'organisme__sigle']
        template_name= "django_tables2/bootstrap4.html"

class EquipeRechercheEnseignantTable(tables.Table):
    role=tables.Column(empty_values=(), orderable=False, verbose_name="Rôle")
    code=tables.Column(empty_values=(), orderable=False)
    action='{% load icons %}\
            {% if perms.scolar.fonctionnalite_postgraduation_gestionequipesrecherche or request.user.enseignant and record.responsable == request.user.enseignant %}\
                <a href="{% url "equiperecherche_update" pk=record.id %}"> {% icon "pencil-alt" %}</a>\
            {% endif %}'
    edit=tables.TemplateColumn(action, orderable=False)

    def __init__(self, *args, **kwargs):
        temp_enseignant = kwargs.pop("enseignant")
        super(EquipeRechercheEnseignantTable, self).__init__(*args, **kwargs)
        self.enseignant=temp_enseignant
        
    def render_role(self, value, record):
        try :
            role_=''
            if record.responsable == self.enseignant :
                role_='Responsable de l\'équipe'
            elif self.enseignant in record.membres.all() :
                role_='Membre'
            return role_
        except Exception:
            return ''
        
    def render_code(self,value,record):
        try :
            if get_institution().activation_public_equipesrecherche or (self.request.user.is_authenticated and self.request.user.has_perm_or_teacher_himself('scolar.fonctionnalitenav_postgraduation_visualisationequipesrecherche', self.enseignant.id)) :
                return format_html("<a href='{0}' target='_blank'><b>{1}</b></a>",reverse('equiperecherche_detail',kwargs={'pk': record.id}),record.code)
            else :
                return format_html("<b>{}</b>",record.code)
        except Exception:
            return ''

    def render_nom(self,value,record):
        try :
            if get_institution().activation_public_equipesrecherche or (self.request.user.is_authenticated and self.request.user.has_perm_or_teacher_himself('scolar.fonctionnalitenav_postgraduation_visualisationequipesrecherche', self.enseignant.id)) :
                return format_html("<a href='{0}' target='_blank'><b>{1}</b></a>",reverse('equiperecherche_detail',kwargs={'pk': record.id}),record.nom)
            else :
                return format_html("<b>{}</b>",record.nom)
        except Exception:
            return ''

    class Meta:
        model= EquipeRecherche
        fields = ['code', 'nom', 'role']
        template_name= "django_tables2/bootstrap4.html"

class OffreFilter(django_filters.FilterSet):
    type = django_filters.ChoiceFilter(field_name='type', choices=TYPE_OFFRE, label='Type', empty_label='Type')
    statut = django_filters.ChoiceFilter(field_name='statut', choices=STATUT_OFFRE, label='Statut de l\'offre', empty_label='Statut de l\'offre')

    class Meta:
        model = Offre
        fields = ('type', 'statut')

class OffreTable(tables.Table):
    organisme__sigle = tables.Column(verbose_name="Organisme")
    action='{% load icons usergroup %}\
            <a href="{% url "offre_detail" pk=record.id %}" > {% icon "eye" %} </a>\
            {% if record.activation_candidatures and record.user and record.user != user and record.statut == "S" %}\
                <br><a href="{% url "candidature_create" offre_pk=record.id %}" class="btn btn-warning"  > Candidater </a> \
            {% endif %}'
    detail   = tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            {% if user.is_authenticated %}\
                    <style>\
                        .nombre-candidatures{\
                            border-radius:20%;\
                            height: 24px;\
                            line-height: 20px;\
                            display: inline-block;\
                            text-align: center;\
                            padding: 2px;\
                            padding-right: 6px;\
                            padding-left: 6px;\
                            color:white;\
                            white-space:nowrap;\
                        }\
                        .nombre-candidatures:hover{\
                            color:white;\
                            }\
                        </style>\
                        {% if record.nb_candidatures %}\
                           <a class="nombre-candidatures" style="background:green;" href="{% url "offre_detail" pk=record.id %}"><strong>{{ record.nb_candidatures }}</strong> Candidature(s)</a><br><br>\
                        {% endif %}\
                {% if perms.scolar.fonctionnalitenav_offres_validation or record.user and record.user == user %}\
                    <a href="{% url "offre_update" pk=record.id %}" class="btn btn-warning"  > Modifier </a> \
                    <a href="{% url "offre_delete" pk=record.id %}" class="btn btn-danger"> Supprimer </a>\
                {% endif %}\
            {% endif %}'
    edit   = tables.TemplateColumn(action, orderable=False)

    def render_date(self,value,record):
        try :
            return value.strftime("%d/%m/%Y")
        except Exception:
            return ''       
             
    class Meta:
        model= Offre
        fields = ('id', 'type', 'intitule', 'user', 'emetteur', 'organisme__sigle', 'date', 'statut')
        template_name= "django_tables2/bootstrap4.html"


class CandidatureTable(tables.Table):
    action='{% load icons usergroup %}\
            <a href="{% url "candidature_detail" pk=record.id %}" > {% icon "eye" %} </a>'
    
    detail   = tables.TemplateColumn(action, orderable=False)
    action='{% load icons %}\
            {% if user.is_authenticated %}\
                {% if perms.scolar.fonctionnalitenav_offres_validation or record.user and record.user == user %}\
                    {% if record.user and record.user == user %}\
                        <a href="{% url "candidature_update" pk=record.id %}" class="btn btn-warning"  > Modifier </a> \
                    {% endif %}\
                    <a href="{% url "candidature_delete" pk=record.id %}" class="btn btn-danger"> Supprimer </a>\
                {% endif %}\
            {% endif %}'
    edit   = tables.TemplateColumn(action, orderable=False)

    def render_date_time(self,value,record):
        try :
            if settings.USE_TZ:
                timezoneLocal = pytz.timezone(settings.TIME_ZONE)
                str_= value.astimezone(timezoneLocal).strftime("%d/%m/%Y %H:%M")
            else :
                str_= value.strftime("%d/%m/%Y %H:%M")
            
            if record.last_edit :
                if settings.USE_TZ:
                    timezoneLocal = pytz.timezone(settings.TIME_ZONE)
                    str_= str_+ " - Dernière modification : "+record.last_edit.astimezone(timezoneLocal).strftime("%d/%m/%Y %H:%M")
                else :
                    str_= str_+ " - Dernière modification : "+record.last_edit.strftime("%d/%m/%Y %H:%M")
                
            return str_
        except Exception:
            return ''     
             
    class Meta:
        model= Candidature
        fields = ('user', 'nom', 'prenom', 'offre', 'date_time',)
        template_name= "django_tables2/bootstrap4.html"
