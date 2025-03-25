import json
from math import pi
import requests

import xmlschema
import xmltojson
import JsonToXML
import xmltodict
import pandas as pd
from io import BytesIO
import io
from PIL import Image, ImageOps

from django.db import transaction
from django.core.files.uploadedfile import InMemoryUploadedFile

from piledesigner.settings import (
    BUSINESS_LOGIC_CREDENTIALS,
)
from .dhpd_serializer.mapping import (
    DRIVEN_PILE_TYPES_SYMBOLS
)
from .mapping import (
    XML_KEYS,
    XML_TO_JSON_KEYS_MAPPING,
    JSON_TO_XML_KEYS_MAPPING,
    CUSTOMER_INFO_COMPANY_KEYS_MAPPING,
    USER_INFO_KEYS_MAPPING,
    CALCULATION_PROJECT_SETTING_KEYS,
    PILE_INPUT_KEYS_MAPPING,
    SOIL_LAYER_INPUT_KEYS_MAPPING,
    ORDER_SETTING_KEYS,
    ORDER_PILE_KEYS,
    ORDER_SOIL_LAYER_KEYS,
    ORDER_SOIL_PROFILE_KEYS,
    PILE_KEY_XLSX_2_JSON_MAPPING,
    SOIL_KEY_XLSX_2_JSON_MAPPING,
    H_LOAD_KEY_XLSX_2_JSON_MAPPING,
    PILE_KEY_JSON_2_XLSX_MAPPING,
    SOIL_KEY_JSON_2_XLSX_MAPPING,
    H_LOAD_KEY_JSON_2_XLSX_MAPPING,
    PILE_OUTPUT_KEYS_MAPPING,
    SOIL_LAYER_OUTPUT_KEYS_MAPPING,
    HORIZONTAL_LOAD_POINT_OUTPUT_KEYS_MAPPING,
    HORIZONTAL_LOAD_POINT_INPUT_KEYS_MAPPING,
    EMPTY_XLSX_PILE,
    EMPTY_XLSX_SOIL_LAYER,
    EMPTY_XLSX_H_LOAD
)
from .models import (
    Project,
    ProjectSettings,
    Pile,
    SoilProfile,
    SoilLayer,
    HorizontalLoadCase,
    HorizontalLoadPile
)
from companies.serializers import CompanyCalculateSerializer
from users.serializers import UserSerializer
from piledesigner.settings import (
    WINDOW_SERVER_IMAGES_DIRECTORY,
    FASTAPI_SERVER_DOMAIN
)

def validate_input_excel_file(excel_file) -> bool:
    """
    Validates the Excel file against an master_template.xlsx 
    or master_template.xls template.
    """
    pass


def validate_input_xml_file(input_file) -> list:
    """
    Validates the XML file against an xml_import_template.xsd schema.
    """
    xml_schema_validator = xmlschema.XMLSchema('../test_datas/xml_import_template.xsd')
    errors = []
    try:
        xml_schema_validator.validate(input_file)

    except xmlschema.XMLSchemaValidationError:
        input_file.seek(0)
        # Collect validation errors
        for error in xml_schema_validator.iter_errors(input_file):
            error_details = {
                'message': getattr(error, 'reason', 'Validation error'),  # Default to a generic message
                'path': getattr(error, 'path', []),  # XPath-like path
                'line': getattr(error, 'position', {}).get('line', None),  # Line number if available
                'column': getattr(error, 'position', {}).get('column', None),  # Column number if available
            }
            errors.append(error_details)

    return errors


def validate_calculate_xml_file(input_file_path) -> list:
    """
    Validates the XML file against an xml_calculate_template.xsd schema.

    Return:
    - the list of errors. If the list is empty -> validation is success
    """
    xml_schema_validator = xmlschema.XMLSchema('../test_datas/xml_calculate_template.xsd')
    errors = []
    try:
        xml_schema_validator.validate(input_file_path)

    except xmlschema.XMLSchemaValidationError:
        # Collect validation errors
        for error in xml_schema_validator.iter_errors(input_file_path):
            error_details = {
                'message': getattr(error, 'reason', 'Validation error'),  # Default to a generic message
                'path': getattr(error, 'path', []),  # XPath-like path
                'line': getattr(error, 'position', {}).get('line', None),  # Line number if available
                'column': getattr(error, 'position', {}).get('column', None),  # Column number if available
            }
            errors.append(error_details)

    return errors


def xml_to_json(input_file) -> dict|None:
    """
    Converts an XML file to a JSON object.
    """
    file_content: str = input_file.read().decode('utf-8')

    # Convert XML to JSON
    json_data: str = xmltojson.parse(file_content)

    # Convert JSON string to Python dictionary
    json_object = json.loads(json_data)

    return json_object


