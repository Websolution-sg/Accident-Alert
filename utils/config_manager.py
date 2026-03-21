#!/usr/bin/env python3
"""
Configuration management system with validation and environment support
Provides centralized configuration with type checking and validation
"""
import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union, Type
from dataclasses import dataclass, field, fields
from pathlib import Path
import logging
from enum import Enum

class Environment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"
    LOCAL = "local"

@dataclass
class TelegramConfig:
    """Telegram API configuration"""
    bot_token: str
    api_id: int
    api_hash: str
    phone_number: str
    session_file: str = "pukiboi_session"
    
    # Channel IDs
    sgaccident_channel_id: int = -1001486947378
    target_channel_id: int = -1003683261194
    
    # Timeouts and limits
    request_timeout: int = 10
    max_retries: int = 3
    rate_limit_delay: float = 1.0

@dataclass 
class WazeConfig:
    """Waze API configuration"""
    api_url: str = "https://www.waze.com/live-map/api/georss"
    
    # Singapore bounding box
    bbox_bottom: float = 1.1304753
    bbox_left: float = 103.6055424
    bbox_right: float = 104.0945619
    bbox_top: float = 1.4764671
    
    # Request configuration
    request_timeout: int = 10
    max_retries: int = 3
    poll_interval: int = 60  # seconds

@dataclass
class GeographicConfig:
    """Geographic filtering configuration"""
    # Singapore bounds
    singapore_north: float = 1.4784
    singapore_south: float = 1.1496 
    singapore_east: float = 104.0853
    singapore_west: float = 103.6065
    
    # Duplicate detection  
    duplicate_detection_radius: int = 100  # meters
    coordinate_precision: int = 3  # decimal places

@dataclass
class MonitoringConfig:
    """System monitoring configuration"""
    health_check_interval: int = 300  # seconds
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    max_log_file_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # Performance settings
    enable_metrics: bool = True
    metrics_retention: int = 1000  # number of metrics to keep
    
    # Error tracking
    max_errors_tracked: int = 100
    error_alert_threshold: int = 10  # errors per hour

@dataclass 
class DatabaseConfig:
    """Database configuration"""
    processed_accidents_file: str = "processed_accidents.json"
    telegram_offset_file: str = "telegram_offset.json"
    user_processed_file: str = "user_processed_accidents.json"
    
    # Data retention
    max_processed_records: int = 10000
    cleanup_interval_hours: int = 24

@dataclass
class SecurityConfig:
    """Security configuration"""  
    validate_coordinates: bool = True
    sanitize_messages: bool = True
    max_message_length: int = 4096
    
    # Rate limiting
    enable_rate_limiting: bool = True
    max_requests_per_minute: int = 30
    
    # Circuit breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60

