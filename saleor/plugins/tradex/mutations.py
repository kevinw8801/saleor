"""
GraphQL mutations for TradEx plugin models.
"""
import graphene
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction

from ...graphql.core.mutations import BaseMutation
from ...graphql.core.types import NonNullList
from ...graphql.core.types.common import ProductError
from ...graphql.core.utils import from_global_id_or_error
from .models import Operation, Holding
from .types import (
    OperationType, HoldingType, OperationInput, HoldingInput,
    OperationUpdateInput, HoldingUpdateInput
)


class OperationCreate(BaseMutation):
    """Create a new trading operation."""
    
    operation = graphene.Field(OperationType)
    
    class Arguments:
        input = OperationInput(required=True, description="Operation data")
    
    class Meta:
        description = "Create a new trading operation."
        error_type_class = ProductError
        error_type_field = "product_errors"
    
    @classmethod
    def clean_input(cls, info, instance, data):
        """Clean and validate input data."""
        cleaned_input = {}
        
        # Validate required fields
        for field in ['date_time', 'operation', 'equity_id', 'equity_name', 
                     'market', 'amount', 'fee', 'currency', 'price', 'status']:
            if field in data:
                cleaned_input[field] = data[field]
        
        # Validate decimal fields are non-negative
        for field in ['amount', 'fee', 'price']:
            if field in cleaned_input:
                value = cleaned_input[field]
                if value < 0:
                    raise ValidationError(f"{field} must be non-negative")
        
        # Validate currency code length
        if 'currency' in cleaned_input:
            currency = cleaned_input['currency'].upper()
            if len(currency) != 3:
                raise ValidationError("Currency must be a 3-character ISO 4217 code")
            cleaned_input['currency'] = currency
        
        return cleaned_input
    
    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform the mutation."""
        input_data = data.get("input")
        cleaned_input = cls.clean_input(info, None, input_data)
        
        with transaction.atomic():
            operation = Operation.objects.create(**cleaned_input)
        
        return OperationCreate(operation=operation)


class OperationUpdate(BaseMutation):
    """Update an existing trading operation."""
    
    operation = graphene.Field(OperationType)
    
    class Arguments:
        id = graphene.ID(required=True, description="Operation ID")
        input = OperationUpdateInput(required=True, description="Updated operation data")
    
    class Meta:
        description = "Update an existing trading operation."
        error_type_class = ProductError
        error_type_field = "product_errors"
    
    @classmethod
    def clean_input(cls, info, instance, data):
        """Clean and validate input data."""
        cleaned_input = {}
        
        # Only include fields that are provided
        for field in ['date_time', 'operation', 'equity_id', 'equity_name', 
                     'market', 'amount', 'fee', 'currency', 'price', 'status']:
            if field in data and data[field] is not None:
                cleaned_input[field] = data[field]
        
        # Validate decimal fields are non-negative
        for field in ['amount', 'fee', 'price']:
            if field in cleaned_input:
                value = cleaned_input[field]
                if value < 0:
                    raise ValidationError(f"{field} must be non-negative")
        
        # Validate currency code length
        if 'currency' in cleaned_input:
            currency = cleaned_input['currency'].upper()
            if len(currency) != 3:
                raise ValidationError("Currency must be a 3-character ISO 4217 code")
            cleaned_input['currency'] = currency
        
        return cleaned_input
    
    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform the mutation."""
        operation_id = from_global_id_or_error(data["id"], OperationType)
        input_data = data.get("input")
        
        try:
            operation = Operation.objects.get(pk=operation_id)
        except Operation.DoesNotExist:
            raise ValidationError("Operation not found")
        
        cleaned_input = cls.clean_input(info, operation, input_data)
        
        with transaction.atomic():
            for field, value in cleaned_input.items():
                setattr(operation, field, value)
            operation.save()
        
        return OperationUpdate(operation=operation)