def json_to_calculate_xml(project_json_data: dict, user, company) -> str:
    """
    The function to convert project json data in database
    to xml content in order to calculate or export xml file.
    """
    project_json_data.pop('name')

    # Settings
    settings = project_json_data.pop('settings')
    project_json_data['projektInfo'] = settings

    if "default_company_info" in project_json_data['projektInfo'].keys()\
        and project_json_data['projektInfo']['default_company_info']:
        project_json_data['projektInfo']['companyAltName'] = company.name
        project_json_data['projektInfo']['companyAltLocation'] = company.location
        project_json_data['projektInfo']['companyAltStreet'] = company.address
        project_json_data['projektInfo']['companyAltPostalCode'] = company.postal_code
        project_json_data['projektInfo']['companyAltEmail'] = company.email
        project_json_data['projektInfo']['companyAltPhone'] = company.phone
        project_json_data['projektInfo']['companyAltFax'] = company.fax
        project_json_data['projektInfo']['companyAltLogo'] = WINDOW_SERVER_IMAGES_DIRECTORY \
                + company.logo

    project_json_data['projektInfo'] = remove_all_unneccessary_keys(
        project_json_data['projektInfo'],
        CALCULATION_PROJECT_SETTING_KEYS
    )

    project_json_data["projektInfo"] = sort_dict_by_keys(
        project_json_data["projektInfo"],
        ORDER_SETTING_KEYS
    )


    # BusinessLogic Credential:
    project_json_data['userMailAddress'] = BUSINESS_LOGIC_CREDENTIALS['userMailAddress']
    project_json_data['userKey'] = BUSINESS_LOGIC_CREDENTIALS['userKey']
    project_json_data['userKeyHorizontal'] = BUSINESS_LOGIC_CREDENTIALS['userKeyHorizontal']

    # Soil profiles
    soil_profiles = project_json_data.pop('soil_profiles')
    output_soil_profiles = []
    for soil_profile in soil_profiles:
        soil_layers = soil_profile.pop('soil_layers')
        soil_layers = remove_all_unneccessary_keys(
            soil_layers,
            list(SOIL_LAYER_INPUT_KEYS_MAPPING.keys())
        )
        for soil_layer in soil_layers:
            soil_layer = sort_dict_by_keys(soil_layer, ORDER_SOIL_LAYER_KEYS)
        soil_profile['_profilName'] = soil_profile.pop('name')
        soil_profile['alleBodenSchichten'] = {
            'BodenSchichtDaten': soil_layers
        }
        soil_profile = sort_dict_by_keys(soil_profile, ORDER_SOIL_PROFILE_KEYS)
        output_soil_profiles.append(soil_profile)
    project_json_data['boden'] = {
        'alleBodenProfile': {
            'BodenProfilDaten': output_soil_profiles
        }
    }

    # Piles
    piles = project_json_data.pop('piles')
    piles = remove_all_unneccessary_keys(piles, list(PILE_INPUT_KEYS_MAPPING.keys()))
    output_piles = []
    for pile in piles:
        pile = sort_dict_by_keys(pile, ORDER_PILE_KEYS)
        output_piles.append(pile)
    project_json_data['pfaehle'] = {
        'LastPunktInputList': {
            'LastPunktInput': output_piles
        }
    }

    # HLoad Cases
    hload_cases = project_json_data.pop('horizontal_loadcases')
    for hload_case in hload_cases:
        hloads = hload_case.pop('horizontal_loads')
        hloads = remove_all_unneccessary_keys(hloads, list(HORIZONTAL_LOAD_POINT_INPUT_KEYS_MAPPING.keys()))
        hload_case['hTabelleName'] = hload_case.pop('name')
        hload_case['hLastPunkte'] = {
            'HLastPunktInput': hloads
        }
    project_json_data['hLasten'] = {
        'hTabellen': {
            'HLastInputTabelle': hload_cases
        }
    }

    # _userInfo
    user_serializer = UserSerializer(user)
    project_json_data['_userInfo'] = user_serializer.data
    project_json_data['_userInfo'] = map_keys(
        project_json_data['_userInfo'],
        USER_INFO_KEYS_MAPPING
    )

    # _customerInfo
    company_serializer = CompanyCalculateSerializer(company)
    project_json_data['_customerInfo'] = company_serializer.data
    project_json_data['_customerInfo'] = map_keys(
        project_json_data['_customerInfo'],
        CUSTOMER_INFO_COMPANY_KEYS_MAPPING
    )
    project_json_data['_customerInfo']['_companyInvoiceStyle'] = company_serializer.data['name']


    project_json_data = map_keys(project_json_data, JSON_TO_XML_KEYS_MAPPING)
    project_json_data = remove_all_unneccessary_keys(project_json_data)
    project_json_data["@xmlns"] = "http://schemas.datacontract.org/2004/07/DHPD"
    project_json_data["@xmlns:i"] = "http://www.w3.org/2001/XMLSchema-instance"


    xml_content = xmltodict.unparse({"InputDaten": project_json_data}, pretty=True)
    return xml_content


