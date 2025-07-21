"""
GraphQL types for TradEx plugin models.
"""
import graphene
from graphene import relay
from graphene_django import DjangoObjectType

from .models import Operation, Holding


class OperationType(DjangoObjectType):
    """GraphQL type for Operation model."""
    
    total_value = graphene.Decimal(description="Total value including fees")
    net_value = graphene.Decimal(description="Net value excluding fees")
    
    class Meta:
        model = Operation
        interfaces = (relay.Node,)
        fields = (
            'id', 'date_time', 'operation', 'equity_id', 'equity_name',
            'market', 'amount', 'fee', 'currency', 'price', 'status',
            'created_at', 'updated_at'
        )
    
    def resolve_total_value(self, info):
        """Resolve total value including fees."""
        return self.total_value
    
    def resolve_net_value(self, info):
        """Resolve net value excluding fees."""
        return self.net_value


class HoldingType(DjangoObjectType):
    """GraphQL type for Holding model."""
    
    total_value = graphene.Decimal(description="Total value of the holding")
    
    class Meta:
        model = Holding
        interfaces = (relay.Node,)
        fields = (
            'id', 'amount', 'purchase_price', 'purchase_time',
            'market', 'currency', 'created_at', 'updated_at'
        )
    
    def resolve_total_value(self, info):
        """Resolve total value of the holding."""
        return self.total_value


class OperationInput(graphene.InputObjectType):
    """Input type for creating/updating operations."""
    
    date_time = graphene.DateTime(required=True, description="Date and time of operation")
    operation = graphene.String(required=True, description="Type of operation (buy, sell, etc.)")
    equity_id = graphene.String(required=True, description="Equity identifier")
    equity_name = graphene.String(required=True, description="Human-readable equity name")
    market = graphene.String(required=True, description="Market or exchange")
    amount = graphene.Decimal(required=True, description="Amount or quantity")
    fee = graphene.Decimal(required=True, description="Operation fee")
    currency = graphene.String(required=True, description="Currency code (ISO 4217)")
    price = graphene.Decimal(required=True, description="Price per unit")
    status = graphene.String(required=True, description="Operation status")


class HoldingInput(graphene.InputObjectType):
    """Input type for creating/updating holdings."""
    
    id = graphene.String(required=True, description="Unique holding identifier")
    amount = graphene.Int(required=True, description="Amount or quantity")
    purchase_price = graphene.Decimal(required=True, description="Purchase price per unit")
    purchase_time = graphene.DateTime(required=True, description="Purchase timestamp")
    market = graphene.String(required=True, description="Market or exchange")
    currency = graphene.String(required=True, description="Currency code (ISO 4217)")


class OperationUpdateInput(graphene.InputObjectType):
    """Input type for updating operations (all fields optional)."""
    
    date_time = graphene.DateTime(description="Date and time of operation")
    operation = graphene.String(description="Type of operation (buy, sell, etc.)")
    equity_id = graphene.String(description="Equity identifier")
    equity_name = graphene.String(description="Human-readable equity name")
    market = graphene.String(description="Market or exchange")
    amount = graphene.Decimal(description="Amount or quantity")
    fee = graphene.Decimal(description="Operation fee")
    currency = graphene.String(description="Currency code (ISO 4217)")
    price = graphene.Decimal(description="Price per unit")
    status = graphene.String(description="Operation status")


class HoldingUpdateInput(graphene.InputObjectType):
    """Input type for updating holdings (all fields optional except id)."""
    
    amount = graphene.Int(description="Amount or quantity")
    purchase_price = graphene.Decimal(description="Purchase price per unit")
    purchase_time = graphene.DateTime(description="Purchase timestamp")
    market = graphene.String(description="Market or exchange")
    currency = graphene.String(description="Currency code (ISO 4217)")