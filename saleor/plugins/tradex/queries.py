"""
GraphQL queries for TradEx plugin models.
"""
import graphene
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField

from ...core.types import FilterInputObjectType
from .models import Operation, Holding
from .types import OperationType, HoldingType


class OperationFilterInput(FilterInputObjectType):
    """Filter input for operations."""
    
    class Meta:
        filterset_class = None  # We'll define custom filters
    
    operation = graphene.String(description="Filter by operation type")
    equity_id = graphene.String(description="Filter by equity ID")
    market = graphene.String(description="Filter by market")
    currency = graphene.String(description="Filter by currency")
    status = graphene.String(description="Filter by status")
    date_from = graphene.DateTime(description="Filter operations from this date")
    date_to = graphene.DateTime(description="Filter operations to this date")


class HoldingFilterInput(FilterInputObjectType):
    """Filter input for holdings."""
    
    class Meta:
        filterset_class = None  # We'll define custom filters
    
    market = graphene.String(description="Filter by market")
    currency = graphene.String(description="Filter by currency")
    purchase_date_from = graphene.DateTime(description="Filter holdings purchased from this date")
    purchase_date_to = graphene.DateTime(description="Filter holdings purchased to this date")


class TradexQueries(graphene.ObjectType):
    """Queries for TradEx plugin."""
    
    # Single object queries
    operation = relay.Node.Field(OperationType)
    holding = relay.Node.Field(HoldingType)
    
    # List queries
    operations = DjangoFilterConnectionField(
        OperationType,
        description="List of trading operations"
    )
    holdings = DjangoFilterConnectionField(
        HoldingType,
        description="List of portfolio holdings"
    )
    
    # Custom queries
    operation_by_id = graphene.Field(
        OperationType,
        id=graphene.Int(required=True),
        description="Get operation by database ID"
    )
    
    holding_by_id = graphene.Field(
        HoldingType,
        id=graphene.String(required=True),
        description="Get holding by ID"
    )
    
    operations_by_equity = graphene.List(
        OperationType,
        equity_id=graphene.String(required=True),
        description="Get all operations for a specific equity"
    )
    
    holdings_by_market = graphene.List(
        HoldingType,
        market=graphene.String(required=True),
        description="Get all holdings from a specific market"
    )
    
    portfolio_summary = graphene.Field(
        graphene.JSONString,
        currency=graphene.String(description="Filter by currency"),
        description="Get portfolio summary with totals"
    )
    
    def resolve_operation_by_id(self, info, id):
        """Resolve operation by database ID."""
        try:
            return Operation.objects.get(pk=id)
        except Operation.DoesNotExist:
            return None
    
    def resolve_holding_by_id(self, info, id):
        """Resolve holding by ID."""
        try:
            return Holding.objects.get(pk=id)
        except Holding.DoesNotExist:
            return None
    
    def resolve_operations_by_equity(self, info, equity_id):
        """Resolve operations for a specific equity."""
        return Operation.objects.filter(equity_id=equity_id).order_by('-date_time')
    
    def resolve_holdings_by_market(self, info, market):
        """Resolve holdings from a specific market."""
        return Holding.objects.filter(market=market).order_by('-purchase_time')
    
    def resolve_portfolio_summary(self, info, currency=None):
        """Resolve portfolio summary."""
        from django.db.models import Sum, Count, Avg
        from decimal import Decimal
        
        # Filter holdings by currency if provided
        holdings_qs = Holding.objects.all()
        operations_qs = Operation.objects.all()
        
        if currency:
            holdings_qs = holdings_qs.filter(currency=currency.upper())
            operations_qs = operations_qs.filter(currency=currency.upper())
        
        # Calculate holdings summary
        holdings_summary = holdings_qs.aggregate(
            total_holdings=Count('id'),
            total_amount=Sum('amount'),
            total_value=Sum('amount') * Avg('purchase_price') if holdings_qs.exists() else Decimal('0'),
            avg_purchase_price=Avg('purchase_price')
        )
        
        # Calculate operations summary
        operations_summary = operations_qs.aggregate(
            total_operations=Count('id'),
            total_buy_operations=Count('id', filter=operations_qs.filter(operation__icontains='buy').query),
            total_sell_operations=Count('id', filter=operations_qs.filter(operation__icontains='sell').query),
            total_fees=Sum('fee'),
            total_volume=Sum('amount')
        )
        
        # Get unique currencies, markets, and equities
        currencies = list(holdings_qs.values_list('currency', flat=True).distinct())
        markets = list(holdings_qs.values_list('market', flat=True).distinct())
        equities = list(operations_qs.values_list('equity_id', flat=True).distinct())
        
        return {
            'holdings': {
                'total_count': holdings_summary['total_holdings'] or 0,
                'total_amount': holdings_summary['total_amount'] or 0,
                'total_value': float(holdings_summary['total_value'] or 0),
                'average_purchase_price': float(holdings_summary['avg_purchase_price'] or 0),
            },
            'operations': {
                'total_count': operations_summary['total_operations'] or 0,
                'buy_count': operations_summary['total_buy_operations'] or 0,
                'sell_count': operations_summary['total_sell_operations'] or 0,
                'total_fees': float(operations_summary['total_fees'] or 0),
                'total_volume': float(operations_summary['total_volume'] or 0),
            },
            'metadata': {
                'currencies': currencies,
                'markets': markets,
                'equities': equities,
                'filter_currency': currency,
            }
        }