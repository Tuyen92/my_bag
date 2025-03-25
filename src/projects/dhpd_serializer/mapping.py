'''This file describes required data mapping between python code and XML-encoded
data for the DHPD-Webclient tool.
'''

import base64
from math import pi


# Custom map function for color code.
def color_mapper(value, to_xml):
    if to_xml:
        # Remove leading "#"
        color = value[1:]

        # We need data in AARRGGBB format
        if len(color) == 6:    # No alpha channel, add it
            return f'FF{color}'
        elif len(color) == 8:  # Alpha channel, move it to the start
            return f'{color[6:]}{color[:6]}'
        else:
            raise ValueError('Unexpected color value: {value}')
    else:
        # Assume we always get 8 character value here
        color = value
        if len(value) != 8:
            raise ValueError('Unexpected color value: {value}')

        # Shift around alpha channel at the end of string and add # symbol
        return f'#{value[2:]}{value[:2]}'


# Custom mapper to encode binary data from model as base64 in XML
# Note: base64 is NOT expected type for xml, but we still use it to later
# Extract and pass image data to the DHPD Proxy tool.
def binary_mapper(data, to_xml):
    if to_xml:
        encoded_data = base64.encodebytes(data)
        # Decode this as string, because base64 IS a string.
        encoded_data = encoded_data.decode()
        return encoded_data

    # This is possible if we import an XML export with company photo
    else:
        # Encode string back to bytes
        encoded_data = data.encode()
        decoded_data = base64.decodebytes(encoded_data)
        return decoded_data


# Extracted pile IDs, their short names and long names in German
PILE_TYPES = {
    0:  ('js', 'Jac-S'),
    1:  ('jo', 'Jac-O'),
    2:  ('jb', 'Jac-B'),
    3:  ('jv', 'Jac-V'),
    4:  ('bp', 'Bohrpfahl'),
    5:  ('a',  'Atlas'),
    6:  ('f',  'Fundex'),
    7:  ('v',  'VGS'),
    14: ('c',  'Betonfertigrammpfahl'),
    15: ('r',  'Stahlrohrrammpfahl, hb=0.8; hs=0.6'),
    16: ('fv', 'Fundex'),
    17: ('fdp','Atlas-FDP')
}


PILE_TYPES_SYMBOLS = [c[1][0] for c in PILE_TYPES.items()]


DRIVEN_PILE_TYPES = {
    14: ('c',  'Betonfertigrammpfahl'),
    15: ('r',  'Stahlrohrrammpfahl, hb=0.8; hs=0.6')
}


DRIVEN_PILE_TYPES_SYMBOLS = [c[1][0] for c in DRIVEN_PILE_TYPES.items()]


CONCRETE_TYPES = {
    25: 'C25/30',
    30: 'C30/37',
    35: 'C35/40',
}


'''This part describes a map for each XML document section in the following
format:
    1. XML Element name
    2. Type of data in the model.
       Specifying "None" in this column changes behavior: NULL Field value is
       always encoded into XML as-is, when unmapping to model, the field is
       never deserialized and is ignored.
    3. Type of data in the XML document
    3. NULL Field value (raises exception if set None and)
    4. Unit converion for encoding element. Can be one of these:
       * Float number. Value will be multiplied by this factor when converting
         to XML and divided when reading from XML.
       * None: Skip conversion
       * Dict: Will do 1:1 mapping, or raise exception if value is unknown
       * Callable: arbitary function that must handle conversion, will be given
         2 arguments: Input value and boolean. Boolean is True if converting to
         XML and False when reading XML data back into model.

    The conversion operation takes the place between casting model type and
    casting the xml type, again. In some cases just type casting is enough
    to get the proper data type (e.g. boolean to int), but for more complex
    cases conversion is here to make sure type casting at the end is successful.
'''

