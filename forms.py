from django import forms
from scolar.models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Field, HTML
from django.shortcuts import get_object_or_404
from crispy_forms.layout import Submit, Button, Hidden
from crispy_forms.bootstrap import TabHolder, Tab, FormActions
from django.urls import reverse
from django_select2.forms import ModelSelect2Widget, Select2Widget, ModelSelect2MultipleWidget, Select2MultipleWidget
from bootstrap_datepicker_plus import DatePickerInput, TimePickerInput, DateTimePickerInput
import datetime

from string import Template
from django.utils.safestring import mark_safe

from django.contrib import messages
from scolar.admin import settings
from django.http.response import Http404
from django.contrib.auth.forms import AuthenticationForm, UsernameField

from django.contrib.auth import password_validation
from captcha.fields import ReCaptchaField

class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
    

    error_messages = {
        'invalid_login':"Identifiants incorrects. Merci d\'entrer des identifiants corrects, à noter que le mot de passe est sensible à la casse (majuscules, minuscules)",
        'inactive': "Ce compte d'utilisateur est inactif",
    }
    
    username = UsernameField(label='', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Utilisateur', 'id': 'username'}))
    password = forms.CharField(label='', widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe',
            'id': 'password',
        }
))

class ImportChargeForm(forms.ModelForm):
    
    class Meta:
        model = Charge
        fields = ['annee_univ', 'periode', 'type', 'obs', 'repeter_chaque_semaine']
    
    def __init__(self, *args, **kwargs):
        super(ImportChargeForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['file']=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
        self.helper.add_input(Submit('submit','Importer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'
    
    
class ChargeFilterForm(forms.Form):

    enseignant_list = forms.ModelMultipleChoiceField(
            queryset=Enseignant.objects.filter(situation='A').order_by('nom', 'prenom'),
            label=u"Enseignants",
            widget=ModelSelect2MultipleWidget(
                    model=Enseignant,
                    search_fields=['nom__icontains','prenom__icontains'],
                ),
            help_text = "Sélection multiple possible. Tapez le nom ou prénom de l'enseignant ou deux espaces pour avoir la liste complète.",
            required = False
        )

    charge_inf = forms.DecimalField(
            label=u"Ratio >= ?? %",
            help_text = "Tapez le ratio en %",
            max_digits=5, decimal_places=2,
            required = False
        )
    
    charge_sup = forms.DecimalField(
            label=u"Ratio <= ?? %",
            help_text = "Tapez le ratio en %",
            max_digits=5, decimal_places=2,
            required = False
        )

    def __init__(self, *args, **kwargs):
        super(ChargeFilterForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    'enseignant_list', 'charge_inf', 'charge_sup',
                    css_class='row'
                ), css_class="col-lg-12"
            ),
            FormActions(
                Submit('submit', 'Filtrer'),
                HTML('{% if perms.scolar.fonctionnalite_enseignants_gestioncharges %}<a class="btn btn-info" href="{% url "charge_batch_create" %}">Importer des Charges</a>{% endif %}'),
                HTML('<a class="btn btn-secondary" href="{% url "home" %}">Annuler</a>')
            )
        )

        self.helper.form_method='POST'
        

class EDTForm(forms.Form):
    groupe = forms.ModelChoiceField(
            queryset=Groupe.objects.filter(section__formation__annee_univ__encours=True, code__isnull=False).order_by('section__formation__programme__ordre','code'),
            label=u"Groupe",
            widget = ModelSelect2Widget(
                model=Groupe,
                search_fields=['code__icontains', 'section__code__icontains', 'section__formation__programme__code__icontains' ] ,
                ),
            required = False,
            help_text = "Tapez le code du groupe ou deux espaces pour avoir la liste complète.",
            )

    etudiant = forms.ModelChoiceField(
            queryset=Etudiant.objects.all().order_by('nom', 'prenom'),
            label=u"Etudiant",
            widget=ModelSelect2Widget(
                    model=Etudiant,
                    search_fields=['nom__icontains', 'prenom__icontains',],

                ),
            help_text = "Tapez le nom ou prénom d'un étudiant ou deux espaces pour avoir la liste complète.",
            required = False
        )
    enseignant = forms.ModelChoiceField(
            queryset=Enseignant.objects.all().order_by('nom', 'prenom'),
            label=u"Enseignant",
            widget=ModelSelect2Widget(
                    model=Enseignant,
                    search_fields=['nom__icontains', 'prenom__icontains',],

                ),
            help_text = "Tapez le nom ou prénom d'un enseignant ou deux espaces pour avoir la liste complète.",
            required = False
        )

    def __init__(self, *args, **kwargs):
        super(EDTForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Trouver',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'


class CommissionValidationCreateForm(forms.Form):

    def __init__(self, pfe_pk, *args, **kwargs):
        super(CommissionValidationCreateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        pfe_=get_object_or_404(PFE, id=pfe_pk)
        these_qs=These.objects.filter(sujet__id=pfe_pk)
        these_=None
        if these_qs.exists() :
            these_=these_qs.first()
        
        if these_ :
            self.fields['pfe'] = forms.ModelChoiceField(disabled=True, queryset=PFE.objects.filter(id=pfe_pk), initial=pfe_pk, label="Thèse")

        else :
            self.fields['pfe'] = forms.ModelChoiceField(disabled=True, queryset=PFE.objects.filter(id=pfe_pk), initial=pfe_pk)
        
        if not these_ :
            self.fields['promoteur'] = forms.CharField(disabled=True, initial=pfe_.promoteur)
            self.fields['coencadrants'] = forms.ModelMultipleChoiceField(
                    label="Coencadrants",
                    queryset = Enseignant.objects.all().order_by('nom', 'prenom'),
                    initial=pfe_.coencadrants.all(),
                    widget=ModelSelect2MultipleWidget,
                    disabled=True,
                    required=False
                )
        enseignant_nb_avis_list=[] 
        for enseignant_ in Enseignant.objects.all().order_by('nom','prenom'):
            if not these_ :
                sollicitations=Validation.objects.filter(Q(pfe__type='P')|Q(pfe__type='M'), expert=enseignant_).order_by('-debut')
            else :
                sollicitations=Validation.objects.filter(Q(pfe__type='D'), expert=enseignant_).order_by('-debut')
            annees_sollicitation = []
            for sollicitation_ in sollicitations :
                annee_sollicitation = sollicitation_.debut.year
                if not annee_sollicitation in annees_sollicitation :
                    annees_sollicitation.append(annee_sollicitation)
            
            str_=str(enseignant_)    
            if not annees_sollicitation :
                str_=str_+" : Aucune sollicitation"
            else :
                str_=str_+" : "
                for annee_sollicitation in annees_sollicitation :
                    str_=str_ + "Sollicitations-"+str(annee_sollicitation)+"("+str(enseignant_.nb_avis_annee(annee_sollicitation))+") Vides-"+str(annee_sollicitation)+"("+str(enseignant_.nb_avis_vides_annee(annee_sollicitation))+") , "
            
            enseignant_nb_avis_list.append((enseignant_.id, str_))
        self.fields['experts'] = forms.MultipleChoiceField(
                label="Membres de la commission",
                choices=enseignant_nb_avis_list,
                widget=Select2MultipleWidget,
                help_text = "Vous pouvez séléctionner plusieurs enseignants. Tapez un nom ou prénom ou 2 espaces pour avoir la liste complète.",
                required = True
                
            )
        self.fields['fin'] = forms.DateField(label='Echéance', input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), initial=datetime.date.today())
        self.helper.add_input(Submit('submit','Créer commission',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'
    
class CompetenceForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(CompetenceForm, self).__init__(*args, **kwargs)
        self.fields['competence_family'] = forms.ChoiceField(
                choices=CompetenceFamily.objects.values_list(),
                label=u"Famille de Compétences",
                widget = Select2Widget(attrs={'style':'width:800px; height:10px;'}),
                required = False,
                help_text = "Tapez un mot clé ou deux espaces pour avoir la liste complète.",
                )
        self.fields['competence'] = forms.ModelChoiceField(
                queryset=Competence.objects.all().order_by('code'),
                label=u"Compétences",
                widget=ModelSelect2Widget(
                        model=Competence,
                        search_fields=['intitule__icontains',],
                        dependent_fields={'competence_family':'competence_family'},
                        attrs={'style':'width:800px; height:10px;'}
                    ),
                help_text = "Tapez un mot clé ou deux espaces pour avoir la liste complète.",
                required = False
            )
        self.fields['competence_element'] = forms.ModelMultipleChoiceField(
                queryset=CompetenceElement.objects.all().order_by('code'),
                label=u"Eléments de Compétences",
                widget=ModelSelect2MultipleWidget(
                        model=CompetenceElement,
                        search_fields=['intitule__icontains',],
                        dependent_fields={'competence':'competence'},
                        attrs={'style':'width:800px; height:10px;'}
                    ),
                help_text = "Vous pouvez séléctionner plusieurs éléments de compétence. Tapez un mot clé ou 2 espaces pour avoir la liste complète.",
                required = False
            )
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Ajouter',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.add_input(Hidden('form_type','filtre'))
        self.helper.form_method='POST'

TYPE_DOC=(
    ('C3L', 'Certificats de Scolarité Trilingues'),
    ('C2L', 'Certificats de Scolarité Bilingues'),
    ('RP1', 'Relevés Provisoires S1'),
    ('RP2', 'Relevés Provisoires S2'),
    ('RA', 'Relevés Annuels'),
    ('RECTS', 'Relevés ECTS'),
    ('FPFE', 'Fiches PFE'),
)

class SelectionFormationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SelectionFormationForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['annee_univ'] = forms.ChoiceField(
                choices=AnneeUniv.objects.all().values_list('annee_univ','annee_univ').order_by('-annee_univ'),
                label=u"Année Universitaire",
                widget = Select2Widget(attrs={'style':'width:800px; height:10px;'}),
                required = True,
                help_text = "Choisir l'année universitaire.",
                )
        self.fields['formation'] = forms.ModelChoiceField(
                queryset=Formation.objects.all().order_by('programme__ordre'),
                label=u"Formation",
                widget=ModelSelect2Widget(
                        model=Formation,
                        search_fields=['programme__code__icontains',],
                        dependent_fields={'annee_univ':'annee_univ'},
                        attrs={'style':'width:800px; height:10px;'}
                    ),
                help_text = "Choisir l'année d'étude ou spécialité. Tapez deux espaces pour avoir toute la liste.",
                required = True
            )
        self.fields['periode'] = forms.ChoiceField(
                choices=Periode.objects.all().values_list('id','code').order_by('ordre'),
                label=u"Période",
                widget = Select2Widget(attrs={'style':'width:800px; height:10px;'}),
                required = False,
                help_text = "Choisir la période si le document est périodique (semestriel, ..)",
                )        
        
        types_documents=list(TYPE_DOC)
        types_documents_a_afficher=[]
        periode_s1=Periode.objects.filter(code="S1")
        periode_s2=Periode.objects.filter(code="S2")
        
        for type in types_documents :
            if (type[0]=="RP1") :
                if periode_s1.exists() :
                    types_documents_a_afficher.append(type)
            elif (type[0]=="RP2") :
                if periode_s2.exists() :
                    types_documents_a_afficher.append(type)
            else :
                types_documents_a_afficher.append(type)
        
        self.fields['type_document'] = forms.ChoiceField(
                choices=types_documents_a_afficher,
                label=u"Type de Document",
                widget=Select2Widget(attrs={'style':'width:800px; height:10px;'}),
                help_text = "Choisir le type de documents groupés à générer",
                required = True
            )
        self.helper.add_input(Submit('submit','Générer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class SelectionInscriptionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SelectionInscriptionForm, self).__init__(*args, **kwargs)
        self.fields['annee_univ'] = forms.ChoiceField(
                choices=AnneeUniv.objects.all().values_list('annee_univ','annee_univ').order_by('-annee_univ'),
                label=u"Année Universitaire",
                widget = Select2Widget(
                    #attrs={'style':'width:800px; height:10px;'}
                    ),
                required = True,
                help_text = "Choisir l'année universitaire.",
                )
        self.fields['formation'] = forms.ModelChoiceField(
                queryset=Formation.objects.all().order_by('programme__ordre'),
                label=u"Formation",
                widget=ModelSelect2Widget(
                        model=Formation,
                        search_fields=['programme__code__icontains',],
                        dependent_fields={'annee_univ':'annee_univ'},
                        #attrs={'style':'width:800px; height:10px;'}
                    ),
                help_text = "Choisir l'année d'étude ou spécialité. Tapez deux espaces pour avoir toute la liste.",
                required = True
            )
        self.fields['inscription'] = forms.ModelChoiceField(
                queryset=Inscription.objects.filter(decision_jury='X').order_by('etudiant__nom', 'etudiant__prenom'),
                label=u"Etudiant",
                widget=ModelSelect2Widget(
                        model=Inscription,
                        search_fields=['etudiant__nom__icontains', 'etudiant__prenom__icontains',],
                        dependent_fields={'formation':'formation'},
                        #attrs={'style':'width:800px; height:10px;'}
                    ),
                help_text = "Choisir l'étudiant à inscrire. Tapez le nom ou le prénom.",
                required = True
            )
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Inscrire',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'


class ValidationPreInscriptionForm(forms.Form):

#     valider_wilaya_residence = forms.BooleanField(initial=False, required=False)
#     valider_commune_residence = forms.BooleanField(initial=False, required=False)
#     valider_adresse_principale = forms.BooleanField(initial=False, required=False)
#     valider_tel = forms.BooleanField(initial=False, required=False)
#     valider_photo = forms.BooleanField(initial=False, required=False)
#     valider_quittance = forms.BooleanField(initial=False, required=False)
#     valider_interne = forms.BooleanField(initial=False, required=False)
#     valider_residence_univ = forms.BooleanField(initial=False, required=False)
#     valider_numero_securite_sociale = forms.BooleanField(initial=False, required=False)
    CHOIX_VALIDATION=(
            ('V', "Inscription valide: les informations sont cohérentes et quittance de payement des frais d'inscription présente."),
            ('N', "Inscription non valide: dossier incomplet.")
        )
    valider_inscription = forms.ChoiceField(label="Validation", 
                                            choices=CHOIX_VALIDATION, 
                                            initial='N', 
                                            required=True,
                                            widget=forms.RadioSelect(),)
    motif_refus = forms.CharField(max_length=1000, widget=forms.Textarea(), required=False,
                                  help_text="Remplir dans le cas de refus pour expliquer les raisons du refus.")
        
    def __init__(self, *args, **kwargs):
        super(ValidationPreInscriptionForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
         
         
        self.helper.add_input(Submit('submit','Envoyer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'


class AbsenceEtudiantReportSelectionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(AbsenceEtudiantReportSelectionForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['formation'] = forms.ModelChoiceField(
                queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'),
                label=u"Formation",
                widget=ModelSelect2Widget(
                        model=Formation,
                        search_fields=['programme__code__icontains',],
                    ),
                help_text = "Choisir l'année d'étude ou spécialité. Tapez deux espaces pour avoir toute la liste.",
                required = True
            )
        self.fields['periode'] = forms.ChoiceField(
                choices=Periode.objects.all().values_list('id','code').order_by('ordre'),
                label=u"Période",
                widget = Select2Widget,
                required = True,
                help_text = "Choisir la période",
                )
        
        self.fields['type_activite_list'] = forms.MultipleChoiceField(
                choices=TYPES_ACT,
                label=u"Type d'Activité Pédagogique",
                widget=Select2MultipleWidget,
                help_text = "Choisir les types d'activités",
                required = True
            )
        self.helper.add_input(Submit('submit','Générer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'
    

class EvaluationCompetenceForm(forms.Form):
    def __init__(self, evaluation_pk, *args, **kwargs):
        super(EvaluationCompetenceForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['competence_element'] = forms.MultipleChoiceField(
            choices=CompetenceElement.objects.filter(competence_elements__matiere__module__evaluations=evaluation_pk).distinct().values_list('id','intitule'),
            label=u"Eléments de Compétences",
            widget=Select2MultipleWidget,
            help_text = "Vous pouvez séléctionner plusieurs éléments de compétence à ajouter. Tapez un mot clé ou 2 espaces pour avoir la liste complète.",
            required = False
        )
        
        try :  
            competence_eval_config_=get_object_or_404(CompetenceEvalConfig, evaluation=evaluation_pk) 
        except Http404 :
            note_A=dict(NOTES_PAR_DEFAUT).get('A')
            note_B=dict(NOTES_PAR_DEFAUT).get('B')            
            note_C=dict(NOTES_PAR_DEFAUT).get('C')
            note_D=dict(NOTES_PAR_DEFAUT).get('D')
            note_E=dict(NOTES_PAR_DEFAUT).get('E')
            note_F=dict(NOTES_PAR_DEFAUT).get('F')
        else :
            note_A=competence_eval_config_.A
            note_B=competence_eval_config_.B
            note_C=competence_eval_config_.C
            note_D=competence_eval_config_.D
            note_E=competence_eval_config_.E
            note_F=competence_eval_config_.F
                                                      
        self.fields['note_A'] = forms.DecimalField(initial=note_A, min_value=0, max_value=20, label="Note de la mention A", required=True)
        self.fields['note_B'] = forms.DecimalField(initial=note_B, min_value=0, max_value=20, label="Note de la mention B", required=True)
        self.fields['note_C'] = forms.DecimalField(initial=note_C, min_value=0, max_value=20, label="Note de la mention C", required=True)
        self.fields['note_D'] = forms.DecimalField(initial=note_D, min_value=0, max_value=20, label="Note de la mention D", required=True)
        self.fields['note_E'] = forms.DecimalField(initial=note_E, min_value=0, max_value=20, label="Note de la mention E", required=True)
        self.fields['note_F'] = forms.DecimalField(initial=note_F, min_value=0, max_value=20, label="Note de la mention F", required=True)                                        
        self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.add_input(Hidden('form_type','filtre'))
        self.helper.form_method='POST'


class SelectChargeConfigForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super(SelectChargeConfigForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['charge_config'] = forms.ModelChoiceField(
                queryset=ActiviteChargeConfig.objects.all().order_by('categorie', 'type'),
                label=u"Modèle de Charge",
                help_text = "Choisir un modèle de charge dans la liste",
                )
        self.fields['periode'] = forms.ModelChoiceField(
                queryset=Periode.objects.all().order_by('code'),
                label=u"Période",
                )
        self.fields['obs'] = forms.CharField(
                max_length=50,
                label=u"Observation",
                help_text = "Complément d'information concernant cette charge, par ex. Nom du Doctorant qui va soutenir",
            )
        self.helper.add_input(Submit('submit','Ajouter',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'

class ExamenCreateForm(forms.Form):
    type_activite = forms.ChoiceField(
            choices= TYPES_ACT_EXAM,
            label=u"Type Examen",
            widget = Select2Widget
            ) 
    date = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), initial=datetime.date.today()) # 

    heure_debut = forms.TimeField(input_formats=['%H:%M'], widget=TimePickerInput(format='%H:%M')) #
    
    duree = forms.TimeField(input_formats=['%H:%M'], widget=TimePickerInput(format='%H:%M')) 

    
    def __init__(self, *args, **kwargs):
        super(ExamenCreateForm, self).__init__(*args, **kwargs)
        
        self.helper=FormHelper()
        
        self.fields['formation'] = forms.ModelChoiceField(
            queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'),
            label=u"Formation",
            widget=ModelSelect2Widget(
                    model=Formation,
                    search_fields=['programme__code__icontains'],
                ),
            help_text = "Indiquez la formation concernée. Tapez le code de la formation (ex. 2ST), ou 2 espaces pour avoir la liste complète.",
            required = True
        )
        self.fields['periode'] = forms.ModelChoiceField(
            queryset=Periode.objects.all().order_by('code'),
            label=u"Période",
            widget=ModelSelect2Widget(
                    model=Periode,
                    search_fields=['code__icontains'],
                ),
            help_text = "Indiquez la période concernée. Tapez le code de la période (ex. S1), ou 2 espaces pour avoir la liste complète.",
            required = True
        )
        self.fields['module'] = forms.ModelChoiceField(
            queryset=Module.objects.filter(formation__annee_univ__encours=True).order_by('matiere__code'),
            label=u"Module",
            widget=ModelSelect2Widget(
                    model=Module,
                    search_fields=['matiere__code__icontains'],
                    dependent_fields={'formation':'formation', 'periode':'periode__periode'},
                ),
            help_text = "Indiquez la période concernée. Tapez le code de la période (ex. S1), ou 2 espaces pour avoir la liste complète.",
            required = True
        )

        self.fields['groupes'] = forms.ModelMultipleChoiceField(
            queryset=Groupe.objects.filter(section__formation__annee_univ__encours=True).order_by('code'),
            label=u"Groupes concernés",
            widget=ModelSelect2MultipleWidget(
                    model=Groupe,
                    search_fields=['code__icontains'],
                    dependent_fields={'formation':'section__formation'},
                ),
            help_text = "Indiquez les groupes. Tapez le code du groupe (ex. G09), ou 2 espaces pour avoir la liste complète.",
            required = True
        )     
        self.helper.add_input(Submit('submit','Créer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'

class ExamenUpdateForm(forms.Form):

    
    def __init__(self, seance_pk, *args, **kwargs):
        super(ExamenUpdateForm, self).__init__(*args, **kwargs)
        
        seance_=get_object_or_404(Seance, id=seance_pk)
        
        self.helper=FormHelper()
        
        self.fields['type_activite'] = forms.ChoiceField(
                choices= TYPES_ACT_EXAM,
                initial=seance_.activite.type,
                label=u"Type Examen",
                widget = Select2Widget
                ) 
        self.fields['date'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), initial=seance_.date) # 
    
        self.fields['heure_debut'] = forms.TimeField(input_formats=['%H:%M'], widget=TimePickerInput(format='%H:%M'), initial=seance_.heure_debut) #

        duree_=datetime.datetime(seance_.date.year, seance_.date.month, seance_.date.day, seance_.heure_fin.hour, seance_.heure_fin.minute) - datetime.timedelta(hours = seance_.heure_debut.hour, minutes = seance_.heure_debut.minute)
        duree_=duree_.time()
        
        self.fields['duree'] = forms.TimeField(input_formats=['%H:%M'], widget=TimePickerInput(format='%H:%M'), initial=duree_) 

        self.fields['formation'] = forms.ModelChoiceField(
            queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'),
            initial=seance_.activite.module.formation,
            label=u"Formation",
            help_text = "Indiquez la formation concernée. Tapez le code de la formation (ex. 2ST), ou 2 espaces pour avoir la liste complète.",
            required = True
        )
        self.fields['formation'].widget.attrs['readonly']=True
        
        self.fields['periode'] = forms.ModelChoiceField(
            queryset=Periode.objects.all().order_by('code'),
            initial=seance_.activite.module.periode.periode,
            label=u"Période",
            help_text = "Indiquez la période concernée. Tapez le code de la période (ex. S1), ou 2 espaces pour avoir la liste complète.",
            required = True
        )
        self.fields['periode'].widget.attrs['readonly']=True
        
        self.fields['module'] = forms.ModelChoiceField(
            queryset=Module.objects.filter(formation__annee_univ__encours=True).order_by('matiere__code'),
            initial=seance_.activite.module,
            label=u"Module",
            help_text = "Indiquez la période concernée. Tapez le code de la période (ex. S1), ou 2 espaces pour avoir la liste complète.",
            required = True
        )
        self.fields['module'].widget.attrs['readonly']=True
        
        self.fields['groupes'] = forms.ModelMultipleChoiceField(
            queryset=Groupe.objects.filter(section__formation__annee_univ__encours=True).order_by('code'),
            initial=seance_.activite.cible.all(),
            label=u"Groupes concernés",
            widget=ModelSelect2MultipleWidget(
                    model=Groupe,
                    search_fields=['code__icontains'],
                    dependent_fields={'formation':'section__formation'},
                ),
            help_text = "Indiquez les groupes. Tapez le code du groupe (ex. G09), ou 2 espaces pour avoir la liste complète.",
            required = True
        )     
        self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'


class ExamenListSelectForm(forms.Form):
        
    def __init__(self, *args, **kwargs):
        super(ExamenListSelectForm, self).__init__(*args, **kwargs)
        
        self.helper=FormHelper()
        self.fields['formation']= forms.ModelChoiceField(
                queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'),
                label=u"Formation concernée par l'examen",
                widget=ModelSelect2Widget(
                    model=Formation,
                    search_fields=['programme__code__icontains'],
                    ),
                help_text = "Tapez le code de la formation ou 2 espaces pour avoir la liste complète.",
                )
        
        self.fields['examen_list'] = forms.ModelMultipleChoiceField(
                queryset=Seance.objects.filter(activite__module__formation__annee_univ__encours=True, activite__type__startswith='E_').order_by('-date', 'heure_debut'),
                label=u"Examens concernés par la répartition",
                widget=ModelSelect2MultipleWidget(
                        model=Seance,
                        search_fields=['activite__module__matiere__code__icontains'],
                        dependent_fields={'formation':'activite__module__formation'},
                    ),
                required = True,
            )

             
        self.helper.add_input(Submit('submit','Sélectionner',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'

class SeanceSallesReservationForm(forms.Form):
        
    def __init__(self, seance_pk, *args, **kwargs):
        super(SeanceSallesReservationForm, self).__init__(*args, **kwargs)
        
        seance_=get_object_or_404(Seance, id=seance_pk)
        
        
        self.helper=FormHelper()
        
        self.fields['seance'] = forms.ModelChoiceField(
                queryset=Seance.objects.all(),
                initial=seance_
            )
        self.fields['seance'].widget.attrs['readonly']=True
        
        self.fields['groupes'] = forms.ModelMultipleChoiceField(
            queryset = Groupe.objects.all(),
            initial= seance_.activite.cible.all(),
            label=u"Groupes concernés",
            widget=ModelSelect2MultipleWidget(
                    model=Groupe,
                    search_fields=['code__icontains'],
                    dependent_fields={'formation':'section__formation'},
                ),
            
        )
        
        self.fields['groupes'].widget.attrs['readonly']=True 
        
        self.fields['capacite_requise'] = forms.IntegerField(initial=seance_.activite.nb_etudiants())
        self.fields['capacite_requise'].widget.attrs['readonly']=True 

        self.fields['capacite_reservee'] = forms.IntegerField(initial=seance_.capacite_reservee())
        self.fields['capacite_reservee'].widget.attrs['readonly']=True 
        
        seance_chevauchement_list=Seance.objects.filter(date=seance_.date).exclude(
                                                                            heure_debut__gt=seance_.heure_fin
                                                                        ).exclude(
                                                                            heure_fin__lt=seance_.heure_debut
                                                                        )
        salle_occupee_list=[]
        for seance_chevauchement_ in seance_chevauchement_list:
            for salle_occupee_ in seance_chevauchement_.salles.all():
                if not salle_occupee_ in salle_occupee_list:
                    salle_occupee_list.append(salle_occupee_.code)
         
        salle_disponible_capacite_list=[]
        for salle_ in Salle.objects.all().order_by('code'):
            if not salle_.code in salle_occupee_list:
                salle_disponible_capacite_list.append((salle_.id, str(salle_)+' : '+str(salle_.capacite()))) 
        
        # Ajouter les salles déjà réservées pour cet examen 
        for salle_reservee in seance_.salles.all():
            # Récupérer les différentes versions de la même salle
            salle_disponible_capacite_list += [(salle_.id, str(salle_)+' : '+str(salle_.capacite())) for salle_ in Salle.objects.filter(code=salle_reservee.code)]
            #salle_disponible_capacite_list.append((salle_.id, str(salle_)+' : '+str(salle_.capacite())))
            
        self.fields['salles'] = forms.MultipleChoiceField(
            choices = salle_disponible_capacite_list,
            initial = [salle_.id for salle_ in seance_.salles.all()],
            label=u"Salles réservées",
            widget=Select2MultipleWidget(attrs={'onchange':'update_capacite_reservee();'},
                ),
            help_text = "Indiquez les salles à réserver.",
            required = True
        )

             
        self.helper.add_input(Submit('submit','Réserver',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'

class SurveillanceUpdateForm(forms.Form):
        
    def __init__(self, seance_pk, *args, **kwargs):
        super(SurveillanceUpdateForm, self).__init__(*args, **kwargs)
        
        seance_=get_object_or_404(Seance, id=seance_pk)
        
        
        self.helper=FormHelper()
        
        self.fields['seance'] = forms.ModelChoiceField(
                queryset=Seance.objects.all(),
                initial=seance_
            )
        self.fields['seance'].widget.attrs['readonly']=True
        
        self.fields['groupes'] = forms.ModelMultipleChoiceField(
            queryset = Groupe.objects.all(),
            initial= seance_.activite.cible.all(),
            label=u"Groupes concernés",
            widget=ModelSelect2MultipleWidget(
                model = Groupe,
                search_fields=['code__icontains',]),
        )
        self.fields['groupes'].widget.attrs['readonly']=True 

        seance_chevauchement_list=Seance.objects.filter(date=seance_.date).exclude(
                                                                            heure_debut__gte=seance_.heure_fin
                                                                        ).exclude(
                                                                            heure_fin__lte=seance_.heure_debut
                                                                        )
        enseignant_occupe_list=[]
        for seance_chevauchement_ in seance_chevauchement_list:
            for enseignant_occupe_ in seance_chevauchement_.activite.assuree_par.all():
                if not enseignant_occupe_ in enseignant_occupe_list:
                    enseignant_occupe_list.append(enseignant_occupe_)
        
        
        enseignant_charge_list=[] 
        for enseignant_ in Enseignant.objects.all().order_by('nom','prenom'):
            if not enseignant_ in enseignant_occupe_list: 
                enseignant_charge_list.append((enseignant_.id, str(enseignant_)+" (Charge= "+str(enseignant_.ratio_charge_annuelle_encours())+"% ) "+
                                               "Surveillances (Nb= "+str(enseignant_.nb_surveillances())+
                                                                " VH= "+str(enseignant_.vh_surveillances())+")"))
            
        for salle_ in seance_.salles.all().order_by('code'):
            #Ajouter les enseignants déjà prévus dans cette salle
            surveillants_charge_list=[]
            for surveillance_ in SurveillanceEnseignant.objects.filter(seance=seance_, salle=salle_):
                surveillants_charge_list.append(
                        (surveillance_.enseignant.id, str(surveillance_.enseignant)+" (Charge= "+str(surveillance_.enseignant.ratio_charge_annuelle_encours())+"% ) "+
                                               "Surveillances (Nb= "+str(surveillance_.enseignant.nb_surveillances())+
                                                                " VH= "+str(surveillance_.enseignant.vh_surveillances())+")")
                    )
            self.fields[salle_.code] = forms.MultipleChoiceField(
                label="Surveillants affectés à la salle: "+salle_.code,
                choices=enseignant_charge_list + surveillants_charge_list,
                initial= [surveillance_.enseignant.id for surveillance_ in SurveillanceEnseignant.objects.filter(seance=seance_, salle=salle_)],
                widget=Select2MultipleWidget,
                help_text = "Vous pouvez séléctionner plusieurs enseignants. Tapez un nom ou prénom ou 2 espaces pour avoir la liste complète.",
                required = True
            )
             
        self.helper.add_input(Submit('submit','Affecter',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'


class ReservationPlaceEtudiantUpdateForm(forms.Form):
        
    def __init__(self, pk, *args, **kwargs):
        super(ReservationPlaceEtudiantUpdateForm, self).__init__(*args, **kwargs)
        
        reservation_=get_object_or_404(ReservationPlaceEtudiant, id=pk)
        
        
        self.helper=FormHelper()
        
        self.fields['inscription'] = forms.CharField(initial = str(reservation_.inscription), disabled = True)
        self.fields['seance'] = forms.CharField(initial = str(reservation_.seance), disabled = True)
        place_reservee_list=ReservationPlaceEtudiant.objects.filter(seance=reservation_.seance).values_list('place')
        self.fields['place'] = forms.ModelChoiceField(
            queryset=Place.objects.filter(salle__in=reservation_.seance.salles.all(), disponible=True).exclude(id__in=place_reservee_list),
            label=u"Place",
            widget=ModelSelect2Widget(
                model=Place,
                search_fields=['salle__code__icontains','code__icontains'],
            ),
            help_text = "Choisir une place. Tapez deux espaces pour avoir toute la liste.",
            required = True
        )
  
             
        self.helper.add_input(Submit('submit','Enregistrer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'


class ExamenSelectForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super(ExamenSelectForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['formation_list'] = forms.ModelMultipleChoiceField(
                queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'),
                label=u"Formations concernées par l'envoi des convocations",
                widget=ModelSelect2MultipleWidget(
                    model=Formation,
                    search_fields=['programme__code__icontains'],
                    ),
                help_text = "Tapez le code de la formation ou 2 espaces pour avoir la liste complète. Sélection multiple possible.",
                )
        self.fields['activite_type_list'] = forms.MultipleChoiceField(
                choices=TYPES_ACT_EXAM,
                label=u"Types d'preuves",
                widget = Select2MultipleWidget
                )
    
        self.fields['date_debut'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y')) # 
        self.fields['date_fin'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y')) # 
        self.helper.add_input(Submit('submit','Envoyer les convocations',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'


class SurveillanceListSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SurveillanceListSelectForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['formation_list'] = forms.ModelMultipleChoiceField(
                queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'),
                label=u"Formations concernées par l'envoi des convocations",
                widget=ModelSelect2MultipleWidget(
                    model=Formation,
                    search_fields=['programme__code__icontains'],
                    ),
                help_text = "Tapez le code de la formation ou 2 espaces pour avoir la liste complète. Sélection multiple possible.",
                )
        self.fields['activite_type_list'] = forms.MultipleChoiceField(
                choices=TYPES_ACT_EXAM,
                label=u"Types d'preuves",
                widget = Select2MultipleWidget
                )
    
        self.fields['date_debut'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y')) # 
        self.fields['date_fin'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y')) # 
        
        self.helper.add_input(Submit('submit','Sélectionner',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'


class DateSelectForm(forms.Form):

    date_debut = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y')) #
    
    def __init__(self, *args, **kwargs):
        super(DateSelectForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Sélectionner',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'


class AffichageExamenSelectForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(AffichageExamenSelectForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['formation'] = forms.ModelChoiceField(
                queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'),
                label=u"Formation concernée par l'affichage des convocations",
                widget=ModelSelect2Widget(
                    model=Formation,
                    search_fields=['programme__code__icontains'],
                    ),
                help_text = "Tapez le code de la formation ou 2 espaces pour avoir la liste complète.",
                )
        self.fields['activite_type_list'] = forms.MultipleChoiceField(
                choices=TYPES_ACT_EXAM,
                label=u"Types d'preuves",
                widget = Select2MultipleWidget
                )
    
        self.fields['date_debut'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y')) # 
        self.fields['date_fin'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y')) # 
        
        self.helper.add_input(Submit('submit','Générer la répartition',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'
        self.helper.attrs['target']='_blank'
        



class SalleConfigForm(forms.Form):
    def __init__(self, salle_pk, *args, **kwargs):
        super(SalleConfigForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        salle_=get_object_or_404(Salle, id = salle_pk)
        # On récupère ou on crée les places de cette salle en fonction du nombre de rangées et de colonnes
        for ligne in range(1,salle_.nb_lignes+1):
            for colonne in char_range(salle_.nb_colonnes):
                place_, created=Place.objects.get_or_create(salle=salle_, num_ligne=ligne, num_colonne=colonne, defaults={
                        'salle':salle_,
                        'num_ligne':ligne,
                        'num_colonne':colonne,
                        'code':str(ligne)+colonne,
                        'disponible':True
                    })
                self.fields[str(place_.num_ligne)+'_'+str(place_.num_colonne)+'_code']=forms.CharField(initial=place_.code, required=True, label='')
                self.fields[str(place_.num_ligne)+'_'+str(place_.num_colonne)+'_disponible']=forms.BooleanField(initial=place_.disponible, required=False, label='')
#         self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
#         self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class SeanceSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SeanceSelectionForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        
        self.fields['enseignant'] = forms.ModelChoiceField(
                queryset=Enseignant.objects.filter(situation='A').order_by('nom', 'prenom'),
                label=u"Enseignant",
                widget=ModelSelect2Widget(
                    model=Enseignant,
                    search_fields=['nom__icontains','prenom__icontains'],
                    ),
                help_text = "Tapez le nom ou prénom ou 2 espaces pour avoir la liste complète",
                )
        self.fields['periode'] = forms.ChoiceField(
                choices=Periode.objects.values_list('id', 'code'),
                label=u"Période",
                widget = Select2Widget
                )
        self.fields['activite'] = forms.ModelChoiceField(
                queryset=Activite.objects.filter(module__formation__annee_univ__encours=True).order_by('module__formation__programme__ordre', 'module__matiere__code'),
                label=u"Activité",
                widget=ModelSelect2Widget(
                        model=Activite,
                        search_fields=['module__matiere__code__icontains',],
                        dependent_fields={'enseignant':'assuree_par', 'periode':'module__periode__periode'},
                    ),
            )
        self.fields['date'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), initial=datetime.date.today()) # 
        
        self.helper.add_input(Submit('submit','Ajouter',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'



class SeanceEtudiantSelectionForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SeanceEtudiantSelectionForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['formation'] = forms.ModelChoiceField(
                queryset=Formation.objects.filter(annee_univ__encours=True).order_by('programme__ordre'),
                label=u"Formation",
                widget=ModelSelect2Widget(
                    model=Formation,
                    search_fields=['programme__code__icontains'],
                    ),
                help_text = "Tapez le code de la formation (1CP, 2CP, 1CS, 2ST, 2SL...) ou 2 espaces pour avoir la liste complète",
                )
        self.fields['periode'] = forms.ChoiceField(
                choices=Periode.objects.values_list('id', 'code'),
                label=u"Période",
                widget = Select2Widget
                )
        self.fields['type_activite'] = forms.ChoiceField(
                choices= TYPES_ACT,
                label=u"Type",
                widget = Select2Widget
                ) 
        self.fields['seance'] = forms.ModelChoiceField(
                queryset=Seance.objects.filter(activite__module__formation__annee_univ__encours=True).order_by('-date', 'heure_debut','activite__module__formation__programme__ordre', 'activite__module__matiere__code'),
                label=u"Séance",
                widget=ModelSelect2Widget(
                        model=Seance,
                        search_fields=['activite__module__matiere__code__icontains',],
                        dependent_fields={'formation':'activite__module__formation', 'periode':'activite__module__periode__periode', 'type_activite':'activite__type'},#cible__activites__
                    ),
            )
         
        self.fields['inscription_absent_list'] =  forms.ModelMultipleChoiceField(
                queryset=Inscription.objects.filter(decision_jury='C', formation__annee_univ__encours=True).order_by('etudiant__nom', 'etudiant__prenom'),
                label=u"Liste des absents",
                widget=ModelSelect2MultipleWidget(
                        model=Inscription,
                        search_fields=['etudiant__nom__icontains', 'etudiant__prenom__icontains',],
                        dependent_fields={'formation':'formation','periode':'inscription_periodes__periodepgm__periode', 'seance__activite':'inscription_periodes__groupe__activites'},#
                    ),
                help_text = "Tapez les noms des absents. Tapez le nom ou prénom ou 2 espaces pour avoir la liste complète.",
                required = True
            )
        self.helper.add_input(Submit('submit','Signaler',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'


class ReleveNotesUpdateForm(forms.Form):

    def __init__(self, inscription_pk, *args, **kwargs):
        super(ReleveNotesUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        inscription_=Inscription.objects.get(id=inscription_pk)
        for periode_ in inscription_.inscription_periodes.all():
            self.fields[periode_.periodepgm.code]=forms.DecimalField(initial=periode_.moy, max_digits=4, decimal_places=2)
            for ue_ in periode_.resultat_ues.all():
                for resultat_ in ue_.resultat_matieres.all():
                    self.fields[resultat_.module.matiere.code]=forms.DecimalField(widget=forms.NumberInput(attrs={'onchange':'recalculer()'}), initial=resultat_.moy_post_delib, max_digits=4, decimal_places=2, required=False)
                    if resultat_.activation_rattrapage():
                        self.fields['rattrapage_'+resultat_.module.matiere.code]=forms.BooleanField(initial=resultat_.entree_rattrapage, required = False, label='')                    
                    if resultat_.activation_dettes():
                        self.fields['dette_'+resultat_.module.matiere.code]=forms.BooleanField(initial=resultat_.dette, required = False, label='')
        self.fields['proposition_decision_jury']=forms.ChoiceField(choices = DECISIONS_JURY, required=False, initial=inscription_.proposition_decision_jury)
        self.fields['moyenne']=forms.DecimalField(max_digits=4, decimal_places=2, required=False, initial=inscription_.moyenne_post_delib())
        self.fields['observation']=forms.CharField(max_length=200, required=False, initial=inscription_.observation,help_text="Remplir dans le cas où vous avez une observation.")        
        self.helper.form_method='POST'


class InscriptionUpdateForm(forms.Form):

    def __init__(self, inscription_pk, *args, **kwargs):
        super(InscriptionUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        inscription_=Inscription.objects.get(id=inscription_pk)
        # créer inscription_periodes selon le programme
        if not inscription_.formation.archive :
            for periode_ in inscription_.formation.programme.periodes.all():
                InscriptionPeriode.objects.get_or_create(inscription=inscription_, periodepgm__periode=periode_.periode, defaults={
                        'inscription':inscription_,
                        'periodepgm':periode_,
                    })
            
            for periode_ in inscription_.inscription_periodes.all().order_by('periodepgm__periode__code'):
                self.fields['groupe_'+str(periode_.id)]=forms.ModelChoiceField(
                    initial= periode_.groupe,
                    required=True,
                    queryset=Groupe.objects.filter(section__formation__annee_univ=inscription_.formation.annee_univ, section__formation__programme__ordre=inscription_.formation.programme.ordre).exclude(code__isnull=True).order_by('code'),
                    label=u"Groupe de la période : "+periode_.periodepgm.periode.code
                )
            self.fields['decision_jury']=forms.ChoiceField(choices = DECISIONS_JURY, required=False, initial=inscription_.decision_jury)
        self.fields['observation']=forms.CharField(max_length=100, required=False, initial=inscription_.observation,
                                                   help_text="Remplir dans le cas où vous avez une observation.")
        
        self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'
        

class NotesUpdateForm(forms.Form):
    def __init__(self, sms_, groupe_pk, module_pk, request, *args, **kwargs):
        super(NotesUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
            module_=get_object_or_404(Module, id = module_pk)
            activation_rattrapage=module_.activation_rattrapage()
        
            if groupe_pk != 0 :
                groupe_=get_object_or_404(Groupe, id = groupe_pk)
                liste_inscrits=Inscription.objects.filter(inscription_periodes__groupe=groupe_.id, inscription_periodes__periodepgm=module_.periode).order_by('etudiant__nom', 'etudiant__prenom')
            else : # dettes
                liste_inscrits=Inscription.objects.filter(resultats__ancien_resultat__isnull=False, resultats__module=module_).order_by('etudiant__nom', 'etudiant__prenom')
                
            #liste_inscrits=Inscription.objects.filter(groupe=groupe_pk)
            liste_evaluations=Evaluation.objects.filter(module=module_pk)
            if module_.somme_ponderation() != 1 and module_.somme_ponderation() != 0:
                messages.error(request, "ATTENTION! La somme des pondérations des évaluations n'est pas égale à 1. Le coordinateur(trice) devrait corriger la formule")
                
            for inscrit_ in liste_inscrits:
                is_admis=inscrit_.is_admis()
                self.fields[inscrit_.etudiant.matricule]=forms.CharField(initial=str(inscrit_.etudiant), disabled = True)
                resultat_=get_object_or_404(Resultat, inscription=inscrit_, module = module_pk)
                for eval_ in liste_evaluations :
                    note_, created=Note.objects.get_or_create(resultat=resultat_, evaluation=eval_, defaults = {'resultat':resultat_,'evaluation':eval_, 'note':0})
                    if not resultat_.acquis:
                        self.fields[str(inscrit_.etudiant.matricule)+"_"+str(eval_.id)]=forms.DecimalField(initial=note_.note, label='',
                                            widget=forms.NumberInput(attrs={'onchange':'update_moy("'+inscrit_.etudiant.matricule+'")'}),
                                            max_digits=4, 
                                            decimal_places=2, 
                                            required = False,
                                            )
                    else:
                        self.fields[str(inscrit_.etudiant.matricule)+"_"+str(eval_.id)]=forms.DecimalField(initial=note_.note, label='',
                                            widget=forms.NumberInput(),
                                            max_digits=4, 
                                            decimal_places=2, 
                                            required = False,
                                            )
                        
                    if resultat_.acquis or is_admis or (resultat_.inscription.decision_jury!='C' and not request.user.has_perm('scolar.fonctionnalite_pedagogie_modificationnotes')):
                        self.fields[str(inscrit_.etudiant.matricule)+"_"+str(eval_.id)].widget.attrs['readonly']=True

                self.fields[inscrit_.etudiant.matricule+'_moy']=forms.DecimalField(initial=resultat_.moy, label='', 
                                                                                   max_digits=4, 
                                                                                   decimal_places=2,
                                                                                   required = False)
                self.fields[inscrit_.etudiant.matricule+'_acquis']=forms.BooleanField(initial=resultat_.acquis, label='', required = False)  
                self.fields[inscrit_.etudiant.matricule+'_acquis'].disabled=is_admis or not request.user.has_perm('scolar.scolar.fonctionnalite_etudiants_reinitialisationnotesetacquis')
                if activation_rattrapage :
                    self.fields[inscrit_.etudiant.matricule+'_moy_rattrapage']=forms.DecimalField(initial=resultat_.moy_rattrapage, label='', 
                                                                                   max_digits=4, 
                                                                                   decimal_places=2,
                                                                                   required = False)
                    self.fields[inscrit_.etudiant.matricule+'_entree_rattrapage']=forms.BooleanField(initial=resultat_.entree_rattrapage, label='', required = False)                   
                
                if (liste_evaluations.exists() or resultat_.acquis or resultat_.inscription.decision_jury!='C') and( not request.user.has_perm('scolar.fonctionnalite_pedagogie_modificationnotes')) :
                    self.fields[inscrit_.etudiant.matricule+'_moy'].widget.attrs['readonly']=True
                    if activation_rattrapage :
                        self.fields[inscrit_.etudiant.matricule+'_moy_rattrapage'].widget.attrs['readonly']=True
                else :
                    if (resultat_.acquis or is_admis) and request.user.has_perm('scolar.fonctionnalite_pedagogie_modificationnotes'):
                        self.fields[inscrit_.etudiant.matricule+'_moy'].widget.attrs['readonly']=True
                        if activation_rattrapage :
                            self.fields[inscrit_.etudiant.matricule+'_moy_rattrapage'].widget.attrs['readonly']=True
                            self.fields[inscrit_.etudiant.matricule+'_entree_rattrapage'].disabled=True
                       
                         
                    
            if groupe_pk != 0 :
                self.fields[str(groupe_.id)+'_'+str(module_.id)]=forms.BooleanField(initial=False, label='Version Finale :', help_text='Saisie de toutes les notes de ce groupe est terminée', required = False)
            if sms_:
                self.fields['otp']=forms.CharField(required=True, label="Mot de Passe (Envoyé par SMS)", help_text="Saisir ici le mot de passe qu'on vient de vous envoyer par SMS. Si vous ne le recevez pas dans la minute qui suit, merci de vérifier que le numéro de téléphone associé à votre compte est correct.")
            self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(request, "ERREUR: lors de la construction du formaulaire de saisie des notes. Merci de le signaler à l'administrateur.")

#DONE sortir du code et mettre dans la base sous forme de table
COMPETENCE_EVAL={
    'Jury':(('0.90', 'A: Très bien'), ('0.75','B: Bien'), ('0.65','C: Assez bien'), ('0.50', 'D: Passable'), ('0.40', 'E: Médiocre'), ('0.25', 'F: Mauvais'), ('0.00', 'Choisir')),
    'Rapporteur': (('0.90', 'A: Très bien'), ('0.75','B: Bien'), ('0.65','C: Assez bien'), ('0.50', 'D: Passable'), ('0.40', 'E: Médiocre'), ('0.25', 'F: Mauvais'), ('0.00', 'Choisir')),
    'Encadreur':(('0.80', 'A: Très bien'), ('0.75','B: Bien'), ('0.65','C: Assez bien'), ('0.50', 'D: Passable'), ('0.40', 'E: Médiocre'), ('0.25', 'F: Mauvais'), ('0.00', 'Choisir')),
    'Rapport':(('0.90', 'A: Très bien'), ('0.75','B: Bien'), ('0.65','C: Assez bien'), ('0.50', 'D: Passable'), ('0.40', 'E: Médiocre'), ('0.25', 'F: Mauvais'), ('0.00', 'Choisir')),
    'Soutenance':(('0.90', 'A: Très bien'), ('0.75','B: Bien'), ('0.65','C: Assez bien'), ('0.50', 'D: Passable'), ('0.40', 'E: Médiocre'), ('0.25', 'F: Mauvais'), ('0.00', 'Choisir')),
    'Poster':(('0.90', 'A: Très bien'), ('0.75','B: Bien'), ('0.65','C: Assez bien'), ('0.50', 'D: Passable'), ('0.40', 'E: Médiocre'), ('0.25', 'F: Mauvais'), ('0.00', 'Choisir')),
    'Equipe':(('0.75', 'A: Très bien'), ('0.70','B: Bien'), ('0.60','C: Assez bien'), ('0.50', 'D: Passable'), ('0.40', 'E: Médiocre'), ('0.25', 'F: Mauvais'), ('0.00', 'Choisir')),

}
class NotesPFEUpdateForm(forms.Form):
    def __init__(self, groupe_pk, module_pk, request, *args, **kwargs):
        super(NotesPFEUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
            module_=get_object_or_404(Module, id = module_pk)
            groupe_=get_object_or_404(Groupe, id = groupe_pk)
            
            if module_.matiere.equipe :
                ids_inscriptions_equipe=[]
                for inscription_ in groupe_.pfe.equipe.inscriptions.all():
                    ids_inscriptions_equipe.append(inscription_.id)    
                liste_inscrits=Inscription.objects.filter(id__in=ids_inscriptions_equipe)
            else : #pfe
                liste_inscrits=Inscription.objects.filter(inscription_periodes__groupe=groupe_pk, inscription_periodes__periodepgm__periode=module_.periode.periode)
             
            liste_evaluations=Evaluation.objects.filter(module=module_pk)
            soutenance_, created = Soutenance.objects.get_or_create(groupe=groupe_, defaults={
                    'groupe':groupe_,
                })
            if module_.matiere.equipe : 
                pfe_, created = PFE.objects.get_or_create(groupe=groupe_, defaults={
                        'groupe':groupe_,
                        'notification':False
                    })
            else : #pfe
                pfe_, created = PFE.objects.get_or_create(groupe=groupe_, defaults={
                        'groupe':groupe_,
                    })                
                    
            for inscrit_ in liste_inscrits:
                resultat_=get_object_or_404(Resultat, inscription=inscrit_, module__matiere = module_.matiere)
                for eval_ in liste_evaluations :
                    
                    try :
                        competence_eval_config_=get_object_or_404(CompetenceEvalConfig, evaluation=eval_)
                    except Http404 :
                        competence_eval_config_choices=(('0.0000', 'Choisir'), (str(round(decimal.Decimal(dict(NOTES_PAR_DEFAUT).get('A')/20),4)), 'A: Très bien'), (str(round(decimal.Decimal(dict(NOTES_PAR_DEFAUT).get('B')/20),4)),'B: Bien'), (str(round(decimal.Decimal(dict(NOTES_PAR_DEFAUT).get('C')/20),4)) ,'C: Assez bien'), (str(round(decimal.Decimal(dict(NOTES_PAR_DEFAUT).get('D')/20), 4)), 'D: Passable'), (str(round(decimal.Decimal(dict(NOTES_PAR_DEFAUT).get('E')/20),4)), 'E: Médiocre'), (str(round(decimal.Decimal(dict(NOTES_PAR_DEFAUT).get('F')/20),4)) , 'F: Mauvais'))
                    else :
                        competence_eval_config_choices=(('0.0000', 'Choisir'), (str(round(competence_eval_config_.A/20,4)), 'A: Très bien'), (str(round(competence_eval_config_.B/20,4)),'B: Bien'), (str(round(competence_eval_config_.C/20,4)) ,'C: Assez bien'), (str(round(competence_eval_config_.D/20,4)), 'D: Passable'), (str(round(competence_eval_config_.E/20,4)), 'E: Médiocre'), (str(round(competence_eval_config_.F/20,4)) , 'F: Mauvais'))
                    
                    note_, created=Note.objects.get_or_create(resultat=resultat_, evaluation=eval_, defaults = {
                        'resultat':resultat_,
                        'evaluation':eval_,
                        'note':0
                        })
                    for competence_ in eval_.competence_elements.all():
                        note_competence_element, created= NoteCompetenceElement.objects.get_or_create(evaluation_competence_element=competence_, note_globale=note_, defaults={
                                'evaluation_competence_element':competence_, 
                                'note_globale':note_,
                                'valeur':0,
                            })
                        if competence_.commune_au_groupe:
                            key_=str(groupe_.code)+"_"+str(eval_.id)+'_'+competence_.competence_element.code
                            if not key_ in self.fields.keys(): 
                                self.fields[key_]=forms.ChoiceField(choices=competence_eval_config_choices, required = True, label='', initial=str(round(decimal.Decimal(note_competence_element.valeur),4)), widget=forms.Select(attrs={'onchange':"update_"+eval_.type+'()'}))
                        else:
                            key_=str(inscrit_.etudiant.matricule)+"_"+str(eval_.id)+'_'+competence_.competence_element.code
                            self.fields[key_]=forms.ChoiceField(choices=competence_eval_config_choices, required = True, label=str(inscrit_.etudiant), initial=str(round(decimal.Decimal(note_competence_element.valeur),4)), widget=forms.Select(attrs={'onchange':"update_"+eval_.type+'()'}))
                    self.fields[str(inscrit_.etudiant.matricule)+"_"+str(eval_.id)]=forms.DecimalField(label='', initial=note_.note, max_digits=4, decimal_places=2, disabled=False)
                    if not ((request.user.has_perm('scolar.fonctionnalite_stages_modificationsoutenances') and module_.matiere.pfe) or ((request.user.is_coordinateur(module_) or request.user.has_perm('scolar.fonctionnalite_stages_modificationsoutenancesequipes')) and module_.matiere.equipe)):
                        self.fields[str(inscrit_.etudiant.matricule)+"_"+str(eval_.id)].widget.attrs['readonly'] = True
                    else:
                        self.fields[str(inscrit_.etudiant.matricule)+"_"+str(eval_.id)].widget.attrs['onchange'] = "update_moyenne()"
                self.fields[inscrit_.etudiant.matricule+'_moy']=forms.DecimalField(label='', initial=resultat_.moy, max_digits=4, decimal_places=2, disabled = False)
                self.fields[inscrit_.etudiant.matricule+'_moy'].widget.attrs['readonly'] = True
                if not module_.matiere.equipe :
                    self.fields[inscrit_.etudiant.matricule+'_mention']=forms.ChoiceField(choices=MENTION, label='', initial=inscrit_.mention, disabled = False)
                    self.fields[inscrit_.etudiant.matricule+'_mention'].widget.attrs['readonly'] = True
            if (request.user.has_perm('scolar.fonctionnalite_stages_modificationsoutenances') and module_.matiere.pfe) or ((request.user.is_coordinateur(module_) or request.user.has_perm('scolar.fonctionnalite_stages_modificationsoutenancesequipes')) and groupe_.section.formation.programme.matiere_equipe==module_.matiere):
                required_=True
            else:
                required_=False
            if groupe_.is_equipe() :
                self.fields[str(groupe_.pfe.id)+'_organisme']=forms.ModelChoiceField(
                    label = "Organisme d'accueil",
                    queryset = Organisme.objects.all(),
                    widget=ModelSelect2Widget(
                        model=Organisme,
                        search_fields=['sigle__icontains', 'nom__icontains'],
                    ),
                    initial=groupe_.pfe.organisme,
                    required = False,
                    disabled=not required_
                        )
                self.fields[str(pfe_.id)+'_tel_promoteur']=forms.CharField(required=False, disabled= not required_, label="", initial=pfe_.tel_promoteur)    
                self.fields[str(pfe_.id)+'_email_promoteur']=forms.CharField(required=False, disabled= not required_, label="", initial=pfe_.email_promoteur)                         
            
            self.fields[str(pfe_.id)+'_intitule']=forms.CharField(required=False, disabled=not required_, initial=pfe_.intitule, label="")
            self.fields[str(pfe_.id)+'_promoteur']=forms.CharField(required=False, disabled= not required_, label="", initial=pfe_.promoteur)
            
#             enseignant_nb_encadrements_list=[] 
#             for enseignant_ in Enseignant.objects.all().order_by('nom','prenom'):
#                 enseignant_nb_encadrements_list.append((enseignant_.id, str(enseignant_)+" Encadrements("+str(enseignant_.nb_encadrements())+")"))
#             coencadrants_initial=[]
#             for enseignant_ in pfe_.coencadrants.all().order_by('nom','prenom'):
#                 coencadrants_initial.append((enseignant_.id, str(enseignant_)+" Encadrements("+str(enseignant_.nb_encadrements())+")"))
# 
#             self.fields[str(pfe_.id)+'_coencadrants'] = forms.MultipleChoiceField(
#                 label="",
#                 choices=enseignant_nb_encadrements_list,
#                 initial=coencadrants_initial,
#                 widget=Select2MultipleWidget,
#                 help_text = "Vous pouvez séléctionner plusieurs enseignants. Tapez un nom ou prénom ou 2 espaces pour avoir la liste complète.",
#                 required = False,
#                 disabled=not required_,
#             )
            if not groupe_.is_equipe():
                self.fields[str(pfe_.id)+'_coencadrants'] = forms.ModelMultipleChoiceField(
                    label="",
                    queryset=Enseignant.objects.all().order_by('nom', 'prenom'),
                    initial=pfe_.coencadrants.all().order_by('nom','prenom'),
                    widget=ModelSelect2MultipleWidget,
                    help_text = "Vous pouvez séléctionner plusieurs enseignants. Tapez un nom ou prénom ou 2 espaces pour avoir la liste complète.",
                    required = False,
                    disabled=not required_,
                )
            
                self.fields[str(soutenance_.id)+'_coencadrant']=forms.ModelChoiceField(
                    label="Coencadrant", 
                    queryset=pfe_.coencadrants.all().order_by('nom','prenom'),
                    initial=soutenance_.coencadrant,            
                    required = False,
                    disabled=not required_,
                    )
                
                self.fields[str(soutenance_.id)+'_president']=forms.ModelChoiceField(required=False, disabled=not required_, label="Président", queryset=Enseignant.objects.all().order_by('nom','prenom'), initial=soutenance_.president)
                self.fields[str(soutenance_.id)+'_rapporteur']=forms.ModelChoiceField(required=False, disabled=not required_, label="Rapporteur", queryset=Enseignant.objects.all().order_by('nom','prenom'), initial=soutenance_.rapporteur)
                self.fields[str(soutenance_.id)+'_examinateur']=forms.ModelChoiceField(required=False, disabled=not required_, label="Examinateur", queryset=Enseignant.objects.all().order_by('nom','prenom'), initial=soutenance_.examinateur)
                self.fields[str(soutenance_.id)+'_invite1']=forms.CharField(required=False, disabled=not required_, label="Invité", initial=soutenance_.invite1)
                self.fields[str(soutenance_.id)+'_invite2']=forms.CharField(required=False, disabled=not required_, label="Invité", initial=soutenance_.invite1)
                self.fields[str(soutenance_.id)+'_depot_biblio']=forms.ChoiceField(required=False, choices=OPTIONS_DEPOT,
                                                                               widget=forms.RadioSelect(attrs={'class': 'form-check-inline'}), 
                                                                               initial=soutenance_.depot_biblio, label="Le jury autorise le dépôt du mémoire à la bibliothèque")
        
            self.fields[str(soutenance_.id)+'_assesseur1']=forms.ModelChoiceField(required=False, disabled=not required_, label="Assesseur1", queryset=Enseignant.objects.all().order_by('nom','prenom'), initial=soutenance_.assesseur1)
            self.fields[str(soutenance_.id)+'_assesseur2']=forms.ModelChoiceField(required=False, disabled=not required_, label="Assesseur2", queryset=Enseignant.objects.all().order_by('nom','prenom'), initial=soutenance_.assesseur2)
            self.fields[str(soutenance_.id)+'_date']=forms.DateField(required=False, disabled=not required_, label='', input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), initial=soutenance_.date)
            
            
            self.fields[str(groupe_.id)+'_'+str(module_.id)]=forms.BooleanField(disabled=False, initial=False, label='Etablir le PV final:', help_text='La modification des notes ne sera plus possible en cochant cette case.', required = False)
            self.fields[str(groupe_.id)+'_'+str(module_.id)].widget.attrs['onchange'] = "update_moyenne()"
#             self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
#             self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire d'évaluation d'un PFE. Merci de le signaler à l'administrateur")

class OrganismeForm(forms.ModelForm):
    class Meta:
        model = Organisme
        fields = ['sigle', 'nom', 'adresse', 'pays', 'type', 'statut', 'nature', 'secteur', 'taille']

    def __init__(self, *args, **kwargs):
        super(OrganismeForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['sigle'].help_text="Saisir en Majuscule."
        self.helper.add_input(Submit('submit','Créer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class PictureWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        html = Template("""<img src="$media$link" width=100% />""")
        return mark_safe(html.substitute(media=settings.MEDIA_URL, link=value))

class InstitutionDetailForm(forms.ModelForm):
    class Meta:
        model = Institution
        fields = ['nom_plateforme', 'nom','nom_a', 'sigle', 'adresse', 'ville', 'ville_a', 'wilaya_institution', 'tel','fax', 'web', 'color', 'email_domain', 'illustration_cursus', 'banniere', 'logo', 'logo_bis','header', 'footer','identifiant_progres','code_etablissement', 'users_direction', 'users_scolarite', 'users_stage', 'email_futurs_stagiaires', 'users_theses', 'users_offres', 'users_demandes_comptes', 'email_webmaster', 'signature_emails', 'activation_emails', 'activation_ddc', 'activation_competences', 'activation_livret_competences', 'activation_charges', 'activation_google_agenda', 'activation_authentification_google', 'activation_feedback', 'activation_theses', 'activation_webhelp', 'activation_lettres_recommandation', 'activation_enregistrement_etudiants', 'activation_offres', 'activation_demandes_comptes', 'activation_public_stages', 'activation_public_projets', 'activation_public_equipesrecherche']
        
    def __init__(self, *args, **kwargs):
        super(InstitutionDetailForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['banniere']=forms.ImageField(label='Bannière', required=False, widget=PictureWidget)
        self.fields['illustration_cursus']=forms.ImageField(label='Illustration du cursus', required=False, widget=PictureWidget)
        self.fields['logo']=forms.ImageField(label="Logo de l'établissement", required=False, widget=PictureWidget)
        self.fields['logo_bis']=forms.ImageField(label="Logo de la plateforme", required=False, widget=PictureWidget)
        self.fields['header']=forms.ImageField(label='Entête', required=False, widget=PictureWidget)
        self.fields['footer']=forms.ImageField(label='Pied de page', required=False, widget=PictureWidget)
        self.fields['wilaya_institution'] = forms.ModelChoiceField(
            queryset=Wilaya.objects.all().order_by('nom'),
            label=u"Wilaya",
            required=False,
            disabled=True,
            )
        self.fields['users_direction']=forms.ModelMultipleChoiceField(
            queryset=User.objects.all().order_by('username'),
            label=u"Utilisateurs qui seront notifiés par e-mail en tant que direction",
            widget=ModelSelect2MultipleWidget(
                    model=User,
                    search_fields=['username__icontains', 'email__icontains'],

                ),
            required = False,
            disabled=True
        )
        self.fields['users_scolarite']=forms.ModelMultipleChoiceField(
            queryset=User.objects.all().order_by('username'),
            label=u"Utilisateurs qui seront notifiés par e-mail en tant que scolarité",
            widget=ModelSelect2MultipleWidget(
                    model=User,
                    search_fields=['username__icontains', 'email__icontains'],

                ),
            required = False,
            disabled=True
        )
        self.fields['users_stage']=forms.ModelMultipleChoiceField(
            queryset=User.objects.all().order_by('username'),
            label=u"Utilisateurs qui seront notifiés par le déroulement du processus de validation des stages de fin d'études",
            widget=ModelSelect2MultipleWidget(
                    model=User,
                    search_fields=['username__icontains', 'email__icontains'],

                ),
            required = False,
            disabled=True
        )
        self.fields['users_theses']=forms.ModelMultipleChoiceField(
            queryset=User.objects.all().order_by('username'),
            label=u"Utilisateurs qui seront notifiés par le déroulement du processus de gestion des thèses de post-graduation",
            widget=ModelSelect2MultipleWidget(
                    model=User,
                    search_fields=['username__icontains', 'email__icontains'],

                ),
            required = False,
            disabled=True
        )
        self.fields['users_offres']=forms.ModelMultipleChoiceField(
            queryset=User.objects.all().order_by('username'),
            label=u"Utilisateurs qui seront notifiés par le déroulement des processus de gestion des offres (emplois, thèses, stages pratiques, etc.)",
            widget=ModelSelect2MultipleWidget(
                    model=User,
                    search_fields=['username__icontains', 'email__icontains'],

                ),
            required = False,
            disabled=True
        )
        self.fields['users_demandes_comptes']=forms.ModelMultipleChoiceField(
            queryset=User.objects.all().order_by('username'),
            label=u"Utilisateurs qui seront notifiés par les nouvelles demandes de compte (pour publier des offres, stages, etc.) (la fonctionnalité doit d'abord être activée)",
            widget=ModelSelect2MultipleWidget(
                    model=User,
                    search_fields=['username__icontains', 'email__icontains'],

                ),
            required = False,
            disabled=True
        )
        for key_ in self.fields.keys():
            self.fields[key_].widget.attrs['readonly']=True
            if key_.startswith('activation') :
                self.fields[key_].disabled=True


class PFEDetailForm(forms.ModelForm):
    class Meta:
        model = PFE
        exclude = ['groupe']

    def __init__(self, *args, **kwargs):
        super(PFEDetailForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['type']=forms.ChoiceField(choices=set(TYPE_STAGE) ^ set((('D', 'Doctorat'),)))
        self.fields['intitule'].widget = forms.Textarea(attrs={'rows':1})
        self.fields['promoteur'].widget = forms.Textarea(attrs={'rows':1})
        self.fields['keywords'].widget = forms.Textarea(attrs={'rows':1})
        
        self.fields['specialites']=forms.ModelMultipleChoiceField(
            queryset = Specialite.objects.all(),
            widget=ModelSelect2MultipleWidget(
                model=Specialite,
                search_fields=['code__icontains', 'intitule__icontains'],
            ),
        )
        self.fields['coencadrants']=forms.ModelMultipleChoiceField(
            label = "Encadrants (enseignants de l'établissement)",
            queryset = Enseignant.objects.all(),
            widget=ModelSelect2MultipleWidget(
                model=Enseignant,
                search_fields=['nom__icontains', 'prenom__icontains'],
            ),
        )
        self.fields['reserve_pour']=forms.ModelMultipleChoiceField(
            queryset = Inscription.objects.all(),
            widget=ModelSelect2MultipleWidget(
                model=Inscription,
                search_fields=['etudiant__nom__icontains', 'etudiant__prenom__icontains']
            ),
        )

        for key_ in self.fields.keys():
            self.fields[key_].widget.attrs['readonly']=True

class EnseignantDetailForm(forms.ModelForm):
    class Meta:
        model = Enseignant
       
        exclude = ['user', 'edt', 'otp', 'charge_statut']
    
    def __init__(self, *args, **kwargs):
        super(EnseignantDetailForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.add_input(Button('cancel', 'Retour', css_class='btn-secondary', onclick="window.history.back()"))
        
        for key_ in self.fields.keys():
            self.fields[key_].widget.attrs['readonly'] = True
            
            
            
            
class SelectOrCreateOrganismeForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SelectOrCreateOrganismeForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['organisme']= forms.ModelChoiceField(
                queryset=Organisme.objects.all().order_by('sigle', 'nom'),
                label="Organisme",
                widget=ModelSelect2Widget(
                        model=Organisme,
                        search_fields=['sigle__icontains', 'nom__icontains']
                    ),
                help_text = "Tapez le sigle ou nom de l'organisme. S'il n'apparaît pas, merci de cliquer sur le bouton Nouveau",
                required = True
            )
        self.helper.add_input(Submit('submit','Sélectionner',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Nouveau', css_class='btn-secondary', onclick="window.location.href='"+reverse('organisme_create_for_pfe_create')+"'"))
        self.helper.form_method='POST'

class PartenaireCreateForm(forms.Form):
    nom = forms.CharField(max_length=50, required=True)
    prenom = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    def __init__(self, *args, **kwargs):
        super(PartenaireCreateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Créer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Nouveau', css_class='btn-secondary', onclick="window.location.href='"+reverse('organisme_list')+"'"))
        self.helper.form_method='POST'

    def clean_email(self):
        email_ = self.cleaned_data['email']
        if email_ :
            qs = User.objects.filter(username__iexact=email_)
            if qs.exists() :
                raise ValidationError("Un utilisateur existe déjà avec cette adresse e-mail")
        return email_ if email_ else None

class SelectSingleModuleForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super(SelectSingleModuleForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['module']= forms.ModelChoiceField(
                queryset=Module.objects.all().order_by('formation__annee_univ__annee_univ','formation__programme__ordre','periode__periode__ordre','matiere__code'),
                label=u"Module",
                widget=ModelSelect2Widget(
                        model=Module,
                        search_fields=['matiere__code__icontains','matiere__titre__icontains'],
    
                    ),
                help_text = "Tapez le code matière ou un mot dans l'intitulé de la matière",
                required = True
            )
        self.helper.add_input(Submit('submit','Copier',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class SelectModuleForm(forms.Form):
    
    def __init__(self, formation_pk, *args, **kwargs):
        super(SelectModuleForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        formation_=Formation.objects.get(id=formation_pk)
        for periode_ in formation_.programme.periodes.all():
            module_list=Module.objects.filter(formation=formation_, periode=periode_)
            for module_ in module_list:
                self.fields['calcul_ne_'+str(module_.id)]=forms.DecimalField(
                    initial=module_.calcul_note_eliminatoire(),
                    label="",
                    max_digits=4, decimal_places=2,
                    required = True
                    )


                self.fields['select_module_'+str(module_.id)]=forms.BooleanField(
                    initial=False,
                    label="",
                    required=False
                    )
        self.helper.form_method='POST'


class SelectPVSettingsForm(forms.Form):
    
    def __init__(self, formation_pk, *args, **kwargs):
        super(SelectPVSettingsForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        formation_=Formation.objects.get(id=formation_pk)
        for periode_ in formation_.programme.periodes.all():
            matiere_list=[]
            for ue in periode_.ues.all():
                for matiere in ue.matieres.all():
                    if not (matiere.code, matiere.code) in matiere_list:
                        matiere_list.append((matiere.code, matiere.code))
            self.fields['matieres_affichage_'+periode_.periode.code]=forms.MultipleChoiceField(required=False, 
                                                                 label='Matières de '+periode_.periode.code+' à afficher sur le PV',
                                                                 widget=forms.CheckboxSelectMultiple,
                                                                 choices=matiere_list,
                                                                 help_text="Sélectionner les modules de la période "+periode_.periode.code+" à afficher sur le PV.")
            self.fields['matieres_moyenne_'+periode_.periode.code]=forms.MultipleChoiceField(required=False, 
                                                                 label='Matières de '+periode_.periode.code+' à considérer dans le calcul de la moyenne',
                                                                 widget=forms.CheckboxSelectMultiple,
                                                                 choices=matiere_list,
                                                                 help_text="Sélectionner les modules de la période "+periode_.periode.code+" à considérer dans le calcul de la moyenne.")
        self.fields['photo'] = forms.BooleanField(required=False, initial=False, help_text="Cochez pour faire apparaître les photos sur le PV.",
                                                                label='Photo')
        self.fields['sort'] = forms.BooleanField(required=False, initial=True, help_text="Cochez pour faire un tri par rang du PV.",
                                                                label='Tri par rang')
        self.fields['anonyme'] = forms.BooleanField(required=False, initial=False, help_text="Cochez pour rendre le PV anonyme.",
                                                                label='Anonyme')
        self.fields['ne'] = forms.BooleanField(required=False, initial=False, help_text="Cochez pour afficher le nombre de notes éliminatoires",
                                                                label='Notes éliminatoires')
        self.fields['rang'] = forms.BooleanField(required=False, initial=False, help_text="Cochez pour afficher le rang.",
                                                                label='Rang')
        self.fields['xlsx'] = forms.BooleanField(required=False, initial=False, help_text="Cochez pour stocker le PV au format XLS",
                                                                label='Excel (Stocké)')
        self.fields['xlsxemail'] = forms.BooleanField(required=False, initial=False, help_text="Cochez pour recevoir le PV au format XLS par e-mail",
                                                                label='Excel (mail)')
        self.fields['signatures'] = forms.BooleanField(required=False, initial=False, help_text="Cochez pour prévoir un espace de signatures en pied de page.",
                                                                label='Signatures')
        self.fields['affichage_decisions_jury'] = forms.BooleanField(required=False, initial=False, help_text="Cochez pour afficher la situation des étudiants (Inscrit, ..)",
                                                        label='Situations')
        self.fields['conges'] = forms.BooleanField(required=False, initial=False, help_text="Cochez pour inclure les étudiants en situation de congé académique",
                                                label='Congés académiques')
        self.helper.form_method='POST'
        
class SelectPVAnnuelSettingsForm(forms.Form):
    photo = forms.BooleanField(required=False, initial=True, help_text="Cochez pour faire apparaître les photos sur le PV.",
                                                                label='Photo')
    sort = forms.BooleanField(required=False, initial=True, help_text="Cochez pour faire un tri par rang du PV.",
                                                                label='Tri par rang')
    tri_nom = forms.BooleanField(required=False, initial=False, help_text="Cochez pour trier les étudiants par nom et prénom (le tri par rang doit être décoché. Si aucune des deux options n'est cochée entre tri par rang et tri par noms alors le tri se fera par groupes)",
                                                                label='Tri par nom et prénom')
    anonyme = forms.BooleanField(required=False, initial=False, help_text="Cochez pour rendre le PV anonyme.",
                                                                label='Anonyme')
    ne = forms.BooleanField(required=False, initial=True, help_text="Cochez pour afficher le nombre de notes éliminatoires",
                                                                label='Notes éliminatoires')
    moy_ue = forms.BooleanField(required=False, initial=False, help_text="Cochez pour afficher la moyenne par UE",
                                                                label='Moyenne UE')
    rang = forms.BooleanField(required=False, initial=True, help_text="Cochez pour afficher le rang.",
                                                                label='Rang')
    signatures = forms.BooleanField(required=False, initial=True, help_text="Cochez pour prévoir un espace de signatures en pied de page.",
                                                                label='Signatures')
    nb_lignes_signatures = forms.IntegerField(required=False, initial=3, help_text="Indiquez le nombre de lignes dans l'espace de signatures (uniquement si les signatures sont activées)",
                                                            label='Nombre de lignes de signatures')
    nb_cases_par_ligne = forms.IntegerField(required=False, initial=8, help_text="Indiquez le nombre de cases par ligne de signatures dans l'espace de signatures (uniquement si les signatures sont activées)",
                                                            label='Nombre de cases par ligne de signatures')
    signatures_modules = forms.BooleanField(required=False, initial=False, help_text="Cochez si vous souhaitez qu'il y ait un espace de signatures d'une seule ligne uniquement avec tous les noms des modules + le chef du département (uniquement si les signatures sont activées).",
                                                            label='Signatures avec les noms des modules en une seule ligne')
    rachat = forms.BooleanField(required=False, initial=False, help_text="Cochez pour rajouter la fonction de rachat.",
                                                                label='Rachat')
    affichage_moy_rachat = forms.BooleanField(required=False, initial=True, help_text="Cochez si vous souhaitez afficher les moyennes annuelles de Rachat",
                                                                label='Affichage des moyennes de rachat')  
    reserve = forms.BooleanField(required=False, initial=False, help_text="Cochez pour rendre le PV réservé à l'administration.",
                                                                label='Réservé')

    xlsx = forms.BooleanField(required=False, initial=False, help_text="Cochez pour stocker le PV au format XLS",
                                                                label='Excel (Stocké)')
    
    xlsxemail = forms.BooleanField(required=False, initial=False, help_text="Cochez pour recevoir le PV au format XLS par e-mail",
                                                                label='Excel (mail)')
 
    post_rattrapage = forms.BooleanField(required=False, initial=False, help_text="Cochez si c'est un PV post-rattrapage.",
                                                                label='Post-Rattrapage')
    
    dates_naissance = forms.BooleanField(required=False, initial=False, help_text="Cochez si vous souhaitez afficher les dates de naissance",
                                                                label='Dates de naissance')       
    
    infos_etudiants_en_premier = forms.BooleanField(required=False, initial=False, help_text="Cochez si vous souhaitez que les informations personnelles des étudiants (nom, prénom, ..) soient affichées en premières colonnes à gauche du PV. Dans le cas contraire, ces informations seront affichées par défaut en dernières colonnes (côté droit du PV)",
                                                                label='Informations des étudiants en premières colonnes')   

    situation_complete = forms.BooleanField(required=False, initial=False, help_text="Cochez si vous souhaitez que la situation complète des étudiants soit affichée. Dans le cas contraire, les étudiants en congé académique quelque soit le motif seront marqués 'Maladie'",
                                                                label='Situation complète')   

    affichage_groupe = forms.BooleanField(required=False, initial=True, help_text="Cochez si vous souhaitez afficher les groupes des étudiants",
                                                                label='Groupes')   

    affichage_final_chaque_periode = forms.BooleanField(required=False, initial=True, help_text="Cochez si vous souhaitez afficher moyennes et rangs et NE pour chaque période",
                                                                label='Moyennes et rangs et NE pour chaque période')   

    affichage_titres_matieres = forms.BooleanField(required=False, initial=False, help_text="Cochez si vous souhaitez afficher les intitulés complet des matières, dans le cas contraire ce sera les codes des matières qui seront affichés",
                                                                label='Intitulés des matières')   
    provisoire = forms.BooleanField(required=False, initial=False, help_text="Cochez si le PV est provisoire (il sera marqué dans le PV qu'il est provisoire et que seul le PV final fera foi)",
                                                                label='Provisoire')   
    longueur = forms.DecimalField(required=False, max_digits=4, decimal_places=2, initial=29.7, help_text="Indiquez la longueur du PV à l'impression (en cm)",
                                                            label="Longueur à l'impression")  
    largeur = forms.DecimalField(required=False, max_digits=4, decimal_places=2, initial=42, help_text="Indiquez la largeur du PV à l'impression (en cm)",
                                                            label="Largeur à l'impression") 
    repeter_entete = forms.BooleanField(required=False, initial=False, help_text="Cochez si vous souhaitez que l'entête soit répétée sur chaque page lors de l'impression",
                                                                label='Entête répétée sur chaque page')  
    affichage_pied_de_page = forms.BooleanField(required=False, initial=True, help_text="Cochez si vous souhaitez afficher l'image du pied de page (contenant le nom de l'institution, ..)",
                                                                label='Pied de page')
    police = forms.IntegerField(required=False, initial=16, help_text="Indiquez le taille de la police des caractères",
                                                            label='Taille des caractères') 
    police_entete = forms.IntegerField(required=False, initial=16, help_text="Indiquez le taille de la police des caractères de l'entête du tableau des notes du PV (contenant les noms des modules)",
                                                            label='Taille des caractères de la première ligne (header)')  
    conges = forms.BooleanField(required=False, initial=True, help_text="Cochez si vous souhaitez afficher congés académiques",
                                                                label='Congés')
    abandons = forms.BooleanField(required=False, initial=True, help_text="Cochez si vous souhaitez afficher les abandons",
                                                                label='Abandons')   
    non_inscrits = forms.BooleanField(required=False, initial=True, help_text="Cochez si vous souhaitez afficher les non-inscrits",
                                                                label='Non-inscrits')   
      
    def __init__(self, formation_pk, *args, **kwargs):
        super(SelectPVAnnuelSettingsForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        formation=Formation.objects.get(id=formation_pk)
        self.fields['post_rattrapage'].disabled=not formation.activation_rattrapage()
        if Inscription.objects.filter(proposition_decision_jury="FD").exists() :
            self.fields['defaillants']=forms.BooleanField(required=False, initial=True, help_text="Cochez si vous souhaitez afficher les défaillants",
                                                                    label='Défaillants')
        self.fields['observations']= forms.BooleanField(required=False, initial=False, help_text="Cochez si vous souhaitez afficher les observations dans le fichier excel",
                                                                label='Observations') 
        self.helper.add_input(Submit('submit','Générer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'
        
        
class PassageSettingsForm(forms.Form):

    def __init__(self, formation_pk, *args, **kwargs):
        super(PassageSettingsForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        formation=Formation.objects.get(id=formation_pk)
        module_list=Module.objects.filter(formation=formation).distinct()
        self.fields['moyenne_passage']=forms.DecimalField(initial=formation.moyenne_passage, max_digits=4, decimal_places=2, label="Moyenne de passage de la formation "+str(formation), help_text="Indiquez la moyenne d'admission pour la formation")
        if formation.activation_rattrapage() :
            for module_ in module_list:  
                self.fields['seuil_'+str(module_.id)]=forms.DecimalField(initial=module_.seuil_rattrapage, max_digits=4, decimal_places=2, label="Seuil Rattrapage "+str(module_), help_text="Indiquez la moyenne seuil du module pour la session normale, si l'étudiant est en dessous alors il sera marqué : doit passer le rattrapage")
        
        
        self.helper.add_input(Submit('submit','Enregistrer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'

class FeedbackUpdateForm(forms.Form):
    REPONSE=(
        ('++','++'),
        ('+','+'),
        ('-','-'),
        ('--','--'),
    )

    def __init__(self, inscription_pk, periode_pk, *args, **kwargs):
        super(FeedbackUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
            inscription_=Inscription.objects.get(id=inscription_pk)
            periodepgm_=PeriodeProgramme.objects.get(id=periode_pk)
            inscription_periode_=InscriptionPeriode.objects.get(inscription=inscription_, periodepgm=periode_pk)
            if inscription_periode_.groupe:
                groupe_section=inscription_periode_.groupe.section.groupes.all().filter(code__isnull=True).get() # le groupe qui représente la section
                activites_suivies_list=Activite.objects.filter(cible__in=[inscription_periode_.groupe, groupe_section], module__periode__periode=periodepgm_.periode)
            else:
                activites_suivies_list=[]
            module_traite_list=[]
            for activite_suivie in activites_suivies_list:
                if not activite_suivie.module.id in module_traite_list:
                    module_traite_list.append(activite_suivie.module.id)
                    key_=str(activite_suivie.module.id)
                    feedback_, created=Feedback.objects.get_or_create(module=activite_suivie.module, inscription=inscription_, defaults={
                        'module':activite_suivie.module,
                        'inscription':inscription_,
                        'show':False
                    })
                    self.fields[key_]=forms.CharField(max_length=1000, required=False, widget=forms.Textarea, label='Commentaire facultatif', initial=feedback_.comment)
                    
                    if activite_suivie.module.matiere.mode_projet:
                        question_list=Question.objects.exclude(projet_na=True).order_by('code')
                    else:
                        question_list=Question.objects.exclude(cours_na=True).order_by('code')
                    for question_ in question_list:
                        key_=str(activite_suivie.module.id)+'_'+str(question_.code)
                        reponse_, created=Reponse.objects.get_or_create(feedback=feedback_, question=question_, defaults={
                            'feedback':feedback_,
                            'question':question_
                        })
                        
                        self.fields[key_]=forms.ChoiceField(choices=self.REPONSE, required=True, label='', initial=reponse_.reponse,
                                 widget=forms.RadioSelect(
                                    attrs={
                                    #'class': 'custom-control custom-radio custom-control-inline'
                                    'class': 'form-check-inline'
                                    }
                                ) 
                        )
                
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de saisie des feedbacks. Merci de le signaler à l'administrateur")

class AbsencesForm(forms.Form):
    
    def __init__(self, groupe_pk, module_pk, *args, **kwargs):
        super(AbsencesForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['seance_date']=forms.DateField(required=True, label="Date de la séance", input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), initial=datetime.date.today()) #
        self.fields['seance_rattrapage']=forms.BooleanField(initial=False, required=False, label="Séance de rattrapage?")
        module_=get_object_or_404(Module, id=module_pk)
        inscription_list_=InscriptionPeriode.objects.filter(groupe=groupe_pk, periodepgm=module_.periode).values('inscription')
        resultat_list=Resultat.objects.filter(ancien_resultat__isnull=True, acquis=False, module__matiere=module_.matiere, inscription__in=inscription_list_, inscription__decision_jury='C').order_by('inscription__etudiant__nom')
        choice_list=[]
        for resultat_ in resultat_list:
            choice_list.append(
                (resultat_.inscription.etudiant.matricule, resultat_.inscription.etudiant)
                ) 
        self.fields['absence_list']=forms.MultipleChoiceField(required=False, choices=choice_list, label="Cochez les absents",
                                        widget=forms.CheckboxSelectMultiple())
        self.helper.add_input(Submit('submit','Signaler',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class AbsenceEtudiantSelectForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        etudiant = kwargs.pop('etudiant', None)
        absence_list=kwargs.pop('absences_a_charger', None)
        date_justification=kwargs.pop('date_justification', None)
        motif=kwargs.pop('motif', None)
        super(AbsenceEtudiantSelectForm, self).__init__(*args, **kwargs)

        self.fields['etudiant'] = forms.ModelChoiceField(
                queryset=Etudiant.objects.all().order_by('nom', 'prenom'),
                label=u"Etudiant",
                widget=ModelSelect2Widget(
                    model=Etudiant,
                    search_fields=['nom__icontains', 'prenom__icontains'],
                    ),
                help_text = "Tapez le nom de l'étudiant ou 2 espaces pour avoir la liste complète.",
                )
        
        self.fields['debut_periode'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), required=False) 
        self.fields['fin_periode'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), required=False)
        self.fields['absence_list'] = forms.ModelMultipleChoiceField(
                queryset=AbsenceEtudiant.objects.filter(seance__activite__module__formation__annee_univ__encours=True, justif=False).order_by('-seance__date','seance__activite__module__matiere__code'),
                label=u"Liste des absences à justifier",
                widget=ModelSelect2MultipleWidget(
                    model=AbsenceEtudiant,
                    search_fields=['seance__activite__module__matiere__code__icontains'],
                    dependent_fields={'etudiant':'etudiant'}
                    ),
                required=False,
                help_text = "Tapez le code du module ou 2 espaces pour avoir la liste complète des absences NON-JUSTIFIÉES. Sélection multiple possible.",
                )
    
        self.fields['date_justification'] = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), required=False) # 
        self.fields['motif'] =  forms.CharField(max_length=256, label="Motif de l'absence", required=False)
        
    
        self.fields['etudiant'].initial=etudiant
        self.fields['absence_list'].initial=absence_list
        self.fields['date_justification'].initial=date_justification
        self.fields['motif'].initial=motif
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Charger les absences de la période / Justifier',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'


class ImportNotesForm(forms.Form):    
    def __init__(self, *args, **kwargs):
        super(ImportNotesForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['formation']=forms.ModelChoiceField(queryset=Formation.objects.filter().order_by('-annee_univ__annee_univ','programme__ordre'))
        self.fields['file']=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
        self.helper.add_input(Submit('submit','Importer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'


class ImportFeedbackForm(forms.Form):

    def __init__(self, module_pk, *args, **kwargs):
        super(ImportFeedbackForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['module']=forms.ModelChoiceField(queryset=Module.objects.filter(id=module_pk), initial=0)
        self.helper.layout=Layout(
            Div(
                'module', Field('file'), css_class="row"
            ),
            FormActions(
                Submit('submit','Importer'),
                HTML('<a class="btn btn-secondary" href="{% url "module_list" %}">Annuler</a>')
            )
        )        
        self.fields['file']=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
    
        self.helper.form_method='POST'

class PlanificationImportFileForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super(PlanificationImportFileForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        
        self.fields['periode'] = forms.ModelChoiceField(queryset=Periode.objects.all(), label='Choisir Période')
        self.fields['file']=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
    
        self.helper.add_input(Submit('submit','Importer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class EDTSelectForm(forms.Form):    
    def __init__(self, *args, **kwargs):
        super(EDTSelectForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        
        self.fields['date_debut'] = forms.DateTimeField(input_formats = settings.DATE_INPUT_FORMATS, widget=DateTimePickerInput(format='%d/%m/%Y'), initial=datetime.date.today())
        self.fields['date_fin'] = forms.DateTimeField(input_formats = settings.DATE_INPUT_FORMATS, widget=DateTimePickerInput(format='%d/%m/%Y'), initial=datetime.date.today() + datetime.timedelta(days = 7))
        self.fields['google_calendar_list'] = forms.ModelMultipleChoiceField(
                queryset=GoogleCalendar.objects.all().order_by('code'),
                label=u"Liste des agendas",
                widget=ModelSelect2MultipleWidget(
                        model=GoogleCalendar,
                        search_fields=['code__icontains'],
                    ),
                help_text = "Sélection multiple possible. Tapez le nom du groupe ou deux espaces pour avoir la liste complète.",
                required = True
            )
        
        self.helper.add_input(Submit('submit','Effacer',css_class='btn-danger'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class EDTImportFileForm(forms.Form):
    
    date_debut = forms.DateTimeField(input_formats = settings.DATE_INPUT_FORMATS, widget=DateTimePickerInput(format='%d/%m/%Y'), initial=datetime.date.today())
    date_fin = forms.DateTimeField(input_formats = settings.DATE_INPUT_FORMATS, widget=DateTimePickerInput(format='%d/%m/%Y'), initial=datetime.date.today() + datetime.timedelta(days = 7))
    file=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
    
    def __init__(self, *args, **kwargs):
        super(EDTImportFileForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Importer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class ImportFileForm(forms.Form):
    file=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
    
    def __init__(self, *args, **kwargs):
        super(ImportFileForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Importer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'


class OTPImportFileForm(forms.Form):
    file=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
    #file=forms.FileField(label='Choisir un fichier')
    otp=forms.CharField(required=True, label="Mot de Passe (Envoyé par SMS)", help_text="Saisir ici le mot de passe qu'on vient de vous envoyer par SMS. Si vous ne le recevez pas dans la minute qui suit, merci de vérifier que le numéro de téléphone associé à votre compte est correct.")
    
    def __init__(self, *args, **kwargs):
        super(OTPImportFileForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Importer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'



class ImportAffectationDiplomeForm(forms.Form):    
    def __init__(self, *args, **kwargs):
        super(ImportAffectationDiplomeForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        
        self.fields['diplome'] = forms.ChoiceField(
                choices=Diplome.objects.values_list('id','intitule'),
                label=u"Diplome",
                widget = Select2Widget(
                #attrs={'style':'width:800px; height:10px;'}
                ),
                required = True,
                help_text = "Choisir le diplome",
                )
        self.fields['formation'] = forms.ModelChoiceField(
                queryset=Formation.objects.filter(programme__ordre__gte=5).order_by('-annee_univ__annee_univ'),
                label=u"Formation",
                widget=ModelSelect2Widget(
                        model=Formation,
                        search_fields=['programme__code__icontains',],
                        dependent_fields={'diplome':'programme__diplome'},
                        #attrs={'style':'width:800px; height:10px;'}
                    ),
                help_text = "Choisir la formation. Tapez deux espaces pour avoir toute la liste.",
                required = True
            )
        self.fields['config_charge'] = forms.ModelChoiceField(
            queryset=ActiviteChargeConfig.objects.all().order_by('type'), required=True, label="Type de l'activité")
        self.fields['file']=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
    
        self.helper.add_input(Submit('submit','Importer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class ImportAffectationForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        super(ImportAffectationForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['formation']=forms.ModelChoiceField(queryset=Formation.objects.all().order_by('annee_univ__annee_univ','programme__ordre'))
        self.fields['file']=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
        self.helper.add_input(Submit('submit','Importer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class ImportDeliberationForm(forms.Form):
    def __init__(self, annee_univ_pk, *args, **kwargs):
        super(ImportDeliberationForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['formation']=forms.ModelChoiceField(queryset=Formation.objects.filter(annee_univ__annee_univ=annee_univ_pk).order_by('annee_univ__annee_univ','programme__ordre'))
        self.fields['file']=forms.FileField(label='Choisir un fichier', widget=forms.FileInput(attrs={'class':"custom-file-input"}))
        self.helper.add_input(Submit('submit','Importer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class MatiereFormHelper(FormHelper):
    #form_method = 'GET'
    layout=Layout(
        TabHolder(
            Tab('Identification',
                Div(
                    'code', 'precision', css_class="row"
                ),
                Div(
                    'coef', 'credit', css_class="row"
                ),
                Div(
                    'titre', 'titre_en', 'titre_a', css_class="row"
                ),
                Div(
                    'vh_cours', 'vh_td', 'vh_tp', 'edition', css_class="row"
                ),
                Div(
                    'pfe', css_class="row"
                ),
                Div(
                    'mode_projet', css_class="row"
                ),
                Div(
                    'equipe', css_class="row"
                ),
                Div(
                    'validable', css_class="row"
                ),
                Div(
                    'seminaire', css_class="row"
                )
            ),
            Tab('Objectifs, Compétences et Pré-requis',
                'ddc', 'pre_requis', 'objectifs'
            ),
            Tab('Contenu',
                'contenu'
            ),
            Tab('Compléments',
                'travail_perso',
                'bibliographie'
            )
        ),
    )

class PermissionsUpdateForm(forms.Form):
    def __init__(self, access_table, group_names, request, *args, **kwargs):
        super(PermissionsUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
            for fonctionnalite, permissions_par_fonctionnalite_et_cpt in access_table.items() :
                for code_et_nom_et_groups in permissions_par_fonctionnalite_et_cpt[0] :
                    for group_name, permission_du_group in code_et_nom_et_groups[2].items() :
                        self.fields[str(group_name)+'_'+code_et_nom_et_groups[0]]=forms.BooleanField()
                        self.fields[str(group_name)+'_'+code_et_nom_et_groups[0]].initial=permission_du_group
                        self.fields[str(group_name)+'_'+code_et_nom_et_groups[0]].label=''
                        self.fields[str(group_name)+'_'+code_et_nom_et_groups[0]].required=False
            
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du tableau de modification des permissions. Merci de le signaler à l'administrateur")

class PermissionsUserUpdateForm(forms.Form):
    def __init__(self, access_table, user_, request, *args, **kwargs):
        super(PermissionsUserUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try :
            groups_=Group.objects.all().order_by('name')
            for group_ in groups_ :
                affectation=Group.objects.filter(id=group_.id, user__in=[user_]).exists()
                self.fields['group_'+group_.name]=forms.BooleanField()
                self.fields['group_'+group_.name].initial=affectation
                self.fields['group_'+group_.name].label=''
                self.fields['group_'+group_.name].required=False
            for fonctionnalite, permissions_par_fonctionnalite_et_cpt in access_table.items() :
                for code_et_nom_et_affectation in permissions_par_fonctionnalite_et_cpt[0] :
                    self.fields['permission_'+code_et_nom_et_affectation[0]]=forms.BooleanField()
                    self.fields['permission_'+code_et_nom_et_affectation[0]].initial=code_et_nom_et_affectation[2]
                    self.fields['permission_'+code_et_nom_et_affectation[0]].label=''
                    self.fields['permission_'+code_et_nom_et_affectation[0]].required=False
            
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du tableau de modification des permissions. Merci de le signaler à l'administrateur")


class UserChoiceForm(forms.Form):
    username=forms.ModelChoiceField(
            queryset=User.objects.all().order_by('username'),
            label=u"Utilisateur",
            widget=ModelSelect2Widget(
                    model=User,
                    search_fields=['username__icontains', 'email__icontains'],

                ),
            help_text = "Tapez le nom d'utilisateur ou une partie du nom d'utilisateur pour faire une recherche",
            required = True
        )
    def __init__(self, *args, **kwargs):
        super(UserChoiceForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Suivant',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

class IntervalleDateSelectForm(forms.Form):

    date_debut = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y')) #
    date_fin = forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y')) #
    
    def __init__(self, *args, **kwargs):
        super(IntervalleDateSelectForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()        
        self.helper.add_input(Submit('submit','Sélectionner',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))

        self.helper.form_method='POST'
class DoctorantCreateForm(forms.Form):
    
    def __init__(self, request, *args, **kwargs):
        super(DoctorantCreateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
                
            self.fields['User'] = forms.ModelChoiceField(
                queryset=User.objects.filter(Q(enseignant__doctorant__isnull=True) & Q(etudiant__doctorant__isnull=True)),
                label=u"Utilisateur existant",
                widget=ModelSelect2Widget(
                        model=User,
                        search_fields=['username__icontains', 'email__icontains',],
                    ),
                help_text = "Cela permettra d'associer le doctorant à tout utilisateur et/ou enseignant et/ou étudiant associé(s) à cette adresse e-mail, tandis que le doctorant peut être étudiant, enseignant, ou les deux.",
                required = False
            ) 
            self.fields['Email'] = forms.EmailField(label="Nouvelle adresse e-mail du doctorant (le compte sera créé)", required=False, help_text="Uniquement si le doctorant n'est ni enseignant ni étudiant existant dans l'établissement, et ce afin de lui créer automatiquement un compte utilisateur sur la plateforme.")
            self.fields['Etudiant'] = forms.BooleanField(label="Étudiant (Nouveau / mise à jour)", required=False, help_text="Cochez si vous souhaitez que l'utilisateur soit un étudiant, s'il ne l'est pas déjà (ayant accès aux fonctionnalités d'étudiant, et il lui sera créé un profil d'étudiant). Si pourun étudiant existant cette case n'est pas cochée, alors ses champs ne seront pas mis à jour")  
            self.fields['Enseignant'] = forms.BooleanField(label="Enseignant (Nouveau / mise à jour)", required=False, help_text="Cochez si vous souhaitez que l'utilisateur soit un enseignant, s'il ne l'est pas déjà (ayant accès aux fonctionnalités d'enseignant, et il lui sera créé un profil d'enseignant). Si pour un enseignant existant cette case n'est pas cochée, alors ses champs ne seront pas mis à jour")    
            self.fields['MatriculeEtud'] = forms.CharField(label="Matricule étudiant", required=False, help_text="Uniquement si le doctorant sera un nouvel utilisateur et étudiant. Le matricule doit être unique par rapport à tous les étudiants de la plateforme.")
            self.fields['Nom'] = forms.CharField(label="Nom", required=False, help_text="Uniquement si le doctorant n'est ni enseignant ni étudiant existant dans l'établissement. Le champs ne sera pas mis à jour si c'est le cas, il ne sera pas nécessaire de le renseigner sauf si c'est un nouveau doctorant.")
            self.fields['Prenoms'] = forms.CharField(label="Prénom(s)", required=False, help_text="Uniquement si le doctorant n'est ni enseignant ni étudiant existants dans l'établissement. Le champs ne sera pas mis à jour si c'est le cas, il ne sera pas nécessaire de le renseigner sauf si c'est un nouveau doctorant.") 
            self.fields['NomA'] = forms.CharField(label="Nom (arabe)", required=False, help_text="Pour un enseignant et/ou étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder le champs déjà existant.")
            self.fields['PrenomsA'] = forms.CharField(label="Prénom(s) (arabe)", required=False, help_text="Pour un enseignant et/ou étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.") 
            self.fields['Genre'] = forms.ChoiceField(choices=SEXE, label="Genre", required=False, help_text="Pour un enseignant et/ou étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.") 
            self.fields['Ddn']=forms.DateField(label="Date de naissance", help_text="Pour un enseignant et/ou étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.", input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), required=False)
            self.fields['LieuNaissance'] = forms.CharField(label="Lieu de naissance", required=False, help_text="Pour un étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.") 
            self.fields['LieuNaissanceA'] = forms.CharField(label="Lieu de naissance (arabe)", required=False, help_text="Pour un étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.") 
            self.fields['WilayaNaissance'] = forms.ModelChoiceField(
                queryset=Wilaya.objects.all(),
                label=u"Wilaya de naissance",
                widget=ModelSelect2Widget(
                        model=Wilaya,
                        search_fields=['code__icontains', 'nom__icontains'],
                    ),
                help_text = "Pour un étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.",
                required = False
            )  
            self.fields['WilayaResidence'] = forms.ModelChoiceField(
                queryset=Wilaya.objects.all(),
                label=u"Wilaya de résidence",
                widget=ModelSelect2Widget(
                        model=Wilaya,
                        search_fields=['code__icontains', 'nom__icontains'],
                    ),
                help_text = "Pour un étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.",
                required = False
            )  
            self.fields['CommuneResidence'] = forms.ModelChoiceField(
                queryset=Commune.objects.all(),
                label=u"Commune de résidence",
                widget=ModelSelect2Widget(
                        model=Commune,
                        search_fields=['code_postal__icontains', 'nom__icontains'],
                    ),
                help_text = "Pour un étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.",
                required = False
            )  
            self.fields['AdressePrincipale'] = forms.CharField(label="Adresse principale", required=False, help_text="Pour un étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.") 
            self.fields['Telephone'] = forms.CharField(label="Tél", required=False, help_text="Pour un enseignant/étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.") 
            self.fields['Interne'] = forms.BooleanField(label="Interne à une cité universitaire", required=False, help_text="Pour un étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.")  
            self.fields['ResidenceU'] = forms.CharField(label="Résidence universitaire", required=False, help_text="Pour un étudiant existant, ce champs permettra la mise à jour. Laissez-le vide si vous voulez garder les champs déjà existants.")
            self.fields['Organisme'] = forms.ModelChoiceField(
                queryset=Organisme.objects.filter(interne=True),
                label=u"Organisme ",
                help_text="Organisme d'affiliation",
                required = False
            )
                   
            self.helper.add_input(Submit('submit','Créer',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire d'ajout du doctorant. Merci de le signaler à l'administrateur")
    
    def clean_Nom(self):
        nom_=self.cleaned_data['Nom']
        user_=self.cleaned_data['User']
        if not user_ and not nom_ :
            raise ValidationError("Vous n'avez pas choisi un utilisateur existant, vous devez renseigner un nom pour votre nouveau doctorant")
        return nom_
    
    def clean_Prenoms(self):
        prenoms_=self.cleaned_data['Prenoms']
        user_=self.cleaned_data['User']
        if not user_ and not prenoms_ :
            raise ValidationError("Vous n'avez pas choisi un utilisateur existant, vous devez renseigner le(s) prénom(s) pour votre nouveau doctorant")
        return prenoms_
            
        
    def clean_Email(self):
        email_ = self.cleaned_data['Email']
        if self.cleaned_data['User'] and email_:
            raise ValidationError("Vous ne pouvez pas changer l'adresse e-mail d'un utilisateur existant. Veuillez laisser ce champs vide.")            
        elif email_ :
            user_qs=User.objects.filter(username__iexact=email_)
            if user_qs.exists() :
                raise ValidationError("Un utilisateur existe déjà avec cette adresse e-mail")
        elif self.cleaned_data['User'] :
            pass
        else :
            raise ValidationError("Vous n'avez pas choisi un utilisateur existant, vous devez renseigner une nouvelle adresse e-mail pour votre nouveau doctorant")
        return email_
    
    def clean_MatriculeEtud(self):
        matricule_ = self.cleaned_data['MatriculeEtud']
        if (not self.cleaned_data['User']) and self.cleaned_data['Etudiant'] and (not matricule_) :
            raise ValidationError("Vous devez un renseigner un matricule pour ce nouvel utilisateur qui va devenir Etudiant")
        if (self.cleaned_data['User']) and (not self.cleaned_data['User'].is_etudiant()) and self.cleaned_data['Etudiant'] and (not matricule_) :
            raise ValidationError("Vous devez un renseigner un matricule pour cet utilisateur existant qui va devenir Etudiant")
                
        
            
        if matricule_ :
            etudiant_qs=Etudiant.objects.filter(matricule=matricule_)
            if etudiant_qs.exists() :
                raise ValidationError("Un étudiant existe déjà avec ce matricule")
        return matricule_



class DoctorantUpdateForm(forms.Form):
    
    def __init__(self, doctorant_pk, request, *args, **kwargs):
        super(DoctorantUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:  
            doctorant_= get_object_or_404(Doctorant, id=doctorant_pk)
            self.fields['Organisme'] = forms.ModelChoiceField(
                queryset=Organisme.objects.filter(interne=True),
                label=u"Organisme ",
                help_text="L'organisme d'affiliation",
                required = False,
                initial=doctorant_.organisme
            )
                   
            self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de modification du doctorant. Merci de le signaler à l'administrateur")
  


class TheseCreateForm(forms.Form):
    
    def __init__(self, request, *args, **kwargs):
        super(TheseCreateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
            annee_en_cours_qs=AnneeUniv.objects.filter(encours=True)
            annee_en_cours=None
            if annee_en_cours_qs.exists() :
                annee_en_cours=annee_en_cours_qs.first()
            self.fields['annee_univ']=forms.ModelChoiceField(
                queryset=AnneeUniv.objects.all().order_by('-annee_univ'),
                label=u"Année universitaire",
                required = False,
                initial=annee_en_cours
            )   
            self.fields['intitule']=forms.CharField(label="Intitulé de la thèse")
            self.fields['directeur'] = forms.ModelChoiceField(
                queryset=Enseignant.objects.all(),
                label=u"Directeur de thèse",
                widget=ModelSelect2Widget(
                        model=Enseignant,
                        search_fields=['nom__icontains', 'prenom__icontains'],
                    ),
                required = False
            ) 
            self.fields['codirecteur'] = forms.ModelChoiceField(
                queryset=Enseignant.objects.all(),
                label=u"Co-directeur de thèse",
                widget=ModelSelect2Widget(
                        model=Enseignant,
                        search_fields=['nom__icontains', 'prenom__icontains'],
                    ),
                required = False
            ) 
            self.fields['directeur_externe']=forms.CharField(label="Directeur externe", required=False)
            self.fields['codirecteur_externe']=forms.CharField(label="Co-directeur externe", required=False)                
            self.fields['resume']=forms.CharField(label="Résumé",  widget=forms.Textarea, required=False)
            self.fields['objectifs']=forms.CharField(label="Objectifs",  widget=forms.Textarea, required=False)
            self.fields['resultats_attendus']=forms.CharField(label="Résultats attendus",  widget=forms.Textarea, required=False)
            self.fields['antecedents']=forms.CharField(label="Antécédents", help_text="Renseignez les antécédents de ce sujet en termes de travaux, produits, phases réalisées, etc.", widget=forms.Textarea, required=False)
            self.fields['echeancier']=forms.CharField(label="Echeancier", help_text="Mettre les différentes étapes en indiquant la durée pour chaque étape", widget=forms.Textarea, required=False)
            self.fields['bibliographie']=forms.CharField(label="Bibliographie",  widget=forms.Textarea, required=False)
            self.fields['projet']=forms.ModelChoiceField(
                queryset=Projet.objects.all(),
                label=u"Projet de recherche (interne)",
                widget=ModelSelect2Widget(
                        model=Projet,
                        search_fields=['intitule__icontains',],
                    ),
                required = False,
            )     
            self.fields['doctorant']=forms.ModelChoiceField(
                # construire la liste des stagiaires potentiels n'ayant pas encore réservé un PFE
                queryset = Doctorant.objects.filter(these__isnull=True),
                widget=ModelSelect2Widget(
                    model=Doctorant,
                    search_fields=['enseignant__nom__icontains', 'etudiant__nom__icontains','enseignant__prenom__icontains', 'etudiant__prenom__icontains'],
                ),
                required=False,
                help_text = "Choisissez le doctorant auquel la thèse est affectée",
            )
            if not request.user.has_perm('scolar.fonctionnalitenav_postgraduation_gestionsujets') :
                self.fields['doctorant'].disabled=True        
                self.fields['statut_validation'] = forms.ChoiceField(choices=STATUT_VALIDATION, label="Statut de validation initial", required=True, initial='C')
                self.fields['statut_validation'].disabled=True
                if request.user.is_enseignant() :
                    self.fields['directeur'].initial=request.user.enseignant
            else :  
                self.fields['statut_validation'] = forms.ChoiceField(choices=STATUT_VALIDATION, label="Statut de validation initial", required=True, initial='S')        
            
            self.helper.add_input(Submit('submit','Déposer',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire d'ajout du sujet de thèse. Merci de le signaler à l'administrateur")    
    
    def clean_codirecteur(self):
        directeur_ = self.cleaned_data['directeur']
        codirecteur_=self.cleaned_data['codirecteur']
        if directeur_ and codirecteur_:
            if directeur_==codirecteur_ :
                raise ValidationError("Le directeur et le codirecteur de thèse doivent être différents.")
        return codirecteur_  
    
class TheseUpdateForm(forms.Form):
    
    def __init__(self, these_pk, request, *args, **kwargs):
        super(TheseUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:  
            these_= get_object_or_404(These, id=these_pk)

            self.fields['annee_univ']=forms.ModelChoiceField(
                queryset=AnneeUniv.objects.all().order_by('-annee_univ'),
                label=u"Année universitaire",
                required = False,
                initial=these_.annee_univ
            )   
            self.fields['intitule']=forms.CharField(label="Intitulé de la thèse", initial=these_.sujet.intitule)
            self.fields['directeur'] = forms.ModelChoiceField(
                queryset=Enseignant.objects.all(),
                label=u"Directeur de thèse",
                widget=ModelSelect2Widget(
                        model=Enseignant,
                        search_fields=['nom__icontains', 'prenom__icontains'],
                    ),
                required = False,
                initial=these_.directeur
            ) 
            self.fields['directeur_externe']=forms.CharField(label="Directeur externe (cordonnées, institution, ..)", required=False, initial=these_.directeur_externe)   

            self.fields['codirecteur'] = forms.ModelChoiceField(
                queryset=Enseignant.objects.all(),
                label=u"Co-directeur de thèse",
                widget=ModelSelect2Widget(
                        model=Enseignant,
                        search_fields=['nom__icontains', 'prenom__icontains'],
                    ),
                required = False,
                initial=these_.codirecteur
            ) 
            self.fields['codirecteur_externe']=forms.CharField(label="Co-directeur externe (cordonnées, institution, ..)", required=False, initial=these_.codirecteur_externe)                
            self.fields['resume']=forms.CharField(label="Résumé",  widget=forms.Textarea, required=False, initial=these_.sujet.resume)
            self.fields['objectifs']=forms.CharField(label="Objectifs",  widget=forms.Textarea, required=False, initial=these_.sujet.objectifs)
            self.fields['resultats_attendus']=forms.CharField(label="Résultats attendus",  widget=forms.Textarea, required=False, initial=these_.sujet.resultats_attendus)
            self.fields['antecedents']=forms.CharField(label="Antécédents", help_text="Renseignez les antécédents de ce sujet en termes de travaux, produits, phases réalisées, etc.", widget=forms.Textarea, required=False, initial=these_.sujet.antecedents)
            self.fields['echeancier']=forms.CharField(label="Echeancier", help_text="Mettre les différentes étapes en indiquant la durée pour chaque étape", widget=forms.Textarea, required=False, initial=these_.sujet.echeancier)
            self.fields['bibliographie']=forms.CharField(label="Bibliographie",  widget=forms.Textarea, required=False, initial=these_.sujet.bibliographie)
            
            self.fields['reponse_aux_experts']=forms.CharField(label="Réponse aux experts", widget=forms.Textarea, required=False, initial=these_.sujet.reponse_aux_experts)
            if these_.sujet.statut_validation!="RR" :
                self.fields['reponse_aux_experts'].disabled=True   
            self.fields['projet']=forms.ModelChoiceField(
                queryset=Projet.objects.all(),
                label=u"Projet de recherche (interne)",
                widget=ModelSelect2Widget(
                        model=Projet,
                        search_fields=['intitule__icontains',],
                    ),
                required = False,
                initial=these_.projet
            )     
                
            self.fields['doctorant']=forms.ModelChoiceField(
                queryset = Doctorant.objects.filter(Q(these__isnull=True)|(Q(these__doctorant=these_.doctorant))),
                widget=ModelSelect2Widget(
                    model=Doctorant,
                    search_fields=['enseignant__nom__icontains', 'etudiant__nom__icontains','enseignant__prenom__icontains', 'etudiant__prenom__icontains'],
                ),
                required=False,
                help_text = "Choisissez le doctorant auquel la thèse est affectée",
                initial=these_.doctorant
            )
            
            if request.user.has_perm('scolar.fonctionnalitenav_postgraduation_gestionsujets') :    
                self.fields['statut_validation'] = forms.ChoiceField(choices=STATUT_VALIDATION, label="Statut de validation", required=True, initial=these_.sujet.statut_validation)                    
            elif these_.sujet.statut_validation=="RR" : #enseignant directeur ou co-directeur, pour révision (condition dans test_func de la view qui appelle ce formulaire)
                self.fields['statut_validation'] = forms.ChoiceField(choices=(('RT','Révision Terminée'),('RR','Révision Requise')), label="Statut de validation", required=True, initial=these_.sujet.statut_validation)
                self.fields['doctorant'].disabled=True
            else :
                self.fields['statut_validation'] = forms.ChoiceField(choices=STATUT_VALIDATION, label="Statut de validation", required=True, initial=these_.sujet.statut_validation)
                self.fields['statut_validation'].disabled=True
                self.fields['doctorant'].disabled=True
            self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de modification du doctorant. Merci de le signaler à l'administrateur")
  
    def clean_codirecteur(self):
        directeur_ = self.cleaned_data['directeur']
        codirecteur_=self.cleaned_data['codirecteur']
        if directeur_ and codirecteur_:
            if directeur_==codirecteur_ :
                raise ValidationError("Le directeur et le codirecteur de thèse doivent être différents.")
        return codirecteur_  

class TheseDetailForm(forms.Form):

    def __init__(self, these_pk, *args, **kwargs):
        super(TheseDetailForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try : 
            these_= get_object_or_404(These, id=these_pk)
            self.fields['annee_univ']=forms.ModelChoiceField(
                queryset=AnneeUniv.objects.all().order_by('-annee_univ'),
                label=u"Année universitaire",
                required = False,
                initial=these_.annee_univ
            )   
            self.fields['intitule']=forms.CharField(label="Intitulé de la thèse", initial=these_.sujet.intitule)
            self.fields['directeur'] = forms.ModelChoiceField(
                queryset=Enseignant.objects.filter(directions__in=[these_]),
                label=u"Directeur de thèse",
                widget=ModelSelect2Widget(
                        model=Enseignant,
                        search_fields=['nom__icontains', 'prenom__icontains'],
                    ),
                required = False,
                initial=these_.directeur
            ) 
            self.fields['directeur_externe']=forms.CharField(label="Directeur externe (cordonnées, institution, ..)", required=False, initial=these_.directeur_externe) 
            self.fields['codirecteur'] = forms.ModelChoiceField(
                queryset=Enseignant.objects.filter(codirections__in=[these_]),
                label=u"Co-directeur de thèse",
                widget=ModelSelect2Widget(
                        model=Enseignant,
                        search_fields=['nom__icontains', 'prenom__icontains'],
                    ),
                required = False,
                initial=these_.codirecteur
            )     
            self.fields['codirecteur_externe']=forms.CharField(label="Co-directeur externe (cordonnées, institution, ..)", required=False, initial=these_.codirecteur_externe)             
            self.fields['resume']=forms.CharField(label="Résumé",  widget=forms.Textarea, required=False, initial=these_.sujet.resume)
            self.fields['objectifs']=forms.CharField(label="Objectifs",  widget=forms.Textarea, required=False, initial=these_.sujet.objectifs)
            self.fields['resultats_attendus']=forms.CharField(label="Résultats attendus",  widget=forms.Textarea, required=False, initial=these_.sujet.resultats_attendus)
            self.fields['antecedents']=forms.CharField(label="Antécédents", help_text="Antécédents de ce sujet en termes de travaux, produits, phases réalisées, etc.", widget=forms.Textarea, required=False, initial=these_.sujet.antecedents)
            self.fields['echeancier']=forms.CharField(label="Echeancier", help_text="Les différentes étapes en indiquant la durée pour chaque étape", widget=forms.Textarea, required=False, initial=these_.sujet.echeancier)
            self.fields['bibliographie']=forms.CharField(label="Bibliographie",  widget=forms.Textarea, required=False, initial=these_.sujet.bibliographie)
            self.fields['reponse_aux_experts']=forms.CharField(label="Réponse aux experts", widget=forms.Textarea, required=False, initial=these_.sujet.reponse_aux_experts)
            self.fields['doctorant']=forms.ModelChoiceField(
                queryset = Doctorant.objects.filter(these__doctorant__isnull=False, these__doctorant=these_.doctorant),
                widget=ModelSelect2Widget(
                    model=Doctorant,
                    search_fields=['enseignant__nom__icontains', 'etudiant__nom__icontains','enseignant__prenom__icontains', 'etudiant__prenom__icontains'],
                ),
                required=False,
                initial=these_.doctorant
            )
            self.fields['projet']=forms.ModelChoiceField(
                queryset=Projet.objects.filter(theses__in=[these_], theses__projet__isnull=False),
                label=u"Projet de recherche (interne)",
                widget=ModelSelect2Widget(
                        model=Projet,
                        search_fields=['intitule__icontains',],
                    ),
                required = False,
                initial=these_.projet
            )    
                
            self.fields['statut_validation'] = forms.ChoiceField(choices=STATUT_VALIDATION, label="Statut de validation", required=True, initial=these_.sujet.statut_validation)                            
            
    
            for key_ in self.fields.keys():
                self.fields[key_].disabled=True     
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction de la page de visualisation du sujet de thèse")

class ProjetDetailForm(forms.ModelForm):
    class Meta:
        model = Projet
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super(ProjetDetailForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        
        self.fields['chef']=forms.ModelChoiceField(
            queryset = Enseignant.objects.all().order_by('nom'),
            widget=ModelSelect2Widget(
                model=Enseignant,
                search_fields=['nom__icontains','prenom__icontains'],
            ),
            required=False,
            initial = self.instance.chef,
        ) 
        self.fields['membres']=forms.ModelMultipleChoiceField(
            queryset = Enseignant.objects.all().order_by('nom'),
            widget=ModelSelect2MultipleWidget(
                model=Enseignant,
                search_fields=['nom__icontains','prenom__icontains'],
            ),
            required=False,
            initial = self.instance.membres.all(),
        ) 
        self.fields['membres_doctorants']=forms.ModelMultipleChoiceField(
            queryset = Doctorant.objects.all(),
            widget=ModelSelect2MultipleWidget(
                model=Doctorant,
                search_fields=['enseignant__nom__icontains', 'etudiant__nom__icontains','enseignant__prenom__icontains', 'etudiant__prenom__icontains'],
            ),
            required=False,
            initial = self.instance.membres.all(),
        )
        self.fields['membres_externes'].widget=forms.Textarea(attrs={'rows':3})
        self.fields['description'].widget = forms.Textarea(attrs={'rows':20})
        
        for key_ in self.fields.keys():
            self.fields[key_].disabled=True  
        
        self.helper.add_input(Button('cancel', 'Retour', css_class='btn-secondary', onclick="window.history.back()"))

class EtatAvancementCreateForm(forms.Form):
    def __init__(self, inscription_pk, *args, **kwargs):
        super(EtatAvancementCreateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try :
            inscription_=get_object_or_404(Inscription, id=inscription_pk)
            self.fields['inscription']=forms.ModelChoiceField(
                queryset = Inscription.objects.filter(id=inscription_.id),
                required=True,
                initial = inscription_,
                disabled=True,
            ) 
            self.fields['jury']=forms.ModelMultipleChoiceField(
                queryset = Enseignant.objects.all().order_by('nom'),
                widget=ModelSelect2MultipleWidget(
                    model=Enseignant,
                    search_fields=['nom__icontains','prenom__icontains'],
                ),
                required=False,
            ) 
            self.helper.add_input(Submit('submit','Créer',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de création d'une évaluation d'état d'avancement")    
    
class EtatAvancementUpdateJuryForm(forms.Form):
    def __init__(self, inscription_pk, *args, **kwargs):
        super(EtatAvancementUpdateJuryForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try :
            inscription_=get_object_or_404(Inscription, id=inscription_pk)
            etat_avancement_=get_object_or_404(EtatAvancement, inscription=inscription_)
            self.fields['inscription']=forms.ModelChoiceField(
                queryset = Inscription.objects.filter(id=inscription_.id),
                required=True,
                initial = inscription_,
                disabled=True,
            ) 
            self.fields['jury']=forms.ModelMultipleChoiceField(
                queryset = Enseignant.objects.all().order_by('nom'),
                widget=ModelSelect2MultipleWidget(
                    model=Enseignant,
                    search_fields=['nom__icontains','prenom__icontains'],
                ),
                required=False,
                initial=etat_avancement_.jury.all(),
            ) 
            self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de modification du jury d'une évaluation d'état d'avancement")    

class EvaluationEtatAvancementForm(forms.Form):
    def __init__(self, pk, generation_pv, request, *args, **kwargs):
        super(EvaluationEtatAvancementForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try :
            etat_avancement_=get_object_or_404(EtatAvancement, id=pk)
            doctorant_=get_object_or_404(Doctorant, id=etat_avancement_.inscription.etudiant.doctorant.id)
            these_=get_object_or_404(These, id=doctorant_.these.id)
            
            permission_jury=False
            permission_jury=permission_jury | request.user.has_perm('scolar.fonctionnalite_postgraduation_gestionavancementdoctorants')
            permission_jury=(permission_jury | (request.user.is_enseignant() and (request.user.enseignant in etat_avancement_.jury.all())))
            
            inscription_qs=Inscription.objects.filter(id=etat_avancement_.inscription.id)
            inscription_=None
            if inscription_qs.exists() :
                inscription_=inscription_qs.first()
            self.fields['inscription']=forms.CharField(
                required=False,
                initial = str(inscription_),
                disabled=True & (not generation_pv),
            ) 
            self.fields['these']=forms.CharField(
                required=False,
                initial = str(these_),
                disabled=True & (not generation_pv) ,
                label="Thèse",
            )                                         
            
            self.fields['directeur']=forms.CharField(
                required=False,
                initial = str(these_.directeur) if these_.directeur else "/",
                disabled=True & (not generation_pv),
                label="Directeur de thèse",
            ) 
            annee_inscription=str(etat_avancement_.inscription)
                
            #self.fields["demande_inscription_annee"] = forms.CharField(max_length=100, required=False, disabled=True & (not generation_pv),
            #                                      label="Demande d'inscription en année : ", initial=str(annee_effective+1) if annee_effective < 5 else "5+")                
            
            if not generation_pv :
                self.fields['jury']=forms.ModelMultipleChoiceField(
                    queryset = Enseignant.objects.all().order_by('nom'),
                    widget=ModelSelect2MultipleWidget(
                        model=Enseignant,
                        search_fields=['nom__icontains','prenom__icontains'],
                    ),
                    required=False,
                    initial=etat_avancement_.jury.all(),
                    disabled=True & (not generation_pv),
                )
            else : 
                enseignant_list=""
                for enseignant_ in etat_avancement_.jury.all() :
                    enseignant_list= enseignant_list + str(enseignant_) +'\n'
                self.fields['jury']=forms.CharField(
                    widget=forms.Textarea(attrs={'rows':etat_avancement_.jury.all().count()+1}),
                    required=False,
                    initial=enseignant_list,
                    disabled=True & (not generation_pv),
                )
                
            
            criteres=Critere.objects.filter(programmes__in=[etat_avancement_.inscription.formation.programme]).order_by('ordre')
            
            for critere_ in criteres :
                evaluation_critere_qs=EvaluationCritere.objects.filter(etat_avancement=etat_avancement_, critere=critere_)
                evaluation_critere_=None
                if evaluation_critere_qs.exists() :
                    evaluation_critere_=evaluation_critere_qs.first()
                   
                for critere_option_ in critere_.options.all().order_by('ordre') :
                    self.fields["option_"+str(critere_.id)+"_"+str(critere_option_.id)]=forms.BooleanField(initial=True if evaluation_critere_ and (critere_option_ in evaluation_critere_.options.all()) else False, required = False, label=str(critere_option_.option), disabled=(not permission_jury) & (not generation_pv))
                if critere_.commentaire :
                    self.fields["commentaire_"+str(critere_.id)] = forms.CharField(max_length=1000, required=False,
                                                  label="Commentaires sur le point évalué", widget= forms.Textarea(attrs={'rows':4}), initial=evaluation_critere_.commentaire if evaluation_critere_ else None, disabled= (not permission_jury) & (not generation_pv))
            
            is_directeur= request.user.is_enseignant() and these_.directeur and request.user.enseignant == these_.directeur
            self.fields['avis_directeur']=forms.CharField(max_length=1000, required=False, widget= forms.Textarea(attrs={'rows':6}), disabled = (not is_directeur) & (not generation_pv),
                                                  label="Avis du directeur de thèse", initial=etat_avancement_.avis_directeur if etat_avancement_ else None)
            
            self.fields['decision_1']=forms.CharField(required=False, disabled = True & (not generation_pv),
                                                  label="Décision 1", initial=dict(DECISIONS_1).get(etat_avancement_.decision_labo) if (etat_avancement_  and etat_avancement_.decision_1) else '/')

            self.fields['decision_finale']=forms.CharField(required=False, disabled = True & (not generation_pv),
                                                  label="Décision finale", initial=dict(DECISIONS_FINALES).get(etat_avancement_.decision_finale) if (etat_avancement_  and etat_avancement_.decision_finale) else '/')

            self.fields['final']=forms.BooleanField(initial=True if etat_avancement_.final else False, required = False, label="Etablir le PV final : La modification de l'évaluation ne sera plus possible", disabled= (not permission_jury) & (not generation_pv))
            self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de modification de l'évaluation d'état d'avancement")    
    

class SeminaireCreateForm(forms.Form):  
    def __init__(self, *args, **kwargs):
        super(SeminaireCreateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try :
            annee_en_cours_qs=AnneeUniv.objects.filter(encours=True)
            annee_en_cours=None
            if annee_en_cours_qs.exists() :
                annee_en_cours=annee_en_cours_qs.first()
            self.fields['annee_univ']=forms.ModelChoiceField(
                queryset=AnneeUniv.objects.all().order_by('-annee_univ'),
                label=u"Annee universitaire",
                required = False,
                initial=annee_en_cours
            )
            self.fields['doctorants']= forms.ModelMultipleChoiceField(
                queryset=Inscription.objects.filter(formation__programme__doctorat=True),
                label=u"Doctorants inscrits",
                widget=ModelSelect2MultipleWidget(
                    model=Inscription,
                    search_fields=['etudiant__nom__icontains','etudiant__prenom__icontains'],
                ),
                help_text = "Tapez le nom ou prénom des doctorants inscrits ou deux espaces pour avoir la liste complète.",   
                required=False
            )
             
            self.fields['animateur_interne']= forms.ModelChoiceField(
                queryset=Enseignant.objects.all(),
                label=u"Enseignant animateur interne",
                widget=ModelSelect2Widget(
                    model=Enseignant,
                    search_fields=['nom__icontains','prenom__icontains'],
                ),
                help_text = "Tapez le nom ou prénom de l'enseignant ou deux espaces pour avoir la liste complète.",
                required = False
            )
            self.fields['animateur_externe']=forms.CharField(label="Enseignant Animateur externe", required = False)
            self.fields['date'] = forms.DateTimeField(input_formats = settings.DATE_INPUT_FORMATS, widget=DateTimePickerInput(format='%d/%m/%Y'), initial=datetime.date.today(), required=False) 
                        
            self.fields['matiere']= forms.ModelChoiceField(
                queryset=Matiere.objects.filter(seminaire=True),
                label=u"Matière séminaire existante",
                widget=ModelSelect2Widget(
                    model=Matiere,
                    search_fields=['code__icontains','titre__icontains'],
                ),
                help_text = "Tapez le nom ou le code de la matière (séminaire) existante pour l'associer à ce séminaire suivi, sinon créer une nouvelle matière séminaire via ce même formulaire sans renseigner ce champs.",
                required = False
            )
            self.fields['code']=forms.CharField(label="Code de la nouvelle matière séminaire à créer", required=False)
            self.fields['titre']=forms.CharField(label="Titre/Thème de la nouvelle matière séminaire à créer", required=False)
            self.fields['objectifs']=forms.CharField(label="Objectifs/Description de la nouvelle matière séminaire à créer", widget=forms.Textarea, required=False)
            self.fields['credit'] = forms.IntegerField(label="Crédits de la matière séminaire à créer", required=False, initial=0)
            self.helper.add_input(Submit('submit','Ajouter',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de création d'un séminaire suivi")    

class SeminaireUpdateForm(forms.Form):
    
    def __init__(self, seminaire_pk, request, *args, **kwargs):
        super(SeminaireUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:  
            seminaire_= get_object_or_404(SeminaireSuivi, id=seminaire_pk)

            self.fields['annee_univ']=forms.ModelChoiceField(
                queryset=AnneeUniv.objects.all().order_by('-annee_univ'),
                label=u"Année universitaire",
                required = False,
                initial=seminaire_.annee_univ
            )   
            self.fields['doctorants']=forms.ModelMultipleChoiceField(
                queryset = Inscription.objects.filter(formation__programme__doctorat=True),
                widget=ModelSelect2MultipleWidget(
                    model=Inscription,
                    search_fields=['etudiant__nom__icontains','etudiant__prenom__icontains'],
                ),
                required=False,
                initial=seminaire_.inscriptions.all()
            )
            self.fields['animateur_interne'] = forms.ModelChoiceField(
                queryset=Enseignant.objects.all(),
                label=u"Animateur interne",
                widget=ModelSelect2Widget(
                        model=Enseignant,
                        search_fields=['nom__icontains', 'prenom__icontains'],
                    ),
                required = False,
                initial=seminaire_.animateur_interne
            ) 
            self.fields['animateur_externe']=forms.CharField(label="Animateur externe", required=False, initial=seminaire_.animateur_externe)                
            self.fields['date']=forms.DateField(label="Date", required=False,input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), initial=seminaire_.date)
            self.fields['matiere']= forms.ModelChoiceField(
                queryset=Matiere.objects.filter(seminaire=True),
                label=u"Matière séminaire existante",
                widget=ModelSelect2Widget(
                    model=Matiere,
                    search_fields=['code__icontains','titre__icontains'],
                ),
                help_text = "Matière séminaire (La modification de la matière séminaire entraine la modification du titre, description et crédits pour ce séminaire suivi et ce en fonction de la matière séminaire choisie)",
                required = False,
                initial=seminaire_.matiere
            )
            '''
            self.fields['titre']=forms.CharField(label="Titre/Thème", initial=seminaire_.matiere.titre, disabled=True)
            self.fields['objectifs']=forms.CharField(label="Objectifs/Description",  widget=forms.Textarea, required=False, initial=seminaire_.matiere.objectifs, disabled=True)
            self.fields['credit']=forms.IntegerField(label="Crédits", required=False, initial=seminaire_.matiere.credit, disabled=True)
            '''
            self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de modification du doctorant. Merci de le signaler à l'administrateur")
  

class SeminaireDetailForm(forms.Form):

    def __init__(self, seminaire_pk, *args, **kwargs):
        super(SeminaireDetailForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try : 
            seminaire_= get_object_or_404(SeminaireSuivi, id=seminaire_pk)
            self.fields['annee_univ']=forms.ModelChoiceField(
                queryset=AnneeUniv.objects.all().order_by('-annee_univ'),
                label=u"Année universitaire",
                required = False,
                initial=seminaire_.annee_univ
            )   
            self.fields['titre']=forms.CharField(label="Thème/Titre", widget=forms.Textarea, required=False, initial=seminaire_.matiere.titre)
            self.fields['doctorants']=forms.ModelMultipleChoiceField(
                # construire la liste des stagiaires potentiels n'ayant pas encore réservé un PFE
                queryset = seminaire_.inscriptions.all(),
                widget=ModelSelect2MultipleWidget(
                    model=Inscription,
                    search_fields=['etudiant__nom__icontains', 'etudiant__prenom__icontains'],
                ),
                required=False,
                initial=seminaire_.inscriptions.all()
                
             )
            self.fields['animateur_interne']=forms.ModelChoiceField(
                queryset = Enseignant.objects.all(),
                widget=ModelSelect2Widget(
                    model=Enseignant,
                    search_fields=['nom__icontains', 'prenom__icontains'],
                ),
                required=False,
                initial=seminaire_.animateur_interne
                 
             )
            self.fields['animateur_externe']=forms.CharField(label="Animateur externe", required=False, initial=seminaire_.animateur_externe)
            self.fields['date']=forms.DateField(label="Date", required=False, initial=seminaire_.date)

            self.fields['objectifs']=forms.CharField(label="Objectifs/Description", widget=forms.Textarea, required=False, initial=seminaire_.matiere.objectifs)
            self.fields['credit']=forms.IntegerField(label="Crédits", required=False, initial=seminaire_.matiere.credit)
            for key_ in self.fields.keys():
                self.fields[key_].disabled=True
                            
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction de la page de visualisation du seminaire")

class DocumentsConfigUpdateForm(forms.Form):
    def __init__(self, documents_config_table, request, *args, **kwargs):
        super(DocumentsConfigUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
            for type, documents_config in documents_config_table.items() :
                for document_config in documents_config :
                    key_=str(document_config.id)
                    self.fields[key_+'_actif']=forms.BooleanField()
                    self.fields[key_+'_actif'].initial=document_config.actif
                    self.fields[key_+'_actif'].label=''
                    self.fields[key_+'_actif'].required=False
                    
                    self.fields[key_+'_autorite']=forms.ModelChoiceField(
                            queryset=Autorite.objects.all().order_by('intitule'),
                            label=u"Autorité",
                            required = False,
                            initial=document_config.autorite,
                            )
                    self.fields[key_+'_autorite_entete']=forms.ModelChoiceField(
                            queryset=Autorite.objects.all().order_by('intitule'),
                            label=u"Autorité d'entête",
                            required = False,
                            initial=document_config.autorite_entete,
                            )
                    
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de la configuration des documents. Merci de le signaler à l'administrateur")


class DetteUpdateForm(forms.Form):
    
    def __init__(self, pk, request, *args, **kwargs):
        super(DetteUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
            resultat_=get_object_or_404(Resultat, id=int(pk))

            self.fields['etat_dette'] = forms.ChoiceField(
                    choices=STATUT_DETTE,
                    label=u"Etat Dette",
                    required = True,
                    initial=resultat_.etat_dette
                    )
            
            self.fields['nouveau_module'] = forms.ModelChoiceField(
                queryset=Module.objects.filter(matiere=resultat_.module.matiere).order_by('-formation__annee_univ__annee_univ'),
                label=u"Module suivi en cours",
                widget=ModelSelect2Widget(
                        model=Module,
                        search_fields=['matiere__code__icontains', 'matiere__titre__icontains'],
                    ),
                help_text = "Choisir le nouveau module en cours suivi.",
                initial = resultat_.resultat_en_cours.module if resultat_.resultat_en_cours else None,
                required = False
            )
            self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de modification du rôle. Merci de le signaler à l'administrateur")

class UserCreateForm(forms.Form):
    
    def __init__(self, request, *args, **kwargs):
        super(UserCreateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
            self.fields['username'] = forms.CharField(label="Identifiant d'utilisateur", required=True)
            self.fields['first_name'] = forms.CharField(label="Prénom(s)", required=False)
            self.fields['last_name'] = forms.CharField(label="Nom", required=False)
            self.fields['email'] = forms.EmailField(required=False)
            self.fields['password'] = forms.CharField(label="Nouveau mot de passe", required=True, widget=forms.PasswordInput() )
            
            self.helper.add_input(Submit('submit','Créer',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de modification de l'utilisateur. Merci de le signaler à l'administrateur")

    def clean_email(self):
        email_ = self.cleaned_data['email']
        if email_ :
            qs = User.objects.filter(email__iexact=email_)
            if qs.exists() :
                raise ValidationError("Un utilisateur est déjà enregistré avec cette adresse e-mail")

        return email_ if email_ else None
    
    def clean_username(self):
        username_ = self.cleaned_data['username']
        
        if username_ :
            qs = User.objects.filter(username__iexact=username_)
            if qs.exists() :
                raise ValidationError("Ce nom d'utilisateur existe déjà")
        else :
            raise ValidationError("Le nom d'utilisateur est obligatoire")

        return username_
            
class UserUpdateForm(forms.Form):
    
    def __init__(self, pk, request, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        try:
            user_=get_object_or_404(User, id=pk)
            self.user = user_
            self.fields['username'] = forms.CharField(initial=user_.username, label="Identifiant d'utilisateur", required=True)
            self.fields['first_name'] = forms.CharField(initial=user_.first_name, label="Prénom(s)", required=False)
            self.fields['last_name'] = forms.CharField(initial=user_.last_name, label="Nom", required=False)
            self.fields['email'] = forms.EmailField(required=False, initial=user_.email)
            self.fields['password'] = forms.CharField(label="Nouveau de mot de passe", required=False, widget=forms.PasswordInput() )
            
            self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
            self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
            self.helper.form_method='POST'
        except Exception:
            if settings.DEBUG:
                raise Exception
            else:
                messages.error(self.request, "ERREUR: lors de la construction du formulaire de modification de l'utilisateur. Merci de le signaler à l'administrateur")

    def clean_email(self):
        email_ = self.cleaned_data['email']
        
        if email_ :
            qs = User.objects.filter(email__iexact=email_)
            if qs.exists() and (qs.first().id != self.user.id) :
                raise ValidationError("Un utilisateur est déjà enregistré avec cette adresse e-mail")

        return email_ if email_ else None
    
    def clean_username(self):
        username_ = self.cleaned_data['username']
        
        if username_ :
            qs = User.objects.filter(username__iexact=username_)
            if qs.exists() and (qs.first().id != self.user.id) :
                raise ValidationError("Ce nom d'utilisateur existe déjà")
        else :
            raise ValidationError("Le nom d'utilisateur est obligatoire")

        return username_ 


class PasswordUpdateForm(forms.Form):
    password = forms.CharField(label="Nouveau mot de passe", required=True, widget=forms.PasswordInput() )
    
    def __init__(self, user, request, *args, **kwargs):
        super(PasswordUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.user = user
        self.helper.add_input(Submit('submit','Modifier le mot de passe',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'
        
        
    def clean_password(self):
        password_ = self.cleaned_data['password']
        try:
            password_validation.validate_password(password_, self.user)
        except forms.ValidationError as error:
            raise error
        return password_
    

class EtudiantMatriculeUpdateForm(forms.Form):
    matricule = forms.RegexField(regex=settings.REGEX_MATRICULE, label="Nouveau matricule", required=True)
    
    def __init__(self, request, *args, **kwargs):
        super(EtudiantMatriculeUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.helper.add_input(Submit('submit','Modifier',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'


class EnregistrementEtudiantCreateForm(forms.ModelForm):
    class Meta:
        model = EnregistrementEtudiant
        fields = ['email', 'nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance', 'wilaya_naissance', 'wilaya_residence', 'commune_residence', 'interne', 'residence_univ', 'addresse_principale','programme', 'nom_a', 'prenom_a', 'lieu_naissance_a', 'photo', 'tel', 'numero_securite_sociale']

    def __init__(self, *args, **kwargs):
        super(EnregistrementEtudiantCreateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['prenom'].label="Prénom(s)"
        self.fields['password'] = forms.CharField(label="Nouveau mot de passe", required=True, widget=forms.PasswordInput() )
        self.fields['sexe'].required=True
        self.fields['date_naissance']=forms.DateField(input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'), label="Date de naissance")
        self.fields['lieu_naissance'].required=True
        self.fields['wilaya_naissance'] = forms.ModelChoiceField(
            queryset=Wilaya.objects.all(),
            label=u"Wilaya de naissance",
            widget=ModelSelect2Widget(
                    model=Wilaya,
                    search_fields=['code__icontains', 'nom__icontains'],
                ),
            help_text = "Sélectionnez un élément en faisant une recherche. Tapez 2 espaces pour avoir la liste complète. Pour l'étranger, choisissez le code 99.",
            required = True
        )  
        self.fields['wilaya_residence'] = forms.ModelChoiceField(
            queryset=Wilaya.objects.all(),
            label=u"Wilaya de résidence",
            widget=ModelSelect2Widget(
                    model=Wilaya,
                    search_fields=['code__icontains', 'nom__icontains'],
                ),
            help_text = "Sélectionnez un élément en faisant une recherche. Tapez 2 espaces pour avoir la liste complète.",
            required = True
        )  
        self.fields['commune_residence'] = forms.ModelChoiceField(
            queryset=Commune.objects.all(),
            label=u"Commune de résidence",
            widget=ModelSelect2Widget(
                    model=Commune,
                    search_fields=['code_postal__icontains', 'nom__icontains'],
                ),
            help_text = "Sélectionnez un élément en faisant une recherche. Tapez 2 espaces pour avoir la liste complète.",
            required = True
        )
        self.fields['residence_univ'].widget = forms.Textarea(attrs={'rows':1})
        self.fields['addresse_principale'].widget = forms.Textarea(attrs={'rows':1})
        self.fields['addresse_principale'].required=True
        self.fields['programme'].queryset=Programme.objects.filter(fictif=False).order_by('diplome', 'ordre')
        self.fields['programme'].label_from_instance=self.label_from_instance
        self.fields['nom_a'].required=True
        self.fields['prenom_a'].required=True
        self.fields['lieu_naissance_a'].required=True
        self.fields['numero_securite_sociale'].label="Numéro de sécurité sociale"
        self.fields['captcha'] = ReCaptchaField()
        self.helper.add_input(Submit('submit','S\'enregistrer',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'
        
    @staticmethod
    def label_from_instance(self):
        return str(self.code) + " - "+self.titre
    
    def clean_email(self):
        email_ = self.cleaned_data['email']
        user_qs=User.objects.filter(username__iexact=email_)
        if user_qs.exists() :
            raise ValidationError("Un utilisateur existe déjà avec cette adresse e-mail")
        return email_
    
    def clean_password(self):
        password_ = self.cleaned_data['password']
        try:
            password_validation.validate_password(password_)
        except forms.ValidationError as error:
            raise error
        return password_


class EnregistrementEtudiantUpdateForm(forms.Form):

    def __init__(self, enregistrement, etudiant, *args, **kwargs):
        super(EnregistrementEtudiantUpdateForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()

        champs_a_comparer=['nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance', 'wilaya_naissance', 'wilaya_residence', 'commune_residence', 'interne', 'residence_univ', 'addresse_principale', 'nom_a', 'prenom_a', 'lieu_naissance_a', 'tel', 'numero_securite_sociale']    
        if etudiant :
            self.fields['etudiant']= forms.ModelChoiceField(
                    queryset=Etudiant.objects.filter(matricule=etudiant.matricule),
                    required = False,
                    initial=etudiant,
                    widget=forms.HiddenInput())
        
        self.fields['nom'] = forms.CharField(disabled=True, required=False, initial=etudiant.nom if etudiant else '', label="Ancien nom")
        self.fields['new_nom'] = forms.CharField(required=False, initial=enregistrement.nom, label="Nouveau nom")
        self.fields['choosenew_nom'] = forms.BooleanField(initial=True if enregistrement.nom else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['prenom'] = forms.CharField(disabled=True, required=False, initial=etudiant.prenom if etudiant else '', label="Ancien(s) prénom(s)")
        self.fields['new_prenom'] = forms.CharField(required=False, initial=enregistrement.prenom, label="Nouveau(x) prénom(s)")
        self.fields['choosenew_prenom'] = forms.BooleanField(initial=True if enregistrement.prenom else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)        

        self.fields['sexe'] = forms.ChoiceField(disabled=True, required=False, initial=etudiant.sexe if etudiant else '', choices=SEXE, label="Ancien sexe") 
        self.fields['new_sexe'] = forms.ChoiceField(initial=enregistrement.sexe, choices=SEXE, label="Nouveau sexe", required=False) 
        self.fields['choosenew_sexe'] = forms.BooleanField(initial=True if enregistrement.sexe else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['nom_a'] = forms.CharField(disabled=True, required=False, initial=etudiant.nom_a if etudiant else '', label="Ancien nom en arabe")
        self.fields['new_nom_a'] = forms.CharField(required=False, initial=enregistrement.nom_a, label="Nouveau nom en arabe")
        self.fields['choosenew_nom_a'] = forms.BooleanField(initial=True if enregistrement.nom_a else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['prenom_a'] = forms.CharField(disabled=True, required=False, initial=etudiant.prenom_a if etudiant else '', label="Ancien(s) prénom(s) en arabe")
        self.fields['new_prenom_a'] = forms.CharField(required=False, initial=enregistrement.prenom_a, label="Nouveau(x) prénom(s) en arabe")
        self.fields['choosenew_prenom_a'] = forms.BooleanField(initial=True if enregistrement.prenom_a else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)        

        self.fields['date_naissance']=forms.DateField(disabled=True, required=False, initial=etudiant.date_naissance if etudiant else None, label="Ancienne date de naissance", input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'))
        self.fields['new_date_naissance']=forms.DateField(required=False, initial=enregistrement.date_naissance, label="Nouvelle date de naissance", input_formats = settings.DATE_INPUT_FORMATS, widget=DatePickerInput(format='%d/%m/%Y'))
        self.fields['choosenew_date_naissance'] = forms.BooleanField(initial=True if enregistrement.date_naissance else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['lieu_naissance'] = forms.CharField(disabled=True, required=False, initial=etudiant.lieu_naissance if etudiant else '', label="Ancien lieu de naissance")
        self.fields['new_lieu_naissance'] = forms.CharField(required=False, initial=enregistrement.lieu_naissance, label="Nouveau lieu de naissance")
        self.fields['choosenew_lieu_naissance'] = forms.BooleanField(initial=True if enregistrement.lieu_naissance else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['lieu_naissance_a'] = forms.CharField(disabled=True, required=False, initial=etudiant.lieu_naissance_a if etudiant else '', label="Ancien lieu de naissance en arabe")
        self.fields['new_lieu_naissance_a'] = forms.CharField(required=False, initial=enregistrement.lieu_naissance_a, label="Nouveau lieu de naissance en arabe")
        self.fields['choosenew_lieu_naissance_a'] = forms.BooleanField(initial=True if enregistrement.lieu_naissance_a else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)
                 
        self.fields['wilaya_naissance'] = forms.ModelChoiceField(
            queryset=Wilaya.objects.all(),
            label=u"Ancienne wilaya de naissance",
            widget=ModelSelect2Widget(
                    model=Wilaya,
                    search_fields=['code__icontains', 'nom__icontains'],
                ),
            required = False,
            initial=etudiant.wilaya_naissance if etudiant else None,
            disabled=True,
        )

        self.fields['new_wilaya_naissance'] = forms.ModelChoiceField(
            queryset=Wilaya.objects.all(),
            label=u"Nouvelle wilaya de naissance",
            widget=ModelSelect2Widget(
                    model=Wilaya,
                    search_fields=['code__icontains', 'nom__icontains'],
                ),
            required = False,
            initial=enregistrement.wilaya_naissance,
        )

        self.fields['choosenew_wilaya_naissance'] = forms.BooleanField(initial=True if enregistrement.wilaya_naissance else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['wilaya_residence'] = forms.ModelChoiceField(
            queryset=Wilaya.objects.all(),
            label=u"Ancienne wilaya de résidence",
            widget=ModelSelect2Widget(
                    model=Wilaya,
                    search_fields=['code__icontains', 'nom__icontains'],
                ),
            required = False,
            initial=etudiant.wilaya_residence if etudiant else None,
            disabled=True,
        )

        self.fields['new_wilaya_residence'] = forms.ModelChoiceField(
            queryset=Wilaya.objects.all(),
            label=u"Nouvelle wilaya de résidence",
            widget=ModelSelect2Widget(
                    model=Wilaya,
                    search_fields=['code__icontains', 'nom__icontains'],
                ),
            required = False,
            initial=enregistrement.wilaya_residence,
        )

        self.fields['choosenew_wilaya_residence'] = forms.BooleanField(initial=True if enregistrement.wilaya_residence else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['commune_residence'] = forms.ModelChoiceField(
            queryset=Commune.objects.all(),
            label=u"Ancienne commune de résidence",
            widget=ModelSelect2Widget(
                    model=Commune,
                    search_fields=['code_postal__icontains', 'nom__icontains'],
                ),
            required = False,
            initial=etudiant.commune_residence if etudiant else None,
            disabled=True,
        )

        self.fields['new_commune_residence'] = forms.ModelChoiceField(
            queryset=Commune.objects.all(),
            label=u"Nouvelle commune de résidence",
            widget=ModelSelect2Widget(
                    model=Commune,
                    search_fields=['code_postal__icontains', 'nom__icontains'],
                ),
            required = False,
            initial=enregistrement.commune_residence,
        )
        self.fields['choosenew_commune_residence'] = forms.BooleanField(initial=True if enregistrement.commune_residence else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)
        
        self.fields['addresse_principale'] = forms.CharField(disabled=True, required=False, initial=etudiant.addresse_principale if etudiant else '', label="Ancienne adresse")
        self.fields['new_addresse_principale'] = forms.CharField(required=False, initial=enregistrement.addresse_principale, label="Nouvelle adresse")
        self.fields['choosenew_addresse_principale'] = forms.BooleanField(initial=True if enregistrement.addresse_principale else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['interne'] = forms.BooleanField(disabled=True, initial=etudiant.interne if etudiant else '', label="Interne (ancienne valeur)", required=False)
        self.fields['new_interne'] = forms.BooleanField(initial=enregistrement.interne, label="Interne (nouvelle valeur)", required=False)
        self.fields['choosenew_interne'] = forms.BooleanField(initial=True if enregistrement.interne else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)
        
        self.fields['residence_univ'] = forms.CharField(disabled=True, required=False, initial=etudiant.residence_univ if etudiant else '', label="Ancienne résidence universitaire")
        self.fields['new_residence_univ'] = forms.CharField(required=False, initial=enregistrement.residence_univ, label="Nouvelle résidence universitaire")
        self.fields['choosenew_residence_univ'] = forms.BooleanField(initial=True if enregistrement.residence_univ else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['tel'] = forms.CharField(disabled=True, required=False, initial=etudiant.tel if etudiant else '', label="Ancien tel")
        self.fields['new_tel'] = forms.CharField(required=False, initial=enregistrement.tel, label="Nouveau tel")
        self.fields['choosenew_tel'] = forms.BooleanField(initial=True if enregistrement.tel else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)

        self.fields['numero_securite_sociale'] = forms.CharField(disabled=True, required=False, initial=etudiant.numero_securite_sociale if etudiant else '', label="Ancien numéro de sécurité sociale")
        self.fields['new_numero_securite_sociale'] = forms.CharField(required=False, initial=enregistrement.numero_securite_sociale, label="Nouveau numéro de sécurité sociale")
        self.fields['choosenew_numero_securite_sociale'] = forms.BooleanField(initial=True if enregistrement.numero_securite_sociale else False, label='Considérer la nouvelle valeur', help_text='La considération de la nouvelle valeur mettra à jour le profil de l\'étudiant', required = False)        
        
        if (enregistrement and enregistrement.statut=="W") :
            if etudiant :
                self.helper.add_input(Submit('submit','Valider',css_class='btn-success'))
            self.helper.add_input(Submit('submit_rejet','Rejeter',css_class='btn-danger'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'
        

class SelectionEtudiantForm(forms.Form):
    def __init__(self, etudiant, *args, **kwargs):
        super(SelectionEtudiantForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['etudiant_choisi'] = forms.ModelChoiceField(
                queryset=Etudiant.objects.all().order_by('nom', 'prenom'),
                label=u"Étudiant existant",
                widget = ModelSelect2Widget(
                        model=Etudiant,
                        search_fields=['matricule__icontains', 'nom__icontains', 'prenom__icontains'],
                    ),
                required = True,
                help_text = "Recherchez l'étudiant correspondant puis appuyez sur 'Comparer' pour lancer la comparaison entre les informations existantes et les informations nouvelles issues de la demande d'enregistrement. La recherche peut se faire par matricule, nom ou prénom.",)
        self.fields['etudiant_choisi'].initial=etudiant
        self.helper.add_input(Submit('submit_selection_etudiant','Comparer',css_class='btn-warning'))
        self.helper.form_method='POST'

class EquipeRechercheDetailForm(forms.ModelForm):
    class Meta:
        model = EquipeRecherche
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super(EquipeRechercheDetailForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        
        self.fields['responsable']=forms.ModelChoiceField(
            queryset = Enseignant.objects.all().order_by('nom'),
            widget=ModelSelect2Widget(
                model=Enseignant,
                search_fields=['nom__icontains','prenom__icontains'],
            ),
            required=False,
            initial = self.instance.responsable,
        ) 
        self.fields['membres']=forms.ModelMultipleChoiceField(
            queryset = Enseignant.objects.all().order_by('nom'),
            widget=ModelSelect2MultipleWidget(
                model=Enseignant,
                search_fields=['nom__icontains','prenom__icontains'],
            ),
            required=False,
            initial = self.instance.membres.all(),
        ) 
        self.fields['membres_doctorants']=forms.ModelMultipleChoiceField(
            queryset = Doctorant.objects.all(),
            widget=ModelSelect2MultipleWidget(
                model=Doctorant,
                search_fields=['enseignant__nom__icontains', 'etudiant__nom__icontains','enseignant__prenom__icontains', 'etudiant__prenom__icontains'],
            ),
            required=False,       
        )
        self.fields['membres_externes'].widget=forms.Textarea(attrs={'rows':3})
        
        self.fields['description'].widget = forms.Textarea(attrs={'rows':20})
        
        for key_ in self.fields.keys():
            self.fields[key_].disabled=True 
        self.helper.add_input(Button('cancel', 'Retour', css_class='btn-secondary', onclick="window.history.back()"))


class SelectOrCreateOrganismeOffreForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(SelectOrCreateOrganismeOffreForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['organisme']= forms.ModelChoiceField(
                queryset=Organisme.objects.all().order_by('sigle', 'nom'),
                label="Organisme",
                widget=ModelSelect2Widget(
                        model=Organisme,
                        search_fields=['sigle__icontains', 'nom__icontains']
                    ),
                help_text = "Tapez le sigle ou nom de l'organisme pour le sélectionner. S'il n'apparaît pas, merci de cliquer sur le bouton Nouveau. La sélection d'un organisme est facultative.",
                required = False
            )
        self.helper.add_input(Submit('submit','Suivant',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Nouveau', css_class='btn-secondary', onclick="window.location.href='"+reverse('organisme_create_for_offre_create')+"'"))
        self.helper.form_method='POST'


class OffreDetailForm(forms.ModelForm):
    class Meta:
        model = Offre
        fields = ['user', 'type', 'emetteur', 'intitule', 'organisme', 'specialites', 'date', 'description', 'statut', 'activation_candidatures', 'notification']

    def __init__(self, *args, **kwargs):
        super(OffreDetailForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['user']=forms.ModelChoiceField(
                queryset=User.objects.filter(id=self.instance.user.id) if self.instance.user else None,
                label=u"Offre déposée par",
                widget=ModelSelect2Widget(
                        model=User,
                        search_fields=['username__icontains', 'email__icontains'],
    
                    ),
                required = False,
                initial=self.instance.user,
                disabled=True
            )
        self.fields['emetteur'].widget = forms.Textarea(attrs={'rows':1})
        self.fields['intitule'].widget = forms.Textarea(attrs={'rows':1})
        self.fields['specialites']=forms.ModelMultipleChoiceField(
            # construire la liste des stagiaires potentiels n'ayant pas encore réservé un PFE
            queryset = Specialite.objects.all(),
            widget=ModelSelect2MultipleWidget(
                model=Specialite,
                search_fields=['code','intitule'],
            ),
            required=False,
            initial=self.instance.specialites.all(),
            disabled=True,
            label="Spécialités ciblées",
        )
        self.fields['organisme']=forms.ModelChoiceField(
                queryset=Organisme.objects.all(),
                initial=self.instance.organisme,
                required=False,
                disabled=True,
            )
        self.fields['description'].widget = forms.Textarea(attrs={'rows':20})
        self.fields['notification'].disabled=True
        self.fields['activation_candidatures'].disabled=True
        
        for key_ in self.fields.keys():
            self.fields[key_].widget.attrs['readonly']=True

class CandidatureDetailForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = ['offre', 'user', 'date_time', 'last_edit', 'nom', 'prenom', 'reponse', 'competences', 'motivations',]

    def __init__(self, *args, **kwargs):
        super(CandidatureDetailForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['user']=forms.ModelChoiceField(
                queryset=User.objects.filter(id=self.instance.user.id) if self.instance.user else None,
                label=u"Candidature par",
                widget=ModelSelect2Widget(
                        model=User,
                        search_fields=['username__icontains', 'email__icontains'],
    
                    ),
                required = False,
                initial=self.instance.user,
                disabled=True
            )
        self.fields['offre']=forms.ModelChoiceField(
                queryset=Offre.objects.all(),
                initial=self.instance.offre,
                required=False,
                disabled=True,
                label=u"Réponse à l'offre",
            )
        
        for key_ in self.fields.keys():
            self.fields[key_].widget.attrs['readonly']=True
            
class DemandeCompteForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(DemandeCompteForm, self).__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.fields['nom'] = forms.CharField(label="Nom", required=True)
        self.fields['prenom'] = forms.CharField(label="Prénom(s)", required=False)
        self.fields['email'] = forms.EmailField(required=True)
        self.fields['motif'] = forms.CharField(label="Motif", required=False, help_text="Indiquez vos intentions quant à la demande du compte (proposition de stages de fin d'études, proposition de thèses, proposition d'offres d'emplois, etc.)")
        self.fields['captcha'] = ReCaptchaField()
        self.helper.add_input(Submit('submit','Demander',css_class='btn-primary'))
        self.helper.add_input(Button('cancel', 'Annuler', css_class='btn-secondary', onclick="window.history.back()"))
        self.helper.form_method='POST'

    def clean_email(self):
        email_ = self.cleaned_data['email']
        if email_ :
            qs = User.objects.filter(username__iexact=email_)
            if qs.exists() :
                raise ValidationError("Un utilisateur existe déjà avec cette adresse e-mail, veuillez plutôt réinitialiser votre mot de passe si vous l'avez oublié.")
        return email_ if email_ else None