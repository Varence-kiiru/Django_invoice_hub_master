"""
Stripe payment processing and subscription management.
Production-ready integration with error handling and retry logic.
"""
import stripe
import logging
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from .models import Organization, Subscription, Invoice
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


# Configure Stripe API key
stripe.api_key = settings.STRIPE_API_KEY


class StripeError(Exception):
    """Custom exception for Stripe-related errors"""
    pass


class SubscriptionManager:
    """
    Manages subscription lifecycle, billing, and payment processing.
    """
    
    PLAN_PRICING = {
        'free': {
            'name': 'Free',
            'price': 0,
            'currency': 'usd',
            'interval': None,
            'features': ['basic_invoicing'],
            'product_id': None,
            'price_id': None
        },
        'starter': {
            'name': 'Starter',
            'price': 29,  # $29/month
            'currency': 'usd',
            'interval': 'month',
            'features': ['basic_invoicing', 'delivery_tracking', 'expense_tracking'],
            'product_id': None,
            'price_id': None
        },
        'professional': {
            'name': 'Professional',
            'price': 79,  # $79/month
            'currency': 'usd',
            'interval': 'month',
            'features': ['basic_invoicing', 'delivery_tracking', 'expense_tracking', 'api_access', 'custom_branding', 'analytics'],
            'product_id': None,
            'price_id': None
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': None,  # Custom
            'currency': 'usd',
            'interval': 'month',
            'features': ['all'],
            'contact_sales': True,
            'product_id': None,
            'price_id': None
        }
    }
    
    @staticmethod
    def ensure_stripe_products():
        """Create or retrieve Stripe products and prices for all plans."""
        try:
            for plan_key, plan_config in SubscriptionManager.PLAN_PRICING.items():
                if plan_key == 'free' or plan_key == 'enterprise':
                    # Skip free plan and enterprise (no Stripe needed)
                    continue
                
                # Check if we already have a price_id
                if plan_config.get('price_id'):
                    continue
                
                # Create product if doesn't exist
                product = stripe.Product.create(
                    name=plan_config['name'],
                    type='service',
                    metadata={'plan': plan_key}
                )
                plan_config['product_id'] = product.id
                
                # Create price for the product
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=int(plan_config['price'] * 100),
                    currency=plan_config['currency'],
                    recurring={
                        'interval': plan_config['interval'],
                        'interval_count': 1
                    },
                    metadata={'plan': plan_key}
                )
                plan_config['price_id'] = price.id
                
                logger.info(f"Created Stripe product {product.id} and price {price.id} for plan {plan_key}")
        
        except stripe.error.StripeError as e:
            logger.error(f"Failed to ensure Stripe products: {str(e)}")
            # Don't raise, just log. Prices might already exist.
    
    @staticmethod
    def create_customer(organization):
        """Create a Stripe customer for an organization"""
        try:
            customer = stripe.Customer.create(
                name=organization.name,
                email=organization.admin_email,
                metadata={
                    'organization_id': organization.id,
                    'organization_slug': organization.slug,
                }
            )
            
            # Save Stripe customer ID to organization
            organization.stripe_customer_id = customer.id
            organization.save(update_fields=['stripe_customer_id'])
            
            logger.info(f"Created Stripe customer {customer.id} for org {organization.slug}")
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {str(e)}")
            raise StripeError(f"Failed to create customer: {str(e)}")
    
    @staticmethod
    def create_subscription(organization, plan, payment_method_id=None):
        """Create a subscription for an organization"""
        try:
            plan_config = SubscriptionManager.PLAN_PRICING.get(plan)
            if not plan_config:
                raise StripeError(f"Invalid plan: {plan}")
            
            # Free plan doesn't need Stripe subscription
            if plan == 'free':
                subscription = Subscription.objects.create(
                    organization=organization,
                    plan=plan,
                    status='active',
                    amount=Decimal('0.00'),
                    payment_method='none',
                    current_period_start=timezone.now().date(),
                    current_period_end=(timezone.now() + timezone.timedelta(days=30)).date()
                )
                organization.plan = 'free'
                organization.status = 'active'
                organization.save(update_fields=['plan', 'status'])
                return subscription
            
            # Ensure Stripe products exist
            SubscriptionManager.ensure_stripe_products()
            
            # Create Stripe customer if not exists
            if not organization.stripe_customer_id:
                SubscriptionManager.create_customer(organization)
            
            # Get the price_id for this plan
            price_id = plan_config.get('price_id')
            if not price_id:
                raise StripeError(f"No price configured for plan {plan}")
            
            # Create subscription in Stripe using price ID
            stripe_subscription = stripe.Subscription.create(
                customer=organization.stripe_customer_id,
                items=[{
                    'price': price_id
                }],
                payment_method=payment_method_id if payment_method_id else None,
                off_session=True if payment_method_id else None,
                metadata={
                    'organization_id': organization.id,
                    'organization_slug': organization.slug,
                }
            )
            
            # Create Subscription record in database
            from datetime import datetime
            current_period_start = datetime.fromtimestamp(
                stripe_subscription.current_period_start,
                tz=timezone.utc
            ).date()
            current_period_end = datetime.fromtimestamp(
                stripe_subscription.current_period_end,
                tz=timezone.utc
            ).date()
            
            subscription = Subscription.objects.create(
                organization=organization,
                plan=plan,
                status='active' if stripe_subscription.status == 'active' else 'trialing',
                amount=Decimal(str(plan_config['price'])),
                current_period_start=current_period_start,
                current_period_end=current_period_end,
                payment_method='stripe',
            )
            
            # Update organization
            organization.stripe_subscription_id = stripe_subscription.id
            organization.plan = plan
            organization.status = 'active'
            organization.subscription_renew_date = current_period_end
            organization.save(update_fields=[
                'stripe_subscription_id', 'plan', 'status', 'subscription_renew_date'
            ])
            
            logger.info(f"Created subscription {stripe_subscription.id} for org {organization.slug}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {str(e)}")
            raise StripeError(f"Failed to create subscription: {str(e)}")
    
    @staticmethod
    def upgrade_plan(organization, new_plan):
        """Upgrade organization to a new plan"""
        try:
            if not organization.stripe_subscription_id:
                # No existing subscription, create new one
                return SubscriptionManager.create_subscription(organization, new_plan)
            
            # Get existing subscription
            stripe_sub = stripe.Subscription.retrieve(organization.stripe_subscription_id)
            
            plan_config = SubscriptionManager.PLAN_PRICING.get(new_plan)
            if not plan_config:
                raise StripeError(f"Invalid plan: {new_plan}")
            
            # Ensure Stripe products exist
            SubscriptionManager.ensure_stripe_products()
            
            # Get the price_id for this plan
            price_id = plan_config.get('price_id')
            if not price_id:
                raise StripeError(f"No price configured for plan {new_plan}")
            
            # Update subscription with new price
            updated_sub = stripe.Subscription.modify(
                stripe_sub.id,
                items=[{
                    'id': stripe_sub.items.data[0].id,
                    'price': price_id
                }],
                proration_behavior='create_prorations',  # Prorate the cost
            )
            
            # Update Subscription record
            subscription = organization.subscription
            subscription.plan = new_plan
            subscription.amount = Decimal(str(plan_config['price']))
            subscription.save()
            
            # Update organization
            organization.plan = new_plan
            organization.save(update_fields=['plan'])
            
            logger.info(f"Upgraded org {organization.slug} to plan {new_plan}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to upgrade plan: {str(e)}")
            raise StripeError(f"Failed to upgrade plan: {str(e)}")
    
    @staticmethod
    def cancel_subscription(organization, reason='customer_request'):
        """Cancel subscription for an organization"""
        try:
            if not organization.stripe_subscription_id:
                raise StripeError("No active Stripe subscription found")
            
            # Cancel in Stripe
            stripe.Subscription.delete(organization.stripe_subscription_id)
            
            # Update Subscription record
            subscription = organization.subscription
            subscription.status = 'cancelled'
            subscription.save()
            
            # Update organization
            organization.status = 'cancelled'
            organization.plan = 'free'
            organization.stripe_subscription_id = None
            organization.save(update_fields=['status', 'plan', 'stripe_subscription_id'])
            
            logger.info(f"Cancelled subscription for org {organization.slug} - reason: {reason}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {str(e)}")
            raise StripeError(f"Failed to cancel subscription: {str(e)}")
    
    @staticmethod
    def retry_failed_payment(organization):
        """Retry a failed payment"""
        try:
            if not organization.stripe_subscription_id:
                raise StripeError("No active Stripe subscription found")
            
            # Retrieve subscription
            stripe_sub = stripe.Subscription.retrieve(organization.stripe_subscription_id)
            
            # Retry payment on the subscription
            stripe.Subscription.modify(
                stripe_sub.id,
                off_session=True
            )
            
            # Update organization status
            organization.status = 'active'
            organization.save(update_fields=['status'])
            
            logger.info(f"Retried payment for org {organization.slug}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retry payment: {str(e)}")
            raise StripeError(f"Failed to retry payment: {str(e)}")
    
    @staticmethod
    def handle_webhook(event):
        """Handle Stripe webhook events"""
        event_type = event['type']
        data = event['data']['object']
        
        try:
            if event_type == 'customer.subscription.updated':
                SubscriptionManager._handle_subscription_updated(data)
            elif event_type == 'customer.subscription.deleted':
                SubscriptionManager._handle_subscription_deleted(data)
            elif event_type == 'invoice.payment_succeeded':
                SubscriptionManager._handle_payment_succeeded(data)
            elif event_type == 'invoice.payment_failed':
                SubscriptionManager._handle_payment_failed(data)
            elif event_type == 'charge.dispute.created':
                SubscriptionManager._handle_dispute_created(data)
            
            return True
        except Exception as e:
            logger.error(f"Error handling webhook {event_type}: {str(e)}")
            raise
    
    @staticmethod
    def _handle_subscription_updated(stripe_subscription):
        """Handle subscription.updated webhook"""
        try:
            org = Organization.objects.get(
                stripe_subscription_id=stripe_subscription['id']
            )
            status_map = {
                'active': 'active',
                'trialing': 'trialing',
                'past_due': 'past_due',
                'canceled': 'cancelled',
            }
            
            subscription = org.subscription
            subscription.status = status_map.get(stripe_subscription['status'], 'active')
            subscription.save()
            
            logger.info(f"Updated subscription status for org {org.slug}")
        except Organization.DoesNotExist:
            logger.warning(f"Org not found for subscription {stripe_subscription['id']}")
    
    @staticmethod
    def _handle_subscription_deleted(stripe_subscription):
        """Handle subscription.deleted webhook"""
        try:
            org = Organization.objects.get(
                stripe_subscription_id=stripe_subscription['id']
            )
            subscription = org.subscription
            subscription.status = 'cancelled'
            subscription.save()
            
            org.status = 'cancelled'
            org.save(update_fields=['status'])
            
            logger.info(f"Deleted subscription for org {org.slug}")
        except Organization.DoesNotExist:
            logger.warning(f"Org not found for subscription {stripe_subscription['id']}")
    
    @staticmethod
    def _handle_payment_succeeded(invoice_data):
        """Handle invoice.payment_succeeded webhook"""
        try:
            stripe_sub_id = invoice_data['subscription']
            org = Organization.objects.get(stripe_subscription_id=stripe_sub_id)
            
            # Create billing invoice record
            Invoice.objects.create(
                organization=org,
                subscription=org.subscription,
                invoice_number=f"INV-{org.id}-{invoice_data['number']}",
                stripe_invoice_id=invoice_data['id'],
                amount=Decimal(str(invoice_data['amount_paid'] / 100)),
                status='paid',
                due_date=timezone.now().date(),
                paid_date=timezone.now().date(),
                description=f"Subscription payment for {org.subscription.plan} plan"
            )
            
            # Update organization status
            org.status = 'active'
            org.save(update_fields=['status'])
            
            logger.info(f"Payment succeeded for org {org.slug}")
        except Organization.DoesNotExist:
            logger.warning(f"Org not found for invoice {invoice_data['id']}")
    
    @staticmethod
    def _handle_payment_failed(invoice_data):
        """Handle invoice.payment_failed webhook"""
        try:
            stripe_sub_id = invoice_data['subscription']
            org = Organization.objects.get(stripe_subscription_id=stripe_sub_id)
            
            # Update organization status
            org.status = 'suspended'
            org.save(update_fields=['status'])
            
            logger.info(f"Payment failed for org {org.slug}")
        except Organization.DoesNotExist:
            logger.warning(f"Org not found for invoice {invoice_data['id']}")
    
    @staticmethod
    def _handle_dispute_created(dispute_data):
        """Handle charge.dispute.created webhook"""
        logger.warning(f"Dispute created: {dispute_data['id']}")


class BillingService:
    """
    Billing operations and invoice generation.
    """
    
    @staticmethod
    @transaction.atomic
    def generate_invoice(organization, amount, description):
        """Generate a billing invoice for an organization"""
        invoice_number = Invoice.objects.filter(
            organization=organization
        ).count() + 1
        
        invoice = Invoice.objects.create(
            organization=organization,
            subscription=organization.subscription,
            invoice_number=f"INV-{organization.id}-{invoice_number:04d}",
            amount=amount,
            status='issued',
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            description=description
        )
        
        return invoice
    
    @staticmethod
    def get_monthly_revenue():
        """Get total monthly recurring revenue (MRR)"""
        active_subs = Subscription.objects.filter(status='active', is_active=True)
        total_mrr = sum(sub.amount for sub in active_subs)
        return Decimal(str(total_mrr))
    
    @staticmethod
    def get_churn_rate(days=30):
        """Calculate churn rate for the last N days"""
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        cancelled = Subscription.objects.filter(
            status='cancelled',
            updated_at__gte=start_date
        ).count()
        
        total = Subscription.objects.filter(is_active=True).count()
        
        if total == 0:
            return 0
        
        return (cancelled / total) * 100
