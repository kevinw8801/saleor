from django.core.management.base import BaseCommand
from django.db import transaction

from saleor.attribute import AttributeInputType, AttributeType
from saleor.attribute.models import Attribute, AttributeValue
from saleor.product import ProductTypeKind
from saleor.product.models import ProductType


class Command(BaseCommand):
    help = "Creates Utility product type with trading-specific attributes"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if product type already exists',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        with transaction.atomic():
            # Check if Utility product type already exists
            utility_product_type = ProductType.objects.filter(slug="utility").first()
            
            if utility_product_type and not force:
                self.stdout.write(
                    self.style.WARNING('Utility product type already exists. Use --force to recreate.')
                )
                return

            if utility_product_type and force:
                self.stdout.write('Deleting existing Utility product type...')
                utility_product_type.delete()

            # Create the Utility product type
            self.stdout.write('Creating Utility product type...')
            utility_product_type = ProductType.objects.create(
                name="Utility",
                slug="utility",
                kind=ProductTypeKind.NORMAL,
                has_variants=False,
                is_shipping_required=False,  # Not shippable as requested
                is_digital=True,  # Makes sense for utility products
            )

            # Create frequency attribute
            self.stdout.write('Creating frequency attribute...')
            frequency_attr = Attribute.objects.create(
                slug="frequency",
                name="Frequency",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.DROPDOWN,
                value_required=False,
                visible_in_storefront=True,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
            )

            # Create frequency attribute values
            frequency_values = [
                ("daily", "Daily"),
                ("weekly", "Weekly"),
                ("monthly", "Monthly"),
                ("quarterly", "Quarterly"),
                ("yearly", "Yearly"),
            ]
            
            for slug, name in frequency_values:
                AttributeValue.objects.create(
                    attribute=frequency_attr,
                    name=name,
                    slug=slug,
                )

            # Create auto-renew attribute (boolean)
            self.stdout.write('Creating auto-renew attribute...')
            auto_renew_attr = Attribute.objects.create(
                slug="auto-renew",
                name="Auto Renew",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.BOOLEAN,
                value_required=False,
                visible_in_storefront=True,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
            )

            # Create trial-period-days attribute (numeric)
            self.stdout.write('Creating trial-period-days attribute...')
            trial_period_attr = Attribute.objects.create(
                slug="trial-period-days",
                name="Trial Period Days",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.NUMERIC,
                value_required=False,
                visible_in_storefront=True,
                filterable_in_dashboard=True,
            )

            # Assign attributes to the product type
            self.stdout.write('Assigning attributes to Utility product type...')
            utility_product_type.product_attributes.add(
                frequency_attr,
                auto_renew_attr,
                trial_period_attr,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created Utility product type with {utility_product_type.product_attributes.count()} attributes'
                )
            )
            
            # Display summary
            self.stdout.write('\nSummary:')
            self.stdout.write(f'- Product Type: {utility_product_type.name} (slug: {utility_product_type.slug})')
            self.stdout.write(f'- Shipping Required: {utility_product_type.is_shipping_required}')
            self.stdout.write(f'- Digital Product: {utility_product_type.is_digital}')
            self.stdout.write(f'- Has Variants: {utility_product_type.has_variants}')
            self.stdout.write('\nAttributes:')
            for attr in utility_product_type.product_attributes.all():
                self.stdout.write(f'- {attr.name} ({attr.input_type})')
                if attr.input_type == AttributeInputType.DROPDOWN:
                    values = [v.name for v in attr.values.all()]
                    self.stdout.write(f'  Values: {", ".join(values)}')