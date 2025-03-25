import xmltodict
import pandas as pd
import requests
from io import BytesIO

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.http import HttpResponse

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied

from shared.permissions import IsAdminOrManager, IsAdminManagerOrAssigned
from companies.models import Company
from users.serializers import UserSerializer
from .models import (
    Project, ProjectSettings, Pile,
    SoilProfile, SoilLayer, UserProjectRel,
    HorizontalLoadCase, HorizontalLoadPile)
from .serializers import (
    ProjectSerializer,
    ProjectSettingsWithoutCompLogoSerializer,
    ProjectDetailSerializer,
    ProjectDetailCalculateSerializer,
    ProjectImportSerializer,
    ProjectCompanyLogoSerializer,
    ProjectTableSerializer,
    ProjectTableNotValidateSerializer
)
from .mapping import (
    PILE_OUTPUT_KEYS_MAPPING,
    SOIL_LAYER_OUTPUT_KEYS_MAPPING,
    HORIZONTAL_LOAD_POINT_OUTPUT_KEYS_MAPPING
)
from .services import (
    map_keys,
    xml_to_json,
    validate_input_xml_file,
    validate_calculate_xml_file,
    update_project_table_data,
    update_project_setting_data,
    restructure_json_data,
    json_to_calculate_xml,
    xlsx_to_json,
    json_to_xlsx_structure,
    delete_calculation_output_data,
    input_xml_content_unit_convert,
    output_xml_content_unit_convert,
    process_driven_pile,
    process_import_driven_pile,
    output_xml_content_round_2_decimal_digits,
    resize_image,
    remove_old_image
)
from piledesigner.settings import (
    FASTAPI_SERVER_DOMAIN,
    DHPD_TOOL_DOMAIN,
    DHPD_SERVER_1,
    DHPD_SERVER_2
)