PROJECT_SETTINGS = {
    #                            Model,   XML, Null, Converter
    '_ProjektName':               (str,   str, None, None),
    '_runHorBemessung':          (bool,  bool, None, None),
    # This one says "Rad" but actually stores value in degrees.
    # Change to pi/180 when webclient is updated for this.
    '_AbtreppungsWinkelRad':    (float, float, None, None),
    '_AchsabstandGleicherTiefe':(float, float, None, None),
    '_AuslastungProzent':       (float, float, None, None),
    '_Beeinflussungsweite':     (float, float, None, None),
    '_EAErhoehungProzent':      (float, float, None, None),
    '_Exzentrizitaet':          (float, float, None, None),
    # Ohne=0, AA=1, RR=2; defined in the Model
    # Consider adding direct mapper to the model record id
    '_FuszBeeinfluszung':         (int,   int, None, None),
    '_FuszErhoehungProzent':    (float, float, None, None),
    # Hardcoded as per-PO request
    '_Knicklaenge':              (None, float, 0.0,  None),
    '_MantelErhoehungProzent':  (float, float, None, None),
    '_MindestEinbindung':       (float, float, None, None),
    '_MindestPfahllaenge':      (float, float, None, None),
    # 1054=0, EAP=1; hardcoded as per-request
    '_Norm':                     (None,   int, 1,    None),
    # TODO: This is supposed to be ≥ 1.0 for cheap version of the software
    '_Schrittweite':            (float, float, None, None),
    '_SpitzendruckMittelung':    (bool,  bool, None, None),
    '_WinkelAusProfilen':        (bool,  bool, None, None),
    '_gammaDruck':              (float, float, None, None),
    '_gammaStaendig':           (float, float, None, None),
    '_gammaVeraenderlich':      (float, float, None, None),
    '_gammaZug':                (float, float, None, None),
    '_gegenRaeumlichenEP':       (bool,  bool, None, None),
    '_ksNichtReduzieren':        (bool,  bool, None, None),
    # All=0, qc und cu=1, Nein=2; defined in the Model
    # Consider adding direct mapper to the model record id
    '_useErhoehung':              (int,   int, None, None),
    '_zulaessigeSetzungCm':     (float, float, None, None),
    # 'C25/30'=25, 'C30/37'=30, 'C35/40'=35; defined in the Model
    # Consider adding direct mapper to the model record id
    '_BetonZyl':                  (int,   int, None, None),
    '_KopfEinbindung':          (float, float, None, None),
    # FIXME: Unknown value, hardcoded for now
    '_MaxLaenge':                (None,  None, 100,  None),
    # Extra from testAxel.xml file. Store empty string for null in XML
    '_projektLocation':           (str,   str, '',   None),
    '_projektPostalCode':         (str,   str, '',   None),
    '_projektStreet':             (str,   str, '',   None),
    '_companyAltEmail':           (str,   str, '',   None),
    # Deprecated, don't set
    '_companyAltFax':            (None,   str, '',   None),
    '_companyAltLocation':        (str,   str, '',   None),
    '_companyAltName':            (str,   str, '',   None),
    '_companyAltPhone':           (str,   str, '',   None),
    '_companyAltPostalCode':      (str,   str, '',   None),
    '_companyAltStreet':          (str,   str, '',   None),
    # Workaround: Pass image data encoded as base64 to decode it in dhpd-proxy
    '_companyAltLogo':          (bytes,   str, None, binary_mapper),
    '_nameAnlageAuszen':          (str,   str, None, None),
    '_seitenBezeichnung':         (str,   str, None, None),
    '_seitenStartNummer':         (int,   int, None, None),
    '_SeiteVonSeiten':           (bool,   int, None, None),
    '_erstelleUebersichtAuszen': (bool,   int, None, None),
    '_UebersichtQuer':           (bool,   int, None, None),
    '_erstelleEinzelnachweise':  (bool,   int, None, None),
    '_zeichneNachweislinien':    (bool,   int, None, None),
    '_UKKotenInTabelle':         (bool,   int, None, None),
    '_erstellegrafikAuszen':     (bool,   int, None, None),
    '_erstellegrafikInnen':      (bool,   int, None, None),

}


SOIL_PROFILE_INPUT = {
    '_profilName':                 (str,  str, None, None),
    # key from PILE_TYPES dictionary
    '_PfahlTyp':                    (int, int, None, None),
    '_grundwasserStand':        (float, float, None, None),
    '_startKote':               (float, float, None, None),
    # Dict is to be passed as-is, don't bother with recursion here
    'alleBodenSchichten':        (dict,  dict, None, None),
}


# The soil profile name is stored outside this object, to be handled separately
SOIL_PROFILE_OUTPUT = {
    # This is serialized long name of pile type OR '\"' sequence
    '_PfahlTyp':                    (str, str, None, None),
    '_schichten':                 (dict, dict, None, None),
}