class OperationDelete(BaseMutation):
    """Delete a trading operation."""
    
    class Arguments:
        id = graphene.ID(required=True, description="Operation ID")
    
    class Meta:
        description = "Delete a trading operation."
        error_type_class = ProductError
        error_type_field = "product_errors"
    
    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform the mutation."""
        operation_id = from_global_id_or_error(data["id"], OperationType)
        
        try:
            operation = Operation.objects.get(pk=operation_id)
        except Operation.DoesNotExist:
            raise ValidationError("Operation not found")
        
        with transaction.atomic():
            operation.delete()
        
        return OperationDelete()


class HoldingCreate(BaseMutation):
    """Create a new portfolio holding."""
    
    holding = graphene.Field(HoldingType)
    
    class Arguments:
        input = HoldingInput(required=True, description="Holding data")
    
    class Meta:
        description = "Create a new portfolio holding."
        error_type_class = ProductError
        error_type_field = "product_errors"
    
    @classmethod
    def clean_input(cls, info, instance, data):
        """Clean and validate input data."""
        cleaned_input = {}
        
        # Validate required fields
        for field in ['id', 'amount', 'purchase_price', 'purchase_time', 'market', 'currency']:
            if field in data:
                cleaned_input[field] = data[field]
        
        # Validate amount is positive
        if 'amount' in cleaned_input:
            if cleaned_input['amount'] <= 0:
                raise ValidationError("Amount must be positive")
        
        # Validate purchase_price is non-negative
        if 'purchase_price' in cleaned_input:
            if cleaned_input['purchase_price'] < 0:
                raise ValidationError("Purchase price must be non-negative")
        
        # Validate currency code length
        if 'currency' in cleaned_input:
            currency = cleaned_input['currency'].upper()
            if len(currency) != 3:
                raise ValidationError("Currency must be a 3-character ISO 4217 code")
            cleaned_input['currency'] = currency
        
        # Check if holding ID already exists
        if 'id' in cleaned_input:
            if Holding.objects.filter(id=cleaned_input['id']).exists():
                raise ValidationError("Holding with this ID already exists")
        
        return cleaned_input
    
    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform the mutation."""
        input_data = data.get("input")
        cleaned_input = cls.clean_input(info, None, input_data)
        
        with transaction.atomic():
            holding = Holding.objects.create(**cleaned_input)
        
        return HoldingCreate(holding=holding)


class HoldingUpdate(BaseMutation):
    """Update an existing portfolio holding."""
    
    holding = graphene.Field(HoldingType)
    
    class Arguments:
        id = graphene.ID(required=True, description="Holding ID")
        input = HoldingUpdateInput(required=True, description="Updated holding data")
    
    class Meta:
        description = "Update an existing portfolio holding."
        error_type_class = ProductError
        error_type_field = "product_errors"
    
    @classmethod
    def clean_input(cls, info, instance, data):
        """Clean and validate input data."""
        cleaned_input = {}
        
        # Only include fields that are provided
        for field in ['amount', 'purchase_price', 'purchase_time', 'market', 'currency']:
            if field in data and data[field] is not None:
                cleaned_input[field] = data[field]
        
        # Validate amount is positive
        if 'amount' in cleaned_input:
            if cleaned_input['amount'] <= 0:
                raise ValidationError("Amount must be positive")
        
        # Validate purchase_price is non-negative
        if 'purchase_price' in cleaned_input:
            if cleaned_input['purchase_price'] < 0:
                raise ValidationError("Purchase price must be non-negative")
        
        # Validate currency code length
        if 'currency' in cleaned_input:
            currency = cleaned_input['currency'].upper()
            if len(currency) != 3:
                raise ValidationError("Currency must be a 3-character ISO 4217 code")
            cleaned_input['currency'] = currency
        
        return cleaned_input
    
    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform the mutation."""
        holding_id = data["id"]  # For Holding, ID is a string, not a global ID
        input_data = data.get("input")
        
        try:
            holding = Holding.objects.get(pk=holding_id)
        except Holding.DoesNotExist:
            raise ValidationError("Holding not found")
        
        cleaned_input = cls.clean_input(info, holding, input_data)
        
        with transaction.atomic():
            for field, value in cleaned_input.items():
                setattr(holding, field, value)
            holding.save()
        
        return HoldingUpdate(holding=holding)


class HoldingDelete(BaseMutation):
    """Delete a portfolio holding."""
    
    class Arguments:
        id = graphene.ID(required=True, description="Holding ID")
    
    class Meta:
        description = "Delete a portfolio holding."
        error_type_class = ProductError
        error_type_field = "product_errors"
    
    @classmethod
    def perform_mutation(cls, _root, info, **data):
        """Perform the mutation."""
        holding_id = data["id"]  # For Holding, ID is a string, not a global ID
        
        try:
            holding = Holding.objects.get(pk=holding_id)
        except Holding.DoesNotExist:
            raise ValidationError("Holding not found")
        
        with transaction.atomic():
            holding.delete()
        
        return HoldingDelete()


class TradexMutations(graphene.ObjectType):
    """Mutations for TradEx plugin."""
    
    # Operation mutations
    operation_create = OperationCreate.Field()
    operation_update = OperationUpdate.Field()
    operation_delete = OperationDelete.Field()
    
    # Holding mutations
    holding_create = HoldingCreate.Field()
    holding_update = HoldingUpdate.Field()
    holding_delete = HoldingDelete.Field()