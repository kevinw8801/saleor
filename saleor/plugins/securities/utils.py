from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.db import models
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from decimal import Decimal

from ...warehouse.models import Stock, Warehouse
from ...product.models import ProductVariant
from .constants import SECURITIES_LEVEL_CRITICAL, SECURITIES_LEVEL_LOW, SECURITIES_LEVEL_NORMAL, SECURITIES_LEVEL_HIGH


def calculate_securities_level(stock: Stock, low_threshold: int = 20, critical_threshold: int = 5) -> str:
    """
    Calculate securities level based on current quantity and thresholds
    
    Args:
        stock: Stock instance
        low_threshold: Percentage threshold for low securities
        critical_threshold: Percentage threshold for critical securities
        
    Returns:
        Securities level: 'critical', 'low', 'normal', or 'high'
    """
    if not hasattr(stock, 'securities_settings') or not stock.securities_settings:
        # Use default calculations if no custom settings
        max_quantity = estimate_max_securities_level(stock)
    else:
        max_quantity = stock.securities_settings.max_stock_level or estimate_max_securities_level(stock)
    
    if max_quantity <= 0:
        return SECURITIES_LEVEL_NORMAL
    
    percentage = (stock.quantity / max_quantity) * 100
    
    if percentage <= critical_threshold:
        return SECURITIES_LEVEL_CRITICAL
    elif percentage <= low_threshold:
        return SECURITIES_LEVEL_LOW
    elif percentage >= 90:  # Consider high securities at 90%
        return SECURITIES_LEVEL_HIGH
    else:
        return SECURITIES_LEVEL_NORMAL


def estimate_max_securities_level(stock: Stock) -> int:
    """
    Estimate maximum securities level based on historical data
    
    Args:
        stock: Stock instance
        
    Returns:
        Estimated maximum securities level
    """
    try:
        from .models import SecuritiesMovement
        
        # Get maximum quantity from last 90 days
        ninety_days_ago = timezone.now() - timedelta(days=90)
        max_quantity = SecuritiesMovement.objects.filter(
            stock=stock,
            timestamp__gte=ninety_days_ago
        ).aggregate(max_qty=models.Max('new_quantity'))['max_qty']
        
        if max_quantity:
            return max_quantity
    except:
        pass
    
    # Fallback: use current quantity * 2 or minimum of 100
    return max(stock.quantity * 2, 100)


def check_low_securities_threshold(warehouse_id: Optional[int] = None, threshold_percentage: int = 20) -> List[Dict[str, Any]]:
    """
    Get list of securities below low securities threshold
    
    Args:
        warehouse_id: Optional warehouse filter
        threshold_percentage: Percentage threshold for low securities
        
    Returns:
        List of low securities items with details
    """
    stocks_query = Stock.objects.select_related('product_variant', 'warehouse')
    
    if warehouse_id:
        stocks_query = stocks_query.filter(warehouse_id=warehouse_id)
    
    low_securities_items = []
    
    for stock in stocks_query:
        securities_level = calculate_securities_level(stock, threshold_percentage)
        
        if securities_level in [SECURITIES_LEVEL_CRITICAL, SECURITIES_LEVEL_LOW]:
            low_securities_items.append({
                'stock_id': stock.id,
                'product_variant_id': stock.product_variant.id,
                'product_name': stock.product_variant.product.name,
                'variant_name': stock.product_variant.name or 'Default',
                'sku': stock.product_variant.sku,
                'warehouse_name': stock.warehouse.name,
                'current_quantity': stock.quantity,
                'securities_level': securities_level,
                'reorder_point': getattr(stock.securities_settings, 'reorder_point', None) if hasattr(stock, 'securities_settings') else None,
                'suggested_reorder_quantity': calculate_reorder_quantity(stock),
            })
    
    return sorted(low_securities_items, key=lambda x: (x['securities_level'] == SECURITIES_LEVEL_CRITICAL, -x['current_quantity']))