SOIL_LAYER_INPUT = {
    '_endKote':                 (float, float, None, None),
    '_bodenArt':                  (str,   str, None, None),
    # These fields are stored as kilo- in XML but shown as mega- units
    '_ESoben':                  (float, float, None, 1000.0),
    '_ESunten':                 (float, float, None, 1000.0),
    '_FuszAbsetzbar':            (bool,   int, None, None),
    '_IstEindringRelevant':      (bool,   int, None, None),
    # Hardcoded as per PO request.
    '_MaxElementWeite':          (None, float, 0.1,  100.0),
    '_cuEP':                    (float, float, None, None),
    '_cuk':                     (float, float, 0,    None),
    '_deltaVonPhi':             (float, float, None, None),
    '_gammaBoden':              (float, float, None, None),
    '_gammaStrichBoden':        (float, float, None, None),
    # UI shows degrees, but we need to store radians
    '_phi':                     (float, float, 0,    pi/180),
    # These values can be empty. Serialize empty as 0
    '_qbk002':                  (float, float, 0,    1000.0),
    '_qbk003':                  (float, float, 0,    1000.0),
    '_qbk01':                   (float, float, 0,    1000.0),
    '_qc':                      (float, float, 0,    None),
    '_qsk':                     (float, float, 0,    1000.0),
    # Custom value converter from RRGGBBAA to AARRGGBB
    '_bodenSchichtColor':         (str,   str, None, color_mapper),
}


SOIL_LAYER_OUTPUT = {
    # Is this value even supposed to go to the soil layer? Seems to be buggy.
    # First layer outputs 'Borderpfahl', but from second and on it is '"' char
    '_Pfahltyp':                 (None,   str, None, None),  # Unknown
    # The conversion value might look confusing. But we normally READ the data,
    # which means we are going to UNMAP, thus divide by this factor.
    '_usedQsk':                 (float, float, None, 1000.0),
    '_usedQbk002':              (float, float, None, 1000.0),
    '_usedQbk003':              (float, float, None, 1000.0),
    '_usedQbk01':               (float, float, None, 1000.0),
}


LOAD_POINT_INPUT = {
    '_Pname'                              : (str,    str, None, None),
    '_AEHoehe'                            : (float, float, None, None),
    '_AlternativeCharakteristischeLastZ'  : (float, float, None, None),
    'AlternativeCharakteristischeMinLastZ': (float, float, None, None),
    '_AlternativeDesignLastZ'             : (float, float, None, None),
    'AlternativeDesignMinLastZ'           : (float, float, None, None),
    # Hidden in the application, actual type and enum is unknown
    '_BetonZyl': (None,    int, 25,   None), # Unknown
    # Consider adding direct mapper to the model record id
    '_BodenProfil'       : (str,    str, None, None),
    '_Hochwert'          : (float, float, None, None),
    '_PfahlAchsAbstandxD': (float, float, 3.0,  None),
    '_PfahlAnzahl'       : (float, float, 1,    None),
    # Consider adding direct mapper to the model record id
    # WARNING    : Shorthands detected from investigation
      '_PfahlTyp': (int,    str, 'bp', {k: v[0] for k, v
                                                      in PILE_TYPES.items()}),
    '_Rechtswert'        : (float, float, None, None),
    '_SollDurchmesser'   : (float, float, None, None),
    '_SollPfahlOberKante': (float, float, None, None),
    # Following 4 values are taken from export file, their purpose is unknown
    '_einzelAusnutzung'         : (None, float, 1.0,  None), # Unknown
    '_einzelExzentrizitaet'     : (None, float, 0.1,  None), # Unknown
    '_einzelKnickLaenge'        : (None, float, 0.0,  None), # Unknown
    '_einzelMaximaleBohrtiefe'  : (None, float, 100.0,None), # Unknown
    '_einzelMindestEindringung' : (float, float, 0.0,None),
    '_einzelzulaessigeSetzungCm': (float, float, 0.0,None),
    # Should be stored in 0-100 range, 0-1 is expected, though
    '_prozentualerMantelAnteil': (float, float, 1.0, 0.01),
}


