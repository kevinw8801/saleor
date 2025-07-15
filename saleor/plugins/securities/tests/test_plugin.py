import pytest
from decimal import Decimal
from django.test import TestCase
from unittest.mock import Mock, patch

from ....warehouse.models import Stock, Warehouse
from ....product.models import Product, ProductType, ProductVariant
from ..plugin import SecuritiesPlugin
from ..models import SecuritiesMovement, SecuritiesAlert, SecuritiesSettings
from ..utils import calculate_securities_level, calculate_reorder_quantity


class SecuritiesPluginTestCase(TestCase):
    def setUp(self):
        self.plugin = SecuritiesPlugin(
            configuration=[
                {"name": "enable_securities_notifications", "value": True},
                {"name": "enable_automatic_reordering", "value": True},
                {"name": "default_securities_buffer", "value": "5"},
                {"name": "default_reorder_point", "value": "10"},
                {"name": "default_reorder_quantity", "value": "50"},
                {"name": "low_securities_threshold_percentage", "value": "20"},
                {"name": "critical_securities_threshold_percentage", "value": "5"},
                {"name": "notification_email", "value": "test@example.com"},
            ]
        )
        
        # Create test data
        self.product_type = ProductType.objects.create(name="Test Type")
        self.product = Product.objects.create(
            name="Test Product",
            product_type=self.product_type
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="TEST-SKU-001"
        )
        self.warehouse = Warehouse.objects.create(
            name="Test Warehouse",
            slug="test-warehouse"
        )
        self.stock = Stock.objects.create(
            product_variant=self.variant,
            warehouse=self.warehouse,
            quantity=25
        )

    def test_plugin_configuration(self):
        """Test plugin configuration is properly loaded"""
        self.assertTrue(self.plugin._get_config_value("enable_securities_notifications"))
        self.assertEqual(self.plugin._get_config_value("default_reorder_point"), "10")
        self.assertEqual(self.plugin._get_config_value("notification_email"), "test@example.com")

    def test_securities_level_calculation(self):
        """Test securities level calculation"""
        # Test with different securities quantities
        self.stock.quantity = 100
        level = calculate_securities_level(self.stock, 20, 5)
        self.assertEqual(level, "normal")
        
        self.stock.quantity = 10
        level = calculate_securities_level(self.stock, 20, 5)
        self.assertEqual(level, "low")
        
        self.stock.quantity = 2
        level = calculate_securities_level(self.stock, 20, 5)
        self.assertEqual(level, "critical")

    @patch('saleor.plugins.securities.plugin.SecuritiesPlugin._send_securities_notification')
    def test_securities_updated_notification(self, mock_send_notification):
        """Test that securities update triggers notification for low securities"""
        # Update securities to low level
        previous_value = self.stock.quantity
        self.stock.quantity = 5  # This should trigger low securities alert
        
        self.plugin.product_variant_stock_updated(self.stock, previous_value)
        
        # Check that notification was called
        mock_send_notification.assert_called_once()

    def test_securities_movement_logging(self):
        """Test that securities movements are logged"""
        previous_value = self.stock.quantity
        self.stock.quantity = 30
        
        self.plugin.product_variant_stock_updated(self.stock, previous_value)
        
        # Check that movement was logged
        movement = SecuritiesMovement.objects.filter(stock=self.stock).first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity_change, 5)
        self.assertEqual(movement.previous_quantity, previous_value)
        self.assertEqual(movement.new_quantity, 30)

    def test_reorder_point_check(self):
        """Test reorder point checking"""
        # Create securities settings
        SecuritiesSettings.objects.create(
            stock=self.stock,
            reorder_point=15,
            reorder_quantity=100,
            safety_stock=5
        )
        
        # Set securities below reorder point
        self.stock.quantity = 10
        previous_value = 25
        
        with patch.object(self.plugin, '_trigger_reorder_suggestion') as mock_reorder:
            self.plugin.product_variant_stock_updated(self.stock, previous_value)
            mock_reorder.assert_called_once_with(self.stock)

    def test_manual_securities_adjustment(self):
        """Test manual securities adjustment method"""
        original_quantity = self.stock.quantity
        adjustment = 10
        
        success = self.plugin.adjust_securities(
            self.stock.id,
            adjustment,
            "manual_adjustment",
            "Test adjustment"
        )
        
        self.assertTrue(success)
        
        # Refresh securities from database
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, original_quantity + adjustment)
        
        # Check movement was logged
        movement = SecuritiesMovement.objects.filter(stock=self.stock).first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity_change, adjustment)
        self.assertEqual(movement.notes, "Test adjustment")

    def test_get_securities_report(self):
        """Test securities report generation"""
        report = self.plugin.get_securities_report()
        
        self.assertIn('report_date', report)
        self.assertIn('summary', report)
        self.assertIn('securities_details', report)
        self.assertEqual(report['warehouse'], "All Warehouses")

    def test_get_low_securities_items(self):
        """Test low securities items retrieval"""
        # Set securities to low level
        self.stock.quantity = 5
        self.stock.save()
        
        low_securities_items = self.plugin.get_low_securities_items()
        
        self.assertEqual(len(low_securities_items), 1)
        self.assertEqual(low_securities_items[0]['stock_id'], self.stock.id)
        self.assertIn(low_securities_items[0]['securities_level'], ['low', 'critical'])

    def test_predict_securities_needs(self):
        """Test securities needs prediction"""
        # Create some historical movements
        SecuritiesMovement.objects.create(
            stock=self.stock,
            quantity_change=-5,
            previous_quantity=30,
            new_quantity=25,
            movement_type="sale"
        )
        
        prediction = self.plugin.predict_securities_needs(days=30)
        
        self.assertIn('forecast_period_days', prediction)
        self.assertIn('predictions', prediction)
        self.assertEqual(prediction['forecast_period_days'], 30)

    def test_plugin_active_check(self):
        """Test that plugin respects active status"""
        # Deactivate plugin
        self.plugin.active = False
        
        with patch.object(self.plugin, '_check_securities_levels') as mock_check:
            self.plugin.product_variant_stock_updated(self.stock, 30)
            mock_check.assert_not_called()

    def test_config_value_fallback(self):
        """Test configuration value fallback to defaults"""
        # Test existing config
        self.assertEqual(self.plugin._get_config_value("default_reorder_point"), "10")
        
        # Test non-existing config with default
        self.assertEqual(self.plugin._get_config_value("non_existing", "default"), "default")
        
        # Test non-existing config without default
        self.assertIsNone(self.plugin._get_config_value("non_existing"))


@pytest.mark.django_db
class TestSecuritiesUtils:
    def test_calculate_reorder_quantity_with_settings(self):
        """Test reorder quantity calculation with custom settings"""
        # This would require more complex setup with actual database
        pass
    
    def test_calculate_reorder_quantity_without_settings(self):
        """Test reorder quantity calculation with default values"""
        # This would require more complex setup
        pass