def calculate_reorder_quantity(stock: Stock) -> int:
    """
    Calculate suggested reorder quantity based on historical demand
    
    Args:
        stock: Stock instance
        
    Returns:
        Suggested reorder quantity
    """
    try:
        from .models import SecuritiesMovement
        
        # Get settings if available
        if hasattr(stock, 'securities_settings') and stock.securities_settings:
            base_reorder = stock.securities_settings.reorder_quantity
            lead_time_days = stock.securities_settings.lead_time_days
            safety_stock = stock.securities_settings.safety_stock
        else:
            base_reorder = 50  # Default
            lead_time_days = 7  # Default
            safety_stock = 5   # Default
        
        # Calculate average daily consumption from last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Get all outbound movements (sales, transfers out, etc.)
        outbound_movements = SecuritiesMovement.objects.filter(
            stock=stock,
            timestamp__gte=thirty_days_ago,
            quantity_change__lt=0  # Negative changes are outbound
        ).aggregate(
            total_out=Sum('quantity_change'),
            movement_count=Count('id')
        )
        
        total_consumed = abs(outbound_movements['total_out'] or 0)
        
        if total_consumed > 0:
            daily_consumption = total_consumed / 30
            lead_time_demand = daily_consumption * lead_time_days
            suggested_quantity = int(lead_time_demand + safety_stock)
            
            # Ensure minimum order quantity
            return max(suggested_quantity, base_reorder)
        
        return base_reorder
        
    except Exception:
        # Fallback to default
        return 50