def json_to_xml_file(json_object: dict, xml_file_name: str) -> bool:
    """
    Converts a JSON object to an XML file path as string.
    """
    try:
        JsonToXML.fromFiletoFile(json_object,"{xml_file_name}.xml")
        return True

    except Exception:
        return False


def scale_float_value(value: float, scale: float, reversed = False) -> float:
    """
    Scale the value with input scale_value.
    
    Attributes:
        - value (float)  : 
        - scale (float)  : 
        - reversed (bool): if True, it's used for the case import xml,
        we need revert unit.
    """
    if str(value) == "NaN":
        return value

    if reversed:
        return round(float(value)/scale, 2)
    return float(value)*scale


def input_xml_content_unit_convert(
        xml_content: dict, reversed: bool = False
    ) -> dict:
    """
    Convert unit of some fields before sending to Business Logic.

    Attribute:
        - xml_content (dict): xml content as json dictionary.
        - reversed (bool)   : if True, it's used for the case import xml,
        we need revert unit.

    Return:
        - dict
    """
    setting_convert_scales = {
        "AbtreppungsWinkelRad": pi/180,
        "MaxLaengs"           : 0.001,
        "MaxBuegel"           : 0.001,
        "MinLaengsAbstand"    : 0.001,
        "Betondeckung"        : 0.001,
        "MvonMaxfuerSchub"    : 0.01
    }

    pile_convert_scales = {
        "prozentualerMantelAnteil": 0.01
    }

    soil_layer_scales = {
        "ESoben"         : 1000,
        "ESunten"        : 1000,
        "MaxElementWeite": 0.01,
        "phi"            : pi/180,
        "qsk"            : 1000,
        "qskStern"       : 1000,
        "qbk002"         : 1000,
        "qbk003"         : 1000,
        "qbk01"          : 1000
    }

    # Project settings:
    if "settings" in xml_content.keys():
        for scale in setting_convert_scales.items():
            try:
                xml_content["settings"][scale[0]] = scale_float_value(
                    xml_content["settings"][scale[0]], scale[1], reversed
                )
            except:
                ...

    # Piles:
    if "piles" in xml_content.keys():
        for pile in xml_content["piles"]:
            for scale in pile_convert_scales.items():
                try:
                    pile[scale[0]] = scale_float_value(
                        pile[scale[0]], scale[1], reversed
                    )
                except:
                    ...

    # Soil layer:
    if "soil_profiles" in xml_content.keys():
        for soil_profile in xml_content["soil_profiles"]:
            if "soil_layers" in soil_profile:
                for soil_layer in soil_profile["soil_layers"]:
                    for scale in soil_layer_scales.items():
                        try:
                            soil_layer[scale[0]] = scale_float_value(
                                soil_layer[scale[0]], scale[1], reversed
                            )
                        except:
                            ...
    return xml_content


def output_xml_content_unit_convert(
        xml_content: dict, reversed: bool = False
    ) -> dict:
    """
    Convert unit of some fields before sending to Business Logic.

    Attribute:
        - xml_content (dict): xml content as json dictionary.
        - reversed (bool)   : if True, it's used for the case import xml,
        we need revert unit.

    Return:
        - dict
    """
    soil_layer_scales = {
        "_usedQsk"   : 0.001,
        "_usedQbk002": 0.001,
        "_usedQbk003": 0.001,
        "_usedQbk01" : 0.001,
    }

    pile_convert_scales = {
        "_EzuR": 100
    }

    # Piles:
    try:
        for pile in xml_content["pfaehle"]["LastPunktOutputList"]["LastPunktOutput"]:
            for scale in pile_convert_scales.items():
                try:
                    pile[scale[0]] = scale_float_value(
                        float(pile[scale[0]]), scale[1], reversed
                    )
                except:
                    ...
    except:
        ...

    # Soil layer:
    try:
        for soil_profile in xml_content["BodenNutzung"]["BodenNutzungDict"]["a:KeyValueOfstringBodenNutzungOutputDB_PsWP3v"]:
            try:
                for soil_layer in soil_profile["a:Value"]["_schichten"]["BodenSchichtNutzung"]:
                    for scale in soil_layer_scales.items():
                        try:
                            soil_layer[scale[0]] = scale_float_value(
                                float(soil_layer[scale[0]]), scale[1], reversed
                            )
                        except:
                            ...
            except:
                ...
    except:
        ...

    return xml_content


