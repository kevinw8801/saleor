"""
GraphQL schema for TradEx plugin.
"""
import graphene

from .mutations import TradexMutations
from .queries import TradexQueries


class TradexSchema(TradexQueries, TradexMutations, graphene.ObjectType):
    """Complete GraphQL schema for TradEx plugin."""
    pass


# Export for integration with main Saleor schema
tradex_schema = TradexSchema()