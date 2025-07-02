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


def get_portfolio_product_type_config():
    """
    Returns the configuration for the Portfolio product type.
    
    Returns:
        dict: Configuration dictionary with product type and attribute specifications.
    """
    return {
        "product_type": {
            "name": "Portfolio",
            "slug": "portfolio", 
            "kind": "normal",  # ProductTypeKind.NORMAL
            "has_variants": False,
            "is_shipping_required": False,  # Not shippable
            "is_digital": True,  # Digital product
        },
        "attributes": [
            {
                "slug": "operation",
                "name": "Operation",
                "type": "product-type",  # AttributeType.PRODUCT_TYPE
                "input_type": "reference",  # AttributeInputType.REFERENCE
                "entity_type": "tradex.Operation",
                "value_required": False,
                "visible_in_storefront": True,
                "filterable_in_dashboard": True,
                "values": []  # Reference attributes point to model instances
            },
            {
                "slug": "portfolio-name",
                "name": "Portfolio Name",
                "type": "product-type",
                "input_type": "plain-text",  # AttributeInputType.PLAIN_TEXT
                "value_required": True,
                "visible_in_storefront": True,
                "filterable_in_dashboard": True,
                "values": []
            },
            {
                "slug": "portfolio-type",
                "name": "Portfolio Type",
                "type": "product-type",
                "input_type": "dropdown",  # AttributeInputType.DROPDOWN
                "value_required": False,
                "visible_in_storefront": True,
                "filterable_in_storefront": True,
                "filterable_in_dashboard": True,
                "values": [
                    {"slug": "equity", "name": "Equity Portfolio"},
                    {"slug": "bond", "name": "Bond Portfolio"},
                    {"slug": "mixed", "name": "Mixed Portfolio"},
                    {"slug": "etf", "name": "ETF Portfolio"},
                    {"slug": "mutual-fund", "name": "Mutual Fund Portfolio"},
                ]
            },
            {
                "slug": "base-currency",
                "name": "Base Currency",
                "type": "product-type",
                "input_type": "dropdown",
                "value_required": True,
                "visible_in_storefront": True,
                "filterable_in_storefront": True,
                "filterable_in_dashboard": True,
                "values": [
                    {"slug": "usd", "name": "US Dollar (USD)", "value": "USD"},
                    {"slug": "eur", "name": "Euro (EUR)", "value": "EUR"},
                    {"slug": "gbp", "name": "British Pound (GBP)", "value": "GBP"},
                    {"slug": "jpy", "name": "Japanese Yen (JPY)", "value": "JPY"},
                    {"slug": "chf", "name": "Swiss Franc (CHF)", "value": "CHF"},
                    {"slug": "cad", "name": "Canadian Dollar (CAD)", "value": "CAD"},
                    {"slug": "aud", "name": "Australian Dollar (AUD)", "value": "AUD"},
                ]
            },
            {
                "slug": "risk-level",
                "name": "Risk Level",
                "type": "product-type",
                "input_type": "dropdown",
                "value_required": False,
                "visible_in_storefront": True,
                "filterable_in_storefront": True,
                "filterable_in_dashboard": True,
                "values": [
                    {"slug": "low", "name": "Low Risk"},
                    {"slug": "medium", "name": "Medium Risk"},
                    {"slug": "high", "name": "High Risk"},
                    {"slug": "very-high", "name": "Very High Risk"},
                ]
            }
        ]
    }


