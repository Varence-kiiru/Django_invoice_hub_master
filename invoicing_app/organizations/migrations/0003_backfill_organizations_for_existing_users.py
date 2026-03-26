# Generated migration to backfill organizations for existing users

from django.db import migrations
from django.utils.text import slugify
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta


def backfill_organizations(apps, schema_editor):
    """
    Create organizations for existing users who don't have one.
    This fixes users created before the organization system was introduced.
    """
    User = apps.get_model('auth', 'User')
    Organization = apps.get_model('organizations', 'Organization')
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')
    Subscription = apps.get_model('organizations', 'Subscription')
    
    # Find all users without an organization
    users_without_org = User.objects.filter(org_memberships__isnull=True).distinct()
    
    print(f"\n📝 Backfilling organizations for {users_without_org.count()} existing users...")
    
    for user in users_without_org:
        try:
            # Create organization name from user's first/last name or username
            if user.first_name and user.last_name:
                org_name = f"{user.first_name} {user.last_name}'s Company"
            elif user.first_name:
                org_name = f"{user.first_name}'s Company"
            else:
                org_name = f"{user.username}'s Company"
            
            # Create unique slug
            base_slug = slugify(org_name)
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Create Organization
            organization = Organization.objects.create(
                name=org_name,
                slug=slug,
                admin_email=user.email,
                plan='free',
                status='active'
            )
            
            # Create OrganizationMember
            OrganizationMember.objects.create(
                organization=organization,
                user=user,
                role='owner',
                is_primary=True
            )
            
            # Create Subscription
            trial_end = timezone.now().date() + timedelta(days=14)
            Subscription.objects.create(
                organization=organization,
                plan='free',
                status='active',
                amount=Decimal('0.00'),
                payment_method='trial',
                current_period_start=timezone.now().date(),
                current_period_end=trial_end
            )
            
            print(f"   ✅ Created organization for {user.email}")
            
        except Exception as e:
            print(f"   ❌ Failed to create organization for {user.email}: {str(e)}")


def reverse_backfill(apps, schema_editor):
    """
    Reverse the migration (optional - removes created organizations).
    Only removes organizations that were auto-created for existing users.
    """
    User = apps.get_model('auth', 'User')
    Organization = apps.get_model('organizations', 'Organization')
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')
    Subscription = apps.get_model('organizations', 'Subscription')
    
    # Find organizations with "Company" in the name (likely auto-generated)
    auto_orgs = Organization.objects.filter(name__contains="'s Company")
    
    print(f"\n🔙 Removing {auto_orgs.count()} backfilled organizations...")
    
    for org in auto_orgs:
        try:
            # Delete related records
            Subscription.objects.filter(organization=org).delete()
            OrganizationMember.objects.filter(organization=org).delete()
            org.delete()
            print(f"   ✅ Deleted organization {org.slug}")
        except Exception as e:
            print(f"   ❌ Failed to delete organization {org.slug}: {str(e)}")


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_organizations, reverse_backfill),
    ]
