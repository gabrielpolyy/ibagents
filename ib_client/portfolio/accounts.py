from typing import List
from pydantic import BaseModel
import logging

from ..core.session import SessionAdapter
from ..core.http import _get

logger = logging.getLogger(__name__)

class Account(BaseModel):
    id: str
    type: str
    desc: str = ""
    covestor: bool = False

class AccountsAdapter(SessionAdapter):
    """Adapter for managing IB accounts"""
    
    def __init__(self):
        super().__init__()
    
    async def get_accounts(self) -> List[Account]:
        """Get list of available accounts"""
        await self._ensure_live()
        
        try:
            data = await _get("/portfolio/accounts")
            logger.debug(f"Accounts data: {data}")
            
            accounts = []
            for account_data in data:
                # Handle different response formats
                if isinstance(account_data, dict):
                    account = Account(
                        id=account_data.get("id", account_data.get("accountId", "")),
                        type=account_data.get("type", account_data.get("accountVan", "")),
                        desc=account_data.get("desc", ""),
                        covestor=account_data.get("covestor", False)
                    )
                    accounts.append(account)
                else:
                    # Sometimes the API returns just account IDs as strings
                    accounts.append(Account(id=str(account_data), type="UNKNOWN"))
            
            logger.info(f"Found {len(accounts)} accounts")
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            raise
    
    async def get_account_summary(self, account_id: str) -> dict:
        """Get summary information for a specific account"""
        await self._ensure_live()
        
        try:
            data = await _get(f"/portfolio/{account_id}/summary")
            logger.debug(f"Account {account_id} summary: {data}")
            return data
        except Exception as e:
            logger.error(f"Failed to get account summary for {account_id}: {e}")
            raise 