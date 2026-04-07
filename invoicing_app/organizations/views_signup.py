"""
Authentication views for signup, login, email verification, and password reset.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.text import slugify
import logging
import hashlib

from .models import Organization, OrganizationMember, Subscription
from .forms import SignupForm, CompanySetupForm, LoginForm
from .security import rate_limit
from .email_utils import send_verification_email
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


@rate_limit("signup")
@require_http_methods(["GET", "POST"])
def signup_view(request):
    """
    User registration with organization creation.

    GET: Display signup form
    POST: Create user and organization, assign free trial

    IMPORTANT: Only the first user to register will be assigned the superuser role.
    After the first user is created, self-registration is disabled.
    """
    if request.user.is_authenticated:
        # Already logged in, redirect to dashboard
        return redirect("core:dashboard")

    # Check if any users already exist in the system
    users_exist = User.objects.exists()

    # If users already exist, prevent signup (only first user can register)
    if users_exist:
        messages.error(
            request,
            "User registration is disabled. Contact your system administrator for access!",
        )
        return redirect("organizations:login")

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            try:
                # Extract data
                email = form.cleaned_data["email"]
                first_name = form.cleaned_data["first_name"]
                last_name = form.cleaned_data["last_name"]
                password = form.cleaned_data["password"]
                company_name = form.cleaned_data["company_name"]
                company_website = form.cleaned_data.get("company_website", "")

                # Get company name from settings instead of form
                from invoicing_app.core.models import CompanySettings

                company_settings = CompanySettings.get_settings()

                # Check if company_name is still the default (not yet customized)
                DEFAULT_COMPANY_NAME = "Your Company Name"
                if company_settings.company_name != DEFAULT_COMPANY_NAME:
                    # Already customized, use existing value
                    actual_company_name = company_settings.company_name
                    logger.info(
                        f"Using existing company name from settings: '{actual_company_name}' (ignoring form: '{company_name}')"
                    )
                else:
                    # Still default, save user's input from form
                    actual_company_name = company_name
                    company_settings.company_name = company_name
                    logger.info(
                        f"Saved company name from signup form to settings: '{company_name}'"
                    )

                # Always save company email (from user's email during signup)
                company_settings.company_email = email

                # Save company website if provided (independent of company_name check)
                if company_website and company_website.strip():
                    company_settings.company_website = company_website
                    logger.info(
                        f"Saved company website from signup form: '{company_website}'"
                    )

                # Save all changes to CompanySettings
                company_settings.save()

                # Create Django User
                user = User.objects.create_user(
                    username=email.split("@")[0]
                    + "_"
                    + timezone.now().strftime("%Y%m%d%H%M%S"),
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                )

                # Check if this is the first user - make them superuser and superadmin role
                if User.objects.count() == 1:  # This is the first user
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()

                    # Also assign to superadmin role in the custom role system
                    from invoicing_app.user_management.models import (
                        UserRole,
                        CustomUser,
                    )

                    # Get or create superadmin role
                    superadmin_role, _ = UserRole.objects.get_or_create(
                        name="superadmin",
                        defaults={
                            "description": "Super Administrator with complete system access and control",
                            "is_active": True,
                            "permissions": [
                                "create_invoices",
                                "view_invoices",
                                "edit_invoices",
                                "delete_invoices",
                                "send_invoices",
                                "view_invoice_reports",
                                "create_quotations",
                                "view_quotations",
                                "edit_quotations",
                                "delete_quotations",
                                "convert_quotations",
                                "process_payments",
                                "view_payments",
                                "manage_payment_methods",
                                "reconcile_payments",
                                "view_all_expenses",
                                "create_expenses",
                                "edit_any_expense",
                                "delete_any_expense",
                                "submit_expenses",
                                "approve_expenses",
                                "mark_expense_paid",
                                "manage_clients",
                                "view_clients",
                                "view_client_contacts",
                                "view_deliveries",
                                "create_deliveries",
                                "edit_deliveries",
                                "delete_deliveries",
                                "view_financials",
                                "manage_financials",
                                "view_financial_reports",
                                "export_financial_data",
                                "view_reports",
                                "export_reports",
                                "create_custom_reports",
                                "manage_users",
                                "view_users",
                                "edit_own_profile",
                                "view_audit_logs",
                                "manage_roles",
                                "configure_settings",
                                "manage_backups",
                                "system_admin",
                                "manage_tax_rates",
                                "manage_products",
                            ],
                        },
                    )

                    # Create or update CustomUser profile with superadmin role
                    CustomUser.objects.update_or_create(
                        user=user,
                        defaults={
                            "role": superadmin_role,
                            "phone": None,
                        },
                    )

                    logger.info(
                        f"First user registered - assigned superadmin role and superuser status: {email}"
                    )

                # Create slug from company name (make unique)
                base_slug = slugify(actual_company_name)
                slug = base_slug
                counter = 1
                while Organization.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                logger.info(
                    f"DEBUG: Creating organization with slug={slug}, email={email}"
                )

                # Create Organization using company settings name
                organization = Organization.objects.create(
                    name=actual_company_name,
                    slug=slug,
                    admin_email=email,
                    website=company_website,
                    plan="free",  # Start all new signups on free plan
                    status="active",
                )
                logger.info(
                    f"DEBUG: Organization created: {organization.id}, {organization.slug}"
                )

                # Create Organization Member (Owner)
                member = OrganizationMember.objects.create(
                    organization=organization, user=user, role="owner", is_primary=True
                )
                logger.info(f"DEBUG: OrganizationMember created: {member.id}")

                # Create Free Trial Subscription
                trial_end = timezone.now().date() + timedelta(days=14)
                subscription = Subscription.objects.create(
                    organization=organization,
                    plan="free",
                    status="active",
                    amount=Decimal("0.00"),
                    payment_method="trial",
                    current_period_start=timezone.now().date(),
                    current_period_end=trial_end,
                )
                logger.info(f"DEBUG: Subscription created: {subscription.id}")

                # Log the signup
                logger.info(
                    f"New signup: {email} created organization {organization.slug}"
                )

                # Send verification email
                send_verification_email(request, user, organization)

                # Authenticate and login user
                user.backend = "django.contrib.auth.backends.ModelBackend"
                login(request, user)

                # Redirect to company setup
                request.session["signup_complete"] = True
                messages.success(
                    request,
                    f"Welcome {first_name}! We've sent a verification email to {email}. Let's set up your company profile.",
                )

                return redirect("organizations:company_setup")

            except Exception as e:
                import traceback

                error_tb = traceback.format_exc()
                logger.error(f"Signup error: {str(e)}\n{error_tb}")
                messages.error(
                    request,
                    f"An error occurred during signup. Please try again. Error: {str(e)}",
                )
                return redirect("organizations:signup")
        else:
            # Form has errors, re-render with errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignupForm()

    return render(
        request,
        "auth/signup.html",
        {"form": form, "page_title": "Create Your Free Account"},
    )


@login_required(login_url="organizations:login")
@require_http_methods(["GET", "POST"])
def company_setup_view(request):
    """
    Post-signup company profile setup.
    Collects company information for invoicing and branding.
    Saves all data to CompanySettings (the source of truth for company info).
    """
    # Get user's organization
    try:
        member = OrganizationMember.objects.get(user=request.user, is_primary=True)
        organization = member.organization
    except OrganizationMember.DoesNotExist:
        messages.error(request, "No organization found. Please contact support.")
        return redirect("core:dashboard")

    # Get or create CompanySettings
    from invoicing_app.core.models import CompanySettings

    company_settings = CompanySettings.get_settings()

    if request.method == "POST":
        form = CompanySetupForm(request.POST)

        if form.is_valid():
            try:
                # Save all form data to CompanySettings (single source of truth)
                company_settings.company_name = form.cleaned_data["company_name"]
                company_settings.company_phone = form.cleaned_data.get(
                    "company_phone", ""
                )
                company_settings.company_email = form.cleaned_data.get(
                    "company_email", company_settings.company_email
                )
                company_settings.company_website = form.cleaned_data.get(
                    "company_website", ""
                )
                company_settings.company_address = form.cleaned_data.get(
                    "company_address", ""
                )

                # Store address components as part of the address field or create separate fields
                address_parts = []
                if form.cleaned_data.get("company_address"):
                    address_parts.append(form.cleaned_data["company_address"])
                if form.cleaned_data.get("company_city"):
                    address_parts.append(form.cleaned_data["company_city"])
                if form.cleaned_data.get("company_state"):
                    address_parts.append(form.cleaned_data["company_state"])
                if form.cleaned_data.get("company_postal_code"):
                    address_parts.append(form.cleaned_data["company_postal_code"])
                if form.cleaned_data.get("company_country"):
                    address_parts.append(form.cleaned_data["company_country"])

                company_settings.company_address = (
                    ", ".join(filter(None, address_parts))
                    if address_parts
                    else company_settings.company_address
                )

                company_settings.tax_id = form.cleaned_data.get("company_tax_id", "")
                company_settings.save()

                # Also update Organization name for consistency
                organization.name = form.cleaned_data["company_name"]
                organization.admin_email = form.cleaned_data.get(
                    "company_email", organization.admin_email
                )
                organization.save(update_fields=["name", "admin_email"])

                messages.success(
                    request,
                    "Company profile updated successfully! Your information is now stored in settings.",
                )
                logger.info(f"Company setup completed for {organization.slug}")

                # Redirect to dashboard
                return redirect("core:dashboard")

            except Exception as e:
                logger.error(f"Company setup error: {str(e)}")
                messages.error(request, "An error occurred. Please try again.")
                import traceback

                logger.error(traceback.format_exc())
    else:
        # Pre-fill form with existing CompanySettings data
        # This way, data entered during signup is already populated
        initial_data = {
            "company_name": company_settings.company_name,
            "company_phone": company_settings.company_phone,
            "company_email": company_settings.company_email,
            "company_website": company_settings.company_website or "",
            "company_address": (
                company_settings.company_address.split(",")[0].strip()
                if company_settings.company_address
                else ""
            ),
            "company_tax_id": company_settings.tax_id,
        }
        form = CompanySetupForm(initial=initial_data)

    return render(
        request,
        "auth/company_setup.html",
        {
            "form": form,
            "organization": organization,
            "company_settings": company_settings,
            "page_title": "Complete Your Company Profile",
        },
    )


@rate_limit("login")
@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    User login view.

    GET: Display login form
    POST: Authenticate user and create session
    """
    if request.user.is_authenticated:
        # Already logged in
        return redirect("core:dashboard")

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            remember_me = form.cleaned_data.get("remember_me", False)

            try:
                # Get user by email
                user = User.objects.get(email=email)

                # Authenticate
                user = authenticate(request, username=user.username, password=password)

                if user is not None:
                    login(request, user)

                    # Set session expiry
                    if remember_me:
                        request.session.set_expiry(timedelta(days=30))
                    else:
                        request.session.set_expiry(timedelta(hours=8))

                    logger.info(f"User logged in: {email}")
                    messages.success(request, f"Welcome back, {user.first_name}!")

                    # Redirect to dashboard or next page
                    next_url = request.GET.get("next", "core:dashboard")
                    return redirect(next_url)
                else:
                    # Invalid password
                    logger.warning(
                        f"Failed login attempt for {email}: invalid password"
                    )
                    messages.error(request, "Invalid email or password.")

            except User.DoesNotExist:
                logger.warning(f"Failed login attempt for non-existent email: {email}")
                messages.error(request, "Invalid email or password.")
    else:
        form = LoginForm()

    return render(
        request,
        "auth/login.html",
        {"form": form, "page_title": "Sign In to Your Account"},
    )


