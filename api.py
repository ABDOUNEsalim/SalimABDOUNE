from rest_framework.views import APIView
from rest_framework.response import Response

from django.shortcuts import render, get_object_or_404
from django_tables2.config import RequestConfig
import threading
from django.db import transaction
from django.template import loader
import requests
from scolar.models import *
import os
from django.utils.safestring import mark_safe
from scolar.tables import OrganismeTable, OrganismeFilter, PFETable, PFEFilter, ValidationTable, MatiereTable, MatiereFilter, InscriptionEtudiantDocumentsTable, InscriptionEtudiantTable, InscriptionFilter, InscriptionGroupeTable, InscriptionTable,\
    EvaluationCompetenceElementTable, EvaluationTable, AbsenceEnseignantFilter,  AbsenceEnseignantTable, AbsenceEtudiantFilter, AbsenceEtudiantTable, ActiviteChargeConfigTable, \
    CompetenceElementTable, CompetenceFamilyTable, CompetenceTable, MatiereCompetenceElementTable, DiplomeTable, CycleTable, AutoriteTable, SpecialiteTable, PeriodeTable, DeliberationFormationTable, PVFilter, \
    ProgrammeTable, FormationTable, PlanificationTable, EtudiantFilter,  EtudiantTable, EnseignantFilter, EnseignantTable, SectionTable, FormationFilter, \
    GroupeAllFilter, GroupeAllTable, GroupeTable, NotesFormationTable, TutoratTable, ModuleFeedbackTable, ModuleFilter, ModuleTable, ChargeEnseignantTable, PVTable, PVEnseignantTable,\
    CoordinationModuleFilter, SemainierTable, FeedbackTable, AnneeUnivTable, SeanceTable, ActiviteEtudiantFilter, ActiviteEtudiantTable, ActiviteTable, ActiviteFilter,\
    PreinscriptionTable, ResidenceUnivTable, PreinscriptionFilter, ExamenTable, ExamenFilter, SalleFilter, SalleTable, PlaceEtudiantFilter, PlaceEtudiantTable,\
    SurveillanceFilter, SurveillanceTable, EnseignementsTable,EncadrementsTable,EncadrementsAttestationTable, SoutenancesAttestationTable, ProgresFormationTable, TraceTable, TraceFilter,\
    NotificationsTable, UserTable, ExportTable, DoctorantTable, DoctorantFilter, TheseFilter, TheseTable, ProjetFilter, ProjetTable, ProjetsEnseignantTable, CritereTable, OptionCritereTable, FormationDoctoratTable, InscriptionDoctoratAvancementTable, SeminairesFilter, SeminairesTable, \
    DomaineConnaissanceTable, PosteTable, PosteFilter, ProgrammeDetteTable, DetteFilter, DetteTable, UserFilter, PersonnelTable, PaysTable, WilayaTable, CommuneTable, SurveillancesEnseignantFilter, EnregistrementEtudiantTable, EnregistrementEtudiantFilter, EquipeRechercheFilter, EquipeRechercheTable, EquipeRechercheEnseignantTable, ExpertisesPFEAttestationTable, OffreFilter, OffreTable, CandidatureTable
    
from functools import reduce
from django.contrib.messages.views import SuccessMessageMixin
from django.core.mail import EmailMessage, send_mass_mail
from django.views.generic.base import TemplateView
from django.db.models.signals import post_save, m2m_changed, post_delete, pre_delete
from django.db.models import Q, Count, Sum, When, Value, Case, F, Max, Min, Avg, OuterRef, Subquery
from django.db.models.functions import Cast, StrIndex, Substr
from django.dispatch import receiver
from scolar.forms import EnseignantDetailForm, AbsenceEtudiantReportSelectionForm, SeanceEtudiantSelectionForm, OTPImportFileForm, PFEDetailForm, OrganismeForm, SelectOrCreateOrganismeForm, COMPETENCE_EVAL, InscriptionUpdateForm, SelectChargeConfigForm, SelectPVSettingsForm, ChargeFilterForm, EvaluationCompetenceForm, NotesPFEUpdateForm, SeanceSelectionForm, PlanificationImportFileForm, EDTForm, CompetenceForm, FeedbackUpdateForm, SelectModuleForm, ReleveNotesUpdateForm, ImportDeliberationForm, AbsencesForm, ImportNotesForm, NotesUpdateForm, ImportFileForm, ImportAffectationForm, MatiereFormHelper, ImportFeedbackForm,\
     SelectionFormationForm, SelectSingleModuleForm, ImportAffectationDiplomeForm, ImportChargeForm, SelectPVAnnuelSettingsForm,DateSelectForm,\
    CommissionValidationCreateForm, ExamenCreateForm, SeanceSallesReservationForm, SurveillanceUpdateForm, InstitutionDetailForm,\
    SelectionInscriptionForm, ValidationPreInscriptionForm, EDTImportFileForm, EDTSelectForm, ExamenSelectForm, AffichageExamenSelectForm,\
    SalleConfigForm, ExamenUpdateForm, ExamenListSelectForm, AbsenceEtudiantSelectForm, SurveillanceListSelectForm, PartenaireCreateForm, ReservationPlaceEtudiantUpdateForm, PermissionsUpdateForm, UserChoiceForm, PermissionsUserUpdateForm, IntervalleDateSelectForm, DoctorantCreateForm, DoctorantUpdateForm, TheseCreateForm, TheseUpdateForm, TheseDetailForm, ProjetDetailForm, EtatAvancementCreateForm, EtatAvancementUpdateJuryForm, EvaluationEtatAvancementForm, SeminaireCreateForm, SeminaireDetailForm, SeminaireUpdateForm, DocumentsConfigUpdateForm, PassageSettingsForm, DetteUpdateForm, UserCreateForm, UserUpdateForm,\
    PasswordUpdateForm, EtudiantMatriculeUpdateForm, EnregistrementEtudiantCreateForm, EnregistrementEtudiantUpdateForm, SelectionEtudiantForm, EquipeRechercheDetailForm, SelectOrCreateOrganismeOffreForm, OffreDetailForm, CandidatureDetailForm, DemandeCompteForm

