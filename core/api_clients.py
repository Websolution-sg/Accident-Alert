#!/usr/bin/env python3
"""
Type-safe API clients for Waze and Telegram services
Uses enhanced error handling, logging, and performance monitoring
"""
import asyncio
import time
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import requests
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel

# Import our utility modules
from utils.error_handling import ResilientAPIClient, with_retry, RetryConfig, global_error_tracker
from utils.logging_utils import create_logger, EnhancedLogger
from utils.performance_monitor import performance_monitor
from core.models import AccidentReport, AccidentSource, WazeAccidentParser, TelegramAccidentParser

class WazeAPIClient:
    """
    Type-safe Waze API client with resilience and monitoring
    """
    
    def __init__(self, api_url: str, bbox: Dict[str, float], 
                 logger: Optional[EnhancedLogger] = None):
        self.api_url = api_url
        self.bbox = bbox
        self.logger = logger or create_logger("waze_client")
        
        # Configure resilient HTTP client
        retry_config = RetryConfig(max_attempts=3, base_delay=2.0, max_delay=30.0)
        self.client = ResilientAPIClient("WazeAPI", retry_config)
        
        # Setup headers for Waze API
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.waze.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        self.parser = WazeAccidentParser()
        
    def fetch_raw_alerts(self) -> List[Dict[str, Any]]:
        """
        Fetch raw alert data from Waze API
        
        Returns:
            List of raw alert dictionaries from Waze
            
        Raises:
            requests.RequestException: If API request fails after retries
        """
        with self.logger.operation_context("fetch_waze_alerts"):
            with performance_monitor.api_monitor.monitor_request("waze", "georss"):
                
                params = {
                    'bottom': self.bbox['bottom'],
                    'left': self.bbox['left'],
                    'right': self.bbox['right'], 
                    'top': self.bbox['top'],
                    'env': 'row',
                    'types': 'alerts,traffic'
                }
                
                response = self.client.get(
                    self.api_url,
                    params=params,
                    headers=self.headers,
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                alerts = data.get('alerts', [])
                
                self.logger.info(f"Fetched {len(alerts)} alerts from Waze API")
                performance_monitor.collector.set_gauge("waze.alerts.count", len(alerts))
                
                return alerts
    
    def fetch_accidents(self) -> List[AccidentReport]:
        """
        Fetch and parse accident reports from Waze API
        
        Returns:
            List of parsed AccidentReport objects
        """
        try:
            alerts = self.fetch_raw_alerts()
            
            # Filter to accident types only
            accident_alerts = [
                alert for alert in alerts
                if (alert.get('type', '').upper() in ['ACCIDENT', 'ACCIDENT_MINOR', 'ACCIDENT_MAJOR'] or
                    alert.get('subtype', '').upper() in ['ACCIDENT', 'ACCIDENT_MINOR', 'ACCIDENT_MAJOR'])
            ]
            
            # Parse into AccidentReport objects
            accidents = []
            for alert in accident_alerts:
                try:
                    accident = self.parser.parse(alert)
                    if accident:
                        accidents.append(accident)
                except Exception as e:
                    global_error_tracker.log_error(e, {'alert_data': alert})
                    self.logger.warning(f"Failed to parse Waze alert: {e}")
            
            self.logger.info(f"Parsed {len(accidents)} accidents from {len(accident_alerts)} accident alerts")
            performance_monitor.collector.set_gauge("waze.accidents.parsed", len(accidents))
            
            return accidents
            
        except Exception as e:
            global_error_tracker.log_error(e, {'operation': 'fetch_accidents'})
            self.logger.error("Failed to fetch accidents from Waze", error=e)
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Waze API
        
        Returns:
            Dictionary with health status information
        """
        try:
            start_time = time.time()
            alerts = self.fetch_raw_alerts()
            response_time = time.time() - start_time
            
            return {
                'status': 'healthy',
                'response_time': response_time,
                'alerts_count': len(alerts),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

class TelegramAPIClient:
    """
    Type-safe Telegram Bot API client
    """
    
    def __init__(self, bot_token: str, logger: Optional[EnhancedLogger] = None):
        self.bot_token = bot_token
        self.logger = logger or create_logger("telegram_bot_client")
        
        # Configure resilient HTTP client
        retry_config = RetryConfig(max_attempts=5, base_delay=1.0, max_delay=60.0)
        self.client = ResilientAPIClient("TelegramBot", retry_config)
        
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, chat_id: str, text: str, parse_mode: str = "Markdown",
                    disable_web_page_preview: bool = True) -> Optional[Dict[str, Any]]:
        """
        Send message via Telegram Bot API
        
        Args:
            chat_id: Target chat ID
            text: Message text
            parse_mode: Message parsing mode (Markdown, HTML, or None)
            disable_web_page_preview: Whether to disable link previews
            
        Returns:
            API response dictionary or None if failed
        """
        with self.logger.operation_context("send_telegram_message", chat_id=chat_id):
            with performance_monitor.api_monitor.monitor_request("telegram", "sendMessage"):
                
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "disable_web_page_preview": disable_web_page_preview
                }
                
                if parse_mode:
                    payload["parse_mode"] = parse_mode
                
                try:
                    response = self.client.post(
                        f"{self.base_url}/sendMessage",
                        json=payload,
                        timeout=10
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    if result.get('ok'):
                        message_id = result['result']['message_id']
                        self.logger.info(f"Message sent successfully (ID: {message_id})")
                        performance_monitor.collector.increment_counter("telegram.messages.sent")
                        return result['result']
                    else:
                        self.logger.error(f"Telegram API error: {result}")
                        return None
                        
                except Exception as e:
                    global_error_tracker.log_error(e, {
                        'operation': 'send_message',
                        'chat_id': chat_id,
                        'text_length': len(text)
                    })
                    self.logger.error("Failed to send Telegram message", error=e)
                    return None
    
    def get_updates(self, offset: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get updates from Telegram Bot API
        
        Args:
            offset: Offset for getting updates
            limit: Maximum number of updates to retrieve
            
        Returns:
            List of update dictionaries
        """
        with performance_monitor.api_monitor.monitor_request("telegram", "getUpdates"):
            
            params = {"limit": limit}
            if offset is not None:
                params["offset"] = offset
            
            try:
                response = self.client.get(
                    f"{self.base_url}/getUpdates",
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get('ok'):
                    updates = result['result']
                    self.logger.debug(f"Retrieved {len(updates)} updates from Telegram")
                    return updates
                else:
                    self.logger.error(f"Telegram API error: {result}")
                    return []
                    
            except Exception as e:
                global_error_tracker.log_error(e, {'operation': 'get_updates'})
                self.logger.error("Failed to get Telegram updates", error=e)
                return []
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on Telegram Bot API"""
        try:
            start_time = time.time()
            response = self.client.get(f"{self.base_url}/getMe", timeout=5)
            response.raise_for_status()
            
            result = response.json()
            response_time = time.time() - start_time
            
            if result.get('ok'):
                bot_info = result['result']
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'bot_username': bot_info.get('username'),
                    'bot_name': bot_info.get('first_name'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': result.get('description', 'Unknown error'),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

class TelegramUserClient:
    """
    Async Telegram user client using Telethon for monitoring channels
    """
    
    def __init__(self, api_id: int, api_hash: str, phone_number: str,
                 session_file: str = "session", logger: Optional[EnhancedLogger] = None):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_file = session_file
        self.logger = logger or create_logger("telegram_user_client")
        
        self.client: Optional[TelegramClient] = None
        self.parser = TelegramAccidentParser()
        self.is_connected = False
        
    async def connect(self) -> bool:
        """
        Connect to Telegram using user credentials
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client = TelegramClient(self.session_file, self.api_id, self.api_hash)
            await self.client.start(phone=self.phone_number)
            
            # Verify connection
            me = await self.client.get_me()
            self.is_connected = True
            
            self.logger.info(f"Connected to Telegram as {me.username} ({me.first_name})")
            performance_monitor.collector.increment_counter("telegram_user.connections.success")
            
            return True
            
        except Exception as e:
            global_error_tracker.log_error(e, {'operation': 'connect'})
            self.logger.error("Failed to connect to Telegram", error=e)
            performance_monitor.collector.increment_counter("telegram_user.connections.failed")
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
            self.logger.info("Disconnected from Telegram")
    
    async def monitor_channel(self, channel_id: int) -> AsyncGenerator[AccidentReport, None]:
        """
        Monitor a channel for new accident messages
        
        Args:
            channel_id: Telegram channel ID to monitor
            
        Yields:
            AccidentReport objects for new accident messages
        """
        if not self.is_connected:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        self.logger.info(f"Starting to monitor channel {channel_id}")
        
        @self.client.on(events.NewMessage(chats=[PeerChannel(channel_id)]))
        async def message_handler(event):
            try:
                message = event.message
                
                # Convert to dict format for parser
                message_data = {
                    'text': message.text or '',
                    'message_id': message.id,
                    'date': message.date.timestamp() if message.date else time.time(),
                    'chat': {'id': channel_id},
                    'from_user': {'username': 'channel'}
                }
                
                # Try to parse as accident
                accident = self.parser.parse(message_data)
                if accident:
                    self.logger.info(f"New accident detected: {accident.id}")
                    performance_monitor.collector.increment_counter("telegram_user.accidents.detected")
                    yield accident
                    
            except Exception as e:
                global_error_tracker.log_error(e, {
                    'operation': 'message_handler',
                    'channel_id': channel_id,
                    'message_id': getattr(event.message, 'id', 'unknown')
                })
                self.logger.error("Error processing channel message", error=e)
        
        # Keep the client running
        try:
            await self.client.run_until_disconnected()
        except Exception as e:
            self.logger.error("Channel monitoring stopped", error=e)
    
    async def get_recent_messages(self, channel_id: int, limit: int = 10) -> List[AccidentReport]:
        """
        Get recent messages from a channel and parse for accidents
        
        Args:
            channel_id: Channel ID to fetch from  
            limit: Maximum number of messages to fetch
            
        Returns:
            List of AccidentReport objects found in recent messages
        """
        if not self.is_connected:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        accidents = []
        
        try:
            async for message in self.client.iter_messages(PeerChannel(channel_id), limit=limit):
                if not message.text:
                    continue
                    
                message_data = {
                    'text': message.text,
                    'message_id': message.id, 
                    'date': message.date.timestamp() if message.date else time.time(),
                    'chat': {'id': channel_id},
                    'from_user': {'username': 'channel'}
                }
                
                accident = self.parser.parse(message_data)
                if accident:
                    accidents.append(accident)
                    
        except Exception as e:
            global_error_tracker.log_error(e, {
                'operation': 'get_recent_messages',
                'channel_id': channel_id
            })
            self.logger.error("Failed to get recent messages", error=e)
        
        self.logger.info(f"Found {len(accidents)} accidents in {limit} recent messages")
        return accidents

# Factory functions for easy client creation
def create_waze_client(api_url: str, bbox: Dict[str, float]) -> WazeAPIClient:
    """Create configured Waze API client"""
    return WazeAPIClient(api_url, bbox)

def create_telegram_bot_client(bot_token: str) -> TelegramAPIClient:
    """Create configured Telegram Bot API client"""
    return TelegramAPIClient(bot_token)

def create_telegram_user_client(api_id: int, api_hash: str, phone_number: str,
                               session_file: str = "session") -> TelegramUserClient:
    """Create configured Telegram User API client"""
    return TelegramUserClient(api_id, api_hash, phone_number, session_file)

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    # Test Waze client
    bbox = {
        'bottom': 1.1304753,
        'left': 103.6055424,  
        'right': 104.0945619,
        'top': 1.4764671
    }
    
    waze_client = create_waze_client("https://www.waze.com/live-map/api/georss", bbox)
    
    print("Testing Waze client...")
    accidents = waze_client.fetch_accidents()
    print(f"Found {len(accidents)} accidents")
    
    health = waze_client.health_check()
    print(f"Waze API health: {health['status']}")
    
    # Test Telegram bot client
    bot_client = create_telegram_bot_client("test_token")
    bot_health = bot_client.health_check()
    print(f"Telegram Bot health: {bot_health['status']}")