LOAD_POINT_OUTPUT = {
    # We have a lot of unknown values here with unknown units / type. These are
    # ignored for now, until specified.
    '_Federsteifigkeit':        (float, float, None, None),
    '_MinFedersteifigkeit':      (None, float, None, None),  # Unknown
    '_MinSetzung':               (None, float, None, None),  # Unknown
    '_Nachweisgruppe':            (int,   int, None, None),
    '_R_d':                     (float, float, None, None),
    '_R_d_Min':                 (float, float, None, None),
    '_Rb_k':                    (float, float, None, None),
    '_Rs_k':                    (float, float, None, None),
    '_Setzung':                 (float, float, None, None),
    '_laenge_mit':              (float, float, None, None),
    '_laenge_ohne':             (float, float, None, None),
    'nachweisErbracht':          (None,  bool, None, None),  # Unknown
    'nachweisErbrachtMin':       (None,  bool, None, None),  # Unknown
    '_GewaehltePfahlAnzahl':     (None,   int, None, None),  # Unknown
    '_GewaehlterDurchmesser':    (None, float, None, None),  # Unknown
    '_PfahlKosten':              (None, float, None, None),  # Unknown
    '_HerstellDauer':            (None, float, None, None),  # Unknown
    '_MaterialKosten':           (None, float, None, None),  # Unknown
    '_hatWasserAuflast':         (None,  bool, None, None),  # Unknown
    '_laengeImWasser':           (None, float, None, None),  # Unknown
    '_ASQuer':                   (None, float, None, None),  # Unknown
    '_AsLaengs':                 (None, float, None, None),  # Unknown
    '_AsLaengsCalc':             (None, float, None, None),  # Unknown
    '_AsQuerCalc':               (None, float, None, None),  # Unknown
    '_BetonGuete':               (None,   str, None, None),  # Unknown
    '_BewBZWLieferlaenge':       (None, float, None, None),  # Unknown
    # This specific value is known to return -1 in case of HLC calculation error
    '_BewTyp':                   (None, float, None, None),  # Unknown
    '_BohrLaenge':               (None, float, None, None),  # Unknown
    '_EindringTiefe':            (None, float, None, None),  # Unknown
    '_EindringTiefeZug':         (None, float, None, None),  # Unknown
    # Called _nachweisER in old dataset. Should be stored in 0-100 range, 0-1
    '_EzuR':                    (float, float, None, 0.01),
    '_EzuRMin':                  (None, float, None, None),  # Unknown
    '_GesamtBewBZWLieferlaenge': (None, float, None, None),  # Unknown
    '_GesamtBohrLaenge':        (float, float, None, None),
    '_KoteUeberdrueckt':         (None, float, None, None),  # Unknown
    '_MMax':                     (None, float, None, None),  # Unknown
    '_PfahlVolumen':            (float, float, None, None),
    '_QMax':                     (None, float, None, None),  # Unknown
    '_Soll_UK_Pfahl':            (None, float, None, None),  # Unknown
    # Called _deltaL in old dataset
    '_delta_Laenge':            (float, float, None, None),
}


HORIZONTAL_LOAD_CASE_INPUT = {
    'hTabelleName':                (str,  str, None, None),
    'hLastPunkte':                (dict, dict, None, None),
}

# The HLC output is stored in separate namespace, name and list to be handled
# HORIZONTAL_LOAD_CASE_OUTPUT = {}


# Object order is following testAxel.xml file.
HORIZONTAL_LOAD_POINT_INPUT = {
    '_Pname':                    (str,    str, None, None),
    '_Grundwasser':             (float, float, 0.0,  None),
    '_Hgkx':                    (float, float, 0.0,  None),
    '_Hgky':                    (float, float, 0.0,  None),
    '_Hqkx':                    (float, float, 0.0,  None),
    '_Hqky':                    (float, float, 0.0,  None),
    '_Mgkx':                    (float, float, 0.0,  None),
    '_Mgky':                    (float, float, 0.0,  None),
    '_Mqkx':                    (float, float, 0.0,  None),
    '_Mqky':                    (float, float, 0.0,  None),
    '_OKBodenBiegung':          (float, float, 0.0,  None),
    '_gkz':                     (float, float, None, None),
    '_qkz':                     (float, float, None, None),
}


