from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from invoicing_app.organizations.models import Organization, OrganizationMember
from invoicing_app.core.models import CompanySettings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Reassign existing users to organization based on company settings"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Get company settings
        company_settings = CompanySettings.get_settings()
        if not company_settings.company_name:
            self.stdout.write(
                self.style.ERROR(
                    "Company name not set in settings. Please configure company settings first."
                )
            )
            return

        company_name = company_settings.company_name
        self.stdout.write(f'Using company name from settings: "{company_name}"')

        # Get or create the organization
        org, created = Organization.objects.get_or_create(
            name=company_name,
            defaults={
                "slug": company_name.lower().replace(" ", "-").replace("_", "-"),
                "admin_email": company_settings.company_email or "admin@company.com",
                "plan": "free",
                "status": "active",
            },
        )

        if created:
            self.stdout.write(
                f"Created new organization: {org.name} (slug: {org.slug})"
            )
        else:
            self.stdout.write(
                f"Using existing organization: {org.name} (slug: {org.slug})"
            )

        # Find users without organization membership
        orphan_users = User.objects.filter(org_memberships__isnull=True)
        self.stdout.write(
            f"Found {orphan_users.count()} users without organization membership"
        )

        # Find users with different organization memberships
        users_with_orgs = User.objects.filter(org_memberships__isnull=False).distinct()
        users_to_reassign = []

        for user in users_with_orgs:
            current_org = user.org_memberships.filter(is_primary=True).first()
            if current_org and current_org.organization.name != company_name:
                users_to_reassign.append((user, current_org.organization.name))

        self.stdout.write(
            f"Found {len(users_to_reassign)} users with different organization names"
        )

        total_users = orphan_users.count() + len(users_to_reassign)

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))
            self.stdout.write(f"Would process {total_users} users:")
            for user in orphan_users[:5]:  # Show first 5
                self.stdout.write(f"  - {user.email}: assign to {company_name}")
            if orphan_users.count() > 5:
                self.stdout.write(f"  ... and {orphan_users.count() - 5} more")

            for user, old_org in users_to_reassign[:5]:  # Show first 5
                self.stdout.write(
                    f'  - {user.email}: reassign from "{old_org}" to "{company_name}"'
                )
            if len(users_to_reassign) > 5:
                self.stdout.write(f"  ... and {len(users_to_reassign) - 5} more")
            return

        # Process orphan users
        assigned_count = 0
        for user in orphan_users:
            try:
                # Clear any existing memberships (shouldn't have any, but just in case)
                OrganizationMember.objects.filter(user=user).delete()

                # Create new membership
                OrganizationMember.objects.create(
                    organization=org,
                    user=user,
                    role="staff",  # Default role for existing users
                    is_primary=True,
                )
                assigned_count += 1
                logger.info(f"Assigned user {user.email} to organization {org.name}")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to assign user {user.email}: {str(e)}")
                )

        # Process users to reassign
        reassigned_count = 0
        for user, old_org_name in users_to_reassign:
            try:
                # Clear existing primary memberships
                OrganizationMember.objects.filter(user=user, is_primary=True).delete()

                # Create new primary membership
                OrganizationMember.objects.create(
                    organization=org,
                    user=user,
                    role="staff",  # Keep existing role logic if needed
                    is_primary=True,
                )
                reassigned_count += 1
                logger.info(
                    f'Reassigned user {user.email} from "{old_org_name}" to "{org.name}"'
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to reassign user {user.email}: {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {assigned_count + reassigned_count} users "
                f"({assigned_count} assigned, {reassigned_count} reassigned)"
            )
        )

        # Update organization user count
        org.user_count = org.members.count()
        org.save()
        self.stdout.write(f"Updated organization user count to {org.user_count}")