#from scolar.forms import *
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound, Http404, HttpResponseForbidden
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, HTML, Button
from crispy_forms.bootstrap import TabHolder, Tab
from django.urls import reverse
from django import forms
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
import random
from bootstrap_datepicker_plus import DatePickerInput
from scolar.admin import settings
from jchart import Chart
from jchart.config import DataSet
from django.shortcuts import redirect
import urllib
from django.contrib import messages
from tablib import Dataset, Databook
from django_select2.forms import ModelSelect2Widget, Select2Widget, ModelSelect2MultipleWidget, Select2MultipleWidget
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
import datetime
from django.core.files.storage import default_storage
from django.contrib.auth.models import Group, Permission
import decimal
from wkhtmltopdf.views import PDFTemplateView, render_pdf_from_template
from django.db.models.aggregates import Avg
from django.contrib.auth.decorators import user_passes_test, permission_required,\
    login_required

from django.db.models.expressions import ExpressionWrapper
from django.db.models.fields import FloatField, DecimalField
import re, string
import operator
from _ast import If, In
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from uuid import uuid4
import pytz
from builtins import Exception
from time import sleep
from pyasn1.type.char import VideotexString
from django.http.response import FileResponse
from django.http import HttpResponseForbidden
from scolar.webhelp import *
from django.utils.html import format_html

#Module pour generation du fichier word
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

import pybase64
import tempfile

from django.views.static import serve
from mimetypes import guess_type
import io

from django.contrib.auth import update_session_auth_hash, login, authenticate
from django.contrib.auth.hashers import check_password

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from scolar import views
from scolar import models
from scolar import tables
from scolar import tests
from scolar import apps
from scolar import admin


 # class MyView(APIView):
 #    def get(self, request):
 #        # your view logic here
 #     return Response({'message': 'Hello, world!'})
 
class AbsencesAPI(APIView):
    def get(self, request):
        all_objects=AbsenceEtudiant.objects.none()
        if self.request.user.is_authenticated :
            if self.request.user.is_etudiant() :
                all_objects = AbsenceEtudiant.objects.filter(etudiant=self.request.user.etudiant, seance__activite__module__formation__annee_univ__encours=True).order_by('-seance__date', '-seance__heure_debut')
            if self.request.user.is_enseignant() :
                #absences des étudiants enseignés durant l'année en cours
                all_objects= (all_objects | AbsenceEtudiant.objects.filter(seance__activite__assuree_par__in=[self.request.user.enseignant] ,seance__activite__module__formation__annee_univ__encours=True).order_by('-seance__date', '-seance__heure_debut', 'etudiant__nom', 'etudiant__prenom')).distinct()
        serializer = AbsenceEtudiantSerializer(all_objects, many=True)
        return Response(serializer.data)

    def post(self):
        pass