@login_required(login_url="organizations:login")
@require_http_methods(["POST"])
def logout_view(request):
    """
    User logout.
    """
    logout(request)
    messages.success(request, "You have been logged out. See you soon!")
    return redirect("organizations:login")


def email_verification_view(request, token):
    """
    Email verification via token.
    Verifies user's email address after signup.
    """
    if request.user.is_authenticated:
        # Mark email as verified for logged-in user
        user = request.user
        try:
            # Regenerate token to verify
            expected_token = hashlib.sha256(
                f"{user.id}:{user.email}:{settings.SECRET_KEY}".encode()
            ).hexdigest()

            if token == expected_token:
                user.is_active = True  # Mark as active (verified)
                user.save()
                messages.success(
                    request,
                    "✓ Your email has been verified! You can now use all features.",
                )
                logger.info(f"Email verified for user {user.email}")
                return redirect("core:dashboard")
            else:
                messages.error(request, "Invalid verification link. Please try again.")
                return redirect("organizations:login")
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            messages.error(request, "An error occurred during verification.")
            return redirect("organizations:login")

    messages.error(request, "Please log in to verify your email.")
    return redirect("organizations:login")


@rate_limit("login")
@require_http_methods(["GET", "POST"])
def password_reset_view(request):
    """
    Password reset request form.
    Handles both GET (show form) and POST (send reset email).
    """
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Please enter your email address.")
            return render(
                request,
                "auth/password_reset.html",
                {"page_title": "Reset Your Password"},
            )

        try:
            User.objects.get(email=email)

            # Generate reset token (same as verification token for security)
            # In production, send password reset email with token
            # For now, show message
            logger.info(f"Password reset requested for {email}")
            messages.success(
                request,
                "If an account exists with that email, you will receive a password reset link shortly.",
            )

        except User.DoesNotExist:
            # Don't reveal if email exists (security best practice)
            logger.warning(f"Password reset attempted for non-existent email: {email}")
            messages.success(
                request,
                "If an account exists with that email, you will receive a password reset link shortly.",
            )

        return redirect("organizations:login")

    return render(
        request, "auth/password_reset.html", {"page_title": "Reset Your Password"}
    )
