from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User

from piledesigner.settings import (
    DHPD_TOOL_DOMAIN,
    WINDOW_SERVER_IMAGES_DIRECTORY
)

from .models import (
    Project, ProjectSettings, Pile,
    SoilProfile, SoilLayer, HorizontalLoadCase,
    HorizontalLoadPile)


class ProjectSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False
    )
    created_by = serializers.SerializerMethodField()
    modified_by = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'users', 'created_date', 'modified_date',
            'created_by', 'modified_by'
        ]

    def get_created_by(self, obj):
        # Assuming 'created_by' is a foreign key to User model
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'name': obj.created_by.last_name  # Adjust to the actual field name for user's name
            }
        return None

    def get_modified_by(self, obj):
        # Assuming 'modified_by' is a foreign key to User model
        if obj.modified_by:
            return {
                'id': obj.modified_by.id,
                'name': obj.modified_by.last_name  # Adjust to the actual field name for user's name
            }
        return None

    def create(self, validated_data):
        if Project.all_objects.filter(
            company=validated_data['company'],
            name=validated_data['name']
        ).exists():
            raise ValidationError({"error": "A project name is existed!"})

        users = validated_data.pop('users', [])
        project = Project.objects.create(**validated_data)

        # Add users to the project
        for user in users:
            project.users.add(user)

        return project


class ProjectSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSettings
        extra_kwargs = {
            'project': {'required': False},
        }
        exclude = [
            'project'
        ]

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}

        # Fill default values for null fields
        for field in self.Meta.model._meta.get_fields():
            try:
                if hasattr(field, 'name'):
                    # Use the null value if the field is NaN or nan.
                    if str(cleaned_attrs.get(field.name)) in ["NaN", "nan"]:
                        cleaned_attrs[field.name] = None
            except:
                ...

        return cleaned_attrs

    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        if data["companyAltLogo"] != "" and data["companyAltLogo"] is not None \
            and data["companyAltLogo"] not in ["NaN", "nan"]:
            data["companyAltLogo"] = DHPD_TOOL_DOMAIN \
                + 'files/images/' \
                + str(data["companyAltLogo"])

        for key in data.keys():
            data[key] = None if data[key] in ["NaN", "nan"] else data[key]

        return data

class ProjectSettingsWithoutCompLogoSerializer(serializers.ModelSerializer):
    """
    The serializers excludes the company logo in setting.
    """
    class Meta:
        model = ProjectSettings
        extra_kwargs = {
            'project': {'required': False},
        }
        exclude = [
            'project', 'companyAltLogo'
        ]


class ProjectSettingsCalculateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSettings
        extra_kwargs = {
            'project': {'required': False},
        }
        exclude = [
            'project',
            'falsermInner'
        ]

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}
        return cleaned_attrs

    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        # Call the validate method directly with serialized data
        validated_data = self.validate(data)

        try:
            if validated_data["companyAltLogo"] != "":
                validated_data["companyAltLogo"] = WINDOW_SERVER_IMAGES_DIRECTORY \
                    + validated_data["companyAltLogo"]

        except:
            ...

        return validated_data


class PileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pile
        extra_kwargs = {
            'project': {'required': False},
        }
        exclude = [
            'project', 'BetonZyl', 'einzelAusnutzung', 'einzelExzentrizitaet', 'einzelKnickLaenge', 'einzelMaximaleBohrtiefe'
        ]

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}

        # Fill default values for null fields
        for field in self.Meta.model._meta.get_fields():
            try:
                if hasattr(field, 'name'):
                    # Use the null value if the field is NaN or nan.
                    if str(cleaned_attrs.get(field.name)) in ["NaN", "nan"]:
                        cleaned_attrs[field.name] = None
            except:
                ...

        return cleaned_attrs
    
    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        # Call the validate method directly with serialized data
        validated_data = self.validate(data)

        return validated_data


class PileNotValidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pile
        extra_kwargs = {
            'project': {'required': False},
        }
        exclude = [
            'project', 'BetonZyl', 'einzelAusnutzung', 'einzelExzentrizitaet', 'einzelKnickLaenge', 'einzelMaximaleBohrtiefe'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Loop over all fields and set them as not required.
        for field in self.fields.values():
            field.required = False

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}
        return cleaned_attrs
    

class PileCalculateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pile
        extra_kwargs = {
            'project': {'required': False},
        }
        exclude = [
            'project'
        ]

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}
        
        # Define a list of fields that must not be null.
        non_nullable_fields = [
            "Pname",
            "AEHoehe",
            "AlternativeCharakteristischeLastZ",
            "AlternativeDesignLastZ",
            "BetonZyl",
            "BodenProfil",
            "Hochwert",
            "Rechtswert",
            "SollDurchmesser",
            "SollPfahlOberKante"
        ]
        
        errors = []
        for field in non_nullable_fields:
            if cleaned_attrs.get(field) is None:
                errors.append(f"{field} be missing.")
                
        if errors:
            raise serializers.ValidationError({"error": errors})

        # Fill default values for null fields
        for field in self.Meta.model._meta.get_fields():
            if hasattr(field, 'default') and field.default is not None:
                # Use the default value if the field is not provided or is null
                if cleaned_attrs.get(field.name) is None:
                    cleaned_attrs[field.name] = field.default
        
        return cleaned_attrs
    
    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        # Call the validate method directly with serialized data
        validated_data = self.validate(data)

        return validated_data


class SoilLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilLayer
        extra_kwargs = {
            'project': {'required': False},
            'soil_profile': {'required': False},
        }
        exclude = ['project', 'soil_profile']

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}

        # Fill default values for null fields
        for field in self.Meta.model._meta.get_fields():
            try:
                if hasattr(field, 'name'):
                    # Use the null value if the field is NaN or nan.
                    if str(cleaned_attrs.get(field.name)) in ["NaN", "nan"]:
                        cleaned_attrs[field.name] = None
            except:
                ...

        return cleaned_attrs
    
    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        # Call the validate method directly with serialized data
        validated_data = self.validate(data)

        return validated_data


class SoilLayerCalculateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilLayer
        extra_kwargs = {
            'project': {'required': False},
            'soil_profile': {'required': False},
        }
        exclude = ['project', 'soil_profile']

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}

        # Define a list of fields that must not be null.
        non_nullable_fields = [
            "endKote"
        ]
        
        errors = []
        for field in non_nullable_fields:
            if cleaned_attrs.get(field) is None:
                errors.append(f"{field} be missing.")
        
        if errors:
            raise serializers.ValidationError({"error": errors})

        # Fill default values for null fields
        for field in self.Meta.model._meta.get_fields():
            if hasattr(field, 'default') and field.default is not None:
                # Use the default value if the field is not provided or is null
                if cleaned_attrs.get(field.name) is None:
                    cleaned_attrs[field.name] = field.default
                
        return cleaned_attrs

    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        # Call the validate method directly with serialized data
        validated_data = self.validate(data)

        if "bodenSchichtColor" in validated_data:
            color = validated_data["bodenSchichtColor"]
            if color[0] == '#':
                color = color[1:]

            # Convert from RGB to HEX
            if len(color) == 6:  # No alpha channel, add it
                validated_data["bodenSchichtColor"] = f'FF{color}'

            elif len(color) == 8:  # Alpha channel, move it to the start
                validated_data["bodenSchichtColor"] = f'{color[6:]}{color[:6]}'

        return validated_data

class SoilProfileSerializer(serializers.ModelSerializer):
    soil_layers = SoilLayerSerializer(many=True)
    class Meta:
        model = SoilProfile
        fields = [
            'id', 'name', 'grundwasserStand',
            'startKote', 'soil_layers'
        ]

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}
        return cleaned_attrs
    

class SoilProfileCalculateSerializer(serializers.ModelSerializer):
    soil_layers = SoilLayerCalculateSerializer(many=True)
    class Meta:
        model = SoilProfile
        fields = [
            'id', 'name', 'pfahlTyp', 'grundwasserStand',
            'startKote', 'soil_layers'
        ]

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}

        # Define a list of fields that must not be null.
        non_nullable_fields = [
            "grundwasserStand",
            "startKote"
        ]

        errors = []
        for field in non_nullable_fields:
            if cleaned_attrs.get(field) is None:
                errors.append(f"{field} be missing.")
        
        if errors:
            raise serializers.ValidationError({"error": errors})

        # Fill default values for null fields
        for field in self.Meta.model._meta.get_fields():
            if hasattr(field, 'default') and field.default is not None:
                # Use the default value if the field is not provided or is null
                if cleaned_attrs.get(field.name) is None:
                    cleaned_attrs[field.name] = field.default() if callable(field.default) else field.default

        return cleaned_attrs
    
    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        # Call the validate method directly with serialized data
        validated_data = self.validate(data)

        return validated_data


class HLoadPileSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorizontalLoadPile
        exclude = ['project', 'case']

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}

        # Fill default values for null fields
        for field in self.Meta.model._meta.get_fields():
            try:
                if hasattr(field, 'name'):
                    # Use the null value if the field is NaN or nan.
                    if str(cleaned_attrs.get(field.name)) in ["NaN", "nan"]:
                        cleaned_attrs[field.name] = None
            except:
                ...

        return cleaned_attrs
    
    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        # Call the validate method directly with serialized data
        validated_data = self.validate(data)

        return validated_data


class HLoadPileCalculateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorizontalLoadPile
        exclude = ['project', 'case']

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}

        # Define a list of fields that must not be null.
        non_nullable_fields = [
            "Pname",
            "gkz",
            "qkz"
        ]

        errors = []
        for field in non_nullable_fields:
            if cleaned_attrs.get(field) is None:
                errors.append(f"{field} be missing.")

        # Fill default values for null fields
        for field in self.Meta.model._meta.get_fields():
            if hasattr(field, 'default') and field.default is not None:
                # Use the default value if the field is not provided or is null
                if cleaned_attrs.get(field.name) is None:
                    cleaned_attrs[field.name] = field.default
                
        if errors:
            raise serializers.ValidationError({"error": errors})
        
        return cleaned_attrs
    
    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        # Call the validate method directly with serialized data
        validated_data = self.validate(data)

        return validated_data


class HLoadCaseSerializer(serializers.ModelSerializer):
    horizontal_loads = HLoadPileSerializer(many=True)
    class Meta:
        model = HorizontalLoadCase
        fields = ['id', 'name', 'horizontal_loads']

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}
        return cleaned_attrs
    
class HLoadCaseCalculateSerializer(serializers.ModelSerializer):
    horizontal_loads = HLoadPileCalculateSerializer(many=True)
    class Meta:
        model = HorizontalLoadCase
        fields = ['id', 'name', 'horizontal_loads']

    def validate(self, attrs):
        model_field_names = {field.name for field in self.Meta.model._meta.get_fields()}
        cleaned_attrs = {key: value for key, value in attrs.items() if key in model_field_names}
        
        # Fill default values for null fields
        for field in self.Meta.model._meta.get_fields():
            if hasattr(field, 'default') and field.default is not None:
                # Use the default value if the field is not provided or is null
                if cleaned_attrs.get(field.name) is None:
                    cleaned_attrs[field.name] = field.default() if callable(field.default) else field.default

        return cleaned_attrs
    
    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        # Call the validate method directly with serialized data
        validated_data = self.validate(data)

        return validated_data


class ProjectDetailSerializer(serializers.ModelSerializer):
    settings = ProjectSettingsSerializer(source='basic_data_settings', read_only=True)
    piles = PileSerializer(many=True, read_only=True)
    soil_profiles = SoilProfileSerializer(many=True)
    horizontal_loadcases = HLoadCaseSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'company', 'settings', 'piles', 'soil_profiles',
            'horizontal_loadcases', 'created_date', 'modified_date',
            'created_by', 'modified_by'
        ]


class ProjectDetailCalculateSerializer(serializers.ModelSerializer):
    settings = ProjectSettingsCalculateSerializer(source='basic_data_settings', read_only=True)
    piles = PileCalculateSerializer(many=True, read_only=True)
    soil_profiles = SoilProfileCalculateSerializer(many=True)
    horizontal_loadcases = HLoadCaseCalculateSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'company', 'settings', 'piles', 'soil_profiles',
            'horizontal_loadcases', 'created_date', 'modified_date',
            'created_by', 'modified_by'
        ]


class ProjectTableSerializer(serializers.ModelSerializer):
    piles = PileSerializer(many=True)
    soil_profiles = SoilProfileSerializer(many=True)
    horizontal_loadcases = HLoadCaseSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            'piles', 'soil_profiles',
            'horizontal_loadcases',
        ]


class ProjectTableNotValidateSerializer(serializers.ModelSerializer):
    piles = PileNotValidateSerializer(many=True)
    soil_profiles = SoilProfileSerializer(many=True)
    horizontal_loadcases = HLoadCaseSerializer(many=True)

    class Meta:
        model = Project
        fields = [
            'piles', 'soil_profiles',
            'horizontal_loadcases',
        ]


class ProjectImportSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        if not (value.name.endswith('.xml') or value.name.endswith('.xlsx')):
            raise serializers.ValidationError("Only XML and Excel files are supported.")
        return value
    

class ProjectCompanyLogoSerializer(serializers.Serializer):
    file = serializers.FileField(required=False, allow_null=True)

    def validate_file(self, value):
        # The case file is None to delete file.
        if value is None:
            return value

        # Check that the uploaded file's content type starts with 'image/'
        if not value.content_type.startswith('image/'):
            raise serializers.ValidationError("Only image files are supported.")

        return value
