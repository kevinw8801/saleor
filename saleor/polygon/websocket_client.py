import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
import threading
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode
from django.conf import settings
from django.utils import timezone

from .models import FinancialInstrument, StockData, CryptoData, ForexData
from .cache import PolygonCacheManager

logger = logging.getLogger(__name__)


class PolygonWebSocketClient:
    """
    WebSocket client for real-time data from Polygon.io
    
    Supports real-time quotes, trades, and market data for stocks, crypto, and forex.
    """
    
    # WebSocket endpoints
    STOCKS_WS_URL = "wss://socket.polygon.io/stocks"
    CRYPTO_WS_URL = "wss://socket.polygon.io/crypto"
    FOREX_WS_URL = "wss://socket.polygon.io/forex"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'POLYGON_IO_API_KEY', None)
        if not self.api_key:
            raise ValueError("Polygon.io API key is required for WebSocket connection")
        
        self.connections = {}  # Store active connections
        self.subscriptions = {}  # Track subscriptions per connection
        self.event_handlers = {}  # Event handler callbacks
        self.auto_reconnect = True
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_attempts = 10
        
        # Threading
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.running = False
        
        # Cache manager for storing real-time data
        self.cache_manager = PolygonCacheManager()
        
        # Data processing callbacks
        self.data_callbacks = {
            'stocks': [],
            'crypto': [],
            'forex': []
        }
    
    async def connect(self, market_type: str = 'stocks') -> bool:
        """
        Connect to Polygon.io WebSocket for specified market
        
        Args:
            market_type: 'stocks', 'crypto', or 'forex'
        """
        if market_type in self.connections:
            logger.warning(f"Already connected to {market_type} WebSocket")
            return True
        
        # Get WebSocket URL for market type
        ws_urls = {
            'stocks': self.STOCKS_WS_URL,
            'crypto': self.CRYPTO_WS_URL,
            'forex': self.FOREX_WS_URL
        }
        
        if market_type not in ws_urls:
            raise ValueError(f"Invalid market type: {market_type}")
        
        ws_url = ws_urls[market_type]
        
        try:
            logger.info(f"Connecting to {market_type} WebSocket: {ws_url}")
            
            # Connect to WebSocket
            websocket = await websockets.connect(ws_url)
            
            # Authenticate
            auth_message = {
                "action": "auth",
                "params": self.api_key
            }
            await websocket.send(json.dumps(auth_message))
            
            # Wait for authentication response
            auth_response = await websocket.recv()
            auth_data = json.loads(auth_response)
            
            if auth_data.get('status') != 'auth_success':
                logger.error(f"Authentication failed for {market_type}: {auth_data}")
                return False
            
            logger.info(f"Successfully authenticated to {market_type} WebSocket")
            
            # Store connection
            self.connections[market_type] = websocket
            self.subscriptions[market_type] = set()
            
            # Start message handler
            asyncio.create_task(self._handle_messages(market_type, websocket))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {market_type} WebSocket: {e}")
            return False
    
    async def disconnect(self, market_type: str = None):
        """Disconnect from WebSocket(s)"""
        if market_type:
            if market_type in self.connections:
                await self.connections[market_type].close()
                del self.connections[market_type]
                if market_type in self.subscriptions:
                    del self.subscriptions[market_type]
                logger.info(f"Disconnected from {market_type} WebSocket")
        else:
            # Disconnect from all
            for mt in list(self.connections.keys()):
                await self.disconnect(mt)
    
    async def subscribe_quotes(self, symbols: List[str], market_type: str = 'stocks'):
        """Subscribe to real-time quotes for symbols"""
        if market_type not in self.connections:
            success = await self.connect(market_type)
            if not success:
                return False
        
        websocket = self.connections[market_type]
        
        # Format symbols for subscription
        if market_type == 'stocks':
            # Stocks use Q.{symbol} for quotes
            formatted_symbols = [f"Q.{symbol.upper()}" for symbol in symbols]
        elif market_type == 'crypto':
            # Crypto uses XQ.{symbol} for quotes
            formatted_symbols = [f"XQ.{symbol.upper()}" for symbol in symbols]
        elif market_type == 'forex':
            # Forex uses C.{symbol} for quotes
            formatted_symbols = [f"C.{symbol.upper()}" for symbol in symbols]
        
        subscribe_message = {
            "action": "subscribe",
            "params": ",".join(formatted_symbols)
        }
        
        try:
            await websocket.send(json.dumps(subscribe_message))
            self.subscriptions[market_type].update(formatted_symbols)
            logger.info(f"Subscribed to {len(symbols)} {market_type} quotes: {symbols}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to {market_type} quotes: {e}")
            return False
    
    async def subscribe_trades(self, symbols: List[str], market_type: str = 'stocks'):
        """Subscribe to real-time trades for symbols"""
        if market_type not in self.connections:
            success = await self.connect(market_type)
            if not success:
                return False
        
        websocket = self.connections[market_type]
        
        # Format symbols for subscription
        if market_type == 'stocks':
            # Stocks use T.{symbol} for trades
            formatted_symbols = [f"T.{symbol.upper()}" for symbol in symbols]
        elif market_type == 'crypto':
            # Crypto uses XT.{symbol} for trades
            formatted_symbols = [f"XT.{symbol.upper()}" for symbol in symbols]
        elif market_type == 'forex':
            # Forex uses CA.{symbol} for aggregates
            formatted_symbols = [f"CA.{symbol.upper()}" for symbol in symbols]
        
        subscribe_message = {
            "action": "subscribe",
            "params": ",".join(formatted_symbols)
        }
        
        try:
            await websocket.send(json.dumps(subscribe_message))
            self.subscriptions[market_type].update(formatted_symbols)
            logger.info(f"Subscribed to {len(symbols)} {market_type} trades: {symbols}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to {market_type} trades: {e}")
            return False
    
    async def unsubscribe(self, symbols: List[str], market_type: str = 'stocks'):
        """Unsubscribe from symbols"""
        if market_type not in self.connections:
            return False
        
        websocket = self.connections[market_type]
        
        unsubscribe_message = {
            "action": "unsubscribe",
            "params": ",".join(symbols)
        }
        
        try:
            await websocket.send(json.dumps(unsubscribe_message))
            for symbol in symbols:
                self.subscriptions[market_type].discard(symbol)
            logger.info(f"Unsubscribed from {len(symbols)} {market_type} symbols: {symbols}")
            return True
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {market_type} symbols: {e}")
            return False
    
    async def _handle_messages(self, market_type: str, websocket):
        """Handle incoming WebSocket messages"""
        reconnect_attempts = 0
        
        while self.running or market_type in self.connections:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                # Process different message types
                if isinstance(data, list):
                    for item in data:
                        await self._process_message(market_type, item)
                else:
                    await self._process_message(market_type, data)
                
                # Reset reconnect attempts on successful message
                reconnect_attempts = 0
                
            except ConnectionClosed:
                logger.warning(f"{market_type} WebSocket connection closed")
                if self.auto_reconnect and reconnect_attempts < self.max_reconnect_attempts:
                    reconnect_attempts += 1
                    logger.info(f"Attempting to reconnect to {market_type} WebSocket (attempt {reconnect_attempts})")
                    await asyncio.sleep(self.reconnect_delay)
                    
                    try:
                        success = await self.connect(market_type)
                        if success:
                            # Resubscribe to previous subscriptions
                            if market_type in self.subscriptions:
                                subscriptions = list(self.subscriptions[market_type])
                                if subscriptions:
                                    resubscribe_message = {
                                        "action": "subscribe",
                                        "params": ",".join(subscriptions)
                                    }
                                    await self.connections[market_type].send(json.dumps(resubscribe_message))
                                    logger.info(f"Resubscribed to {len(subscriptions)} {market_type} subscriptions")
                    except Exception as e:
                        logger.error(f"Reconnection failed for {market_type}: {e}")
                else:
                    logger.error(f"Max reconnection attempts reached for {market_type}")
                    break
                    
            except Exception as e:
                logger.error(f"Error handling {market_type} WebSocket message: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(self, market_type: str, message: Dict[str, Any]):
        """Process individual WebSocket message"""
        try:
            # Determine message type
            msg_type = message.get('ev')  # event type
            
            if msg_type in ['Q', 'XQ', 'C']:  # Quote messages
                await self._process_quote_message(market_type, message)
            elif msg_type in ['T', 'XT', 'CA']:  # Trade messages
                await self._process_trade_message(market_type, message)
            elif msg_type == 'status':
                logger.info(f"{market_type} WebSocket status: {message}")
            else:
                logger.debug(f"Unhandled {market_type} message type: {msg_type}")
            
            # Call registered callbacks
            for callback in self.data_callbacks.get(market_type, []):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(market_type, message)
                    else:
                        callback(market_type, message)
                except Exception as e:
                    logger.error(f"Error in {market_type} data callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing {market_type} message: {e}")
    
    async def _process_quote_message(self, market_type: str, message: Dict[str, Any]):
        """Process quote message and cache the data"""
        try:
            symbol = message.get('sym', '').replace('X:', '').replace('C:', '')
            if not symbol:
                return
            
            # Create cache key and data
            cache_key = f"ws_{market_type}_quote_{symbol}"
            quote_data = {
                'symbol': symbol,
                'bid': message.get('b'),
                'ask': message.get('a'),
                'bid_size': message.get('bs'),
                'ask_size': message.get('as'),
                'timestamp': message.get('t'),
                'exchange': message.get('x'),
                'market_type': market_type,
                'source': 'websocket'
            }
            
            # Cache the quote data
            self.cache_manager.set(cache_key, quote_data, 'quote')
            
            # Store in database if enabled
            if getattr(settings, 'POLYGON_STORE_WEBSOCKET_DATA', False):
                await self._store_quote_in_db(symbol, quote_data, market_type)
                
        except Exception as e:
            logger.error(f"Error processing quote message: {e}")
    
    async def _process_trade_message(self, market_type: str, message: Dict[str, Any]):
        """Process trade message and cache the data"""
        try:
            symbol = message.get('sym', '').replace('X:', '').replace('C:', '')
            if not symbol:
                return
            
            # Create cache key and data
            cache_key = f"ws_{market_type}_trade_{symbol}"
            trade_data = {
                'symbol': symbol,
                'price': message.get('p'),
                'size': message.get('s'),
                'timestamp': message.get('t'),
                'exchange': message.get('x'),
                'conditions': message.get('c', []),
                'market_type': market_type,
                'source': 'websocket'
            }
            
            # Cache the trade data
            self.cache_manager.set(cache_key, trade_data, 'quote')
            
            # Store in database if enabled
            if getattr(settings, 'POLYGON_STORE_WEBSOCKET_DATA', False):
                await self._store_trade_in_db(symbol, trade_data, market_type)
                
        except Exception as e:
            logger.error(f"Error processing trade message: {e}")
    
    async def _store_quote_in_db(self, symbol: str, quote_data: Dict, market_type: str):
        """Store quote data in database"""
        # This would be implemented to store real-time data in the database
        # For now, we'll just cache it
        pass
    
    async def _store_trade_in_db(self, symbol: str, trade_data: Dict, market_type: str):
        """Store trade data in database"""
        # This would be implemented to store real-time data in the database
        # For now, we'll just cache it
        pass
    
    def add_data_callback(self, market_type: str, callback: Callable):
        """Add callback function for real-time data"""
        if market_type not in self.data_callbacks:
            self.data_callbacks[market_type] = []
        self.data_callbacks[market_type].append(callback)
    
    def remove_data_callback(self, market_type: str, callback: Callable):
        """Remove callback function"""
        if market_type in self.data_callbacks:
            try:
                self.data_callbacks[market_type].remove(callback)
            except ValueError:
                pass
    
    def start(self):
        """Start the WebSocket client"""
        self.running = True
        logger.info("Polygon WebSocket client started")
    
    def stop(self):
        """Stop the WebSocket client"""
        self.running = False
        logger.info("Polygon WebSocket client stopped")
    
    def get_cached_quote(self, symbol: str, market_type: str = 'stocks') -> Optional[Dict[str, Any]]:
        """Get cached real-time quote from WebSocket data"""
        cache_key = f"ws_{market_type}_quote_{symbol.upper()}"
        return self.cache_manager.get(cache_key, 'quote')
    
    def get_cached_trade(self, symbol: str, market_type: str = 'stocks') -> Optional[Dict[str, Any]]:
        """Get cached real-time trade from WebSocket data"""
        cache_key = f"ws_{market_type}_trade_{symbol.upper()}"
        return self.cache_manager.get(cache_key, 'quote')


class PolygonWebSocketManager:
    """
    Manager for Polygon WebSocket connections with threading support
    
    This class manages WebSocket connections in a separate thread to avoid
    blocking the main Django application.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.client = None
        self.loop = None
        self.thread = None
        self.is_running = False
    
    def start(self):
        """Start WebSocket manager in separate thread"""
        if self.is_running:
            logger.warning("WebSocket manager is already running")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        logger.info("Polygon WebSocket manager started")
    
    def stop(self):
        """Stop WebSocket manager"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.loop and self.client:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), self.loop)
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Polygon WebSocket manager stopped")
    
    def _run_event_loop(self):
        """Run asyncio event loop in thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.client = PolygonWebSocketClient(self.api_key)
            self.client.start()
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"Error in WebSocket event loop: {e}")
        finally:
            self.loop.close()
    
    def subscribe_quotes(self, symbols: List[str], market_type: str = 'stocks'):
        """Subscribe to quotes (thread-safe)"""
        if not self.is_running or not self.client:
            logger.error("WebSocket manager is not running")
            return False
        
        future = asyncio.run_coroutine_threadsafe(
            self.client.subscribe_quotes(symbols, market_type), 
            self.loop
        )
        try:
            return future.result(timeout=10)
        except Exception as e:
            logger.error(f"Error subscribing to quotes: {e}")
            return False
    
    def subscribe_trades(self, symbols: List[str], market_type: str = 'stocks'):
        """Subscribe to trades (thread-safe)"""
        if not self.is_running or not self.client:
            logger.error("WebSocket manager is not running")
            return False
        
        future = asyncio.run_coroutine_threadsafe(
            self.client.subscribe_trades(symbols, market_type), 
            self.loop
        )
        try:
            return future.result(timeout=10)
        except Exception as e:
            logger.error(f"Error subscribing to trades: {e}")
            return False
    
    def get_cached_quote(self, symbol: str, market_type: str = 'stocks') -> Optional[Dict[str, Any]]:
        """Get cached quote data"""
        if self.client:
            return self.client.get_cached_quote(symbol, market_type)
        return None
    
    def get_cached_trade(self, symbol: str, market_type: str = 'stocks') -> Optional[Dict[str, Any]]:
        """Get cached trade data"""
        if self.client:
            return self.client.get_cached_trade(symbol, market_type)
        return None


# Global WebSocket manager instance
_websocket_manager = None

def get_websocket_manager() -> PolygonWebSocketManager:
    """Get global WebSocket manager instance"""
    global _websocket_manager
    if _websocket_manager is None:
        api_key = getattr(settings, 'POLYGON_IO_API_KEY', None)
        _websocket_manager = PolygonWebSocketManager(api_key)
    return _websocket_manager