"""
GraphQL types for TradEx plugin models.
"""
import graphene
from graphene import relay

from ...graphql.core.types import BaseObjectType
from ...graphql.core.scalars import DateTime, Decimal
from .models import Operation, Holding


class OperationType(BaseObjectType):
    """GraphQL type for Operation model."""
    
    id = graphene.ID()
    date_time = DateTime(description="Date and time when the operation occurred")
    operation = graphene.String(description="Type of operation")
    equity_id = graphene.String(description="Equity identifier")
    equity_name = graphene.String(description="Human-readable name of the equity")
    market = graphene.String(description="Market or exchange")
    amount = Decimal(description="Amount or quantity")
    fee = Decimal(description="Fee charged for the operation")
    currency = graphene.String(description="Currency code")
    price = Decimal(description="Price per unit")
    status = graphene.String(description="Status of the operation")
    created_at = DateTime(description="Creation timestamp")
    updated_at = DateTime(description="Last update timestamp")
    
    total_value = Decimal(description="Total value including fees")
    net_value = Decimal(description="Net value excluding fees")

    def resolve_total_value(self, info):
        """Resolve total value including fees."""
        return self.total_value

    def resolve_net_value(self, info):
        """Resolve net value excluding fees."""
        return self.net_value


class HoldingType(BaseObjectType):
    """GraphQL type for Holding model."""
    
    id = graphene.ID()
    amount = graphene.Int(description="Amount or quantity of the holding")
    purchase_price = Decimal(description="Purchase price per unit")
    purchase_time = DateTime(description="Date and time when the holding was purchased")
    market = graphene.String(description="Market or exchange")
    currency = graphene.String(description="Currency code")
    created_at = DateTime(description="Creation timestamp")
    updated_at = DateTime(description="Last update timestamp")
    
    total_value = Decimal(description="Total value of the holding")
    
    def resolve_total_value(self, info):
        """Resolve total value of the holding."""
        return self.total_value


# Input types for mutations
class OperationInput(graphene.InputObjectType):
    """Input type for creating operations."""
    date_time = DateTime(required=True)
    operation = graphene.String(required=True)
    equity_id = graphene.String(required=True)
    equity_name = graphene.String(required=True)
    market = graphene.String(required=True)
    amount = Decimal(required=True)
    fee = Decimal(required=True)
    currency = graphene.String(required=True)
    price = Decimal(required=True)
    status = graphene.String(required=True)


class OperationUpdateInput(graphene.InputObjectType):
    """Input type for updating operations."""
    date_time = DateTime()
    operation = graphene.String()
    equity_id = graphene.String()
    equity_name = graphene.String()
    market = graphene.String()
    amount = Decimal()
    fee = Decimal()
    currency = graphene.String()
    price = Decimal()
    status = graphene.String()


class HoldingInput(graphene.InputObjectType):
    """Input type for creating holdings."""
    id = graphene.String(required=False)
    amount = graphene.Int(required=True)
    purchase_price = Decimal(required=True)
    purchase_time = DateTime(required=True)
    market = graphene.String(required=True)
    currency = graphene.String(required=True)


class HoldingUpdateInput(graphene.InputObjectType):
    """Input type for updating holdings."""
    amount = graphene.Int()
    purchase_price = Decimal()
    purchase_time = DateTime()
    market = graphene.String()
    currency = graphene.String()