#-------------------------------------------------   
class ResultatsAPI(APIView):
    def get(self, request):
        all_objects=Resultat.objects.none()
        if self.request.user.is_authenticated :
            if self.request.user.is_etudiant() :
                all_objects = Resultat.objects.filter(inscription__etudiant=self.request.user.etudiant, inscription__formation__annee_univ__encours=True).order_by('module__matiere__code', 'module__periode__code')
            if self.request.user.is_enseignant() : 
                #résultats des étudiants enseignés durant l'année en cours
                all_activites = Activite.objects.filter(module__formation__annee_univ__encours=True).filter((Q(module__coordinateur=self.request.user.enseignant) | (Q(assuree_par__in=[self.request.user.enseignant])&(~Q(type__startswith='E_'))))).distinct().order_by('module__periode__code')
                for activite_ in all_activites :
                    periodepgm_= activite_.module.periode
                    all_results = Resultat.objects.filter(module=activite_.module, inscription__inscription_periodes__periodepgm=periodepgm_, inscription__inscription_periodes__groupe__in=activite_.cible.all())
                    all_objects = all_objects | all_results
                all_objects = all_objects.distinct().order_by('module__matiere__code','inscription__groupe__code',  'inscription__etudiant__nom', 'inscription__etudiant__prenom')
            
        serializer = ResultatSerializer(all_objects, many=True)
        return Response(serializer.data)

    def post(self):
        pass     
#------------------------------------------------
class EDTEtudiantAPI(APIView):
    def get(self, request):
        all_objects=EDTEtudiant.objects.none()
        if self.request.user.is_authenticated :
            if self.request.user.is_etudiant() :
                serializer = EDTEtudiant.objects.filter(etudiant=self.request.user.etudiant, seance__activite__module__formation__annee_univ__encours=True).order_by('-seance__date', '-seance__heure_debut')
          
        return Response(serializer.data)

    def post(self):
        pass    
#------------------------------------------------
class activation_authentification_google(APIView):
    def get(self, request):
     try :
        institution_ = Institution.objects.all()
        if institution_.exists():
            institution_=institution_[0]
            return institution_.activation_authentification_google
        else :
            return False
     except Exception :
         raise Exception
      
    def post(self):
        pass        
#----------------------------------------------------    
class  get_groupe_list_from_str(APIView):
    def get(self, request):
     def get_groupe_list_from_str(student_set):
      groupe_list=[]
      str_groupe_list=student_set.split('+')
      for str_groupe in str_groupe_list:
        groupe_elements=str_groupe.split()
        formation_str=groupe_elements[0]
        section_str=groupe_elements[1]
        groupe_str=groupe_elements[2] if len(groupe_elements)==3 else None
        if groupe_str:
            groupe=get_object_or_404(Groupe, code=groupe_str, section__code=section_str, section__formation__programme__code=formation_str, section__formation__annee_univ__encours=True)
        else:
            groupe=get_object_or_404(Groupe, code__isnull=True, section__code=section_str, section__formation__programme__code=formation_str, section__formation__annee_univ__encours=True)
        groupe_list.append(groupe)
        
        return groupe_list
    
    def post(self):
        pass        
    
#----------------------------------------------------------
class get_enseignant_list_from_str(APIView):
 def get(self, request):
    def get_enseignant_list_from_str(teacher_set, separator):
     """
         Cette fonction est utilisée pour retrouver la liste des enseignants de la base de Talents
         qui correspondent à la liste des enseignants générée dans les activités importées de l'export de FET.
         Attention, il faut que les noms de enseignants dans FET correspondent aux noms dans la base de Talents
     """
     enseignant_list=[]
     str_enseignant_list=teacher_set.split(separator)
     for str_enseignant in str_enseignant_list:
         enseignant_elements=str_enseignant.split()
         #traiter les noms composés
         prenom_initial=enseignant_elements[len(enseignant_elements)-1]
         nom_=enseignant_elements[0]
         for i in range(1, len(enseignant_elements)-1):
             nom_+=' '+enseignant_elements[i]
        
         enseignant=Enseignant.objects.get(nom__icontains=nom_, prenom__startswith=prenom_initial)
         enseignant_list.append(enseignant)
         
     return enseignant_list
 def post(self):
       pass     
 #--------------------------------------------------------------------
 class releve_notes_list_pdf_view(APIView):
  def get(self, request):  
    def releve_notes_list_pdf_view(request, formation_pk, periode_pk):
     if not (request.user.has_perm('scolar.fonctionnalitenav_etudiants_documentsgroupes')):
        messages.error(request,"Vous n'avez pas la permission d'exécution de cette opération")
        return redirect('/accounts/login/?next=%s' % request.path)
    try:
        t = threading.Thread(target=views.task_releves_notes_pdf,args=[formation_pk, request.user])
        t.setDaemon(True)
        t.start()
        messages.success(request,"Votre demande de génération des relevés de notes est prise en compte.")
        messages.success(request,"Une notification vous sera transmise une fois la tâche terminée.")

    except Exception:
        if settings.DEBUG:
            raise Exception
        else:
            messages.error(request,"ERREUR: lors de génération des relevés de notes. Merci de le signaler à l'administrateur.")
    return HttpResponseRedirect(reverse('document_list'))
 def post(self):
     pass     
 #--------------------------------------------------------------------
 