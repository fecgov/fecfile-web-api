from uuid import UUID
from .utils.committee_membership import add_user_to_committee
from rest_framework import filters, viewsets, mixins, pagination, status
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from fecfiler import settings
from fecfiler.email import send_email_notification
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.committee_accounts.utils.accounts import (
    create_committee_account,
    get_committee_account_data,
    raise_if_cannot_create_committee_account,
)
from fecfiler.user.utils import delete_active_sessions_for_user_and_committee
from fecfiler.settings import FLAG__ENABLE_EMAIL
from django.http import (
    HttpResponseBadRequest,
    HttpResponseServerError,
)
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .serializers import CommitteeAccountSerializer, CommitteeMembershipSerializer
from django.db.models.fields import TextField
from django.db.models.functions import Coalesce, Concat
from django.db.models import Q, Value, Case, When, IntegerField
import structlog
from rest_framework.permissions import BasePermission

logger = structlog.get_logger(__name__)


class CommitteeMemberListPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"


class CommitteePagination(pagination.PageNumberPagination):
    page_size = 100


class CommitteeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    serializer_class = CommitteeAccountSerializer
    pagination_class = CommitteePagination

    def get_queryset(self):
        user = self.request.user
        return CommitteeAccount.objects.filter(members=user).order_by("-committee_id")

    @extend_schema(
        request=CommitteeAccountSerializer,
        responses=CommitteeAccountSerializer,
        parameters=[
            OpenApiParameter(name="id", type=str, location=OpenApiParameter.PATH)
        ],
    )
    @action(detail=True, methods=["post"])
    def activate(self, request, pk):
        committee: CommitteeAccount = self.get_object()
        if not committee or committee.disabled is not None:
            return Response("Committee could not be activated", status=403)
        try:
            committee_data = self.update_committee_record_for_activate(committee)
        except Exception as e:
            logger.error(
                f"User {request.user.email} failed to update "
                f"committee record for committee activation "
                f"{committee_data.get("committee_id")}: {str(e)}"
            )
        request.session["committee_id"] = str(committee_data.get("committee_id"))
        request.session["committee_uuid"] = str(committee_data.get("id"))
        return Response(committee_data)

    @action(detail=False, methods=["post"])
    def create_account(self, request):
        try:
            committee_id = request.data.get("committee_id")
            if not committee_id:
                raise Exception("no committee_id provided")
            account = create_committee_account(committee_id, request.user)
            return Response(self.get_serializer(account).data)
        except Exception as e:
            logger.error(
                f"User {request.user.email} failed to create committee account "
                f"{committee_id}: {str(e)}"
            )
            raise

    @action(detail=False, methods=["get"], url_path="get-available-committee")
    def get_available_committee(self, request):
        try:
            committee_id = request.query_params.get("committee_id")
            committee = get_committee_account_data(committee_id)
            raise_if_cannot_create_committee_account(committee_id, request.user)
            return Response(committee)
        except Exception as e:
            logger.error(
                f"User {request.user.email} failed to retrieve "
                f"committee for account creation "
                f"{committee_id}: {str(e)}"
            )
            response = {"message": "No available committee found."}
            return Response(response, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        response = super(CommitteeViewSet, self).list(request, *args, **kwargs)
        response.data["results"] = [
            self.add_committee_account_data(committee_account)
            for committee_account in response.data["results"]
        ]
        return response

    def add_committee_account_data(self, committee_account):
        committee_data = get_committee_account_data(committee_account["committee_id"])
        return {**committee_account, **(committee_data or {})}

    def update_committee_record_for_activate(self, committee: CommitteeAccount):
        committee_data = get_committee_account_data(committee.committee_id)
        committee.filing_frequency = committee_data.get("filing_frequency", None)
        committee.candidate_office = committee_data.get("candidate_office", None)
        committee.candidate_state = committee_data.get("candidate_state", None)
        committee.candidate_district = committee_data.get("candidate_district", None)
        committee.save()
        return {**CommitteeAccountSerializer(committee).data, **(committee_data or {})}


class CommitteeOwnedViewMixin(viewsets.GenericViewSet):
    """ModelViewSet for models using CommitteeOwnedModel
    Inherit this view set to filter the queryset by the user's committee
    """

    def get_queryset(self):
        committee_uuid = self.get_committee_uuid()
        return super().get_queryset().filter(committee_account_id=committee_uuid)

    def get_committee_uuid(self):
        committee_uuid = self.request.session.get("committee_uuid")
        if not committee_uuid:
            raise PermissionDenied("You must activate a committee account")
        return committee_uuid

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if "page" in request.query_params:
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class IsCommitteeAdministrator(BasePermission):
    """
    Allows access only to committee administrators.
    """

    def has_permission(self, request, view):
        committee_uuid = request.session.get("committee_uuid")
        if not committee_uuid:
            return False
        role = (
            Membership.objects.filter(
                user=request.user, committee_account_id=committee_uuid
            )
            .values_list("role", flat=True)
            .first()
        )
        return role == Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR


class CommitteeMembershipViewSet(CommitteeOwnedViewMixin, viewsets.ModelViewSet):
    serializer_class = CommitteeMembershipSerializer
    pagination_class = CommitteeMemberListPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["name", "email", "role", "is_active", "created"]
    ordering = ["-created"]

    queryset = Membership.objects.all()

    def get_permissions(self):
        if self.action in (
            "update",
            "partial_update",
            "destroy",
            "remove_member",
            "add_member",
        ):
            self.permission_classes = [IsCommitteeAdministrator]
        return super().get_permissions()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                name=Coalesce(
                    Concat(
                        "user__last_name",
                        Value(", "),
                        "user__first_name",
                        output_field=TextField(),
                    ),
                    Value(""),
                    output_field=TextField(),
                ),
                email=Coalesce("user__email", "pending_email", output_field=TextField()),
                is_active=~Q(user=None),
            )
        )

    @action(detail=False, methods=["post"], url_path="add-member", url_name="add_member")
    def add_member(self, request):
        try:
            committee_id = self.request.session["committee_id"]

            email = request.data.get("email", None)
            role = request.data.get("role", None)

            # Check for necessary fields
            missing_fields = []
            if email is None or len(email) == 0:
                missing_fields.append("email")

            if role is None:
                missing_fields.append("role")

            if len(missing_fields) > 0:
                raise ValidationError(f"Missing fields: {', '.join(missing_fields)}")

            # Check for valid role
            choice_of = False
            for choice in Membership.CommitteeRole.choices:
                if role in choice:
                    choice_of = True
                    break
            if not choice_of:
                raise ValidationError("Invalid role")

            new_member = add_user_to_committee(email, committee_id, role)

            # if no Exception was returned, send email notification to the user
            if not isinstance(new_member, BaseException):
                # fall back to email if name is unavailable
                full_name = request.user.get_full_name() or request.user.email
                logger.info(
                    f"User {full_name} added {email} to committee "
                    f"{committee_id} as {role}"
                )
                if FLAG__ENABLE_EMAIL:
                    committee_data = get_committee_account_data(committee_id)
                    committee_name = committee_data.get("name", None)

                    self.sendAddMemberEmailNotification(
                        committee_id,
                        committee_name,
                        email,
                        full_name,
                        role,
                    )
            else:
                logger.error(
                    f"User {request.user.id} attempted to add {email} to committee "
                    f"{committee_id} as {role}"
                )

            return Response(CommitteeMembershipSerializer(new_member).data, status=200)
        except Exception as e:
            logger.error(f"""
                Failed to add email {email} to committtee {type(e)}
                {committee_id} as {role} {str(e)}
                """)
            return (
                HttpResponseBadRequest()
                if isinstance(e, ValidationError)
                else HttpResponseServerError()
            )

    @action(
        detail=True,
        methods=["delete"],
        url_path="remove-member",
        url_name="remove_member",
    )
    def remove_member(self, request, pk: UUID):
        member: Membership = self.get_object()
        committee_id = request.session["committee_id"]
        if member.user == request.user:
            logger.info(
                f"{request.user.id} attempted to remove themselves "
                f"from committee {committee_id}"
            )
            return Response(
                {"error": "You cannot remove yourself from the committee."}, status=400
            )

        # Call the model's delete method (which already checks the admin count)
        try:
            member.delete()
            if member.user is not None:
                delete_active_sessions_for_user_and_committee(
                    str(member.user.id), committee_id
                )
                logger.info(
                    f"{request.user.id} removed user {member.user.id} "
                    f"from committee {committee_id}"
                )
            else:
                logger.info(
                    f"{request.user.id} removed pending membership {member.id} "
                    f"from committee {committee_id}"
                )
            return Response({"success": "Membership removed."})
        except ValidationError as e:
            logger.error(f"{str(e)}")
            return Response({"error": str(e)}, status=400)

    def update(self, request, *args, **kwargs):
        existing_member = self.get_object()
        committee = existing_member.committee_account
        # member updates
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_role = request.data.get("role")

        member_string = ""
        if existing_member.user is not None:
            user_id = existing_member.user.id
            member_string = f"user {user_id}"
        else:
            membership_id = existing_member.id
            member_string = f"pending membership {membership_id}"

        logger.info(
            f"Updating role for {member_string} in committee {committee} to {new_role}"
        )

        return super().update(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        you_first = request.query_params.get("you_first")
        logger.info(you_first)
        if you_first != "true":
            return super().list(request)
        page_param = self.paginator.page_query_param if self.paginator else "page"

        is_first_page = request.query_params.get(page_param, "1") == "1"
        queryset = self.filter_queryset(self.get_queryset())

        if is_first_page and request.user.is_authenticated:
            queryset = queryset.annotate(
                is_current_user=Case(
                    When(user=request.user, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )

            existing_ordering = queryset.query.order_by
            queryset = queryset.order_by("-is_current_user", *existing_ordering)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def sendAddMemberEmailNotification(
            self, committee_id, committee_name, email, full_name, role
    ):
        subject = f"{full_name} has added you to a FECfile+ committee account"

        # adjust links based on space
        if settings.SPACE == "local":
            fecfile_link = "http://localhost:4200/login"
        else:
            if not settings.SPACE or settings.SPACE == "prod":
                envbit = ""
            else:
                envbit = f"{settings.SPACE}."
            fecfile_link = f"https://{envbit}fecfile.fec.gov/login"

        body_text = (
            f"{full_name} has added you as a {role} in FECfile+ "
            "for the following committee:\n"
            "\n"
            f"Committee ID: {committee_id}\n"
            f"Committee Name: {committee_name}\n"
            "\n"
            "You can access the committee account by signing in to FECfile+:\n"
            f"{fecfile_link}\n"
            "\n"
            "Important: You must have a Login.gov account to sign in to FECfile+. "
            "If you don't already have a Login.gov account for this email, "
            "select \"Create an account\" to get started.\n"
            "\n"
            "==================================================================\n"
            "\n"
            "If you are receiving this email in error or have any questions, "
            "please contact the FEC Electronic Filing Office "
            "toll-free at (800) 424-9530 ext. 1307 or locally at (202) 694-1307.\n"
            "\n"
            f"FECfile+: {fecfile_link}\n"
            "Contact us: "
            "https://www.fec.gov/contact/"
            "#filing-reports-and-amendments-reporting-specific-transactions\n"
            "\n"
            "FEC.gov: https://www.fec.gov/\n"
            "Electronic filing overview: "
            "https://www.fec.gov/help-candidates-and-committees/"
            "filing-reports/electronic-filing/\n"
            "Privacy Policy: https://www.fec.gov/about/privacy-and-security-policy/"
        )

        try:
            send_email_notification(
                to_email=email, subject=subject, body_text=body_text
            )
        except Exception as e:
            logger.error(
                f"Emailing {email} invite to {committee_id} failed: {str(e)}"
            )