@dataclass
class AppConfig:
    """Main application configuration"""
    # Environment settings
    environment: Environment = Environment.LOCAL
    debug: bool = False
    
    # Component configurations
    telegram: TelegramConfig = field(default_factory=lambda: TelegramConfig("", 0, "", ""))
    waze: WazeConfig = field(default_factory=WazeConfig)
    geographic: GeographicConfig = field(default_factory=GeographicConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Deployment settings
    deployment_region: str = "us-central1-a"
    vm_name: str = "sg-accident-monitor"
    project_id: str = "verdant-petal-485213-h2"

class ConfigurationError(Exception):
    """Configuration validation error"""
    pass

class ConfigManager:
    """
    Configuration manager with validation and environment support
    """
    
    def __init__(self, config_dir: str = "config", 
                 environment: Optional[Environment] = None):
        self.config_dir = Path(config_dir)
        self.environment = environment or self._detect_environment()
        self.config: Optional[AppConfig] = None
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
    def _detect_environment(self) -> Environment:
        """Detect environment from environment variables or file"""
        env_name = os.getenv("APP_ENVIRONMENT", "local").lower()
        
        try:
            return Environment(env_name)
        except ValueError:
            logging.warning(f"Unknown environment '{env_name}', defaulting to LOCAL")
            return Environment.LOCAL
            
    def _validate_config(self, config: AppConfig) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate required Telegram settings
        if not config.telegram.bot_token:
            errors.append("telegram.bot_token is required")
        if not config.telegram.api_id:
            errors.append("telegram.api_id is required")  
        if not config.telegram.api_hash:
            errors.append("telegram.api_hash is required")
        if not config.telegram.phone_number:
            errors.append("telegram.phone_number is required")
            
        # Validate geographic bounds
        geo = config.geographic
        if geo.singapore_north <= geo.singapore_south:
            errors.append("singapore_north must be greater than singapore_south")
        if geo.singapore_east <= geo.singapore_west:
            errors.append("singapore_east must be greater than singapore_west")
            
        # Validate Waze bbox
        waze = config.waze
        if waze.bbox_top <= waze.bbox_bottom:
            errors.append("waze.bbox_top must be greater than bbox_bottom")
        if waze.bbox_right <= waze.bbox_left:
            errors.append("waze.bbox_right must be greater than bbox_left")
            
        # Validate monitoring settings
        if config.monitoring.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append("monitoring.log_level must be a valid logging level")
            
        return errors
        
    def load_from_file(self, filename: str) -> AppConfig:
        """Load configuration from file"""
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
            
        try:
            with open(file_path, 'r') as f:
                if filename.endswith('.json'):
                    data = json.load(f)
                elif filename.endswith('.yaml') or filename.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    raise ConfigurationError(f"Unsupported file format: {filename}")
                    
            config = self._dict_to_config(data)
            
            # Validate configuration
            errors = self._validate_config(config)
            if errors:
                raise ConfigurationError(f"Configuration validation failed: {errors}")
                
            return config
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ConfigurationError(f"Error parsing configuration file: {e}")
            
    def _dict_to_config(self, data: Dict[str, Any]) -> AppConfig:
        """Convert dictionary to AppConfig object"""
        # Handle environment
        if 'environment' in data:
            if isinstance(data['environment'], str):
                data['environment'] = Environment(data['environment'])
                
        # Create nested config objects
        if 'telegram' in data:
            data['telegram'] = TelegramConfig(**data['telegram'])
        if 'waze' in data:  
            data['waze'] = WazeConfig(**data['waze'])
        if 'geographic' in data:
            data['geographic'] = GeographicConfig(**data['geographic'])
        if 'monitoring' in data:
            data['monitoring'] = MonitoringConfig(**data['monitoring'])
        if 'database' in data:
            data['database'] = DatabaseConfig(**data['database'])
        if 'security' in data:
            data['security'] = SecurityConfig(**data['security'])
            
        return AppConfig(**data)
        
    def load_from_environment(self) -> AppConfig:
        """Load configuration from environment variables"""
        config = AppConfig()
        
        # Load Telegram config from env vars
        if os.getenv('TELEGRAM_BOT_TOKEN'):
            config.telegram.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if os.getenv('TELEGRAM_API_ID'):
            config.telegram.api_id = int(os.getenv('TELEGRAM_API_ID'))
        if os.getenv('TELEGRAM_API_HASH'):
            config.telegram.api_hash = os.getenv('TELEGRAM_API_HASH')
        if os.getenv('TELEGRAM_PHONE'):
            config.telegram.phone_number = os.getenv('TELEGRAM_PHONE')
            
        # Load other settings from env vars
        if os.getenv('LOG_LEVEL'):
            config.monitoring.log_level = os.getenv('LOG_LEVEL').upper()
        if os.getenv('DEBUG'):
            config.debug = os.getenv('DEBUG').lower() in ['true', '1', 'yes']
            
        return config
        
    def save_to_file(self, config: AppConfig, filename: str):
        """Save configuration to file"""
        file_path = self.config_dir / filename
        
        # Convert config to dict
        data = self._config_to_dict(config)
        
        try:
            with open(file_path, 'w') as f:
                if filename.endswith('.json'):
                    json.dump(data, f, indent=2, default=str)
                elif filename.endswith('.yaml') or filename.endswith('.yml'):
                    yaml.dump(data, f, default_flow_style=False)
                else:
                    raise ConfigurationError(f"Unsupported file format: {filename}")
                    
        except Exception as e:
            raise ConfigurationError(f"Error saving configuration: {e}")
            
    def _config_to_dict(self, config: AppConfig) -> Dict[str, Any]:
        """Convert AppConfig to dictionary"""
        result = {}
        
        for field in fields(config):
            value = getattr(config, field.name)
            
            if hasattr(value, '__dict__'):
                # Convert dataclass to dict
                result[field.name] = {
                    f.name: getattr(value, f.name) 
                    for f in fields(value)
                }
            elif isinstance(value, Enum):
                result[field.name] = value.value
            else:
                result[field.name] = value
                
        return result
        
    def get_config(self) -> AppConfig:
        """Get current configuration"""
        if self.config is None:
            self.load_configuration()
        return self.config
        
    def load_configuration(self):
        """Load configuration using priority order"""
        # 1. Try environment-specific file
        env_file = f"config.{self.environment.value}.yaml"
        try:
            self.config = self.load_from_file(env_file)
            logging.info(f"Loaded configuration from {env_file}")
            return
        except ConfigurationError:
            pass
            
        # 2. Try default config file
        try:
            self.config = self.load_from_file("config.yaml")
            logging.info("Loaded configuration from config.yaml")
            return
        except ConfigurationError:
            pass
            
        # 3. Load from environment variables
        self.config = self.load_from_environment()
        logging.info("Loaded configuration from environment variables")
        
        # Validate final configuration
        errors = self._validate_config(self.config)
        if errors:
            raise ConfigurationError(f"Configuration validation failed: {errors}")

def create_production_config() -> AppConfig:
    """Create production configuration template"""
    return AppConfig(
        environment=Environment.PRODUCTION,
        debug=False,
        telegram=TelegramConfig(
            bot_token="8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ",
            api_id=37340693,
            api_hash="59c3213333e09271844a64d38be167a4",
            phone_number="+6598590227",
            session_file="pukiboi_session"
        ),
        monitoring=MonitoringConfig(
            log_level="INFO",
            health_check_interval=300,
            enable_metrics=True
        ),
        security=SecurityConfig(
            enable_rate_limiting=True,
            circuit_breaker_failure_threshold=5
        )
    )

# Global configuration manager
config_manager = ConfigManager()

def get_config() -> AppConfig:
    """Get global configuration"""
    return config_manager.get_config()

if __name__ == "__main__":
    # Example usage - create sample config files
    config_mgr = ConfigManager() 
    
    # Create production config
    prod_config = create_production_config()
    config_mgr.save_to_file(prod_config, "config.production.yaml")
    
    # Create development config  
    dev_config = create_production_config()
    dev_config.environment = Environment.DEVELOPMENT
    dev_config.debug = True
    dev_config.monitoring.log_level = "DEBUG"
    config_mgr.save_to_file(dev_config, "config.development.yaml")
    
    print("Sample configuration files created!")
    
    # Test loading
    loaded_config = config_mgr.load_from_file("config.production.yaml")
    print(f"Loaded config for {loaded_config.environment.value} environment")