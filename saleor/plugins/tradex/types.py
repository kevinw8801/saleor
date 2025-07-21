"""
GraphQL types for TradEx plugin models.
"""
import graphene
from graphene import relay

from ...graphql.core.types import BaseObjectType
from ...graphql.core.scalars import DateTime
from .models import Operation, Holding


class OperationType(BaseObjectType):
    """GraphQL type for Operation model."""
    
    id = graphene.ID()
    date_time = DateTime(description="Date and time when the operation occurred")
    operation = graphene.String(description="Type of operation")
    equity_id = graphene.String(description="Equity identifier")
    equity_name = graphene.String(description="Human-readable name of the equity")
    market = graphene.String(description="Market or exchange")
    amount = graphene.Decimal(description="Amount or quantity")
    fee = graphene.Decimal(description="Fee charged for the operation")
    currency = graphene.String(description="Currency code")
    price = graphene.Decimal(description="Price per unit")
    status = graphene.String(description="Status of the operation")
    created_at = DateTime(description="Creation timestamp")
    updated_at = DateTime(description="Last update timestamp")
    
    total_value = graphene.Decimal(description="Total value including fees")
    net_value = graphene.Decimal(description="Net value excluding fees")

    def resolve_total_value(self, info):
        """Resolve total value including fees."""
        return self.total_value

    def resolve_net_value(self, info):
        """Resolve net value excluding fees."""
        return self.net_value


class HoldingType(BaseObjectType):
    """GraphQL type for Holding model."""
    
    id = graphene.ID()
    equity_id = graphene.String(description="Equity identifier")
    equity_name = graphene.String(description="Human-readable name of the equity")
    market = graphene.String(description="Market or exchange")
    shares = graphene.Decimal(description="Number of shares held")
    avg_price = graphene.Decimal(description="Average price per share")
    currency = graphene.String(description="Currency code")
    created_at = DateTime(description="Creation timestamp")
    updated_at = DateTime(description="Last update timestamp")
    
    total_value = graphene.Decimal(description="Total value of the holding")
    
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
    amount = graphene.Decimal(required=True)
    fee = graphene.Decimal(required=True)
    currency = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    status = graphene.String(required=True)


class OperationUpdateInput(graphene.InputObjectType):
    """Input type for updating operations."""
    date_time = DateTime()
    operation = graphene.String()
    equity_id = graphene.String()
    equity_name = graphene.String()
    market = graphene.String()
    amount = graphene.Decimal()
    fee = graphene.Decimal()
    currency = graphene.String()
    price = graphene.Decimal()
    status = graphene.String()


class HoldingInput(graphene.InputObjectType):
    """Input type for creating holdings."""
    equity_id = graphene.String(required=True)
    equity_name = graphene.String(required=True)
    market = graphene.String(required=True)
    shares = graphene.Decimal(required=True)
    avg_price = graphene.Decimal(required=True)
    currency = graphene.String(required=True)


class HoldingUpdateInput(graphene.InputObjectType):
    """Input type for updating holdings."""
    equity_id = graphene.String()
    equity_name = graphene.String()
    market = graphene.String()
    shares = graphene.Decimal()
    avg_price = graphene.Decimal()
    currency = graphene.String()