PREFIX_DELETED = " - deleted"

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]  # You can change this based on your permission logic

    def get_queryset(self):
        """
        Limit the queryset based on the user's role.
        - Admins can see all projects in the company.
        - Employees can only see projects they are assigned to.
        """
        company_id = self.kwargs.get('company_id')
        user = self.request.user
        queryset = Project.objects.filter(company__id=company_id)

        # If the user is an 'Employee', filter projects to only those the user is assigned to
        user_role = self.request.user.groups.values_list("name", flat=True)[0]
        if user_role == 'Employee':
            # Get the projects assigned to the user
            assigned_projects = UserProjectRel.objects.filter(user=user).values_list('project', flat=True)
            queryset = queryset.filter(id__in=assigned_projects)

        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a project by its ID.
        Employees can only retrieve projects they are assigned to.
        """
        project = self.get_object()  # Get the project instance

        # Check if the user is an 'Employee' and if they are assigned to the project
        user_role = self.request.user.groups.values_list("name", flat=True)[0]
        if user_role == 'Employee':
            # Check if the employee is assigned to the project
            if not UserProjectRel.objects.filter(user=request.user, project=project).exists():
                raise PermissionDenied("You do not have permission to access this project.")

        # Serialize the project with additional related data
        serializer = ProjectDetailSerializer(project, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def perform_create(self, serializer):
        """
        Ensure the user can only create a project within their allowed company.
        """
        company_id = self.kwargs.get('company_id')
        company = Company.objects.get(id=company_id)
        
        # Ensure the current user is an admin of the company
        user_profile = self.request.user.user_profile
        user_role = self.request.user.groups.values_list("name", flat=True)[0]
        if user_profile.company != company or user_role not in ['Admin', 'Manager']:
            raise PermissionDenied("You must be an admin of the company to create a project.")

        project = serializer.save(
            company=company,
            created_by=self.request.user,
            modified_by=self.request.user
        )

        # Create default settings for the project
        ProjectSettings.objects.create(
            project=project,
            name=project.name,  # Set settings name to project name
        )

    def perform_update(self, serializer):
        """
        Automatically update modified_by when modifying a project.
        """
        serializer.save(modified_by=self.request.user)

    @action(detail=True, methods=['get'], url_path='pdf', permission_classes=[IsAdminManagerOrAssigned])
    def pdf(self, request, pk=None, company_id=None):
        """
        Get pdf url.
        """
        try:
            project = self.get_object()  # Get the project instance
            return Response(
                {"pdf": DHPD_TOOL_DOMAIN + 'pdf/' + project.pdf},
                status=status.HTTP_200_OK
            )
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'], url_path='xml', permission_classes=[IsAdminManagerOrAssigned])
    def xml(self, request, pk=None, company_id=None):
        """
        Get xml url.
        """
        project = self.get_object()
        serializer = ProjectDetailCalculateSerializer(project, context={'request': request})
        xml_data = dict(serializer.data)

        user = self.request.user
        company = Company.objects.get(id=company_id)
        xml_data = process_driven_pile(xml_data)
        xml_data = input_xml_content_unit_convert(xml_data)
        xml_content = json_to_calculate_xml(xml_data, user, company)

        if not xml_content:
            return Response({"detail": "XML content not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create an HttpResponse with the XML content as an attachment
        response = HttpResponse(xml_content, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="project_{project.name}.xml"'

        return response
    
    @action(detail=True, methods=['get'], url_path='xlsx', permission_classes=[IsAdminManagerOrAssigned])
    def export_excel(self, request, pk=None, company_id=None):
        """
        Get xlsx file.
        """
        project = self.get_object()
        serializer = ProjectDetailSerializer(project, context={'request': request})
        xlsx_data = dict(serializer.data)
        xlsx_data = json_to_xlsx_structure(xlsx_data)

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="data.xlsx"'

        # Write multiple DataFrames to different sheets
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            workbook  = writer.book
            for sheet_name, records in xlsx_data.items():
                # Convert each sheet's data to a DataFrame
                df = pd.DataFrame(records)
                df.to_excel(writer, index=False, sheet_name=sheet_name)

                # Access the XlsxWriter workbook and worksheet objects.
                worksheet = writer.sheets[sheet_name]

                # Define a number format.
                number_format = workbook.add_format({'num_format': '0.00'})

                # Apply format only to numeric columns
                for col_num, column in enumerate(df.columns):
                    if pd.api.types.is_numeric_dtype(df[column]):  # Check if column is numeric
                        worksheet.set_column(col_num, col_num, None, number_format)

        return response

    @action(detail=True, methods=['get'], url_path='assigned-users', permission_classes=[IsAdminOrManager])
    def get_assigned_user(self, request, pk=None, company_id=None):
        """
        Retrieve users are assigned to a specific project.
        """
        project = self.get_object()
        user_relations = project.assigned_projects.all()  # Reverse relationship from Project to UserProjectRel
        users = [rel.user for rel in user_relations]  # Extract the User objects
        serializer = UserSerializer(users, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'], url_path='unassigned-users', permission_classes=[IsAdminOrManager])
    def get_unassigned_user(self, request, pk=None, company_id=None):
        """
        Retrieve users are not assigned to a specific project.
        """
        project = self.get_object()
        company = Company.objects.get(id=company_id)
        user_relations = company.users.all()

        # Get the IDs of users already assigned to the project
        assigned_user_ids = project.assigned_projects.values_list('user_id', flat=True)

        # Filter users who are not assigned to the project
        users_lst = user_relations.exclude(user_id__in=assigned_user_ids)
        unassigned_users = [user.user for user in users_lst]

        # Serialize the unassigned users
        serializer = UserSerializer(unassigned_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], url_path='delete-project', permission_classes=[IsAdminOrManager])
    def delete_project(self, request, pk=None, company_id=None):
        """
        Endpoint to soft delete a project (deactivate or remove relationships).
        Only accessible to admins.
        """
        project = self.get_object()
        project_name = f"{project.name}{PREFIX_DELETED}"
        while Project.all_objects.filter(name=project_name).exists():
            project_name += PREFIX_DELETED
        project.name = project_name
        project.is_active = False
        project.save()

        return Response(
            {'detail': 'Project deleted successfully.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['delete'], url_path='delete-multi-projects', permission_classes=[IsAdminOrManager])
    def delete_multi_projects(self, request, company_id=None):
        """
        Endpoint to delete multiple projects at once.
        Only accessible to admins or managers of the company.
        """
        project_ids = request.data.get("project_ids", [])
        
        if not project_ids:
            return Response({"detail": "No project IDs provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the company from the provided company_id
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user belongs to the same company
        user_profile = request.user.user_profile
        if user_profile.company != company:
            raise PermissionDenied("You do not have permission to delete projects from this company.")

        # Get the projects to delete
        projects = Project.objects.filter(id__in=project_ids, company=company)

        if projects.count() != len(project_ids):
            return Response({"detail": "One or more projects not found in the specified company."}, status=status.HTTP_404_NOT_FOUND)

        # Perform the deletion
        # projects.delete() => We should only perform soft deletion
        for project in projects:
            project_name = f"{project.name}{PREFIX_DELETED}"
            while Project.all_objects.filter(name=project_name).exists():
                project_name += PREFIX_DELETED
            project.name = project_name
            project.is_active = False
            project.save()

        return Response({"detail": "Projects deleted successfully."}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='copy-multi-projects', permission_classes=[IsAdminOrManager])
    def copy_multi_projects(self, request, company_id=None):
        """
        Endpoint to delete multiple projects at once.
        Only accessible to admins or managers of the company.
        """
        try:
            project_ids = request.data.get("project_ids", [])
            
            if not project_ids:
                return Response({"detail": "No project IDs provided."}, status=status.HTTP_400_BAD_REQUEST)

            # Get the company from the provided company_id
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                return Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

            # Get the projects to delete
            projects = Project.objects.filter(id__in=project_ids, company=company)

            if projects.count() != len(project_ids):
                return Response({"detail": "One or more projects not found in the specified company."}, status=status.HTTP_404_NOT_FOUND)

            # Perform the deletion
            for project in projects:
                project.copy_project(self.request.user)

            return Response({"detail": "Projects copy successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='assign-users', permission_classes=[IsAdminOrManager])
    def assign_users(self, request, pk=None, company_id=None):
        """
        Endpoint to assign a list of users to a project.
        Only accessible to admins or managers of the company.
        """
        project = self.get_object()
        user_ids = request.data.get("user_ids", [])
        
        if not user_ids:
            return Response(
                {"detail": "No user IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if users exist
        users = User.objects.filter(id__in=user_ids)
        if users.count() != len(user_ids):
            return Response({"detail": "One or more users not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create UserProjectRel instances for each user
        for user in users:
            if user.user_profile.company != project.company:
                raise PermissionDenied(f"User {user.email} does not belong to the same company as the project.")
            UserProjectRel.objects.get_or_create(user=user, project=project)

        return Response(
            {"detail": "Users assigned to the project successfully."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='unassign-users', permission_classes=[IsAdminOrManager])
    def unassign_users(self, request, pk=None, company_id=None):
        """
        Endpoint to unassign a list of users from a project.
        Only accessible to admins or managers of the company.
        """
        project = self.get_object()
        user_ids = request.data.get("user_ids", [])
        
        if not user_ids:
            return Response(
                {"detail": "No user IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if users exist
        users = User.objects.filter(id__in=user_ids)
        if users.count() != len(user_ids):
            return Response(
                {"detail": "One or more users not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete UserProjectRel instances for each user
        for user in users:
            if user.user_profile.company != project.company:
                raise PermissionDenied(
                    f"User {user.email} does not belong to the same company as the project."
                )
            try:
                user_project_rel = UserProjectRel.objects.get(user=user, project=project)
                user_project_rel.delete()
            except UserProjectRel.DoesNotExist:
                return Response(
                    {"detail": f"User {user.email} is not assigned to this project."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response({"detail": "Users unassigned from the project successfully."}, status=status.HTTP_200_OK)

    # Action to assign a user to a project
    @action(detail=True, methods=['post'], url_path='assign-user', permission_classes=[IsAdminOrManager])
    def assign_user(self, request, pk=None, company_id=None):
        """
        Assign a user to a project if they both belong to the same company.
        """
        project = self.get_object()
        user_id = request.data.get("user_id")
        user = get_object_or_404(User, pk=user_id)
        
        # Check if the user and project belong to the same company
        if user.user_profile.company != project.company:
            return Response(
                {"detail": "User and project must belong to the same company."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the user is already assigned to the project
        if UserProjectRel.objects.filter(user=user, project=project).exists():
            return Response(
                {"detail": "User is already assigned to this project."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the relationship between the user and the project
        UserProjectRel.objects.create(user=user, project=project)
        
        return Response(
            {"detail": "User assigned to project successfully."},
            status=status.HTTP_200_OK
        )

    # Action to unassign a user from a project
    @action(detail=True, methods=['post'], url_path='unassign-user', permission_classes=[IsAdminOrManager])
    def unassign_user(self, request, pk=None, company_id=None):
        """
        Unassign a user from a project.
        """
        project = self.get_object()
        user_id = request.data.get("user_id")
        user = get_object_or_404(User, pk=user_id)
        
        # Check if the user is assigned to the project
        user_project_rel = UserProjectRel.objects.filter(user=user, project=project).first()
        if not user_project_rel:
            return Response(
                {"detail": "User is not assigned to this project."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Delete the relationship between the user and the project
        user_project_rel.delete()
        
        return Response(
            {"detail": "User unassigned from project successfully."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='reset-default-settings', permission_classes=[IsAdminManagerOrAssigned])
    def reset_settings(self, request, pk=None, company_id=None):
        """
        Reset the project settings to default values.
        """
        project = self.get_object()  # Get the project instance

        # Reset settings to default values
        ProjectSettings.objects.update_or_create(
            project=project,
            defaults={
                "name": project.name,
                "projektLocation": '',
                "projektStreet": '',
                "projektPostalCode": '',
                "companyAltName": '',
                "companyAltLocation": '',
                "companyAltStreet": '',
                "companyAltPostalCode": '',
                "companyAltEmail": '',
                "companyAltPhone": '',
                "companyAltFax": '',
                "companyAltLogo": '',
                "Schrittweite": 0.01,
                "runHorBemessung": False,
                "AchsabstandGleicherTiefe": 0,
                "AuslastungProzent": 100,
                "Beeinflussungsweite": 20,
                "EAErhoehungProzent": 0,
                "Exzentrizitaet": 0.1,
                "FuszBeeinfluszung": 0,
                "MindestEinbindung": 2.5,
                "zulaessigeSetzungCm": 2,
                "BetonZyl": 25,
                "MaxLaenge": 100,
                "MantelErhoehungProzent": 15,
                "Knicklaenge": 0,
                "FuszErhoehungProzent": 15,
                "useErhoehung": 2,
                "SpitzendruckMittelung": False,
                "MindestPfahllaenge": 3,
                "Norm": 1,
                "gammaDruck": 1.4,
                "gammaZug": 1.5,
                "KopfEinbindung": 0.5,
                "ksNichtReduzieren": False,
                "gegenRaeumlichenEP": True,
                "gammaStaendig": 1.35,
                "gammaVeraenderlich": 1.5,
                "WinkelAusProfilen": False,
                "AbtreppungsWinkelRad": 45,
                "nameAnlageAuszen": '',
                "seitenBezeichnung": 'Seite',
                "seitenStartNummer": 1,
                "SeiteVonSeiten": 0,
                "erstelleUebersichtAuszen": 1,
                "UebersichtQuer": 1,
                "erstelleEinzelnachweise": 1,
                "zeichneNachweislinien": 1,
                "UKKotenInTabelle": 1,
                "erstellegrafikAuszen": 1,
                "erstellegrafikInnen": 1,
                "qskQcAb0": False,
                "qbkQcAb0": False,
                "qskCukAb0": False,
                "qbkCukAb0": False,
                "MaxLaengs": 0.016,
                "MaxBuegel": 0.008,
                "MinLaengsAbstand": 0.1,
                "Stahlsorte": "B500B",
                "falsermInner": 1,
                "MvonMaxfuerSchub": 0.5,
                "Betondeckung": 0.12,
            }
        )

        return Response({"message": "Project settings have been reset to default values."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'], url_path='update-settings', permission_classes=[IsAdminManagerOrAssigned])
    def update_settings(self, request, pk=None, company_id=None):
        """
        Update project settings.
        """
        project = self.get_object()
        serializer = ProjectSettingsWithoutCompLogoSerializer(data=request.data['settings'])

        if serializer.is_valid():
            setting_datas = serializer.data
            try:
                update_project_setting_data(setting_datas, project)

                return Response(
                    {"message": "Project settings updated successfully."},
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['put'], url_path='update-table-datas', permission_classes=[IsAdminManagerOrAssigned])
    def update_table_data(self, request, pk=None, company_id=None):
        """
        Update full project details including related objects.
        """
        project = self.get_object()
        serializer = ProjectTableNotValidateSerializer(data=request.data)

        if serializer.is_valid():
            table_datas = serializer.data
            try:
                update_project_table_data(table_datas, project)
                return Response(
                    {"message": "Project details updated successfully."},
                    status=status.HTTP_200_OK
                )

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='upload-company-logo', permission_classes=[IsAdminManagerOrAssigned])
    def upload_project_company_logo(self, request, pk=None, company_id=None):
        """
        Upload company logo in project settings.
        """
        serializer = ProjectCompanyLogoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        project = self.get_object()

        try:
            if project.basic_data_settings.companyAltLogo != "":
                remove_old_image(project.basic_data_settings.companyAltLogo)

            if file:
                fastapi_url = (f'{FASTAPI_SERVER_DOMAIN}'
                        f'user/uploadImage/')
                
                file = resize_image(file)

                files = {"image": file}
                response = requests.post(fastapi_url, files=files, timeout=20)
                project.basic_data_settings.companyAltLogo = response.json()["file_name"]
            
            else:
                project.basic_data_settings.companyAltLogo = ""
                project.basic_data_settings.save()
                return Response(
                    {"message": "The company logo is deleted successfully."},
                    status=status.HTTP_200_OK
                )

            project.basic_data_settings.save()

            return Response(
                {"file": DHPD_TOOL_DOMAIN + 'files/images/' + project.basic_data_settings.companyAltLogo},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='import-file', permission_classes=[IsAdminManagerOrAssigned])
    def import_project_data(self, request, pk=None, company_id=None):
        """
        Import project data from an XML or Excel file.
        """
        serializer = ProjectImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        project = self.get_object()

        try:
            if file.name.endswith('.xml'):
                errors = validate_input_xml_file(file)
                if errors:
                    return Response({"error": errors}, status=status.HTTP_400_BAD_REQUEST)
                file.seek(0)
                file_json_content = xml_to_json(file)
                file.seek(0)
                file_json_content = map_keys(file_json_content)
                file_json_content = restructure_json_data(file_json_content)

                # Ignore Project name and Company Logo when import data
                file_json_content["settings"].pop("name")
                file_json_content["settings"].pop("companyAltLogo")

                file_json_content = process_import_driven_pile(file_json_content)
                file_json_content = input_xml_content_unit_convert(file_json_content, reversed=True)
                update_project_setting_data(file_json_content, project)

            elif file.name.endswith('.xlsx'):
                file_json_content = xlsx_to_json(file)

            update_project_table_data(file_json_content, project, is_import_data=True)

            return Response(
                {"message": "Project entirely updated successfully."},
                status=status.HTTP_200_OK
            )

        #     if file.name.endswith('.xml'):
        #         self.validate_input_xml(file_content)
        #     elif file.name.endswith('.xlsx'):
        #         self._import_from_excel(file_content)
        #     else:
        #         return Response({"error": "Unsupported file format."}, status=status.HTTP_400_BAD_REQUEST)

        #     return Response({"message": "Project data imported successfully."}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='calculate', permission_classes=[IsAdminManagerOrAssigned])
    def calculate(self, request, pk=None, company_id=None):
        """
        Endpoint aims to trigger request FastAPI for project calculation.
        """
        self.error = None
        self.data = {}

        # Retrieve additional query parameters from the URL
        dhpd_server = request.query_params.get('dhpd_server', 0)
        dhpd_server = DHPD_SERVER_2 if int(dhpd_server)==1 else DHPD_SERVER_1

        project = self.get_object()
        delete_calculation_output_data(project)
        print("ALready deleted output data!")
        serializer = ProjectDetailCalculateSerializer(project, context={'request': request})
        xml_data = dict(serializer.data)

        user = self.request.user
        company = Company.objects.get(id=company_id)
        xml_data = process_driven_pile(xml_data)
        xml_data = input_xml_content_unit_convert(xml_data)
        xml_content = json_to_calculate_xml(xml_data, user, company)
        
        calculate_template_xml = xmltodict.parse(xml_content)

        fastapi_url = (f'{FASTAPI_SERVER_DOMAIN}'
                       f'project/calculateByXMLString/')
        response = requests.post(
            fastapi_url,
            # json={'xml_content': {"InputDaten": xml_data}},
            json={
                'xml_content': calculate_template_xml,
                'dhpd_server': dhpd_server
            },
            verify=False,
            timeout=500)
        
        print("Done request to Business Logic!")
        # Serialize the project with additional related data

        # Make sure web connection is OK
        if response.status_code == 200:
            data = response.json()
        else:
            return Response(
                {"detail": "Failed to get data from DHPD proxy!"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(data)
        # Check if error message was set, which marks failure when executing
        # DHPD-WebClient program. checking for xml_output_data object makes
        # sure we go here if dhpd proxy has failed to extract xml data,
        # so we get the underlying problem reason if it is available.
        if 'error_msg' in data \
          and data['error_msg'] is not None \
          and 'xml_output_data' not in data:

            # Check if this error happened because of project data or
            # calculation server is down.

            # If DHPD Proxy receives "False" as xml_content input, it switches
            # into connection testing mode that will use known working project.
            con_test = requests.post(
                fastapi_url,
                json={'xml_content': False},
                verify=False)

            if con_test.json()['error_msg'] is not None:
                self.error = {
                    'status_message': 'Calculate Connection Error'}
                self.data = con_test.json()['error_msg']
                return Response(
                    self.data,
                    status=status.HTTP_400_BAD_REQUEST
                )

            # This means we tried to do calculation with correct test data and
            # it works. Meaning it's a problem with this project.
            else:
                self.error = {
                    'status_message': 'Calculate Connection Error'}
                self.data = data['error_msg']
                return Response(
                    self.data,
                    status=status.HTTP_400_BAD_REQUEST
                )

        # At this point we have calculation result as JSON'ized XML which can
        # be error message in ErrorData or Fehler keys, OR real result.
        xml_output_data = data['xml_output_data']
        print(xml_output_data)

        # 1. Check if the ErrorData key exists, this contain errors detected by
        # DHPD-WebClient tool.
        if 'ErrorData' in xml_output_data.keys():
            self.error = {
                'status_message': 'Calculation Error',
                'data': (xml_output_data['ErrorData']
                            ['_errorList']['InfoInhalt'])
            }
            return Response(
                data,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Commit raw calculation result to object state
        self.data = data

        # Update PDF export link ASAP
        try:
            pdf = data['pdf']
            project.pdf = pdf
            project.save()
        except:
            ...

        result = xml_output_data['OutputDaten']
        # DHPD-Web tool unpacks singular items from list into dict. Thus, we
        # do some ugly wrapping into list to unify behavior for below code.
        try:
            if (type(_ := result['pfaehle']['LastPunktOutputList']
            ['LastPunktOutput']) is dict):

                (result['pfaehle']['LastPunktOutputList']
                ['LastPunktOutput']) = [_]
        except:
            ...

        try:
            if (type(_ := result['BodenNutzung']['BodenNutzungDict']
            ['a:KeyValueOfstringBodenNutzungOutputDB_PsWP3v']) is dict):

                (result['BodenNutzung']['BodenNutzungDict']
                ['a:KeyValueOfstringBodenNutzungOutputDB_PsWP3v']) = [_]
        except:
            ...

        try:
            if (type(_ := result['hLasten']['LastPunktOutputDict']
            ['a:KeyValueOfstringArrayOfHLastPunktHorOutputDB_PsWP3v']) is dict):

                (result['hLasten']['LastPunktOutputDict']
                ['a:KeyValueOfstringArrayOfHLastPunktHorOutputDB_PsWP3v']) = [_]
        except:
            ...

        # Split calculation results into dicts to simplify processing
        try:
            result_piles = {
                x['_Pname']: x
                for x in result['pfaehle']['LastPunktOutputList']['LastPunktOutput']}
        except:
            ...

        try:
            result_soils = {
                x['a:Key']: x['a:Value']
                for x in result['BodenNutzung']['BodenNutzungDict']['a:KeyValueOfstringBodenNutzungOutputDB_PsWP3v']}
        except:
            ...

        try:
            result_hlcs = {
                x['a:Key']: x['a:Value']
                for x in result['hLasten']['LastPunktOutputDict']['a:KeyValueOfstringArrayOfHLastPunktHorOutputDB_PsWP3v']}
        except:
            ...

        try:
            result = output_xml_content_unit_convert(result)
        except:
            ...
        try:
            result = output_xml_content_round_2_decimal_digits(result)
        except:
            ...
        
        try:
            for pile_name in result_piles.keys():
                try:
                    current_pile = Pile.objects.get(project=project, Pname=pile_name)
                    for key,val in PILE_OUTPUT_KEYS_MAPPING.items():
                        try:
                            result_piles[pile_name][val] = None if str(result_piles[pile_name][val]) in ["NaN", "nan"] \
                                else result_piles[pile_name][val]
                            current_pile.__setattr__(key, result_piles[pile_name][val])
                        except:
                            ...
                    current_pile.save()
                except:
                    ...
        except:
            ...

        try:
            for soil_prof_name, soil_profile_data in result_soils.items():
                try:
                    soil_prof = SoilProfile.objects.get(project=project,name=soil_prof_name)
                    current_layers = SoilLayer.objects.filter(soil_profile=soil_prof).order_by("row_index")
                    layers = soil_profile_data['_schichten']['BodenSchichtNutzung']
                    layers = [layers] if not isinstance(layers, list) else layers
                    for layer, current_layer in zip(layers, current_layers):
                        try:
                            for key,val in SOIL_LAYER_OUTPUT_KEYS_MAPPING.items():
                                try:
                                    layer[val] = None if str(layer[val]) in ["NaN", "nan"] else layer[val]
                                    current_layer.__setattr__(key, layer[val])
                                    current_layer.save()
                                except Exception as e:
                                    ...
                        except:
                            ...
                except:
                    ...
        except:
            ...

        try:
            for hcase_name, hcase_data in result_hlcs.items():
                try:
                    hcase = HorizontalLoadCase.objects.get(project=project,name=hcase_name)
                    current_hloads = HorizontalLoadPile.objects.filter(case=hcase).order_by("row_index")
                    hloads = hcase_data['HLastPunktHorOutput']
                    hloads = [hloads] if not isinstance(hloads, list) else hloads
                    for hload, current_hload in zip(hloads, current_hloads):
                        try:
                            for key,val in HORIZONTAL_LOAD_POINT_OUTPUT_KEYS_MAPPING.items():
                                try:
                                    hload[val] = None if str(hload[val]) in ["NaN", "nan"] else hload[val]
                                    current_hload.__setattr__(key, hload[val])
                                    current_hload.save()
                                except Exception as e:
                                    ...
                        except:
                            ...
                except:
                    ...
        except:
            ...

        # 2. Check if Fehler (=Mistake) field is not empty. These are given by
        # calculation server.
        # XML→JSON serializer makes this field into dict if is it's empty,
        #   but if there is an error message, it will be a string.
        if isinstance(error_text := xml_output_data['OutputDaten']['_fehlerText'], str):
            self.error = {
                'status_message': 'Calculation Error',
                'data': error_text}
            for pop_key in [
                "pfaehle",
                "hLasten",
                "gruppenStatiken",
                "Kosten",
                "BodenNutzung",
                "KostenOutput"
            ]:
                try:
                    data['xml_output_data']['OutputDaten'].pop(pop_key)
                except:
                    ...
            return Response(
                    data,
                    status=status.HTTP_400_BAD_REQUEST
                )

        project = self.get_object()
        serializer = ProjectDetailSerializer(project, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
