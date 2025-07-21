"""
GraphQL queries for TradEx plugin models.
"""
import graphene
from graphene import relay

from ...graphql.core.fields import BaseField
from ...graphql.core.utils import from_global_id_or_error
from .models import Operation, Holding
from .types import OperationType, HoldingType


class TradexQueries(graphene.ObjectType):
    """GraphQL queries for TradEx plugin."""
    
    operation = BaseField(
        OperationType,
        id=graphene.Argument(graphene.ID, required=True),
        description="Look up an operation by ID."
    )
    
    operations = graphene.List(
        OperationType,
        description="List of operations."
    )
    
    holding = BaseField(
        HoldingType,
        id=graphene.Argument(graphene.ID, required=True),
        description="Look up a holding by ID."
    )
    
    holdings = graphene.List(
        HoldingType,
        description="List of holdings."
    )

    def resolve_operation(self, info, id):
        """Resolve a single operation by ID."""
        _, operation_id = from_global_id_or_error(id, only_type="Operation")
        return Operation.objects.get(pk=operation_id)

    def resolve_operations(self, info):
        """Resolve list of operations."""
        return Operation.objects.all()

    def resolve_holding(self, info, id):
        """Resolve a single holding by ID."""
        _, holding_id = from_global_id_or_error(id, only_type="Holding")
        return Holding.objects.get(pk=holding_id)

    def resolve_holdings(self, info):
        """Resolve list of holdings."""
        return Holding.objects.all()