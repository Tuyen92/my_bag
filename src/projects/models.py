from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db import models, transaction
from django.db.models import Manager, UniqueConstraint

from shared.models import BaseModel, ActiveManager
from companies.models import Company
from .dhpd_serializer.mapping import PILE_TYPES, CONCRETE_TYPES

# Create your models here.
class Project(BaseModel):
    name = models.CharField( max_length=255, verbose_name="Project Name", help_text="The name of the project.")
    user = models.ManyToManyField( User, related_name="projects", through="UserProjectRel", verbose_name="Users", help_text="The list of users this project belongs to.")
    company = models.ForeignKey( Company, related_name="projects", on_delete=models.CASCADE, verbose_name="Company", help_text="The company this project belongs to.")
    pdf = models.CharField( max_length=255, verbose_name="PDF", default="", help_text="The pdf url of the project.")
    xml = models.CharField( max_length=255, verbose_name="XML", default="", help_text="The xml url of the project.")

    objects = ActiveManager()  # Custom manager for active records
    all_objects = Manager()   # Include all records (active and inactive)
    
    class Meta:
        ordering = ['-created_date']
        constraints = [
            UniqueConstraint(fields=['company', 'name'], name='unique_company_proj_name'),
        ]

    def __str__(self):
        return self.name
    
    def copy_project(self, user=None, new_name_suffix=" Copy"):
        """
        Create a copy of the current project with a modified name.
        
        :param new_name_suffix: The suffix to append to the project name.
        :return: The new Project object.
        """
        try:
            with transaction.atomic():
                # Create a copy of the project
                project_name = f"{self.name}{new_name_suffix}"
                while Project.all_objects.filter(name=project_name).exists():
                    project_name += new_name_suffix
                new_project = Project.objects.create(
                    name=project_name,
                    company=self.company,
                    pdf=self.pdf,
                    xml=self.xml,
                    created_by=user,
                    modified_by=user
                )

                # Copy Settings
                self.basic_data_settings.copy_setting(new_project)

                # Copy Piles
                original_piles = self.piles.all()
                for pile in original_piles:
                    pile.copy_pile(new_project)

                # Copy Soil profiles
                original_soil_profiles = self.soil_profiles.all()
                for soil_profile in original_soil_profiles:
                    soil_profile.copy_soil_profile(new_project)

                # Copy Horizontal cases
                original_horizontal_cases = self.horizontal_loadcases.all()
                for horizontal_case in original_horizontal_cases:
                    horizontal_case.copy_horizontal_cases(new_project)

                return new_project

        except Exception as e:
            raise Exception(e) from e


class UserProjectRel(models.Model):
    user = models.ForeignKey(User, related_name="assigned_users", on_delete=models.CASCADE)
    project = models.ForeignKey(Project, related_name="assigned_projects", on_delete=models.CASCADE)
    date_joined = models.DateField(default=now)


PILE_TYPE_CHOICES = [
    (key, name)
    for key, (short_name, name)
    in PILE_TYPES.items()
]


CONCRETE_TYPE_CHOICES = [
    (key, name)
    for key, name
    in CONCRETE_TYPES.items()
]


