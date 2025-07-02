"""
Utility functions for the Tradex plugin.
This module provides helper functions for managing the Utility product type.
"""

def get_utility_product_type_config():
    """
    Returns the configuration for the Utility product type.
    
    Returns:
        dict: Configuration dictionary with product type and attribute specifications.
    """
    return {
        "product_type": {
            "name": "Utility",
            "slug": "utility",
            "kind": "normal",  # ProductTypeKind.NORMAL
            "has_variants": False,
            "is_shipping_required": False,  # Not shippable as requested
            "is_digital": True,  # Makes sense for utility products
        },
        "attributes": [
            {
                "slug": "frequency",
                "name": "Frequency",
                "type": "product-type",  # AttributeType.PRODUCT_TYPE
                "input_type": "dropdown",  # AttributeInputType.DROPDOWN
                "value_required": False,
                "visible_in_storefront": True,
                "filterable_in_storefront": True,
                "filterable_in_dashboard": True,
                "values": [
                    {"slug": "daily", "name": "Daily"},
                    {"slug": "weekly", "name": "Weekly"},
                    {"slug": "monthly", "name": "Monthly"},
                    {"slug": "quarterly", "name": "Quarterly"},
                    {"slug": "yearly", "name": "Yearly"},
                ]
            },
            {
                "slug": "auto-renew",
                "name": "Auto Renew",
                "type": "product-type",  # AttributeType.PRODUCT_TYPE
                "input_type": "boolean",  # AttributeInputType.BOOLEAN
                "value_required": False,
                "visible_in_storefront": True,
                "filterable_in_storefront": True,
                "filterable_in_dashboard": True,
                "values": []  # Boolean attributes don't need predefined values
            },
            {
                "slug": "trial-period-days",
                "name": "Trial Period Days",
                "type": "product-type",  # AttributeType.PRODUCT_TYPE
                "input_type": "numeric",  # AttributeInputType.NUMERIC
                "value_required": False,
                "visible_in_storefront": True,
                "filterable_in_dashboard": True,
                "values": []  # Numeric attributes don't need predefined values
            }
        ]
    }


def validate_utility_product_type_setup():
    """
    Validates that the Utility product type configuration is correct.
    
    Returns:
        tuple: (is_valid, validation_messages)
    """
    config = get_utility_product_type_config()
    messages = []
    is_valid = True
    
    # Validate product type
    product_type = config["product_type"]
    if not product_type.get("name"):
        messages.append("Product type name is required")
        is_valid = False
    
    if not product_type.get("slug"):
        messages.append("Product type slug is required")
        is_valid = False
    
    if product_type.get("is_shipping_required", True):
        messages.append("Warning: Utility product type should not require shipping")
    
    # Validate attributes
    attributes = config["attributes"]
    if len(attributes) != 3:
        messages.append(f"Expected 3 attributes, found {len(attributes)}")
        is_valid = False
    
    required_attribute_slugs = {"frequency", "auto-renew", "trial-period-days"}
    found_attribute_slugs = {attr["slug"] for attr in attributes}
    
    missing_attributes = required_attribute_slugs - found_attribute_slugs
    if missing_attributes:
        messages.append(f"Missing required attributes: {missing_attributes}")
        is_valid = False
    
    # Validate frequency attribute has values
    frequency_attr = next((attr for attr in attributes if attr["slug"] == "frequency"), None)
    if frequency_attr and len(frequency_attr.get("values", [])) == 0:
        messages.append("Frequency attribute should have predefined values")
        is_valid = False
    
    if is_valid:
        messages.append("Utility product type configuration is valid")
    
    return is_valid, messages


def get_plugin_summary():
    """
    Returns a summary of the Tradex plugin functionality.
    
    Returns:
        dict: Plugin summary with features and configuration.
    """
    return {
        "plugin_id": "tradex.plugin",
        "plugin_name": "Tradex",
        "description": "Trading and exchange functionality plugin for Saleor",
        "features": [
            "Utility product type creation",
            "Trading-specific attributes (frequency, auto-renew, trial-period-days)",
            "API integration configuration",
            "Webhook support",
            "Sandbox mode for testing"
        ],
        "configuration_options": [
            "api_key (Secret)",
            "api_secret (Secret)", 
            "sandbox_mode (Boolean)",
            "webhook_url (String)",
            "auto_setup_utility_type (Boolean)"
        ],
        "utility_product_type": {
            "characteristics": [
                "Not shippable (is_shipping_required=False)",
                "Digital product (is_digital=True)",
                "No variants (has_variants=False)",
                "Regular product type (kind=normal)"
            ],
            "attributes": [
                "Frequency: Dropdown with daily/weekly/monthly/quarterly/yearly options",
                "Auto Renew: Boolean field for automatic renewal",
                "Trial Period Days: Numeric field for trial period length"
            ]
        },
        "management_commands": [
            "setup_utility_product_type: Creates the Utility product type with attributes"
        ],
        "methods": [
            "setup_utility_product_type(): Public method to manually setup the product type",
            "_setup_utility_product_type(): Private method for automatic setup on plugin activation"
        ]
    }