HORIZONTAL_LOAD_POINT_OUTPUT = {
    '_AsLaengs':                (float, float, None, None),
    '_AsLaengsCalc':            (float, float, None, None),
    '_AsLaengsMin':              (None, float, None, None),  # Unknown
    '_AsQuer':                  (float, float, None, None),
    '_AsQuerCalc':              (float, float, None, None),
    '_AsSchubMin':               (None, float, None, None),  # Unknown
    '_Berechnung':               (None,  bool, None, None),  # Unknown
    '_BerechnungOK':             (None, float, None, None),  # Unknown
    '_BewTyp':                    (str,   str, None, None),
    # These 2 values are %, but it is unknown if range is 0-1 or 0-100
    '_EpsO':                    (float, float, None, 0.01),  # O, not 0
    '_Eps1':                    (float, float, None, 0.01),
    '_KoteUeberdrueckt':        (float, float, None, None),
    '_MMax':                    (float, float, None, None),
    '_MxMax':                   (float, float, None, None),
    '_MyMax':                   (float, float, None, None),
    '_Nachweisgruppe':            (int,   int, None, None),
    '_QMax':                    (float, float, None, None),
    '_QxMax':                   (float, float, None, None),
    '_QyMax':                   (float, float, None, None),
    '_wOben':                   (float, float, None, None),
    '_wxOben':                  (float, float, None, None),
    '_wyOben':                  (float, float, None, None),
    '_MdKopf':                   (None, float, None, None),  # Unknown
    '_MdKopfx':                  (None, float, None, None),  # Unknown
    '_MdKopfy':                  (None, float, None, None),  # Unknown
    '_wStrichKopf':              (None, float, None, None),  # Unknown
    '_wStrichKopfx':             (None, float, None, None),  # Unknown
    '_wStrichKopfy':             (None, float, None, None),  # Unknown
}


# Additional key mapping that store name translations between XML and model…
PROJECT_SETTING_KEYS = {
    'name': '_ProjektName',
    'runHorBemessung': '_runHorBemessung',
    'AbtreppungsWinkelRad': '_AbtreppungsWinkelRad',
    'AchsabstandGleicherTiefe': '_AchsabstandGleicherTiefe',
    'AuslastungProzent': '_AuslastungProzent',
    'Beeinflussungsweite': '_Beeinflussungsweite',
    'EAErhoehungProzent': '_EAErhoehungProzent',
    'Exzentrizitaet': '_Exzentrizitaet',
    'FuszBeeinfluszung': '_FuszBeeinfluszung',
    'FuszErhoehungProzent': '_FuszErhoehungProzent',
    'Knicklaenge': '_Knicklaenge',
    'MantelErhoehungProzent': '_MantelErhoehungProzent',
    'MindestEinbindung': '_MindestEinbindung',
    'MindestPfahllaenge': '_MindestPfahllaenge',
    'Norm': '_Norm',
    'Schrittweite': '_Schrittweite',
    'SpitzendruckMittelung': '_SpitzendruckMittelung',
    'WinkelAusProfilen': '_WinkelAusProfilen',
    'gammaDruck': '_gammaDruck',
    'gammaStaendig': '_gammaStaendig',
    'gammaVeraenderlich': '_gammaVeraenderlich',
    'gammaZug': '_gammaZug',
    'gegenRaeumlichenEP': '_gegenRaeumlichenEP',
    'ksNichtReduzieren': '_ksNichtReduzieren',
    'useErhoehung': '_useErhoehung',
    'zulaessigeSetzungCm': '_zulaessigeSetzungCm',
    'BetonZyl': '_BetonZyl',
    'KopfEinbindung': '_KopfEinbindung',
    'MaxLaenge': '_MaxLaenge',
    'ProjektOrt': '_projektLocation',
    'ProjektPLZ': '_projektPostalCode',
    'ProjektStrasze': '_projektStreet',
    'companyAltEmail': '_companyAltEmail',
    'companyAltFax': '_companyAltFax',
    'companyAltLocation': '_companyAltLocation',
    'companyAltName': '_companyAltName',
    'companyAltPhone': '_companyAltPhone',
    'companyAltPostalCode': '_companyAltPostalCode',
    'companyAltStreet': '_companyAltStreet',
    'companyAltLogo': '_companyAltLogo',
    'nameAnlageAuszen': '_nameAnlageAuszen',
    'seitenBezeichnung': '_seitenBezeichnung',
    'seitenStartNummer': '_seitenStartNummer',
    'SeiteVonSeiten': '_SeiteVonSeiten',
    'erstelleUebersichtAuszen': '_erstelleUebersichtAuszen',
    'UebersichtQuer': '_UebersichtQuer',
    'erstelleEinzelnachweise': '_erstelleEinzelnachweise',
    'zeichneNachweislinien': '_zeichneNachweislinien',
    'UKKotenInTabelle': '_UKKotenInTabelle',
    'erstellegrafikAuszen': '_erstellegrafikAuszen',
    'erstellegrafikInnen': '_erstellegrafikInnen',
}