class ProjectSettings(models.Model):
    # Link to Project
    project = models.OneToOneField(Project, on_delete=models.CASCADE, primary_key=True, related_name="basic_data_settings")
    
    name                     = models.CharField('Project Name', max_length=64, help_text='Name for this project')
    projektLocation          = models.CharField('projektLocation', null=True, blank=True, default='', max_length=128, help_text='')
    projektStreet            = models.CharField('projektStreet', null=True, blank=True, default='', max_length=128, help_text='')
    projektPostalCode        = models.CharField('projektPostalCode', null=True, blank=True, default='', max_length=128, help_text='')
    companyAltName           = models.CharField('companyAltName', null=True, blank=True, default='', max_length=128, help_text='')
    companyAltLocation       = models.CharField('companyAltLocation', null=True, blank=True, default='', max_length=128, help_text='')
    companyAltStreet         = models.CharField('companyAltStreet', null=True, blank=True, default='', max_length=128, help_text='')
    companyAltPostalCode     = models.CharField('companyAltPostalCode', null=True, blank=True, default='', max_length=128, help_text='')
    companyAltEmail          = models.CharField('companyAltEmail', null=True, blank=True, default='', max_length=128, help_text='')
    companyAltPhone          = models.CharField('companyAltPhone', null=True, blank=True, default='', max_length=128, help_text='')
    companyAltFax            = models.CharField('companyAltFax', null=True, blank=True, default='', max_length=128, help_text='')
    companyAltLogo           = models.CharField('companyAltLogo', null=True, blank=True, default='', max_length=128, help_text='')
    Schrittweite             = models.FloatField('Schrittweite', blank=True, default=0.1, help_text='')
    runHorBemessung          = models.BooleanField('runHorBemessung', blank=True, default=False, help_text='')
    AchsabstandGleicherTiefe = models.FloatField('AchsabstandGleicherTiefe', blank=True, default=0, help_text='')
    AuslastungProzent        = models.FloatField('AuslastungProzent', blank=True, default=100, help_text='')
    Beeinflussungsweite      = models.FloatField('Beeinflussungsweite', blank=True, default=20, help_text='')
    EAErhoehungProzent       = models.FloatField('EAErhoehungProzent', blank=True, default=0, help_text='')
    Exzentrizitaet           = models.FloatField('Exzentrizitaet', blank=True, default=0.1, help_text='')
    FuszBeeinfluszung        = models.IntegerField('FuszBeeinfluszung', blank=True, default=0, help_text='')
    MindestEinbindung        = models.FloatField('MindestEinbindung', blank=True, default=2.5, help_text='')
    zulaessigeSetzungCm      = models.FloatField('zulaessigeSetzungCm', blank=True, default=2, help_text='')
    BetonZyl                 = models.IntegerField('BetonZyl', blank=True, default=25, choices=CONCRETE_TYPE_CHOICES, help_text='')
    MaxLaenge                = models.IntegerField('MaxLaenge', blank=True, default=100, help_text='')
    MantelErhoehungProzent   = models.FloatField('MantelErhoehungProzent', blank=True, default=15, help_text='')
    Knicklaenge              = models.FloatField('Knicklaenge', blank=True, default=0, help_text='')
    FuszErhoehungProzent     = models.FloatField('FuszErhoehungProzent', blank=True, default=15, help_text='')
    useErhoehung             = models.IntegerField('useErhoehung', blank=True, default=2, help_text='')
    SpitzendruckMittelung    = models.BooleanField('SpitzendruckMittelung', blank=True, default=False, help_text='')
    MindestPfahllaenge       = models.FloatField('MindestPfahllaenge', blank=True, default=3, help_text='')
    Norm                     = models.IntegerField('Norm', blank=True, default=1, help_text='')
    gammaDruck               = models.FloatField('gammaDruck', blank=True, default=1.4, help_text='')
    gammaZug                 = models.FloatField('gammaZug', blank=True, default=1.5, help_text='')
    KopfEinbindung           = models.FloatField('KopfEinbindung', blank=True, default=0.5, help_text='')
    ksNichtReduzieren        = models.BooleanField('ksNichtReduzieren', blank=True, default=True, help_text='')
    gegenRaeumlichenEP       = models.BooleanField('gegenRaeumlichenEP', blank=True, default=True, help_text='')
    gammaStaendig            = models.FloatField('gammaStaendig', blank=True, default=1.35, help_text='')
    gammaVeraenderlich       = models.FloatField('gammaVeraenderlich', blank=True, default=1.5, help_text='')
    WinkelAusProfilen        = models.BooleanField('WinkelAusProfilen', blank=True, default=True, help_text='')
    bemesseHorizontal        = models.BooleanField('bemesseHorizontal', blank=True, default=True, help_text='')
    AbtreppungsWinkelRad     = models.FloatField('AbtreppungsWinkelRad', blank=True, default=45, help_text='')
    nameAnlageAuszen         = models.CharField('nameAnlageAuszen', null=True, blank=True, default='', help_text='')
    seitenBezeichnung        = models.CharField('seitenBezeichnung', blank=True, default='Seite', help_text='')
    seitenStartNummer        = models.IntegerField('seitenStartNummer', blank=True, default=1, help_text='')
    SeiteVonSeiten           = models.IntegerField('SeiteVonSeiten', blank=True, default=1, help_text='')
    erstelleUebersichtAuszen = models.IntegerField('erstelleUebersichtAuszen', blank=True, default=1, help_text='')
    UebersichtQuer           = models.IntegerField('UebersichtQuer', blank=True, default=1, help_text='')
    erstelleEinzelnachweise  = models.IntegerField('erstelleEinzelnachweise', blank=True, default=1, help_text='')
    zeichneNachweislinien    = models.IntegerField('zeichneNachweislinien', blank=True, default=1, help_text='')
    UKKotenInTabelle         = models.IntegerField('UKKotenInTabelle', blank=True, default=1, help_text='')
    erstellegrafikAuszen     = models.IntegerField('erstellegrafikAuszen', blank=True, default=1, help_text='')
    erstellegrafikInnen      = models.IntegerField('erstellegrafikInnen', blank=True, default=1, help_text='')
    qskQcAb0                 = models.BooleanField('qskQcAb0',default=False)
    qbkQcAb0                 = models.BooleanField('qbkQcAb0',default=False)
    qskCukAb0                = models.BooleanField('qskCukAb0',default=False)
    qbkCukAb0                = models.BooleanField('qbkCukAb0',default=False)
    MaxLaengs                = models.FloatField('MaxLaengs',default=20)
    MaxBuegel                = models.FloatField('MaxBuegel',default=10)
    MinLaengsAbstand         = models.FloatField('MinLaengsAbstand',default=100)
    MindestEindringung       = models.FloatField('MindestEindringung',default=0.75)
    Stahlsorte               = models.CharField('Stahlsorte',default="B500B")
    StandardPfahlTyp         = models.CharField('StandardPfahlTyp',default="bp")
    falsermInner             = models.IntegerField('falsermInner',default=1)
    MvonMaxfuerSchub         = models.FloatField('MvonMaxfuerSchub',default=50)
    Betondeckung             = models.FloatField('Betondeckung',default=100)

    default_company_info     = models.BooleanField('default_company_info', blank=True, default=True, help_text='')

    def copy_setting(self, new_project: Project):
        """
        Create a new copy setting datas for the new project.
        """
        try:
            if not isinstance(new_project, Project):
                raise ValueError("new_project must be an instance of Project")

            copy_setting = ProjectSettings.objects.create(
                project                  = new_project,
                name                     = new_project.name,
                projektLocation          = self.projektLocation,
                projektStreet            = self.projektStreet,
                projektPostalCode        = self.projektPostalCode,
                companyAltName           = self.companyAltName,
                companyAltLocation       = self.companyAltLocation,
                companyAltStreet         = self.companyAltStreet,
                companyAltPostalCode     = self.companyAltPostalCode,
                companyAltEmail          = self.companyAltEmail,
                companyAltPhone          = self.companyAltPhone,
                companyAltFax            = self.companyAltFax,
                Schrittweite             = self.Schrittweite,
                runHorBemessung          = self.runHorBemessung,
                AchsabstandGleicherTiefe = self.AchsabstandGleicherTiefe,
                AuslastungProzent        = self.AuslastungProzent,
                Beeinflussungsweite      = self.Beeinflussungsweite,
                EAErhoehungProzent       = self.EAErhoehungProzent,
                Exzentrizitaet           = self.Exzentrizitaet,
                FuszBeeinfluszung        = self.FuszBeeinfluszung,
                MindestEinbindung        = self.MindestEinbindung,
                zulaessigeSetzungCm      = self.zulaessigeSetzungCm,
                BetonZyl                 = self.BetonZyl,
                MaxLaenge                = self.MaxLaenge,
                MantelErhoehungProzent   = self.MantelErhoehungProzent,
                Knicklaenge              = self.Knicklaenge,
                FuszErhoehungProzent     = self.FuszErhoehungProzent,
                useErhoehung             = self.useErhoehung,
                SpitzendruckMittelung    = self.SpitzendruckMittelung,
                MindestPfahllaenge       = self.MindestPfahllaenge,
                Norm                     = self.Norm,
                gammaDruck               = self.gammaDruck,
                gammaZug                 = self.gammaZug,
                KopfEinbindung           = self.KopfEinbindung,
                ksNichtReduzieren        = self.ksNichtReduzieren,
                gegenRaeumlichenEP       = self.gegenRaeumlichenEP,
                gammaStaendig            = self.gammaStaendig,
                gammaVeraenderlich       = self.gammaVeraenderlich,
                WinkelAusProfilen        = self.WinkelAusProfilen,
                bemesseHorizontal        = self.bemesseHorizontal,
                AbtreppungsWinkelRad     = self.AbtreppungsWinkelRad,
                nameAnlageAuszen         = self.nameAnlageAuszen,
                seitenBezeichnung        = self.seitenBezeichnung,
                seitenStartNummer        = self.seitenStartNummer,
                SeiteVonSeiten           = self.SeiteVonSeiten,
                erstelleUebersichtAuszen = self.erstelleUebersichtAuszen,
                UebersichtQuer           = self.UebersichtQuer,
                erstelleEinzelnachweise  = self.erstelleEinzelnachweise,
                zeichneNachweislinien    = self.zeichneNachweislinien,
                UKKotenInTabelle         = self.UKKotenInTabelle,
                erstellegrafikAuszen     = self.erstellegrafikAuszen,
                erstellegrafikInnen      = self.erstellegrafikInnen,
                qskQcAb0                 = self.qskQcAb0,
                qbkQcAb0                 = self.qbkQcAb0,
                qskCukAb0                = self.qskCukAb0,
                qbkCukAb0                = self.qbkCukAb0,
                MaxLaengs                = self.MaxLaengs,
                MaxBuegel                = self.MaxBuegel,
                MinLaengsAbstand         = self.MinLaengsAbstand,
                MindestEindringung       = self.MindestEindringung,
                Stahlsorte               = self.Stahlsorte,
                StandardPfahlTyp         = self.StandardPfahlTyp,
                falsermInner             = self.falsermInner,
                MvonMaxfuerSchub         = self.MvonMaxfuerSchub,
                Betondeckung             = self.Betondeckung,
                default_company_info     = self.default_company_info
            )

            return copy_setting

        except Exception as e:
            raise Exception(e) from e