def generate_securities_report(warehouse_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate comprehensive securities report
    
    Args:
        warehouse_id: Optional warehouse filter
        
    Returns:
        Comprehensive securities report data
    """
    stocks_query = Stock.objects.select_related('product_variant', 'warehouse')
    
    if warehouse_id:
        stocks_query = stocks_query.filter(warehouse_id=warehouse_id)
        warehouse_name = Warehouse.objects.get(id=warehouse_id).name
    else:
        warehouse_name = "All Warehouses"
    
    # Calculate securities levels
    securities_levels = {
        SECURITIES_LEVEL_CRITICAL: 0,
        SECURITIES_LEVEL_LOW: 0,
        SECURITIES_LEVEL_NORMAL: 0,
        SECURITIES_LEVEL_HIGH: 0,
    }
    
    total_value = Decimal('0.00')
    total_items = 0
    out_of_stock_count = 0
    
    securities_details = []
    
    for stock in stocks_query:
        securities_level = calculate_securities_level(stock)
        securities_levels[securities_level] += 1
        
        if stock.quantity == 0:
            out_of_stock_count += 1
        
        total_items += stock.quantity
        
        # Calculate securities value (if cost data is available)
        try:
            from .models import SecuritiesBatch
            latest_batch = SecuritiesBatch.objects.filter(
                stock=stock,
                cost_per_unit__isnull=False
            ).order_by('-received_date').first()
            
            if latest_batch:
                securities_value = latest_batch.cost_per_unit * stock.quantity
                total_value += securities_value
            else:
                securities_value = None
        except:
            securities_value = None
        
        securities_details.append({
            'stock_id': stock.id,
            'product_name': stock.product_variant.product.name,
            'variant_name': stock.product_variant.name or 'Default',
            'sku': stock.product_variant.sku,
            'warehouse': stock.warehouse.name,
            'quantity': stock.quantity,
            'securities_level': securities_level,
            'value': securities_value,
        })
    
    # Get movement summary for last 30 days
    movement_summary = get_movement_summary(warehouse_id, days=30)
    
    return {
        'report_date': timezone.now().isoformat(),
        'warehouse': warehouse_name,
        'summary': {
            'total_securities_items': len(securities_details),
            'total_quantity': total_items,
            'total_value': total_value,
            'out_of_stock_count': out_of_stock_count,
            'securities_levels': securities_levels,
        },
        'movement_summary': movement_summary,
        'securities_details': securities_details,
        'low_securities_items': check_low_securities_threshold(warehouse_id),
    }


def get_movement_summary(warehouse_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
    """
    Get securities movement summary for specified period
    
    Args:
        warehouse_id: Optional warehouse filter
        days: Number of days to analyze
        
    Returns:
        Movement summary data
    """
    try:
        from .models import SecuritiesMovement
        
        start_date = timezone.now() - timedelta(days=days)
        
        movements_query = SecuritiesMovement.objects.filter(timestamp__gte=start_date)
        
        if warehouse_id:
            movements_query = movements_query.filter(stock__warehouse_id=warehouse_id)
        
        # Aggregate by movement type
        movement_types = movements_query.values('movement_type').annotate(
            total_movements=Count('id'),
            total_quantity_change=Sum('quantity_change')
        )
        
        total_inbound = 0
        total_outbound = 0
        
        type_summary = {}
        for movement in movement_types:
            movement_type = movement['movement_type']
            quantity_change = movement['total_quantity_change'] or 0
            
            type_summary[movement_type] = {
                'count': movement['total_movements'],
                'quantity_change': quantity_change
            }
            
            if quantity_change > 0:
                total_inbound += quantity_change
            else:
                total_outbound += abs(quantity_change)
        
        return {
            'period_days': days,
            'total_inbound': total_inbound,
            'total_outbound': total_outbound,
            'net_change': total_inbound - total_outbound,
            'movement_types': type_summary,
        }
        
    except Exception:
        return {
            'period_days': days,
            'total_inbound': 0,
            'total_outbound': 0,
            'net_change': 0,
            'movement_types': {},
        }


def predict_securities_needs(days: int = 30) -> Dict[str, Any]:
    """
    Predict securities needs for specified period using simple forecasting
    
    Args:
        days: Number of days to forecast
        
    Returns:
        Securities prediction data
    """
    try:
        from .models import SecuritiesMovement, SecuritiesForecast
        
        # Get historical consumption data
        lookback_days = min(days * 3, 90)  # Use 3x forecast period or max 90 days
        start_date = timezone.now() - timedelta(days=lookback_days)
        
        predictions = []
        
        # Get all stocks with recent activity
        active_stocks = Stock.objects.filter(
            securities_movements__timestamp__gte=start_date
        ).distinct()
        
        for stock in active_stocks:
            # Calculate historical daily consumption
            outbound_movements = SecuritiesMovement.objects.filter(
                stock=stock,
                timestamp__gte=start_date,
                quantity_change__lt=0
            ).aggregate(
                total_consumed=Sum('quantity_change')
            )
            
            total_consumed = abs(outbound_movements['total_consumed'] or 0)
            daily_consumption = total_consumed / lookback_days if lookback_days > 0 else 0
            
            # Predict demand for forecast period
            predicted_demand = int(daily_consumption * days)
            
            # Calculate if reorder is needed
            current_stock = stock.quantity
            safety_stock = getattr(stock.securities_settings, 'safety_stock', 5) if hasattr(stock, 'securities_settings') else 5
            
            stock_at_end = current_stock - predicted_demand
            needs_reorder = stock_at_end <= safety_stock
            
            if needs_reorder:
                reorder_quantity = calculate_reorder_quantity(stock)
            else:
                reorder_quantity = 0
            
            predictions.append({
                'stock_id': stock.id,
                'product_name': stock.product_variant.product.name,
                'variant_name': stock.product_variant.name or 'Default',
                'sku': stock.product_variant.sku,
                'warehouse': stock.warehouse.name,
                'current_quantity': current_stock,
                'predicted_demand': predicted_demand,
                'daily_consumption': round(daily_consumption, 2),
                'stock_at_end_period': stock_at_end,
                'needs_reorder': needs_reorder,
                'suggested_reorder_quantity': reorder_quantity,
            })
        
        # Sort by urgency (stocks that will run out first)
        predictions.sort(key=lambda x: (not x['needs_reorder'], x['stock_at_end_period']))
        
        return {
            'forecast_period_days': days,
            'total_stocks_analyzed': len(predictions),
            'stocks_needing_reorder': len([p for p in predictions if p['needs_reorder']]),
            'predictions': predictions,
        }
        
    except Exception as e:
        return {
            'forecast_period_days': days,
            'total_stocks_analyzed': 0,
            'stocks_needing_reorder': 0,
            'predictions': [],
            'error': str(e),
        }


def check_expiring_securities(days_ahead: int = 7) -> List[Dict[str, Any]]:
    """
    Check for securities that is expiring within specified days
    
    Args:
        days_ahead: Number of days to check ahead for expiring securities
        
    Returns:
        List of expiring securities items
    """
    try:
        from .models import SecuritiesBatch
        
        expiry_date_limit = timezone.now().date() + timedelta(days=days_ahead)
        
        expiring_batches = SecuritiesBatch.objects.filter(
            expiry_date__lte=expiry_date_limit,
            expiry_date__gte=timezone.now().date(),
            is_expired=False,
            quantity__gt=0
        ).select_related('stock__product_variant', 'stock__warehouse')
        
        expiring_items = []
        
        for batch in expiring_batches:
            days_until_expiry = (batch.expiry_date - timezone.now().date()).days
            
            expiring_items.append({
                'batch_id': batch.id,
                'batch_number': batch.batch_number,
                'stock_id': batch.stock.id,
                'product_name': batch.stock.product_variant.product.name,
                'variant_name': batch.stock.product_variant.name or 'Default',
                'sku': batch.stock.product_variant.sku,
                'warehouse': batch.stock.warehouse.name,
                'quantity': batch.quantity,
                'expiry_date': batch.expiry_date.isoformat(),
                'days_until_expiry': days_until_expiry,
                'is_expired': days_until_expiry <= 0,
                'cost_per_unit': batch.cost_per_unit,
                'total_value': batch.cost_per_unit * batch.quantity if batch.cost_per_unit else None,
            })
        
        return sorted(expiring_items, key=lambda x: x['days_until_expiry'])
        
    except Exception:
        return []


def create_security(
    symbol: str,
    security_type: str,
    name: str,
    exchange: str = '',
    currency: str = 'USD',
    sector: str = '',
    industry: str = '',
    country: str = '',
    market_cap: Optional[int] = None,
    description: str = ''
) -> 'Securities':
    """
    Create a new security record
    
    Args:
        symbol: Trading symbol
        security_type: Type of security (STOCK, ETF, etc.)
        name: Full name of the security
        exchange: Exchange where traded
        currency: Currency code
        sector: Business sector
        industry: Industry classification
        country: Country code
        market_cap: Market capitalization
        description: Security description
        
    Returns:
        Created Securities instance
    """
    try:
        from .models import Securities
        
        security = Securities.objects.create(
            symbol=symbol.upper(),
            security_type=security_type,
            name=name,
            exchange=exchange,
            currency=currency,
            sector=sector,
            industry=industry,
            country=country,
            market_cap=market_cap,
            description=description
        )
        return security
    except Exception as e:
        raise ValueError(f"Failed to create security: {str(e)}")


def get_security_by_symbol(symbol: str, security_type: Optional[str] = None) -> Optional['Securities']:
    """
    Get security by symbol and optionally by type
    
    Args:
        symbol: Trading symbol
        security_type: Optional security type filter
        
    Returns:
        Securities instance if found, None otherwise
    """
    try:
        from .models import Securities
        
        query = Securities.objects.filter(symbol=symbol.upper())
        if security_type:
            query = query.filter(security_type=security_type)
            
        return query.first()
    except Exception:
        return None


def search_securities(
    symbol_contains: Optional[str] = None,
    name_contains: Optional[str] = None,
    security_type: Optional[str] = None,
    exchange: Optional[str] = None,
    sector: Optional[str] = None,
    is_active: bool = True,
    limit: int = 100
) -> List['Securities']:
    """
    Search securities with various filters
    
    Args:
        symbol_contains: Symbol contains text
        name_contains: Name contains text
        security_type: Security type filter
        exchange: Exchange filter
        sector: Sector filter
        is_active: Active status filter
        limit: Maximum results to return
        
    Returns:
        List of matching Securities instances
    """
    try:
        from .models import Securities
        
        query = Securities.objects.filter(is_active=is_active)
        
        if symbol_contains:
            query = query.filter(symbol__icontains=symbol_contains)
        if name_contains:
            query = query.filter(name__icontains=name_contains)
        if security_type:
            query = query.filter(security_type=security_type)
        if exchange:
            query = query.filter(exchange=exchange)
        if sector:
            query = query.filter(sector=sector)
            
        return list(query.order_by('symbol')[:limit])
    except Exception:
        return []


def get_securities_by_type(security_type: str, is_active: bool = True) -> List['Securities']:
    """
    Get all securities of a specific type
    
    Args:
        security_type: Type of security (STOCK, ETF, etc.)
        is_active: Filter by active status
        
    Returns:
        List of Securities instances
    """
    try:
        from .models import Securities
        
        return list(Securities.objects.filter(
            security_type=security_type,
            is_active=is_active
        ).order_by('symbol'))
    except Exception:
        return []


def update_security_market_data(
    security_id: str,
    market_cap: Optional[int] = None,
    sector: Optional[str] = None,
    industry: Optional[str] = None,
    description: Optional[str] = None
) -> bool:
    """
    Update market data for a security
    
    Args:
        security_id: UUID of the security
        market_cap: Market capitalization
        sector: Business sector
        industry: Industry classification
        description: Security description
        
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        from .models import Securities
        
        security = Securities.objects.get(security_id=security_id)
        
        if market_cap is not None:
            security.market_cap = market_cap
        if sector is not None:
            security.sector = sector
        if industry is not None:
            security.industry = industry
        if description is not None:
            security.description = description
            
        security.save()
        return True
    except Exception:
        return False


def get_securities_statistics() -> Dict[str, Any]:
    """
    Get statistics about securities in the database
    
    Returns:
        Dictionary with securities statistics
    """
    try:
        from .models import Securities
        from django.db.models import Count
        
        total_securities = Securities.objects.count()
        active_securities = Securities.objects.filter(is_active=True).count()
        
        # Statistics by type
        by_type = Securities.objects.values('security_type').annotate(
            count=Count('security_id')
        ).order_by('security_type')
        
        # Statistics by exchange
        by_exchange = Securities.objects.exclude(exchange='').values('exchange').annotate(
            count=Count('security_id')
        ).order_by('-count')[:10]
        
        # Statistics by sector
        by_sector = Securities.objects.exclude(sector='').values('sector').annotate(
            count=Count('security_id')
        ).order_by('-count')[:10]
        
        return {
            'total_securities': total_securities,
            'active_securities': active_securities,
            'inactive_securities': total_securities - active_securities,
            'by_type': list(by_type),
            'by_exchange': list(by_exchange),
            'by_sector': list(by_sector),
        }
    except Exception:
        return {
            'total_securities': 0,
            'active_securities': 0,
            'inactive_securities': 0,
            'by_type': [],
            'by_exchange': [],
            'by_sector': [],
        }


def add_daily_price(
    security_id: str,
    date: str,  # YYYY-MM-DD format
    open_price: float,
    high_price: float,
    low_price: float,
    close_price: float,
    volume: int,
    adjusted_close: Optional[float] = None
) -> bool:
    """
    Add daily price data for a security
    
    Args:
        security_id: UUID of the security
        date: Trading date in YYYY-MM-DD format
        open_price: Opening price
        high_price: Highest price
        low_price: Lowest price
        close_price: Closing price
        volume: Trading volume
        adjusted_close: Optional adjusted closing price
        
    Returns:
        True if added successfully, False otherwise
    """
    try:
        from .models import Securities, SecurityDailyPrices
        from datetime import datetime
        from decimal import Decimal
        
        security = Securities.objects.get(security_id=security_id)
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Use update_or_create to handle duplicates
        price_record, created = SecurityDailyPrices.objects.update_or_create(
            security=security,
            date=date_obj,
            defaults={
                'open_price': Decimal(str(open_price)),
                'high_price': Decimal(str(high_price)),
                'low_price': Decimal(str(low_price)),
                'close_price': Decimal(str(close_price)),
                'volume': volume,
                'adjusted_close': Decimal(str(adjusted_close)) if adjusted_close else None,
            }
        )
        return True
    except Exception as e:
        return False


def get_latest_price(security_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the latest price data for a security
    
    Args:
        security_id: UUID of the security
        
    Returns:
        Dictionary with latest price data or None
    """
    try:
        from .models import Securities, SecurityDailyPrices
        
        security = Securities.objects.get(security_id=security_id)
        latest_price = SecurityDailyPrices.objects.filter(
            security=security
        ).order_by('-date').first()
        
        if latest_price:
            return {
                'security_id': str(latest_price.security.security_id),
                'symbol': latest_price.security.symbol,
                'date': latest_price.date.isoformat(),
                'open_price': float(latest_price.open_price),
                'high_price': float(latest_price.high_price),
                'low_price': float(latest_price.low_price),
                'close_price': float(latest_price.close_price),
                'adjusted_close': float(latest_price.adjusted_close) if latest_price.adjusted_close else None,
                'volume': latest_price.volume,
                'price_change': float(latest_price.price_change),
                'price_change_percent': float(latest_price.price_change_percent),
                'trading_range': float(latest_price.trading_range),
            }
        return None
    except Exception:
        return None


def get_price_history(
    security_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get price history for a security
    
    Args:
        security_id: UUID of the security
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        limit: Maximum number of records to return
        
    Returns:
        List of price records
    """
    try:
        from .models import Securities, SecurityDailyPrices
        from datetime import datetime
        
        security = Securities.objects.get(security_id=security_id)
        query = SecurityDailyPrices.objects.filter(security=security)
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(date__gte=start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(date__lte=end_date_obj)
        
        prices = query.order_by('-date')[:limit]
        
        return [
            {
                'date': price.date.isoformat(),
                'open_price': float(price.open_price),
                'high_price': float(price.high_price),
                'low_price': float(price.low_price),
                'close_price': float(price.close_price),
                'adjusted_close': float(price.adjusted_close) if price.adjusted_close else None,
                'volume': price.volume,
                'price_change': float(price.price_change),
                'price_change_percent': float(price.price_change_percent),
            }
            for price in prices
        ]
    except Exception:
        return []


def get_price_by_date(security_id: str, date: str) -> Optional[Dict[str, Any]]:
    """
    Get price data for a specific date
    
    Args:
        security_id: UUID of the security
        date: Date in YYYY-MM-DD format
        
    Returns:
        Price data for the date or None
    """
    try:
        from .models import Securities, SecurityDailyPrices
        from datetime import datetime
        
        security = Securities.objects.get(security_id=security_id)
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        price = SecurityDailyPrices.objects.filter(
            security=security,
            date=date_obj
        ).first()
        
        if price:
            return {
                'date': price.date.isoformat(),
                'open_price': float(price.open_price),
                'high_price': float(price.high_price),
                'low_price': float(price.low_price),
                'close_price': float(price.close_price),
                'adjusted_close': float(price.adjusted_close) if price.adjusted_close else None,
                'volume': price.volume,
                'price_change': float(price.price_change),
                'price_change_percent': float(price.price_change_percent),
            }
        return None
    except Exception:
        return None


def bulk_add_daily_prices(price_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Bulk add daily price data
    
    Args:
        price_data: List of dictionaries with price data
            Each dict should contain: security_id, date, open_price, high_price, 
            low_price, close_price, volume, adjusted_close (optional)
            
    Returns:
        Dictionary with success/error counts
    """
    try:
        from .models import Securities, SecurityDailyPrices
        from datetime import datetime
        from decimal import Decimal
        
        success_count = 0
        error_count = 0
        
        for data in price_data:
            try:
                security = Securities.objects.get(security_id=data['security_id'])
                date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
                
                SecurityDailyPrices.objects.update_or_create(
                    security=security,
                    date=date_obj,
                    defaults={
                        'open_price': Decimal(str(data['open_price'])),
                        'high_price': Decimal(str(data['high_price'])),
                        'low_price': Decimal(str(data['low_price'])),
                        'close_price': Decimal(str(data['close_price'])),
                        'volume': data['volume'],
                        'adjusted_close': Decimal(str(data['adjusted_close'])) if data.get('adjusted_close') else None,
                    }
                )
                success_count += 1
            except Exception:
                error_count += 1
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'total_processed': len(price_data)
        }
    except Exception:
        return {
            'success_count': 0,
            'error_count': len(price_data) if price_data else 0,
            'total_processed': len(price_data) if price_data else 0
        }


def get_price_statistics(security_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Get price statistics for a security over specified days
    
    Args:
        security_id: UUID of the security
        days: Number of days to analyze
        
    Returns:
        Dictionary with price statistics
    """
    try:
        from .models import Securities, SecurityDailyPrices
        from datetime import datetime, timedelta
        from django.db.models import Avg, Max, Min, Sum
        
        security = Securities.objects.get(security_id=security_id)
        start_date = timezone.now().date() - timedelta(days=days)
        
        prices = SecurityDailyPrices.objects.filter(
            security=security,
            date__gte=start_date
        )
        
        if not prices.exists():
            return {
                'symbol': security.symbol,
                'period_days': days,
                'trading_days': 0,
                'statistics': {}
            }
        
        stats = prices.aggregate(
            avg_close=Avg('close_price'),
            max_high=Max('high_price'),
            min_low=Min('low_price'),
            avg_volume=Avg('volume'),
            total_volume=Sum('volume'),
            max_volume=Max('volume'),
            min_volume=Min('volume')
        )
        
        latest_price = prices.order_by('-date').first()
        earliest_price = prices.order_by('date').first()
        
        period_return = 0
        if earliest_price and latest_price:
            period_return = ((latest_price.close_price - earliest_price.close_price) / earliest_price.close_price) * 100
        
        return {
            'symbol': security.symbol,
            'period_days': days,
            'trading_days': prices.count(),
            'period_return_percent': float(period_return),
            'statistics': {
                'average_close_price': float(stats['avg_close'] or 0),
                'highest_price': float(stats['max_high'] or 0),
                'lowest_price': float(stats['min_low'] or 0),
                'average_volume': int(stats['avg_volume'] or 0),
                'total_volume': int(stats['total_volume'] or 0),
                'max_volume': int(stats['max_volume'] or 0),
                'min_volume': int(stats['min_volume'] or 0),
            },
            'latest_price': {
                'date': latest_price.date.isoformat(),
                'close_price': float(latest_price.close_price),
                'volume': latest_price.volume
            } if latest_price else None
        }
    except Exception:
        return {
            'symbol': 'Unknown',
            'period_days': days,
            'trading_days': 0,
            'period_return_percent': 0,
            'statistics': {},
            'latest_price': None
        }