SOIL_PROFILE_INPUT_KEYS = {
    'soil_table_name': '_profilName',
    'pfahlTyp': '_PfahlTyp',
    'grundwasserStand': '_grundwasserStand',
    'startKote': '_startKote',
    'list_soil_layers': 'alleBodenSchichten',
}


SOIL_PROFILE_OUTPUT_KEYS = {
    'pfahlTyp': '_PfahlTyp',
    'list_soil_layers': '_schichten',
}


SOIL_LAYER_INPUT_KEYS = {
    'endKote': '_endKote',
    'bodenArt': '_bodenArt',
    'ESoben': '_ESoben',
    'ESunten': '_ESunten',
    'FuszAbsetzbar': '_FuszAbsetzbar',
    'IstEindringRelevant': '_IstEindringRelevant',
    'MaxElementWeite': '_MaxElementWeite',
    'cuEP': '_cuEP',
    'cuk': '_cuk',
    'deltaVonPhi': '_deltaVonPhi',
    'gammaBoden': '_gammaBoden',
    'gammaStrichBoden': '_gammaStrichBoden',
    'phi': '_phi',
    'qbk002': '_qbk002',
    'qbk003': '_qbk003',
    'qbk01': '_qbk01',
    'qc': '_qc',
    'qsk': '_qsk',
    'bodenSchichtColor': '_bodenSchichtColor'
}


SOIL_LAYER_OUTPUT_KEYS = {
    'PfahlTyp': '_Pfahltyp',
    'usedQsk': '_usedQsk',
    'usedQbk002': '_usedQbk002',
    'usedQbk003': '_usedQbk003',
    'usedQbk01': '_usedQbk01'
}


HORIZONTAL_LOAD_CASE_INPUT_KEYS = {
    'hlc_table_name': 'hTabelleName',
    'list_hlcs': 'hLastPunkte',
}


HORIZONTAL_LOAD_POINT_INPUT_KEYS = {
    'Pname': '_Pname',
    'Grundwasser': '_Grundwasser',
    'Hgkx': '_Hgkx',
    'Hgky': '_Hgky',
    'Hqkx': '_Hqkx',
    'Hqky': '_Hqky',
    'Mgkx': '_Mgkx',
    'Mgky': '_Mgky',
    'Mqkx': '_Mqkx',
    'Mqky': '_Mqky',
    'OKBodenBiegung': '_OKBodenBiegung',
    'gkz': '_gkz',
    'qkz': '_qkz',
}


HORIZONTAL_LOAD_POINT_OUTPUT_KEYS = {
    'AsLaengs': '_AsLaengs',
    'AsLaengsCalc': '_AsLaengsCalc',
    'AsLaengsMin': '_AsLaengsMin',
    'AsQuer': '_AsQuer',
    'AsQuerCalc': '_AsQuerCalc',
    'AsSchubMin': '_AsSchubMin',
    'Berechnung': '_Berechnung',
    'BerechnungOK': '_BerechnungOK',
    'BewTyp': '_BewTyp',
    'Eps0': '_EpsO',
    'Eps1': '_Eps1',
    'KoteUeberdrueckt': '_KoteUeberdrueckt',
    'MMax': '_MMax',
    'MxMax': '_MxMax',
    'MyMax': '_MyMax',
    'Nachweisgruppe': '_Nachweisgruppe',
    'QMax': '_QMax',
    'QxMax': '_QxMax',
    'QyMax': '_QyMax',
    'wOben': '_wOben',
    'wxOben': '_wxOben',
    'wyOben': '_wyOben',
    'MdKopf': '_MdKopf',
    'MdKopfx': '_MdKopfx',
    'MdKopfy': '_MdKopfy',
    'wStrichKopf': '_wStrichKopf',
    'wStrichKopfx': '_wStrichKopfx',
    'wStrichKopfy': '_wStrichKopfy',
}