class Pile(models.Model):
    id        = models.AutoField(primary_key=True)  # Auto-incrementing integer ID
    project   = models.ForeignKey( Project, on_delete=models.CASCADE, related_name="piles")
    row_index = models.IntegerField(blank=False, null=False, default=0)

    # It is possible to save semi-empty sheet, so no field must be required to
    # allow DB serialization. It also must be possible to store null value, to
    # which is going to be used for empty cell.
    Pname                                = models.CharField('Name',null=True,max_length=64,help_text='Unique load point name for this project')
    AEHoehe                              = models.FloatField('Drilling level',null=True,help_text='')
    AlternativeCharakteristischeLastZ    = models.FloatField('AlternativeCharakteristischeLastZ',null=True,help_text='')
    AlternativeCharakteristischeMinLastZ = models.FloatField('AlternativeCharakteristischeMinLastZ',default=0,help_text='') # additional
    AlternativeDesignLastZ               = models.FloatField('AlternativeDesignLastZ',null=True,help_text='')
    AlternativeDesignMinLastZ            = models.FloatField('AlternativeDesignMinLastZ',default=0,help_text='') # additional
    # Hardcoded in serializer until purpose is clarified
    BetonZyl = models.IntegerField('BetonZyl', null=True,default=25, blank=True, help_text='')
    # TODO: Store FK to soil profile table to ensure consistency
    BodenProfil        = models.CharField('Soil Profile',null=True,max_length=64,help_text='')
    Hochwert           = models.FloatField('Hochwert',null=True,help_text='')
    PfahlAchsAbstandxD = models.FloatField('PfahlAchsAbstandxD',null=True,default=3,blank=True,help_text='')
    PfahlAnzahl        = models.IntegerField('PfahlAnzahl',null=True,default=1,blank=True,help_text='')
    PfahlTyp           = models.CharField('PfahlTyp',null=True,default='bp',blank=True,max_length=16,help_text='')
    Rechtswert         = models.FloatField('Rechtswert',null=True,help_text='')
    SollDurchmesser    = models.FloatField('SollDurchmesser',null=True,help_text='')
    SollPfahlOberKante = models.FloatField('SollPfahlOberKante',null=True,help_text='')

    # These 4 are hardcoded in serializer until notified what is the purpose
    einzelAusnutzung          = models.IntegerField('einzelAusnutzung',null=True,default=1, blank=True,help_text='')
    einzelExzentrizitaet      = models.FloatField('einzelExzentrizitaet',null=True,default=0.1, blank=True,help_text='')
    einzelKnickLaenge         = models.IntegerField('einzelKnickLaenge',null=True,default=0, blank=True,help_text='')
    einzelMaximaleBohrtiefe   = models.IntegerField('einzelMaximaleBohrtiefe',null=True,default=100, blank=True,help_text='')
    einzelMindestEindringung  = models.FloatField('einzelMindestEindringung',null=True,default=2.5, blank=True,help_text='')
    einzelzulaessigeSetzungCm = models.FloatField('einzelzulaessigeSetzungCm',null=True,default=0,blank=True,help_text='')
    prozentualerMantelAnteil  = models.FloatField('prozentualerMantelAnteil',null=True,default=100,blank=True,help_text='')

    # Calculation result fields. All unknown fields are ignored for now.
    Federsteifigkeit   = models.FloatField('Federsteifigkeit',null=True,default=None,help_text='')
    Nachweisgruppe     = models.FloatField('Nachweisgruppe',null=True,default=None,help_text='')
    R_d                = models.FloatField('R_d',null=True,default=None,help_text='')
    R_d_Min            = models.FloatField('R_d_Min',null=True,default=None,help_text='')
    Rb_k               = models.FloatField('Rb_k',null=True,default=None,help_text='')
    Rs_k               = models.FloatField('Rs_k',null=True,default=None,help_text='')
    Setzung            = models.FloatField('Setzung',null=True,default=None,help_text='')
    laenge_mit         = models.FloatField('laenge_mit',null=True,default=None,help_text='')
    laenge_ohne        = models.FloatField('laenge_ohne',null=True,default=None,help_text='')
    EzuR               = models.FloatField('EzuR',null=True,default=None,help_text='')
    GesamtBohrLaenge   = models.FloatField('GesamtBohrLaenge',null=True,default=None,help_text='')
    PfahlVolumen       = models.FloatField('PfahlVolumen',null=True,default=None,help_text='')
    delta_Laenge       = models.FloatField('delta_Laenge',null=True,default=None,help_text='')
    Soll_UK_Pfahl      = models.FloatField('Soll_UK_Pfahl',null=True,default=None,help_text='')
    BohrLaenge         = models.FloatField('BohrLaenge',null=True,default=None,help_text='')
    AsLaengs           = models.FloatField('AsLaengs',null=True,default=None,help_text='')
    BewBZWLieferlaenge = models.FloatField('BewBZWLieferlaenge',null=True,default=None,help_text='')
    EindringTiefe      = models.FloatField('EindringTiefe',null=True,default=None,help_text='')

    class Meta:
        ordering = ['row_index']
        constraints = [
            UniqueConstraint(fields=['project', 'Pname'], name='unique_project_pname'),
            # UniqueConstraint(fields=['project', 'row_index'], name='unique_project_row_index'),
        ]

    def __str__(self):
        return f"Pile {self.Pname} ({self.project.name})"
    
    def copy_pile(self, new_project: Project):
        """
        Create a new copy pile for the new project.
        """
        try:
            if not isinstance(new_project, Project):
                raise ValueError("new_project must be an instance of Project")
            
            copy_pile = Pile.objects.create(
                project                              = new_project,
                row_index                            = self.row_index,
                Pname                                = self.Pname,
                AEHoehe                              = self.AEHoehe,
                AlternativeCharakteristischeLastZ    = self.AlternativeCharakteristischeLastZ,
                AlternativeCharakteristischeMinLastZ = self.AlternativeCharakteristischeMinLastZ,
                AlternativeDesignLastZ               = self.AlternativeDesignLastZ,
                AlternativeDesignMinLastZ            = self.AlternativeDesignMinLastZ,
                BetonZyl                             = self.BetonZyl,
                BodenProfil                          = self.BodenProfil,
                Hochwert                             = self.Hochwert,
                PfahlAchsAbstandxD                   = self.PfahlAchsAbstandxD,
                PfahlAnzahl                          = self.PfahlAnzahl,
                PfahlTyp                             = self.PfahlTyp,
                Rechtswert                           = self.Rechtswert,
                SollDurchmesser                      = self.SollDurchmesser,
                SollPfahlOberKante                   = self.SollPfahlOberKante,
                einzelAusnutzung                     = self.einzelAusnutzung,
                einzelExzentrizitaet                 = self.einzelExzentrizitaet,
                einzelKnickLaenge                    = self.einzelKnickLaenge,
                einzelMaximaleBohrtiefe              = self.einzelMaximaleBohrtiefe,
                einzelMindestEindringung             = self.einzelMindestEindringung,
                einzelzulaessigeSetzungCm            = self.einzelzulaessigeSetzungCm,
                prozentualerMantelAnteil             = self.prozentualerMantelAnteil,
                Federsteifigkeit                     = self.Federsteifigkeit,
                Nachweisgruppe                       = self.Nachweisgruppe,
                R_d                                  = self.R_d,
                R_d_Min                              = self.R_d_Min,
                Rb_k                                 = self.Rb_k,
                Rs_k                                 = self.Rs_k,
                Setzung                              = self.Setzung,
                laenge_mit                           = self.laenge_mit,
                laenge_ohne                          = self.laenge_ohne,
                EzuR                                 = self.EzuR,
                GesamtBohrLaenge                     = self.GesamtBohrLaenge,
                PfahlVolumen                         = self.PfahlVolumen,
                delta_Laenge                         = self.delta_Laenge
            )

            return copy_pile

        except Exception as e:
            raise Exception(e) from e