def get_operation_model_structure():
    """
    Returns the Operation model structure and field specifications.
    
    Returns:
        dict: Operation model field specifications.
    """
    return {
        "model_name": "Operation",
        "db_table": "tradex_operation",
        "description": "Model to store trading operations data",
        "fields": [
            {
                "name": "date_time",
                "type": "DateTimeField",
                "description": "Date and time when the operation occurred",
                "required": True
            },
            {
                "name": "operation",
                "type": "CharField(max_length=100)",
                "description": "Type of operation (e.g., buy, sell, dividend, split)",
                "required": True
            },
            {
                "name": "equity_id",
                "type": "CharField(max_length=50)",
                "description": "Equity identifier (ticker symbol, ISIN, etc.)",
                "required": True,
                "indexed": True
            },
            {
                "name": "equity_name",
                "type": "CharField(max_length=255)",
                "description": "Human-readable name of the equity",
                "required": True
            },
            {
                "name": "market",
                "type": "CharField(max_length=100)",
                "description": "Market or exchange where the operation took place",
                "required": True,
                "indexed": True
            },
            {
                "name": "amount",
                "type": "DecimalField(max_digits=15, decimal_places=6)",
                "description": "Amount or quantity of the operation (non-negative)",
                "required": True,
                "validators": ["MinValueValidator(0)"]
            },
            {
                "name": "fee",
                "type": "DecimalField(max_digits=12, decimal_places=4)",
                "description": "Fee charged for the operation (non-negative)",
                "required": True,
                "validators": ["MinValueValidator(0)"]
            },
            {
                "name": "currency",
                "type": "CharField(max_length=3)",
                "description": "Currency code (ISO 4217 format, e.g., USD, EUR)",
                "required": True
            },
            {
                "name": "price",
                "type": "DecimalField(max_digits=15, decimal_places=6)",
                "description": "Price per unit (non-negative)",
                "required": True,
                "validators": ["MinValueValidator(0)"]
            },
            {
                "name": "status",
                "type": "CharField(max_length=50)",
                "description": "Status of the operation (e.g., completed, pending, failed)",
                "required": True,
                "indexed": True
            }
        ],
        "indexes": [
            "equity_id",
            "date_time", 
            "operation",
            "status",
            "market"
        ],
        "methods": [
            "total_value: Calculate total value including fees",
            "net_value: Calculate net value excluding fees"
        ]
    }


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
            "Portfolio product type with operation references",
            "Operation model for trading data storage",
            "Trading-specific attributes (frequency, auto-renew, trial-period-days)",
            "Portfolio management attributes (name, type, currency, risk level)",
            "API integration configuration",
            "Webhook support",
            "Sandbox mode for testing"
        ],
        "configuration_options": [
            "api_key (Secret)",
            "api_secret (Secret)", 
            "sandbox_mode (Boolean)",
            "webhook_url (String)",
            "auto_setup_utility_type (Boolean)",
            "auto_setup_portfolio_type (Boolean)"
        ],
        "models": [
            "Operation: Trading operations data with 10 fields and 5 indexes"
        ],
        "product_types": {
            "utility": {
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
            "portfolio": {
                "characteristics": [
                    "Not shippable (is_shipping_required=False)",
                    "Digital product (is_digital=True)",
                    "No variants (has_variants=False)",
                    "Regular product type (kind=normal)"
                ],
                "attributes": [
                    "Operation: Reference to Operation model instances",
                    "Portfolio Name: Plain text field for portfolio identification",
                    "Portfolio Type: Dropdown with equity/bond/mixed/etf/mutual-fund options",
                    "Base Currency: Dropdown with major currencies (USD, EUR, GBP, etc.)",
                    "Risk Level: Dropdown with low/medium/high/very-high options"
                ]
            }
        },
        "management_commands": [
            "setup_utility_product_type: Creates the Utility product type with attributes",
            "setup_portfolio_product_type: Creates the Portfolio product type with operation references"
        ],
        "methods": [
            "setup_utility_product_type(): Public method to manually setup the utility product type",
            "setup_portfolio_product_type(): Public method to manually setup the portfolio product type",
            "setup_all_product_types(): Public method to setup both product types",
            "_setup_utility_product_type(): Private method for automatic utility setup",
            "_setup_portfolio_product_type(): Private method for automatic portfolio setup"
        ]
    }