def process_driven_pile(
        xml_content: dict
    ) -> dict:
    """
    Process when choosing driven pile.
    Need to change to qsk_stern
    """
    try:
        # Step 1: Get Soil profile including the driven piles.
        driven_soil_profiles = []
        for pile in xml_content["piles"]:
            if pile["PfahlTyp"] in DRIVEN_PILE_TYPES_SYMBOLS:
                driven_soil_profiles.append(pile["BodenProfil"])

        # Step 2: Switch to qsk_stern for the soil profiles applied
        # for the driven piles.
        if driven_soil_profiles:
            for soil_profile in xml_content["soil_profiles"]:
                for soil_layer in soil_profile["soil_layers"]:
                    if soil_profile["name"] in driven_soil_profiles:
                        soil_layer["qskStern"] = soil_layer["qsk"]
                        soil_layer["qsk"] = 0
                    else:
                        soil_layer["qskStern"] = 0

    except:
        ...

    return xml_content


def process_import_driven_pile(
        xml_content: dict
    ) -> dict:
    """
    Process when import driven pile.
    Need to map qsk and qsk_stern to qsk
    """
    try:
        for soil_profile in xml_content["soil_profiles"]:
            for soil_layer in soil_profile["soil_layers"]:
                if soil_layer["qsk"] == "NaN" or soil_layer["qsk"] == 0:
                    soil_layer["qsk"] = soil_layer["qskStern"]
                    soil_layer["qskStern"] = None

    except:
        ...

    return xml_content


def output_xml_content_round_2_decimal_digits(xml_content: dict) -> dict:
    """
    Function round float number in output xml content to only 2
    decimal digits.
    """
    # Piles:
    try:
        for pile in xml_content["pfaehle"]["LastPunktOutputList"]["LastPunktOutput"]:
            for key in pile.keys():
                try:
                    pile[key] = round(float(pile[key]), 2)
                except:
                    ...
    except:
        ...

    # Soil layer:
    try:
        for soil_profile in xml_content["BodenNutzung"]["BodenNutzungDict"]["a:KeyValueOfstringBodenNutzungOutputDB_PsWP3v"]:
            try:
                for soil_layer in soil_profile["a:Value"]["_schichten"]["BodenSchichtNutzung"]:
                    for key in soil_layer.keys():
                        try:
                            soil_layer[key] = round(float(soil_layer[key]), 2)
                        except:
                            ...
            except:
                ...
    except:
        ...

    return xml_content