class SoilProfile(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing integer ID
    # pk = models.BigIntegerField( primary_key=True, editable=False)
    project = models.ForeignKey( Project, on_delete=models.CASCADE, related_name="soil_profiles")

    name = models.CharField('Profile Name', max_length=128, help_text='')

    # can be hard code because of missing on UI
    pfahlTyp = models.IntegerField('pfahlTyp', null=True, blank=True, default=4, choices=PILE_TYPE_CHOICES, help_text='')
    grundwasserStand = models.FloatField('grundwasserStand', null=True, help_text='')
    startKote = models.FloatField('startKote', null=True, help_text='')

    class Meta:
        constraints = [
            UniqueConstraint(fields=['project', 'name'], name='unique_project_soilprofile_name'),
        ]

    def __str__(self):
        return f"SoilProfile {self.name} ({self.project.name})"
    
    def copy_soil_profile(self, new_project: Project):
        """
        Create a new copy soil profile for the new project.
        """
        try:
            with transaction.atomic():
                if not isinstance(new_project, Project):
                    raise ValueError("new_project must be an instance of Project")

                copy_soil_profile = SoilProfile.objects.create(
                    project          = new_project,
                    name             = self.name,
                    pfahlTyp         = self.pfahlTyp,
                    grundwasserStand = self.grundwasserStand,
                    startKote        = self.startKote,
                )

                original_soil_layers = self.soil_layers.all()

                for soil_layer in original_soil_layers:
                    soil_layer.copy_soil_layer(new_project, copy_soil_profile)

                return copy_soil_profile

        except Exception as e:
            raise Exception(e) from e


class SoilLayer(models.Model):
    id           = models.AutoField(primary_key=True)  # Auto-incrementing integer ID
    project      = models.ForeignKey( Project, on_delete=models.CASCADE, related_name="soil_layers")
    soil_profile = models.ForeignKey( SoilProfile, on_delete=models.CASCADE, related_name="soil_layers")

    row_index           = models.IntegerField(blank=False, null=False, default=0)
    endKote             = models.FloatField('endKote', null=True, help_text='')
    bodenArt            = models.CharField('bodenArt',null=True,default="", blank=True, max_length=64, help_text='')
    ESoben              = models.FloatField('ESoben',null=True,default=0, blank=True, help_text='')
    ESunten             = models.FloatField('ESunten',null=True,default=0, blank=True, help_text='')
    FuszAbsetzbar       = models.BooleanField('FuszAbsetzbar',null=True, default=False, help_text='')
    IstEindringRelevant = models.BooleanField('IstEindringRelevant',null=True, default=False, help_text='')
    MaxElementWeite     = models.FloatField('MaxElementWeite', null=True, default=0.1, blank=True, help_text='')
    cuEP                = models.FloatField('cuEP', null=True,default=0, blank=True, help_text='')
    cuk                 = models.FloatField('cuk', null=True,default="NaN", blank=True, help_text='')
    deltaVonPhi         = models.FloatField('deltaVonPhi', null=True,default=0.67, blank=True, help_text='')
    gammaBoden          = models.FloatField('gammaBoden',null=True,default=19, blank=True, help_text='')
    gammaStrichBoden    = models.FloatField('gammaStrichBoden',null=True,default=19, blank=True, help_text='')
    phi                 = models.FloatField('phi',null=True,default=0, blank=True, help_text='')
    qbk002              = models.FloatField('qbk002', null=True,default=0, blank=True, help_text='')
    qbk003              = models.FloatField('qbk003', null=True,default=0, blank=True, help_text='')
    qbk01               = models.FloatField('qbk01', null=True,default=0, blank=True, help_text='')
    qc                  = models.FloatField('qc',null=True,default="NaN", blank=True, help_text='')
    qsk                 = models.FloatField('qsk', null=True,default=0, blank=True, help_text='')
    qskStern            = models.FloatField('qskStern', null=True,default=0, blank=True, help_text='')
    bodenSchichtColor   = models.CharField('bodenSchichtColor',null=True,default='D8D8D8', blank=True, max_length=10, help_text='')
    tauNk               = models.FloatField('tauNk', null=True,default=0, blank=True, help_text='')
    qskZug              = models.FloatField('qskZug', null=True,default=0, blank=True, help_text='')
    # Output Qsk/Qbk values in case Cu or Qc were used
    PfahlTyp = models.CharField('PfahlTyp', null=True, blank=True, default=None, help_text='')
    usedQsk    = models.FloatField('usedQsk', null=True, default=None, help_text='')
    usedQbk002 = models.FloatField('usedQbk002', null=True, default=None, help_text='')
    usedQbk003 = models.FloatField('usedQbk003', null=True, default=None, help_text='')
    usedQbk01  = models.FloatField('usedQbk01', null=True, default=None, help_text='')

    class Meta:
        ordering = ['row_index']

    def __str__(self):
        return f"SoilLayer {self.row_index} ({self.soil_profile.name})"

    def copy_soil_layer(self, new_project: Project, soil_profile: SoilProfile):
        """
        Create a new copy soil layer for the new soil profile and the new project.
        """
        try:
            if not isinstance(new_project, Project):
                raise ValueError("new_project must be an instance of Project")

            if not isinstance(soil_profile, SoilProfile):
                raise ValueError("soil_profile must be an instance of SoilProfile")

            copy_soil_layer = SoilLayer.objects.create(
                project             = new_project,
                soil_profile        = soil_profile,
                row_index           = self.row_index,
                endKote             = self.endKote,
                bodenArt            = self.bodenArt,
                ESoben              = self.ESoben,
                ESunten             = self.ESunten,
                FuszAbsetzbar       = self.FuszAbsetzbar,
                IstEindringRelevant = self.IstEindringRelevant,
                MaxElementWeite     = self.MaxElementWeite,
                cuEP                = self.cuEP,
                cuk                 = self.cuk,
                deltaVonPhi         = self.deltaVonPhi,
                gammaBoden          = self.gammaBoden,
                gammaStrichBoden    = self.gammaStrichBoden,
                phi                 = self.phi,
                qbk002              = self.qbk002,
                qbk003              = self.qbk003,
                qbk01               = self.qbk01,
                qc                  = self.qc,
                qsk                 = self.qsk,
                qskStern            = self.qskStern,
                tauNk               = self.tauNk,
                qskZug              = self.qskZug,
                bodenSchichtColor   = self.bodenSchichtColor,
                usedQsk             = self.usedQsk,
                usedQbk002          = self.usedQbk002,
                usedQbk003          = self.usedQbk003,
                usedQbk01           = self.usedQbk01
            )

            return copy_soil_layer

        except Exception as e:
            raise Exception(e) from e


class HorizontalLoadCase(models.Model):
    id      = models.AutoField(primary_key=True)  # Auto-incrementing integer ID
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="horizontal_loadcases")
    name    = models.CharField('Case Name', blank=True, max_length=128, help_text='')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['project', 'name'], name='unique_project_hloadcase_name'
            ),
        ]

    def __str__(self):
        return f"Hload case {self.name} ({self.project.name})"

    def copy_horizontal_cases(self, new_project: Project):
        """
        Create a new copy horizontal case for the new project.
        """
        try:
            with transaction.atomic():
                if not isinstance(new_project, Project):
                    raise ValueError("new_project must be an instance of Project")

                copy_horizontal_cases = HorizontalLoadCase.objects.create(
                    project          = new_project,
                    name             = self.name
                )

                original_horizontal_loads = self.horizontal_loads.all()

                for h_load in original_horizontal_loads:
                    h_load.copy_horizontal_load(new_project, copy_horizontal_cases)

                return copy_horizontal_cases

        except Exception as e:
            raise Exception(e) from e

