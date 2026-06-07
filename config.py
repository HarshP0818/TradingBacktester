"""
Configuration loader module for the backtesting engine.
Loads YAML configuration and provides access to all parameters.
"""
import yaml
import os
from logging_config import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages loading and accessing configuration from YAML file."""
    
    def __init__(self, config_path="config.yaml"):
        """
        Initialize config manager.
        
        Args:
            config_path: Path to config.yaml file (relative or absolute)
        """
        # If relative path, make it relative to the directory where this file is
        if not os.path.isabs(config_path):
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                config_path
            )
        
        self.config_path = config_path
        self.config = self._load_config()
        logger.info(f"Loaded configuration from {config_path}")
    
    def _load_config(self):
        """Load YAML configuration file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                if config is None:
                    raise ValueError("Configuration file is empty")
                return config
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise
    
    def get(self, key_path, default=None):
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value (e.g., "backtest.initial_cash")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            config.get("backtest.initial_cash") -> 100000
            config.get("strategy.fast_window") -> 20
        """
        keys = key_path.split(".")
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            if default is None:
                logger.warning(f"Configuration key not found: {key_path}")
            return default
    
    def get_backtest_config(self):
        """Get all backtest configuration."""
        return self.config.get("backtest", {})
    
    def get_strategy_config(self):
        """Get all strategy configuration."""
        return self.config.get("strategy", {})
    
    def get_data_config(self):
        """Get all data configuration."""
        return self.config.get("data", {})
    
    def get_position_sizing_config(self):
        """Get all position sizing configuration."""
        return self.config.get("position_sizing", {})
    
    def get_database_config(self):
        """Get database configuration."""
        db_config = self.config.get("database", {})
        # Replace environment variable placeholders
        if "user" in db_config and "${DB_USER}" in str(db_config["user"]):
            db_config["user"] = os.getenv("DB_USER")
        if "password" in db_config and "${DB_PASSWORD}" in str(db_config["password"]):
            db_config["password"] = os.getenv("DB_PASSWORD")
        return db_config


def load_config(config_path="config.yaml"):
    """Convenience function to load configuration."""
    return ConfigManager(config_path)