def map_keys(data: dict, mapping: dict = XML_TO_JSON_KEYS_MAPPING) -> dict|list:
    """
    Recursively maps keys in a multi-level dictionary based on a mapping dictionary.

    :param data: The input dictionary with keys to be mapped.
    :param mapping: A dictionary where keys are old keys and values are new keys.
    :return: A new dictionary with keys mapped based on the mapping dictionary.
    """
    if isinstance(data, dict):
        # Create a new dictionary with mapped keys
        return {
            mapping.get(key, key): map_keys(value, mapping)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        # If the value is a list, apply the mapping to each item
        return [map_keys(item, mapping) for item in data]
    else:
        # Return the value directly if it's neither a dict nor a list
        return data


def validate_project_name(project_name: str, company) -> bool:
    """
    The function check to see whether project name is exist.

    Attribute:
    - project_name: str
    - company: Company

    Return:
    - bool: True if not exist, False if exist.
    """
    return not Project.all_objects.filter(
        name=project_name,
        company=company
    ).exists()


def update_project_setting_data(json_setting_data: dict, project: Project) -> bool:
    """
    The function update the setting data for project.

    Attributes:
        - json_setting_data: dict
        - project: Project model object
    Return: bool
    """

    try:
        with transaction.atomic():
            # Update or create settings
            if 'settings' in json_setting_data.keys():
                json_setting_data = json_setting_data['settings']
            
            if 'companyAltLogo' in json_setting_data.keys():
                json_setting_data.pop('companyAltLogo')

            if 'name' in json_setting_data.keys():
                if project.name != json_setting_data['name']\
                    and not validate_project_name(json_setting_data['name'],project.company):
                    raise Exception("A new project name is existed!")
                project.name = json_setting_data['name']
                project.save()

            for key in json_setting_data.keys():
                if json_setting_data[key] == "true":
                    json_setting_data[key] = True
                if json_setting_data[key] == "false":
                    json_setting_data[key] = False

            allowed_fields = {field.name for field in ProjectSettings._meta.concrete_fields}
            filtered_data = {key: value for key, value in json_setting_data.items() if key in allowed_fields}
            ProjectSettings.objects.update_or_create(
                project=project,
                defaults=filtered_data
            )
        return True

    except Exception as e:
        raise Exception(e) from e


def update_project_table_data(
        json_table_datas: dict,
        project: Project,
        is_import_data: bool = True
    ) -> bool:
    """
    The function store or update table data

    Attributes:
        - json_table_datas: dict
        - project: Project model object
        - is_import_data: bool (if True, the function will
        delete all the old and create the new)
    Return: bool
    """
    # Get the project data from the request
    pile_data = json_table_datas.get('piles', [])
    soil_profile_data = json_table_datas.get('soil_profiles', [])
    horizontal_loadcases = json_table_datas.get('horizontal_loadcases', [])

    try:
        with transaction.atomic():

            if is_import_data:
                Pile.objects.filter(project=project).delete()
                SoilProfile.objects.filter(project=project).delete()
                SoilLayer.objects.filter(project=project).delete()
                HorizontalLoadCase.objects.filter(project=project).delete()
                HorizontalLoadPile.objects.filter(project=project).delete()

            # Update or Create Pile
            pile_ids = []
            for pile in pile_data:
                try:
                    pile_id = pile.pop('id', None)  # Optional ID for updating
                    pile_ids.append(pile_id)

                    allowed_fields = {field.name for field in Pile._meta.concrete_fields}
                    filtered_data = {key: value for key, value in pile.items() if key in allowed_fields}
                    Pile.objects.update_or_create(
                        id=pile_id, project=project, defaults=filtered_data
                    )
                except:
                    ...

            # Update or Create SoilProfile
            soil_profile_ids = []
            soil_layer_ids = []
            for soil_profile in soil_profile_data:
                try:
                    soil_profile_id = soil_profile.pop('id', None)  # Optional ID for updating
                    soil_profile_ids.append(soil_profile_id)
                    soil_layer_data = soil_profile.pop('soil_layers', [])
                    if 'soil_table_name' in soil_profile.keys():
                        soil_profile['name'] = soil_profile.pop('soil_table_name')

                    allowed_fields = {field.name for field in SoilProfile._meta.concrete_fields}
                    filtered_data = {key: value for key, value in soil_profile.items() if key in allowed_fields}
                    profile, created = SoilProfile.objects.update_or_create(
                        id=soil_profile_id, project=project, defaults=filtered_data
                    )

                    # Update SoilLayer for this profile
                    for layer in soil_layer_data:
                        try:
                            layer_id = layer.pop('id', None)  # Optional ID for updating
                            soil_layer_ids.append(layer_id)
                            layer['FuszAbsetzbar'] = True if str(layer['FuszAbsetzbar']) in ["true", "True", "1"] else False
                            layer['IstEindringRelevant'] = True if str(layer['IstEindringRelevant']) in ["true", "True", "1"] else False

                            allowed_fields = {field.name for field in SoilLayer._meta.concrete_fields}
                            filtered_data = {key: value for key, value in layer.items() if key in allowed_fields}
                            filtered_data = {key: value if value != "NaN" else None for key, value in filtered_data.items()}
                            SoilLayer.objects.update_or_create(
                                id=layer_id, project=project, soil_profile=profile, defaults=filtered_data
                            )
                        except:
                            ...
                except Exception as e:
                    ...

            # Update HorizontalLoadCase
            hload_case_ids = []
            hload_ids = []
            for h_load_case in horizontal_loadcases:
                try:
                    h_load_case_id = h_load_case.pop('id', None)  # Optional ID for updating
                    hload_case_ids.append(h_load_case_id)
                    horizontal_loads = h_load_case.pop('horizontal_loads', [])
                    if 'hlc_table_name' in h_load_case.keys():
                        h_load_case['name'] = h_load_case.pop('hlc_table_name')
                    case, created = HorizontalLoadCase.objects.update_or_create(
                        id=h_load_case_id, project=project, defaults=h_load_case
                    )

                    # Update HorizontalLoadPile
                    for h_load in horizontal_loads:
                        h_load_id = h_load.pop('id', None)  # Optional ID for updating
                        hload_ids.append(h_load_id)

                        allowed_fields = {field.name for field in HorizontalLoadPile._meta.concrete_fields}
                        filtered_data = {key: value for key, value in h_load.items() if key in allowed_fields}
                        HorizontalLoadPile.objects.update_or_create(
                            id=h_load_id, project=project, case=case, defaults=filtered_data
                        )
                except:
                    ...
            return True

    except Exception as e:
        raise Exception(e) from e


def restructure_json_data(json_data: dict) -> dict:
    """
    The function restructure the input json data
    to be correct with expected structure.
    The input comes from XML Import Functionality.
    """
    json_data           = json_data['InputDaten']
    project_settings    = json_data['projektInfo']

    try:
        soil_profiles = json_data['boden']['alleBodenProfile']['BodenProfilDaten']
    except:
        ...
        
    try:
        piles = json_data['pfaehle']['LastPunktInputList']['LastPunktInput']
    except:
        ...

    try:
        hload_cases = json_data['hLasten']['hTabellen']['HLastInputTabelle']
    except:
        ...

    project_data_json = {}

    # Load project settings
    project_data_json['settings'] = {
        XML_TO_JSON_KEYS_MAPPING.get(k, k): v for k, v in project_settings.items()
    }

    try:
        # Load project piles
        project_data_json['piles'] = []
        piles = [piles] if not isinstance(piles, list) else piles
        for row_index, pile in enumerate(piles):
            try:
                pile_json = {
                    XML_TO_JSON_KEYS_MAPPING.get(k, k): v for k, v in pile.items()
                }
                pile_json["row_index"] = row_index
                project_data_json['piles'].append(dict(pile_json))

            except:
                pass
    except:
        ...

    try:
        # Load project soil profiles
        project_data_json['soil_profiles'] = []
        soil_profiles = [soil_profiles] if not isinstance(soil_profiles, list) else soil_profiles
        for soil_profile in soil_profiles:
            try:
                soil_profile_json = {
                    XML_TO_JSON_KEYS_MAPPING.get(k, k): v for k, v in soil_profile.items()
                }
                soil_profile_json['soil_layers'] = []

                soil_layers = soil_profile['alleBodenSchichten']['BodenSchichtDaten']
                soil_layers = [soil_layers] if not isinstance(soil_layers, list) else soil_layers
                for row_index, soil_layer in enumerate(soil_layers):
                    try:
                        soil_layer_json = {
                            XML_TO_JSON_KEYS_MAPPING.get(k, k): v for k, v in soil_layer.items()
                        }

                        # Convert color from HEX to RGB
                        if "bodenSchichtColor" in soil_layer_json:
                            color = soil_layer_json["bodenSchichtColor"]
                            if color[:2] == 'FF':
                                soil_layer_json["bodenSchichtColor"] = color[2:]
                            else:
                                soil_layer_json["bodenSchichtColor"] = f'{color[2:]}{color[:2]}'
                        
                        soil_layer_json["row_index"] = row_index
                        soil_profile_json['soil_layers'].append(dict(soil_layer_json))
                    except:
                        ...
                soil_profile_json.pop('alleBodenSchichten')
                project_data_json['soil_profiles'].append(dict(soil_profile_json))

            except:
                pass
    except:
        ...

    try:
        # Load project hload cases
        project_data_json['horizontal_loadcases'] = []
        hload_cases = [hload_cases] if not isinstance(hload_cases, list) else hload_cases
        for hload_case in hload_cases:
            try:
                hload_case_json = {
                    XML_TO_JSON_KEYS_MAPPING.get(k, k): v for k, v in hload_case.items()
                }
                hload_case_json['horizontal_loads'] = []

                horizontal_loads = hload_case['list_hlcs']['HLastPunktInput']
                horizontal_loads = [horizontal_loads] if not isinstance(horizontal_loads, list) else horizontal_loads
                for row_index, horizontal_load in enumerate(horizontal_loads):
                    try:
                        horizontal_load_json = {
                            XML_TO_JSON_KEYS_MAPPING.get(k, k): v for k, v in horizontal_load.items()
                        }
                        horizontal_load_json["row_index"] = row_index
                        hload_case_json['horizontal_loads'].append(dict(horizontal_load_json))
                    except:
                        ...
                hload_case_json.pop('list_hlcs')
                project_data_json['horizontal_loadcases'].append(dict(hload_case_json))

            except:
                pass
    except:
        ...

    return project_data_json


def remove_all_unneccessary_keys(json_data: dict, keep_keys: list = XML_KEYS) -> dict|list:
    if isinstance(json_data, dict):
        # Process dictionary
        return {
            key: remove_all_unneccessary_keys(value, keep_keys)
            for key, value in json_data.items()
            if key in keep_keys
        }
    elif isinstance(json_data, list):
        # Process list
        return [remove_all_unneccessary_keys(item, keep_keys) for item in json_data]
    else:
        # Base case: Return the value if it's neither a dict nor a list
        return json_data


def sort_dict_by_keys(data: dict, key_order: list, include_unlisted=True, default=None) -> dict:
    """
    Sorts a dictionary based on a list of keys.

    Args:
        data (dict): The dictionary to sort.
        key_order (list): The desired order of keys.
        include_unlisted (bool): Whether to include keys not in the key_order.
        default: Default value for missing keys in key_order.

    Returns:
        dict: A new dictionary sorted by the key_order.
    """
    # Include keys from key_order, setting default for missing ones
    sorted_data = {key: data.get(key, default) for key in key_order}

    # Optionally include keys not in key_order
    if include_unlisted:
        unlisted_keys = {key: value for key, value in data.items() if key not in key_order}
        sorted_data.update(unlisted_keys)

    return sorted_data


def xlsx_to_json(input_file) -> dict:
    """
    Reads all sheets from an Excel file in-memory.

    :param file: In-memory file (e.g., from Django request.FILES).
    :return: Dictionary with sheet names as keys and DataFrames as values.
    """
    try:
        # Read all sheets into a dictionary
        all_sheets = pd.read_excel(BytesIO(input_file.read()), sheet_name=None)
        json_data = {sheet_name: df for sheet_name, df in all_sheets.items()}
        sheet_names = list(json_data.keys())

        project_data_json = {}

        # pile data
        project_data_json['piles'] = []
        try:
            pile_sheets = json_data[sheet_names[0]]
            pile_sheets = pile_sheets.dropna(subset=['Lastpunkt'])
            pile_sheets = pile_sheets.astype(object).where(pd.notnull(pile_sheets), None)
            pile_sheets_json = pile_sheets.to_dict(orient="records")
            for row_index, pile in enumerate(pile_sheets_json):
                pile = remove_all_unneccessary_keys(pile, list(PILE_KEY_XLSX_2_JSON_MAPPING.keys()))
                pile = map_keys(pile, PILE_KEY_XLSX_2_JSON_MAPPING)
                pile["row_index"] = row_index
                project_data_json['piles'].append(pile)
        except:
            ...
        
        # soil_profiles:
        ## Get the last soil profile name:
        end_soil_profile_index = 0
        sheet_len = len(sheet_names)
        for idx, sheet in enumerate(reversed(sheet_names)):
            if sheet[-5:]=='-Info':
                end_soil_profile_index = sheet_len-idx-1
                break

        ## Get all soil profiles:
        project_data_json['soil_profiles'] = []
        for sheet_index in range(1,end_soil_profile_index,2):
            try:
                # Soil layers
                soil_layers = json_data[sheet_names[sheet_index]]
                try:
                    soil_layers = soil_layers.dropna(subset=['Endkote'])
                    soil_layers = soil_layers.astype(object).where(pd.notnull(soil_layers), None)
                except:
                    ...
                soil_layers_json = soil_layers.to_dict(orient='records')

                # Soil profile

                soil_profile = json_data[sheet_names[sheet_index+1]]
                try:
                    soil_profile = soil_profile.dropna(subset=['Grundwasserstand'])
                    soil_profile = soil_profile.astype(object).where(pd.notnull(soil_profile), None)
                    soil_profile = soil_profile.to_dict(orient='records')[0]
                except:
                    ...
                soil_profile['soil_layers'] = soil_layers_json
                try:
                    soil_profile = remove_all_unneccessary_keys(soil_profile, list(SOIL_KEY_XLSX_2_JSON_MAPPING.keys()))
                    soil_profile = map_keys(soil_profile, SOIL_KEY_XLSX_2_JSON_MAPPING)
                except:
                    ...

                if not isinstance(soil_profile, dict):
                    soil_profile = {
                        'soil_layers': [],
                        'grundwasserStand': None,
                        'startKote': None
                    }
                soil_profile['pfahlTyp'] = 4 # This field is hard coded for now. Need ask Dr. Hilla to clarify.
                soil_profile['name'] = sheet_names[sheet_index]
                for row_index, soil_layer in enumerate(soil_profile['soil_layers']):
                    soil_layer['row_index'] = row_index

                project_data_json['soil_profiles'].append(soil_profile)
            
            except:
                ...
            # print(project_data_json['soil_profiles'])

        # Horizontal Loads
        project_data_json['horizontal_loadcases'] = []
        for sheet_index in range(end_soil_profile_index+1,len(sheet_names)):
            try:
                # Horizontal loads
                h_loads = json_data[sheet_names[sheet_index]]
                h_loads = h_loads.dropna(subset=['Lastpunkt'])
                h_loads = h_loads.astype(object).where(pd.notnull(h_loads), None)
                h_loads = h_loads.to_dict(orient='records')
                h_loads = remove_all_unneccessary_keys(h_loads, list(H_LOAD_KEY_XLSX_2_JSON_MAPPING.keys()))
                h_loads = map_keys(h_loads, H_LOAD_KEY_XLSX_2_JSON_MAPPING)
                for row_index, h_load in enumerate(h_loads):
                    h_load['row_index'] = row_index

                # horizontal load case
                hload_case = {
                    "name": sheet_names[sheet_index],
                    "horizontal_loads": h_loads
                }
                project_data_json['horizontal_loadcases'].append(hload_case)
            except:
                ...

        return project_data_json

    except Exception as e:
        return None


def json_to_xlsx_structure(json_object: dict) -> dict:
    """
    The function convert project data json object
    to xlsx structure with sheets as json object.
    """
    output_xlsx = {}

    # output_xlsx['Project info'] = [{
    #     "Name": json_object['settings']['name'],
    #     "Language": "de"
    # }]

    output_xlsx['Pfahltabelle'] = []

    # pile
    if not json_object['piles']:
        output_xlsx['Pfahltabelle'].append(EMPTY_XLSX_PILE)
    for pile in json_object['piles']:
        pile = map_keys(pile, PILE_KEY_JSON_2_XLSX_MAPPING)
        pile = remove_all_unneccessary_keys(pile, list(PILE_KEY_XLSX_2_JSON_MAPPING.keys()))
        pile = sort_dict_by_keys(
            pile,
            list(PILE_KEY_XLSX_2_JSON_MAPPING.keys())
        )
        output_xlsx['Pfahltabelle'].append(pile)

    # soil
    for soil_profile in json_object['soil_profiles']:
        output_xlsx[soil_profile['name']] = []
        if not soil_profile['soil_layers']:
            output_xlsx[soil_profile['name']].append(EMPTY_XLSX_SOIL_LAYER)
        for soil_layer in soil_profile['soil_layers']:
            soil_layer = map_keys(soil_layer, SOIL_KEY_JSON_2_XLSX_MAPPING)
            soil_layer = remove_all_unneccessary_keys(soil_layer, list(SOIL_KEY_XLSX_2_JSON_MAPPING.keys()))
            soil_layer = sort_dict_by_keys(
                soil_layer,
                list(SOIL_KEY_XLSX_2_JSON_MAPPING.keys())[4:]
            )
            output_xlsx[soil_profile['name']].append(soil_layer)
            
        output_xlsx[soil_profile['name']+"-Info"] = [{
            "Grundwasserstand": soil_profile['grundwasserStand'],
            "Startkote": soil_profile['startKote']
        }]

    # horizontal load
    for h_load_case in json_object['horizontal_loadcases']:
        output_xlsx[h_load_case['name']] = []
        if not h_load_case['horizontal_loads']:
            output_xlsx[h_load_case['name']].append(EMPTY_XLSX_H_LOAD)
        for h_load in h_load_case['horizontal_loads']:
            h_load = map_keys(h_load, H_LOAD_KEY_JSON_2_XLSX_MAPPING)
            h_load = remove_all_unneccessary_keys(h_load, list(H_LOAD_KEY_XLSX_2_JSON_MAPPING.keys()))
            h_load = sort_dict_by_keys(
                h_load,
                list(H_LOAD_KEY_XLSX_2_JSON_MAPPING.keys())
            )
            output_xlsx[h_load_case['name']].append(h_load)

    return output_xlsx


def delete_calculation_output_data(project):
    """
    The function make all output data to be empty if calculation meet error.
    """
    try:
        piles = Pile.objects.filter(project=project)
        for pile in piles:
            for key,_val in PILE_OUTPUT_KEYS_MAPPING.items():
                try:
                    pile.__setattr__(key, None)
                except:
                    ...
            pile.save()
    except:
        ...

    try:
        soil_profs = SoilProfile.objects.filter(project=project)
        for soil_prof in soil_profs:
            current_soil_layers = SoilLayer.objects.filter(soil_profile=soil_prof).order_by("row_index")
            for current_soil in current_soil_layers:
                try:
                    for key,val in SOIL_LAYER_OUTPUT_KEYS_MAPPING.items():
                        try:
                            current_soil.__setattr__(key, None)
                            current_soil.save()
                        except Exception as e:
                            ...
                except:
                    ...
    except:
        ...

    try:
        h_cases = HorizontalLoadCase.objects.filter(project=project)
        for h_case in h_cases:
            hloads = HorizontalLoadPile.objects.filter(case=h_case).order_by("row_index")
            for hload in hloads:
                try:
                    for key,val in HORIZONTAL_LOAD_POINT_OUTPUT_KEYS_MAPPING.items():
                        try:
                            hload.__setattr__(key, None)
                            hload.save()
                        except Exception as e:
                            ...
                except:
                    ...
    except:
        ...


def resize_image(uploaded_image, size=(100, 100)):
    """
    The function resize the uploaded image with fixed size
    before storing in CDN.
    """

    # Open the uploaded image
    img = Image.open(uploaded_image)
    
    # Convert to RGB if necessary (e.g., PNG with transparency might be in RGBA)
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    
    # Crop and resize the image to a square using ImageOps.fit.
    # This will crop the image (centered by default) and resize it to `size`.
    img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
    
     # Determine the image format.
    # If the original format is not available, default to JPEG.
    image_format = img.format if img.format else "JPEG"
    
    # JPEG does not support transparency, so if we're saving as JPEG and the image has an alpha channel, convert it to RGB.
    if image_format.upper() == "JPEG" and img.mode == "RGBA":
        img = img.convert("RGB")
    
    # Save the resulting image to an in-memory file
    output_io = io.BytesIO()
    img.save(output_io, format=image_format)
    output_io.seek(0)
    
    # Create an InMemoryUploadedFile so that Django can handle it like a normal uploaded file.
    resized_image = InMemoryUploadedFile(
        output_io,
        None,  # field name (optional)
        uploaded_image.name,
        uploaded_image.content_type,
        output_io.getbuffer().nbytes,
        None
    )

    return resized_image


def remove_old_image(old_image_file_name: str):
    """
    The function requests to fastAPI to delete the old image.
    """
    fastapi_url = (f'{FASTAPI_SERVER_DOMAIN}'
                       f'user/removeOldImage/')
    payload = {"file_name": old_image_file_name}
    headers = {"Content-Type": "application/json"}

    try:
        requests.post(fastapi_url, data=json.dumps(payload), headers=headers, timeout=10)

    except:
        ...
