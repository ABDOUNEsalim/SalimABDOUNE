from django.conf import settings
from scolar.models import Institution, AnneeUniv

def institution(request):
    context={}
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
    context['institution'] = institution_
    context['annee_univ_list'] = AnneeUniv.objects.all().order_by('-annee_univ')
    return context 
    