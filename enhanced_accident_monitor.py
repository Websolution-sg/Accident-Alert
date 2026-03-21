#!/usr/bin/env python3
"""
Enhanced Accident Monitoring System
Modern, resilient accident monitoring with comprehensive error handling,
performance monitoring, and structured logging.
"""
import asyncio
import sys
import time
import signal
from typing import Set, Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

# Import our enhanced modules
from utils.config_manager import ConfigManager, get_config, AppConfig
from utils.logging_utils import create_logger, EnhancedLogger, health_monitor
from utils.performance_monitor import performance_monitor
from core.api_clients import create_waze_client, create_telegram_bot_client, create_telegram_user_client
from core.models import AccidentReport, AccidentSource, MessageStatus

class AccidentMonitoringSystem:
    """
    Main accident monitoring system with enhanced architecture
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = create_logger("accident_monitor")
        
        # Track processed accidents to avoid duplicates
        self.processed_accidents: Set[str] = set()
        self.recent_accidents: List[AccidentReport] = []
        self.max_recent_accidents = 1000
        
        # API clients
        self.waze_client = None
        self.telegram_bot_client = None
        self.telegram_user_client = None
        
        # Control flags
        self.is_running = False
        self.shutdown_requested = False
        
        # Statistics
        self.stats = {
            'waze_accidents_processed': 0,
            'telegram_accidents_processed': 0,
            'messages_sent': 0,
            'errors_encountered': 0,
            'start_time': None
        }
        
    async def initialize(self) -> bool:
        """
        Initialize the monitoring system
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            with self.logger.operation_context("system_initialization"):
                self.logger.info("Initializing Enhanced Accident Monitoring System")
                
                # Initialize API clients
                self._initialize_clients()
                
                # Start performance monitoring
                performance_monitor.start_monitoring(
                    interval=self.config.monitoring.health_check_interval
                )
                
                # Setup signal handlers for graceful shutdown
                self._setup_signal_handlers()
                
                # Load processed accidents from storage
                self._load_processed_accidents()
                
                self.logger.info("System initialization completed successfully")
                return True
                
        except Exception as e:
            self.logger.error("Failed to initialize monitoring system", error=e)
            return False
    
    def _initialize_clients(self):
        """Initialize API clients with configuration"""
        # Waze client
        bbox = {
            'bottom': self.config.waze.bbox_bottom,
            'left': self.config.waze.bbox_left,
            'right': self.config.waze.bbox_right,
            'top': self.config.waze.bbox_top
        }
        self.waze_client = create_waze_client(self.config.waze.api_url, bbox)
        
        # Telegram Bot client
        self.telegram_bot_client = create_telegram_bot_client(
            self.config.telegram.bot_token
        )
        
        # Telegram User client
        if self.config.telegram.api_id and self.config.telegram.api_hash:
            self.telegram_user_client = create_telegram_user_client(
                api_id=self.config.telegram.api_id,
                api_hash=self.config.telegram.api_hash,
                phone_number=self.config.telegram.phone_number,
                session_file=self.config.telegram.session_file
            )
        
        self.logger.info("API clients initialized successfully")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)
    
    def _load_processed_accidents(self):
        """Load previously processed accidents from storage"""
        try:
            processed_file = Path(self.config.database.processed_accidents_file)
            if processed_file.exists():
                import json
                with open(processed_file, 'r') as f:
                    data = json.load(f)
                    self.processed_accidents = set(
                        data.get('waze_accidents', []) + 
                        data.get('telegram_accidents', [])
                    )
                self.logger.info(f"Loaded {len(self.processed_accidents)} processed accident IDs")
                
        except Exception as e:
            self.logger.warning("Failed to load processed accidents", error=e)
    
    def _save_processed_accidents(self):
        """Save processed accidents to storage"""
        try:
            import json
            processed_file = Path(self.config.database.processed_accidents_file)
            
            # Split by source for compatibility
            waze_accidents = [
                acc_id for acc_id in self.processed_accidents 
                if acc_id.startswith('waze_')
            ]
            telegram_accidents = [
                acc_id for acc_id in self.processed_accidents 
                if acc_id.startswith('telegram_')
            ]
            
            data = {
                'waze_accidents': waze_accidents,
                'telegram_accidents': telegram_accidents,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(processed_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error("Failed to save processed accidents", error=e)
    
    async def process_waze_accidents(self) -> List[AccidentReport]:
        """
        Process accidents from Waze API
        
        Returns:
            List of new accident reports
        """
        new_accidents = []
        
        try:
            with self.logger.operation_context("waze_processing"):
                # Fetch accidents from Waze
                accidents = self.waze_client.fetch_accidents()
                
                for accident in accidents:
                    if accident.id not in self.processed_accidents:
                        # Check for near duplicates in recent accidents
                        if not self._is_duplicate_accident(accident):
                            accident.status = MessageStatus.PROCESSED
                            new_accidents.append(accident)
                            
                            self.processed_accidents.add(accident.id)
                            self._add_to_recent_accidents(accident)
                            
                            performance_monitor.collector.increment_counter(
                                "waze.accidents.new",
                                tags={'type': accident.accident_type.value}
                            )
                
                self.stats['waze_accidents_processed'] += len(new_accidents)
                self.logger.info(f"Processed {len(new_accidents)} new Waze accidents")
                
        except Exception as e:
            self.logger.error("Failed to process Waze accidents", error=e)
            self.stats['errors_encountered'] += 1
            
        return new_accidents
    
    async def process_telegram_channel(self) -> List[AccidentReport]:
        """
        Process accidents from Telegram channel monitoring
        
        Returns:
            List of new accident reports from Telegram
        """
        new_accidents = []
        
        if not self.telegram_user_client:
            return new_accidents
        
        try:
            with self.logger.operation_context("telegram_processing"):
                # Connect if not already connected
                if not self.telegram_user_client.is_connected:
                    connected = await self.telegram_user_client.connect()
                    if not connected:
                        self.logger.error("Failed to connect to Telegram user client")
                        return new_accidents
                
                # Get recent messages from monitored channel
                accidents = await self.telegram_user_client.get_recent_messages(
                    channel_id=self.config.telegram.sgaccident_channel_id,
                    limit=20  # Check last 20 messages
                )
                
                for accident in accidents:
                    if accident.id not in self.processed_accidents:
                        if not self._is_duplicate_accident(accident):
                            accident.status = MessageStatus.PROCESSED
                            new_accidents.append(accident)
                            
                            self.processed_accidents.add(accident.id)
                            self._add_to_recent_accidents(accident)
                            
                            performance_monitor.collector.increment_counter(
                                "telegram.accidents.new"
                            )
                
                self.stats['telegram_accidents_processed'] += len(new_accidents)
                self.logger.info(f"Processed {len(new_accidents)} new Telegram accidents")
                
        except Exception as e:
            self.logger.error("Failed to process Telegram accidents", error=e)
            self.stats['errors_encountered'] += 1
            
        return new_accidents
    
    def _is_duplicate_accident(self, accident: AccidentReport) -> bool:
        """Check if accident is a duplicate of recent accidents"""
        for recent in self.recent_accidents:
            if accident.is_duplicate_of(recent, self.config.geographic.duplicate_detection_radius):
                self.logger.debug(f"Duplicate accident detected: {accident.id}")
                return True
        return False
    
    def _add_to_recent_accidents(self, accident: AccidentReport):
        """Add accident to recent accidents list"""
        self.recent_accidents.append(accident)
        
        # Keep only recent accidents (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.recent_accidents = [
            acc for acc in self.recent_accidents 
            if acc.timestamp >= cutoff_time
        ]
        
        # Limit size
        if len(self.recent_accidents) > self.max_recent_accidents:
            self.recent_accidents = self.recent_accidents[-self.max_recent_accidents:]
    
    async def send_accident_alert(self, accident: AccidentReport) -> bool:
        """
        Send accident alert via Telegram
        
        Args:
            accident: AccidentReport to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            with self.logger.operation_context("send_alert", accident_id=accident.id):
                message = accident.to_telegram_message()
                
                result = self.telegram_bot_client.send_message(
                    chat_id=str(self.config.telegram.target_channel_id),
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
                
                if result:
                    accident.forwarded_message_id = result.get('message_id')
                    self.stats['messages_sent'] += 1
                    
                    self.logger.info(
                        f"Accident alert sent successfully",
                        accident_id=accident.id,
                        message_id=result.get('message_id')
                    )
                    
                    performance_monitor.collector.increment_counter(
                        "alerts.sent",
                        tags={'source': accident.source.value}
                    )
                    
                    return True
                else:
                    self.logger.warning(f"Failed to send accident alert: {accident.id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error sending accident alert", error=e, accident_id=accident.id)
            self.stats['errors_encountered'] += 1
            return False
    
    async def monitoring_cycle(self):
        """Execute one monitoring cycle"""  
        cycle_start = time.time()
        
        try:
            with self.logger.operation_context("monitoring_cycle"):
                # Process Waze accidents
                waze_accidents = await self.process_waze_accidents()
                
                # Process Telegram accidents  
                telegram_accidents = await self.process_telegram_channel()
                
                # Send alerts for all new accidents
                all_accidents = waze_accidents + telegram_accidents
                
                for accident in all_accidents:
                    success = await self.send_accident_alert(accident)
                    if not success:
                        accident.status = MessageStatus.FAILED
                    
                    # Small delay between messages to respect rate limits
                    if self.config.telegram.rate_limit_delay > 0:
                        await asyncio.sleep(self.config.telegram.rate_limit_delay)
                
                # Save processed accidents
                if all_accidents:
                    self._save_processed_accidents()
                
                cycle_duration = time.time() - cycle_start
                performance_monitor.collector.record_timing(
                    "monitoring_cycle.duration", 
                    cycle_duration
                )
                
                self.logger.debug(
                    f"Monitoring cycle completed in {cycle_duration:.2f}s",
                    waze_accidents=len(waze_accidents),
                    telegram_accidents=len(telegram_accidents),
                    total_new=len(all_accidents)
                )
                
        except Exception as e:
            self.logger.error("Error in monitoring cycle", error=e)
            self.stats['errors_encountered'] += 1
    
    async def run(self):
        """
        Main monitoring loop
        """
        if not await self.initialize():
            self.logger.critical("Failed to initialize system, exiting")
            return False
            
        self.is_running = True
        self.stats['start_time'] = datetime.now()
        
        self.logger.info("Starting accident monitoring system")
        
        try:
            while self.is_running and not self.shutdown_requested:
                await self.monitoring_cycle()
                
                # Wait between check cycles
                await asyncio.sleep(self.config.waze.poll_interval) 
                
                # Log health status periodically
                if int(time.time()) % (self.config.monitoring.health_check_interval) == 0:
                    health_monitor.log_health_status()
                    self._log_statistics()
                    
        except KeyboardInterrupt:
            self.logger.info("Monitoring interrupted by user")
        except Exception as e:
            self.logger.critical("Critical error in monitoring loop", error=e)
        finally:
            await self.shutdown()
    
    def _log_statistics(self):
        """Log system statistics"""
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']
            self.logger.info(
                "System statistics",
                uptime_hours=round(uptime.total_seconds() / 3600, 2),
                waze_accidents=self.stats['waze_accidents_processed'],
                telegram_accidents=self.stats['telegram_accidents_processed'],
                messages_sent=self.stats['messages_sent'],
                errors=self.stats['errors_encountered'],
                processed_ids_count=len(self.processed_accidents)
            )
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Initiating system shutdown")
        
        self.is_running = False
        
        # Save final state
        self._save_processed_accidents()
        
        # Disconnect Telegram user client
        if self.telegram_user_client and self.telegram_user_client.is_connected:
            await self.telegram_user_client.disconnect()
        
        # Stop performance monitoring
        performance_monitor.stop_monitoring()
        
        # Log final statistics
        self._log_statistics()
        
        self.logger.info("System shutdown completed")

async def main():
    """Main entry point"""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Create and run monitoring system
        monitor = AccidentMonitoringSystem(config)
        await monitor.run()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    import sys
    
    # Set up basic logging for startup
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nShutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"Startup failed: {e}")
        sys.exit(1)