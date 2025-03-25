import requests

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from piledesigner.settings import (
    FASTAPI_SERVER_DOMAIN,
    DHPD_TOOL_DOMAIN
)
from projects.services import (
    resize_image,
    remove_old_image
)
from shared.permissions import IsAdmin
from projects.serializers import ProjectCompanyLogoSerializer
from .models import Company
from .serializers import CompanyUpdateWithoutLogoSerializer

class CompanyViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsAdmin]

    def update(self, request, pk=None):
        """
        Update company information.
        """
        try:
            # Fetch the company based on the provided primary key (ID)
            company = Company.objects.get(id=pk)

            # The IsAdmin permission will automatically check if the user has permission
            self.check_object_permissions(request, company)

            # Deserialize and validate the incoming data
            serializer = CompanyUpdateWithoutLogoSerializer(company, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Company.DoesNotExist:
            return Response({"error": "Company not found."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='upload-company-logo')
    def upload_project_company_logo(self, request, pk=None):
        """
        Upload company logo.
        """
        company = Company.objects.get(id=pk)
        self.check_object_permissions(request, company)

        serializer = ProjectCompanyLogoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        try:
            if company.logo != "":
                remove_old_image(company.logo)
            
            if file:
                fastapi_url = (f'{FASTAPI_SERVER_DOMAIN}'
                        f'user/uploadImage/')

                file = resize_image(file)

                files = {"image": file}
                response = requests.post(fastapi_url, files=files, timeout=10)
                company.logo = response.json()["file_name"]
            
            else:
                company.logo = ""
                company.save()
                return Response(
                    {"message": "The company logo is deleted successfully."},
                    status=status.HTTP_200_OK
                )

            company.save()

            return Response(
                {"file": DHPD_TOOL_DOMAIN + 'files/images/' + company.logo},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
