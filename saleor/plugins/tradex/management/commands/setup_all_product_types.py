from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Sets up both Utility and Portfolio product types for Tradex plugin"

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if product types already exist',
        )
        parser.add_argument(
            '--utility-only',
            action='store_true',
            help='Setup only Utility product type',
        )
        parser.add_argument(
            '--portfolio-only',
            action='store_true',
            help='Setup only Portfolio product type',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        utility_only = options.get('utility_only', False)
        portfolio_only = options.get('portfolio_only', False)
        
        # If both flags are set or neither, setup both
        if (utility_only and portfolio_only) or (not utility_only and not portfolio_only):
            utility_only = False
            portfolio_only = False
        
        self.stdout.write(
            self.style.SUCCESS('Setting up Tradex plugin product types...\n')
        )

        if not portfolio_only:
            self.stdout.write('=== Setting up Utility Product Type ===')
            try:
                call_command('setup_utility_product_type', force=force, verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS('✓ Utility product type setup completed\n')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Utility product type setup failed: {e}\n')
                )

        if not utility_only:
            self.stdout.write('=== Setting up Portfolio Product Type ===')
            try:
                call_command('setup_portfolio_product_type', force=force, verbosity=1)
                self.stdout.write(
                    self.style.SUCCESS('✓ Portfolio product type setup completed\n')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Portfolio product type setup failed: {e}\n')
                )

        self.stdout.write(
            self.style.SUCCESS('All requested product types have been processed!')
        )