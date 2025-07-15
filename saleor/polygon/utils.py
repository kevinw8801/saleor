import requests
from decimal import Decimal
from typing import Optional, Dict, Any


class PolygonRPCClient:
    def __init__(self, rpc_url: str = "https://polygon-rpc.com"):
        self.rpc_url = rpc_url
        self.session = requests.Session()

    def make_request(self, method: str, params: list = None) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }
        
        response = self.session.post(self.rpc_url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            raise Exception(f"RPC Error: {result['error']}")
        
        return result.get("result")

    def get_balance(self, address: str) -> Decimal:
        result = self.make_request("eth_getBalance", [address, "latest"])
        return Decimal(int(result, 16)) / Decimal(10**18)

    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return self.make_request("eth_getTransactionByHash", [tx_hash])

    def get_block_number(self) -> int:
        result = self.make_request("eth_blockNumber")
        return int(result, 16)


def validate_polygon_address(address: str) -> bool:
    if not address or len(address) != 42:
        return False
    
    if not address.startswith('0x'):
        return False
    
    try:
        int(address[2:], 16)
        return True
    except ValueError:
        return False


def format_polygon_value(value: int, decimals: int = 18) -> Decimal:
    return Decimal(value) / Decimal(10**decimals)


def wei_to_matic(wei_value: int) -> Decimal:
    return format_polygon_value(wei_value, 18)