"""
Configuration Manager for RAG System
Handles persistent configuration storage and retrieval
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SystemConfiguration:
    """System configuration settings"""
    # LLM Settings
    llm_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2048

    # RAG Settings
    confidence_threshold: float = 0.5
    top_k_results: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 50

    # Prompt Template
    system_prompt_template: str = """You are an intelligent AI assistant with expertise in analyzing and answering questions based on provided documents.

Your capabilities:
- Provide accurate, well-structured answers based on the given context
- Cite specific information from the context when relevant
- Acknowledge when information is not available in the context
- Maintain a helpful, professional tone

Response guidelines:
- Answer directly and concisely
- Use information from the provided context
- If context doesn't contain the answer, state this clearly
- Format responses for readability"""

    # Metadata
    last_updated: Optional[str] = None
    updated_by: Optional[str] = None


class ConfigurationManager:
    """Manages system configuration with persistence"""

    # Available LLM models with metadata
    AVAILABLE_MODELS = [
        {
            "id": "gpt-4o",
            "name": "GPT-4 Optimized",
            "provider": "OpenAI",
            "description": "Most capable model, best for complex reasoning",
            "context_length": 128000,
            "cost_per_1k_tokens": 0.03,
            "recommended": False
        },
        {
            "id": "gpt-4o-mini",
            "name": "GPT-4 Optimized Mini",
            "provider": "OpenAI",
            "description": "Balanced performance and cost, great for most tasks",
            "context_length": 128000,
            "cost_per_1k_tokens": 0.0015,
            "recommended": True
        },
        {
            "id": "gpt-4-turbo",
            "name": "GPT-4 Turbo",
            "provider": "OpenAI",
            "description": "Fast and powerful, excellent for complex tasks",
            "context_length": 128000,
            "cost_per_1k_tokens": 0.02,
            "recommended": False
        },
        {
            "id": "gpt-3.5-turbo",
            "name": "GPT-3.5 Turbo",
            "provider": "OpenAI",
            "description": "Fast and economical, good for simple queries",
            "context_length": 16385,
            "cost_per_1k_tokens": 0.001,
            "recommended": False
        }
    ]

    def __init__(self, config_path: str = "data/system_config.json"):
        self.config_path = Path(config_path)
        self.config: SystemConfiguration = SystemConfiguration()
        self._ensure_config_dir()
        self._load_config()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """Load configuration from file or create default"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.config = SystemConfiguration(**data)
                    logger.info(f"✅ Configuration loaded from {self.config_path}")
            else:
                # Create default configuration
                self._save_config()
                logger.info(f"✅ Default configuration created at {self.config_path}")
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            logger.info("Using default configuration")

    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
            logger.info(f"✅ Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
            raise

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return asdict(self.config)

    def update_config(self, updates: Dict[str, Any], user_email: Optional[str] = None) -> Dict[str, Any]:
        """Update configuration with new values"""
        try:
            # Validate and update configuration
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                else:
                    logger.warning(f"Unknown configuration key: {key}")

            # Update metadata
            self.config.last_updated = datetime.utcnow().isoformat()
            self.config.updated_by = user_email

            # Save to file
            self._save_config()

            logger.info(f"✅ Configuration updated by {user_email or 'unknown'}")
            return asdict(self.config)

        except Exception as e:
            logger.error(f"❌ Failed to update configuration: {e}")
            raise

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available LLM models"""
        return self.AVAILABLE_MODELS

    def get_current_model(self) -> str:
        """Get currently selected model"""
        return self.config.llm_model

    def set_model(self, model_id: str, user_email: Optional[str] = None) -> Dict[str, Any]:
        """Set LLM model"""
        # Validate model exists
        valid_models = [m["id"] for m in self.AVAILABLE_MODELS]
        if model_id not in valid_models:
            raise ValueError(f"Invalid model: {model_id}. Available models: {valid_models}")

        return self.update_config({"llm_model": model_id}, user_email)

    def get_confidence_threshold(self) -> float:
        """Get confidence threshold"""
        return self.config.confidence_threshold

    def set_confidence_threshold(self, threshold: float, user_email: Optional[str] = None) -> Dict[str, Any]:
        """Set confidence threshold"""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")

        return self.update_config({"confidence_threshold": threshold}, user_email)

    def get_prompt_template(self) -> str:
        """Get system prompt template"""
        return self.config.system_prompt_template

    def set_prompt_template(self, template: str, user_email: Optional[str] = None) -> Dict[str, Any]:
        """Set system prompt template"""
        if not template or not template.strip():
            raise ValueError("Prompt template cannot be empty")

        return self.update_config({"system_prompt_template": template}, user_email)

    def reset_to_defaults(self, user_email: Optional[str] = None) -> Dict[str, Any]:
        """Reset configuration to defaults"""
        self.config = SystemConfiguration()
        self.config.last_updated = datetime.utcnow().isoformat()
        self.config.updated_by = user_email
        self._save_config()
        logger.info(f"✅ Configuration reset to defaults by {user_email or 'unknown'}")
        return asdict(self.config)


# Global configuration manager instance
_config_manager_instance: Optional[ConfigurationManager] = None


def set_config_manager(config_manager: ConfigurationManager):
    """Set global configuration manager instance"""
    global _config_manager_instance
    _config_manager_instance = config_manager


def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager instance"""
    if not _config_manager_instance:
        raise RuntimeError("Configuration manager not initialized")
    return _config_manager_instance
