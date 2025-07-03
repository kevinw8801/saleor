from django.core.management.base import BaseCommand
from django.db import transaction

from saleor.attribute import AttributeInputType, AttributeType
from saleor.attribute.models import Attribute
from saleor.product import ProductTypeKind
from saleor.product.models import ProductType


class Command(BaseCommand):
    help = "Creates Portfolio product type with operation reference attribute"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if product type already exists',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        with transaction.atomic():
            # Check if Portfolio product type already exists
            portfolio_product_type = ProductType.objects.filter(slug="portfolio").first()
            
            if portfolio_product_type and not force:
                self.stdout.write(
                    self.style.WARNING('Portfolio product type already exists. Use --force to recreate.')
                )
                return

            if portfolio_product_type and force:
                self.stdout.write('Deleting existing Portfolio product type...')
                portfolio_product_type.delete()

            # Create the Portfolio product type
            self.stdout.write('Creating Portfolio product type...')
            portfolio_product_type = ProductType.objects.create(
                name="Portfolio",
                slug="portfolio",
                kind=ProductTypeKind.NORMAL,
                has_variants=False,
                is_shipping_required=False,  # Portfolios are not shippable
                is_digital=True,  # Digital product
            )

            # Create operation reference attribute
            self.stdout.write('Creating operation reference attribute...')
            operation_attr = Attribute.objects.create(
                slug="operation",
                name="Operation",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.REFERENCE,
                value_required=False,
                visible_in_storefront=True,
                filterable_in_dashboard=True,
                entity_type="tradex.Operation",  # Reference to our Operation model
            )

            # Create holdings reference attribute
            self.stdout.write('Creating holdings reference attribute...')
            holdings_attr = Attribute.objects.create(
                slug="holdings",
                name="Holdings",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.REFERENCE,
                value_required=False,
                visible_in_storefront=True,
                filterable_in_dashboard=True,
                entity_type="tradex.Holding",  # Reference to our Holding model
            )

            # Create portfolio management attributes
            self.stdout.write('Creating portfolio management attributes...')
            
            # Portfolio name attribute
            portfolio_name_attr = Attribute.objects.create(
                slug="portfolio-name",
                name="Portfolio Name",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.PLAIN_TEXT,
                value_required=True,
                visible_in_storefront=True,
                filterable_in_dashboard=True,
            )

            # Portfolio type attribute
            portfolio_type_attr = Attribute.objects.create(
                slug="portfolio-type",
                name="Portfolio Type",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.DROPDOWN,
                value_required=False,
                visible_in_storefront=True,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
            )

            # Create portfolio type values
            from saleor.attribute.models import AttributeValue
            portfolio_types = [
                ("equity", "Equity Portfolio"),
                ("bond", "Bond Portfolio"),
                ("mixed", "Mixed Portfolio"),
                ("etf", "ETF Portfolio"),
                ("mutual-fund", "Mutual Fund Portfolio"),
            ]
            
            for slug, name in portfolio_types:
                AttributeValue.objects.create(
                    attribute=portfolio_type_attr,
                    name=name,
                    slug=slug,
                )

            # Base currency attribute
            base_currency_attr = Attribute.objects.create(
                slug="base-currency",
                name="Base Currency",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.DROPDOWN,
                value_required=True,
                visible_in_storefront=True,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
            )

            # Create common currency values
            currencies = [
                ("USD", "US Dollar"),
                ("EUR", "Euro"),
                ("GBP", "British Pound"),
                ("JPY", "Japanese Yen"),
                ("CHF", "Swiss Franc"),
                ("CAD", "Canadian Dollar"),
                ("AUD", "Australian Dollar"),
            ]
            
            for code, name in currencies:
                AttributeValue.objects.create(
                    attribute=base_currency_attr,
                    name=f"{name} ({code})",
                    slug=code.lower(),
                    value=code,
                )

            # Cash balance attribute
            cash_attr = Attribute.objects.create(
                slug="cash",
                name="Cash",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.NUMERIC,
                value_required=False,
                visible_in_storefront=True,
                filterable_in_dashboard=True,
            )

            # Risk level attribute
            risk_level_attr = Attribute.objects.create(
                slug="risk-level",
                name="Risk Level",
                type=AttributeType.PRODUCT_TYPE,
                input_type=AttributeInputType.DROPDOWN,
                value_required=False,
                visible_in_storefront=True,
                filterable_in_storefront=True,
                filterable_in_dashboard=True,
            )

            # Create risk level values
            risk_levels = [
                ("low", "Low Risk"),
                ("medium", "Medium Risk"),
                ("high", "High Risk"),
                ("very-high", "Very High Risk"),
            ]
            
            for slug, name in risk_levels:
                AttributeValue.objects.create(
                    attribute=risk_level_attr,
                    name=name,
                    slug=slug,
                )

            # Assign attributes to the product type
            self.stdout.write('Assigning attributes to Portfolio product type...')
            portfolio_product_type.product_attributes.add(
                operation_attr,
                holdings_attr,
                portfolio_name_attr,
                portfolio_type_attr,
                base_currency_attr,
                cash_attr,
                risk_level_attr,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created Portfolio product type with {portfolio_product_type.product_attributes.count()} attributes'
                )
            )
            
            # Display summary
            self.stdout.write('\nSummary:')
            self.stdout.write(f'- Product Type: {portfolio_product_type.name} (slug: {portfolio_product_type.slug})')
            self.stdout.write(f'- Shipping Required: {portfolio_product_type.is_shipping_required}')
            self.stdout.write(f'- Digital Product: {portfolio_product_type.is_digital}')
            self.stdout.write(f'- Has Variants: {portfolio_product_type.has_variants}')
            self.stdout.write('\nAttributes:')
            for attr in portfolio_product_type.product_attributes.all():
                self.stdout.write(f'- {attr.name} ({attr.input_type})')
                if attr.input_type == AttributeInputType.DROPDOWN:
                    values = [v.name for v in attr.values.all()]
                    if values:
                        self.stdout.write(f'  Values: {", ".join(values)}')