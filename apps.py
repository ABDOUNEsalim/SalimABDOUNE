from django.apps import AppConfig
from django.db.models.signals import post_migrate

def initial_groups_create_if_not_exists(sender, **kwargs):
    from django.contrib.auth.models import Group
    
    group_, created = Group.objects.get_or_create(name='etudiant', defaults={
                'name': 'etudiant'
            })
    if created :
        print("Rôle/Group 'etudiant' créé.")

    group_, created = Group.objects.get_or_create(name='enseignant', defaults={
                'name': 'enseignant'
            })
    if created :
        print("Rôle/Group 'enseignant' créé.")
        
    group_, created = Group.objects.get_or_create(name='partenaire', defaults={
                'name': 'partenaire'
            })
    if created :
        print("Rôle/Group 'partenaire' créé.")
        
    group_, created = Group.objects.get_or_create(name='doctorant', defaults={
                'name': 'doctorant'
            })
    if created :
        print("Rôle/Group 'doctorant' créé.")

def initial_permissions_create_update_delete(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    from scolar.models import User
    
    #Le code de permission doit contenir au minimum deux parties séparées par un tiret du 8 _
    #La première partie doit obligatoirement contenir le mot clé 'fonctionnalite', ou 'fonctionnalitenav' pour les fonctionnalités prévues à être visibles dans la barre latérale de navigation
    #La deuxième partie contiendra un intitulé du bloc de fonctionnalités, qui sera affiché dans la page de configuration
    #L'ajout de nouveaux codes de permissions peut se faire dans cette section, le retrait des codes de permission les retirera de la base de données, c'est donc à manipuler avec précaution.
    #La modification des descriptions des permissions est possible. 
    #Toutes les permissions sont mises à jour au prochain migrate (en post-migrate, même s'il n'y a aucune migration à appliquer)
    
    permissions = (
    
        ("fonctionnalite_configurationetablissement_visualisation", "Visualiser la configuration de l'établissement : Institution, résidences universitaires, charges, géo, rôles et droits d'accès, autorités, liste des utilisateurs, liste du personnel.."),
        ("fonctionnalite_configurationetablissement_modification", "Modifier la configuration de l'établissement : Institution, résidences universitaires, charges, géo, rôles et droits d'accès, autorités, configuration des documents, configuration des utilisateurs, personnel.."),
        ("fonctionnalitenav_configurationetablissement_enregistrementetudiants", "Valider l'enregistrement des nouveaux utilisateurs (étudiants) (Uniquement si la fonctionnalité est activée depuis les paramètres de l'établissement)"),
    
    
        ("fonctionnalitenav_dashboard_etudiants", "Visualiser le dashboard des étudiants : Effectifs, lieux de résidences, assiduité, etc"),
        ("fonctionnalitenav_dashboard_enseignants", "Visualiser le dashboard des enseignants : Effectifs, assiduité, répartition des charges, etc"),
        ("fonctionnalitenav_dashboard_formations", "Visualiser le dashboard des formations : Ratios des décisions de jury par année, global, etc"),
        ("fonctionnalitenav_dashboard_stages", "Visualiser le dashboard des stages"),
    
    
        ("fonctionnalitenav_etudiants_annuairecomplet", "Visualiser l'annuaire complet des étudiants (+toutes leurs inscriptions)"),
        ("fonctionnalitenav_etudiants_groupes", "Visualiser la liste des groupes de l'année en cours"),
        ("fonctionnalitenav_etudiants_documentsgroupes", "Générer les documents groupés concernant l'étudiant : Certificats de scolarité, relevés de notes, fiches PFE, .."),
        ("fonctionnalitenav_etudiants_preinscriptions", "Afficher et valider les préinscriptions de tous les étudiants."),
        ("fonctionnalitenav_etudiants_visualisationabsences", "Visualiser la liste des absences des étudiants"),
        ("fonctionnalitenav_etudiants_signalementabsences", "Signaler les absences des étudiants"),
        ("fonctionnalitenav_etudiants_rapportabsences", "Visualiser le rapport des absences des étudiants par formation, période, type d'activité pédagogique, .."),
    
        ("fonctionnalite_etudiants_justificationabsences", "Justifier les absences des étudiants"),
        ("fonctionnalite_etudiants_visualisationsensible", "Visualiser les informations sensibles des étudiants (tél, ..)"),
        ("fonctionnalite_etudiants_gestion", "Ajouter/Importer/Modifier les étudiants, inscriptions, affectations aux groupes, tutorats, et autres informations relatives aux étudiants"),
        ("fonctionnalite_etudiants_suppression", "Supprimer les étudiants"),
        ("fonctionnalite_etudiants_visualisationnotesprofil", "Visualiser les notes (relevés et ECTS) dans le profil des étudiants"),            
        ("fonctionnalite_etudiants_documents", "Télécharger les documents prêts des étudiants : Fiches d'inscription, relevés et certificats PDF signés, attestations.. (permission ne couvrant pas les documents volontairement non-signés -S)"),
        ("fonctionnalite_etudiants_documentsnonsignes", "Télécharger les documents non signés de l'étudiant"),
        ("fonctionnalite_etudiants_reinitialisationnotesetacquis", "Réinitialiser les notes des périodes/UE/modules des étudiants, insertion des modules acquis"),
        ("fonctionnalite_etudiants_visualisationinfosfamille", "Visualiser les informations sensibles de l'étudiant : fonction des parents, moyenne du bac,ect"),
        ("fonctionnalite_etudiants_export", "Exporter les étudiants"),
    
        ("fonctionnalitenav_enseignants_annuairecomplet", "Visualiser l'annuaire complet des enseignants"),
        ("fonctionnalitenav_enseignants_visualisationabsences", "Visualiser la liste des absences des enseignants"),
        ("fonctionnalitenav_enseignants_signalementabsences", "Signaler les absences des enseignants"),
        ("fonctionnalitenav_enseignants_visualisationcharges", "Visualiser la liste des charges des enseignants"),
    
        ("fonctionnalite_enseignants_visualisationsensible", "Visualiser les informations sensibles des enseignants (tél, ..)"),
        ("fonctionnalite_enseignants_gestion", "Ajouter, importer et modifier les enseignants"),
        ("fonctionnalite_enseignants_suppression", "Supprimer les enseignants"),
        ("fonctionnalite_enseignants_export", "Exporter les enseignants"),

        ("fonctionnalite_enseignants_documents", "Télécharger les documents prêts des enseignants"),
        ("fonctionnalite_enseignants_justificationabsences", "Justifier les absences des enseignants"),
        ("fonctionnalite_enseignants_gestioncharges", "Importer/Ajouter/Modifier des charges concernant des enseignants"),
    
    
        ("fonctionnalitenav_pedagogie_gestionprogrammes", "Gérer le catalogue des programmes et matières, configurer les diplômes, spécialités, périodes, cycles, domaines de connaissances.."),
        ("fonctionnalitenav_pedagogie_visualisationfeedbacks", "Visualiser la liste des feedbacks des enseignements (commentaires des étudiants non inclus dans la permission)"),
        ("fonctionnalitenav_pedagogie_edt", "Visualiser les emplois du temps publics des groupes, étudiants et enseignants via l'EDT Finder"),
        ("fonctionnalitenav_pedagogie_visualisationcoordination", "Visualiser les coordination de tous les modules : coordinateurs, évaluations, formules, .."),
        ("fonctionnalitenav_pedagogie_visualisationnotes", "Visualiser les notes de tous les modules, par formation, par période.."),
        ("fonctionnalitenav_pedagogie_visualisationdettes", "Visualiser les dettes de tous les modules par programme"),
        ("fonctionnalitenav_pedagogie_generationpvsdeliberation", "Générer les PVs de délibération, calcul des notes éliminatoires (+PVs des NE), calcul des rangs et moyennes, confirmation et envoi des décisions, passage à l'année suivante.."),
        ("fonctionnalitenav_pedagogie_visualisationpvsdeliberation", "Visualiser tous les PVs de délibération"),

        ("fonctionnalite_pedagogie_visualisationcommentairesfeedbacks", "Visualiser les commentaires de feedback des étudiants"),
        ("fonctionnalite_pedagogie_importationfeedbacks", "Importer les feedbacks des modules"),
        ("fonctionnalite_pedagogie_validationfeedbacks", "Valider/modifier les feedbacks des étudiants et leur état de validation"),
        ("fonctionnalite_pedagogie_gestioncompetences", "Gérer la base de compétences : Ajout de familles de compétences, compétences, et éléments de compétences"),
        ("fonctionnalite_pedagogie_gestioncoordination", "Gérer la coordination de tous les modules : Affecter les coordinateurs, modifier les évaluations, formules, .. "),
        ("fonctionnalite_pedagogie_modificationnotes", "Modifier/Importer les notes de tous les modules"),
        ("fonctionnalite_pedagogie_gestiondettes", "Gérer les dettes de tous les modules par programme"),
        
        ("fonctionnalitenav_Export_exportationprogres", "Exporter des fichiers selon les canevas de progres"),
        ("fonctionnalitenav_Export_exportationlistes", "Exporter des différents listes(list service national selon le canevas,maladie,non inscrit, abandon...)"),

    
        ("fonctionnalitenav_planification_visualisationformations", "Visualiser la liste des formations existantes par année universitaire, avec leurs sections et groupes"),
        ("fonctionnalitenav_planification_activites", "Gérer la planification des activités : Importation, ajout, suppression"),
        ("fonctionnalitenav_planification_chargementagenda", "Charger l'Agenda (Google, ..) avec les activités planifiées"),
        ("fonctionnalitenav_planification_reinitialisationagenda", "Réinitialiser l'Agenda (Google, ..)"),
    
        ("fonctionnalite_planification_gestionformations", "Gérer les formations par année universitaire : Création, modification, suppression des années universitaires, formations, sections et groupes"),
        ("fonctionnalite_planification_visualisationseances", "Visualiser les séances des activités de tous les modules"),
        ("fonctionnalite_planification_gestionseances", "Gérer les séances de tous les modules : Ajouter des séances de rattrapage, .."),

    
        ("fonctionnalitenav_examens_gestionsalles", "Gérer la liste des salles d'examen"),
        ("fonctionnalitenav_examens_visualisationexamens", "Visualiser la liste des examens"),
        ("fonctionnalitenav_examens_visualisationsurveillance", "Visualiser la répartition des surveillants aux examens"),
        ("fonctionnalitenav_examens_visualisationplacesetudiants", "Visualiser la répartition des étudiants dans les salles d'examen"),
        ("fonctionnalitenav_examens_exportatonlisteplaces", "Exporter la liste des places disponibles dans toutes les salles d'examen"),
    
        ("fonctionnalite_examens_gestionexamens", "Gérer les examens : Création, modification, affectation des surveillants, placement des étudiants, envoi des convocations.."),
        ("fonctionnalite_examens_visualisationreprographie", "Visualiser la reprographie des examens"),
    
        ("fonctionnalitenav_stages_visualisationstages", "Visualiser la liste des stages de fin d'études et de master"),
        ("fonctionnalitenav_stages_soumission", "Soumettre un sujet de stage (permission n'affectant pas le droit naturel des étudiants, enseignants et partenaires à soumettre un stage)"),
        ("fonctionnalitenav_stages_validation", "Contrôler le processus de validation des stages, visionner leurs états de validation, leur affecter des experts/commissions, modifier les stages, supprimer les stages.."),
        ("fonctionnalitenav_stages_experts", "Visualiser l'index des experts (expertisant les sujets de stage)"),
        ("fonctionnalitenav_stages_visualisationsoutenances", "Visualiser la liste des soutenances de stages de PFE et Master + PVs + Fiches d'évaluation .."),
        ("fonctionnalitenav_stages_visualisationpartenaires", "Visualiser la liste des organismes partenaires"),
        ("fonctionnalitenav_stages_exportationpartenaires", "Exporter la liste des organismes partenaires"),
        ("fonctionnalitenav_stages_exportationstages", "Exporter la liste des stages de fin d'étude et de master"),
        ("fonctionnalitenav_stages_visualisationsoutenancesequipes", "Visualiser la liste des soutenances de toutes les matières d'équipe (+PVs, fiches d'évaluation, liste des équipes ..)"),
        ("fonctionnalitenav_stages_visualisationstatistiques", "Visualiser les statistiques des soutenances"),
        
        
        ("fonctionnalite_stages_gestionpartenaires", "Gérer/Importer les organismes partenaires, créer des comptes utilisateurs aux partenaires afin qu'ils puissent déposer des sujets de stage"),
        ("fonctionnalite_stages_importation", "Importer les sujets de stages et leurs affectations aux groupes"),
        ("fonctionnalite_stages_modificationsoutenances", "Modifier les soutenances de tous les PFE et Master (dates, jurys, mentions, ..)"),
        ("fonctionnalite_stages_modificationsoutenancesequipes", "Modifier les soutenances de toutes les matières d'équipe (dates, jurys, mentions, ..)"),
        
        ("fonctionnalitenav_postgraduation_visualisationdoctorants", "Visualiser la liste et les profils des doctorants (profils enseignant et/ou étudiant), ainsi que les crédits cumulés des doctorants."),
        ("fonctionnalitenav_postgraduation_visualisationsujets", "Visualiser la liste des sujets de doctorat visibles"),
        ("fonctionnalitenav_postgraduation_gestionsujets", "Gérer la liste des sujets de doctorat et thèses : Ajout, modification, suppression, constitution des commissions d'experts et contrôle de validation, affectation des sujets aux doctorants"),
        ("fonctionnalitenav_postgraduation_visualisationavancementdoctorants", "Visualiser l'état d'avancement des doctorants, les décisions et avis du jury, labos, décisions finales.."),
        ("fonctionnalitenav_postgraduation_visualisationseminaires", "Visualiser la liste des séminaires"),
        ("fonctionnalitenav_postgraduation_visualisationprojetsrecherche", "Visualiser la liste des projets de recherche"),
        ("fonctionnalitenav_postgraduation_preinscriptions", "Afficher et valider les préinscriptions de tous les doctorants."),
        ("fonctionnalitenav_postgraduation_visualisationequipesrecherche","Visualiser les équipes de recherche"),

        ("fonctionnalite_postgraduation_gestiondoctorants", "Ajouter/Importer/Modifier/Supprimer les doctorants, inscriptions, affiliations, et autres informations relatives aux doctorants"),
        ("fonctionnalite_postgraduation_visualisationsensibledoctorants", "Visualiser les informations sensibles des doctorants (dans leurs profils étudiants et enseignant)"),
        ("fonctionnalite_postgraduation_visualisationdocumentsdoctorants", "Visualiser les documents des doctorants : Relevé des séminaires, certificats, ..(Permission ne couvrant pas les documents non signés)"),
        ("fonctionnalite_postgraduation_visualisationdocumentsnonsignesdoctorants", "Visualiser les documents non signés des doctorants"),
        ("fonctionnalite_postgraduation_gestionseminaires", "Gérer la liste des séminaires : Ajout, modification, suppression, .."),
        ("fonctionnalite_postgraduation_gestionavancementdoctorants", "Gérer l'état d'avancement des doctorants, jurys, évaluations, .."),
        ("fonctionnalite_postgraduation_decision1", "Gérer les premières décisions pour les états d'avancement en post-graduation"),
        ("fonctionnalite_postgraduation_decisionsfinales", "Gérer les décisions finales (conseil scientifique..) pour les états d'avancement en post-graduation" ),
        ("fonctionnalite_postgraduation_gestionprojetsrecherche", "Gérer la liste des projets de recherche : Ajout, modification, suppression, .."),
        ("fonctionnalite_postgraduation_gestioncriteres", "Gérer la liste des critères (et leurs options) pris en compte dans l'état d'avancement (ajout, suppression, modification) .."),
        ("fonctionnalite_postgraduation_gestionequipesrecherche","Gérer les équipes de recherche"),
        
        ("fonctionnalite_tracabilite_visualisation", "Visualiser les données de traçabilité (actions faîtes par les utilisateurs)"),
        ("fonctionnalite_tracabilite_suppression", "Supprimer les données de traçabilité"),
        
        ("fonctionnalitenav_postes_visualisation", "Visualiser la liste des postes"),
        ("fonctionnalite_postes_gestion", "Gérer la liste des postes"),

        ("fonctionnalitenav_offres_validation", "Valider/Modifier/Supprimer les offres d'emploi, de thèse, de stages pratiques, et autres offres."), 
        
    )
    
    permission_codenames=[]
    for permission_ in permissions :
        permission_codenames.append(permission_[0])
        permission_existante, created= Permission.objects.get_or_create(codename=permission_[0], defaults={
                'codename': permission_[0],
                'content_type': ContentType.objects.get_for_model(User),
                'name': permission_[1]
            })
        if created :
            print("Permission : '"+permission_[0]+"' : créée.")
        else :
            if permission_existante.name!=permission_[1] :
                permission_existante.name=permission_[1]
                permission_existante.save()
                print("Permission : '"+permission_[0]+"' : Description modifiée.")
    permissions_final_list=Permission.objects.filter(codename__startswith='fonctionnalite')
    for permission_in_db in permissions_final_list :
        if not (permission_in_db.codename in permission_codenames) :
            codename_=permission_in_db.codename
            permission_in_db.delete()
            print("Permission : '"+codename_+"' : supprimée.")
        

class ScolarConfig(AppConfig):
    name = 'scolar'
    
    def ready(self):
        
        post_migrate.connect(initial_groups_create_if_not_exists, sender=self)
        post_migrate.connect(initial_permissions_create_update_delete, sender=self)