class HorizontalLoadPile(models.Model):
    id      = models.AutoField(primary_key=True)  # Auto-incrementing integer ID
    project = models.ForeignKey( Project, on_delete=models.CASCADE, related_name="horizontal_loads")
    case    = models.ForeignKey( HorizontalLoadCase, on_delete=models.CASCADE, related_name="horizontal_loads")

    # TODO: Reference pile from the external load by FK
    row_index           = models.IntegerField(blank=False, null=False, default=0)
    Pname               = models.CharField('Pile', null=True, max_length=64, help_text='')
    Grundwasser         = models.FloatField('Grundwasser',null=True,default=0, help_text='')
    Hgkx                = models.FloatField('Hgkx',null=True,default=0, blank=True, help_text='')
    Hgky                = models.FloatField('Hgky',null=True,default=0, blank=True, help_text='')
    Hqkx                = models.FloatField('Hqkx',null=True,default=0, blank=True, help_text='')
    Hqky                = models.FloatField('Hqky',null=True,default=0, blank=True, help_text='')
    Mgkx                = models.FloatField('Mgkx',null=True,default=0, blank=True, help_text='')
    Mgky                = models.FloatField('Mgky',null=True,default=0, blank=True, help_text='')
    Mqkx                = models.FloatField('Mqkx',null=True,default=0, blank=True, help_text='')
    Mqky                = models.FloatField('Mqky',null=True,default=0, blank=True, help_text='')
    OKBodenBiegung      = models.FloatField('OKBodenBiegung',null=True,default=0, blank=True, help_text='')
    gkz                 = models.FloatField('gkz',null=True, help_text='')
    # Thisfield is not has on UI
    pAnOberkante        = models.FloatField('pAnOberkante', default=1.9, help_text='')
    qkz                 = models.FloatField('qkz',null=True, help_text='')

    # Output fields
    AsLaengs         = models.FloatField('AsLaengs', null=True, default=None, help_text='')
    AsLaengsCalc     = models.FloatField('AsLaengsCalc', null=True, default=None, help_text='')
    AsQuer           = models.FloatField('AsQuer', null=True, default=None, help_text='')
    AsQuerCalc       = models.FloatField('AsQuerCalc', null=True, default=None, help_text='')
    BewTyp           = models.FloatField('BewTyp', null=True, default=None, help_text='')
    Eps0             = models.FloatField('Eps0', null=True, default=None, help_text='')
    Eps1             = models.FloatField('Eps1', null=True, default=None, help_text='')
    KoteUeberdrueckt = models.FloatField('KoteUeberdrueckt', null=True, default=None, help_text='')
    MMax             = models.FloatField('MMax', null=True, default=None, help_text='')
    MxMax            = models.FloatField('MxMax', null=True, default=None, help_text='')
    MyMax            = models.FloatField('MyMax', null=True, default=None, help_text='')
    Nachweisgruppe   = models.FloatField('Nachweisgruppe', null=True, default=None, help_text='')
    QMax             = models.FloatField('QMax', null=True, default=None, help_text='')
    QxMax            = models.FloatField('QxMax', null=True, default=None, help_text='')
    QyMax            = models.FloatField('QyMax', null=True, default=None, help_text='')
    wOben            = models.FloatField('wOben', null=True, default=None, help_text='')
    wxOben           = models.FloatField('wxOben', null=True, default=None, help_text='')
    wyOben           = models.FloatField('wyOben', null=True, default=None, help_text='')

    class Meta:
        ordering = ['row_index']
        constraints = [
            UniqueConstraint(
                fields=['case', 'Pname'], name='unique_hloadcase_hloadname'
            ),
        ]

    def __str__(self):
        return f"Hload {self.Pname} ({self.case.name})"

    def copy_horizontal_load(self, new_project: Project, horizontal_case: HorizontalLoadCase):
        """
        Create a new copy horizontal load for the new horizontal case
        and the new project.
        """
        try:
            if not isinstance(new_project, Project):
                raise ValueError("new_project must be an instance of Project")

            if not isinstance(horizontal_case, HorizontalLoadCase):
                raise ValueError("horizontal_case must be an instance of HorizontalLoadCase")

            copy_h_load = HorizontalLoadPile.objects.create(
                project             = new_project,
                case                = horizontal_case,
                row_index           = self.row_index,
                Pname               = self.Pname,
                Grundwasser         = self.Grundwasser,
                Hgkx                = self.Hgkx,
                Hgky                = self.Hgky,
                Hqkx                = self.Hqkx,
                Hqky                = self.Hqky,
                Mgkx                = self.Mgkx,
                Mgky                = self.Mgky,
                Mqkx                = self.Mqkx,
                Mqky                = self.Mqky,
                OKBodenBiegung      = self.OKBodenBiegung,
                gkz                 = self.gkz,
                pAnOberkante        = self.pAnOberkante,
                qkz                 = self.qkz,
                AsLaengs            = self.AsLaengs,
                AsLaengsCalc        = self.AsLaengsCalc,
                AsQuer              = self.AsQuer,
                AsQuerCalc          = self.AsQuerCalc,
                BewTyp              = self.BewTyp,
                Eps0                = self.Eps0,
                Eps1                = self.Eps1,
                KoteUeberdrueckt    = self.KoteUeberdrueckt,
                MMax                = self.MMax,
                MxMax               = self.MxMax,
                MyMax               = self.MyMax,
                Nachweisgruppe      = self.Nachweisgruppe,
                QMax                = self.QMax,
                QxMax               = self.QxMax,
                QyMax               = self.QyMax,
                wOben               = self.wOben,
                wxOben              = self.wxOben,
                wyOben              = self.wyOben
            )

            return copy_h_load

        except Exception as e:
            raise Exception(e) from e
