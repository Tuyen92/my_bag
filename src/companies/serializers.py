from rest_framework import serializers

from companies.models import Company
from piledesigner.settings import (
    DHPD_TOOL_DOMAIN,
    WINDOW_SERVER_IMAGES_DIRECTORY
)

class CompanyDefaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['name']

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'address', 'location',
            'postal_code', 'email', 'logo', 'phone',
            'fax'
        ]

    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        try:
            if data["logo"] != "":
                data["logo"] = DHPD_TOOL_DOMAIN + 'files/images/' \
                    + data["logo"]

        except:
            ...

        return data
    

class CompanyUpdateWithoutLogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'address', 'location',
            'postal_code', 'email', 'phone',
            'fax'
        ]


class CompanyCalculateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'address', 'location',
            'postal_code', 'email', 'logo', 'phone',
            'fax'
        ]

    def to_representation(self, instance):
        """
        Invoke validate() during serialization.
        """
        data = super().to_representation(instance)

        try:
            if data["logo"] != "":
                data["logo"] = WINDOW_SERVER_IMAGES_DIRECTORY \
                    + data["logo"]

        except:
            ...

        return data
