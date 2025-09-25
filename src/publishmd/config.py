"""Configuration loading and plugin management."""

import importlib
import yaml
from pathlib import Path
from typing import Any, Dict, List, Union

from .base import Emitter, Transformer, Filter


class ConfigLoader:
    """Loads and validates configuration from YAML files."""

    @staticmethod
    def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            Dictionary containing the configuration
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config or {}

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """
        Validate the configuration structure.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        # At least one of these sections must be present
        required_sections = ["emitters", "transformers", "filters"]
        if not any(section in config for section in required_sections):
            raise ValueError(
                f"Configuration must contain at least one of: {', '.join(required_sections)}"
            )

        for section in ["emitters", "transformers", "filters"]:
            if section in config:
                if not isinstance(config[section], list):
                    raise ValueError(f"'{section}' must be a list")

                for item in config[section]:
                    if not isinstance(item, dict):
                        raise ValueError(
                            f"Each item in '{section}' must be a dictionary"
                        )

                    if "name" not in item:
                        raise ValueError(f"Each item in '{section}' must have a 'name'")

                    if "type" not in item:
                        raise ValueError(f"Each item in '{section}' must have a 'type'")


class PluginLoader:
    """Loads and instantiates plugins from configuration."""

    @staticmethod
    def load_plugin_class(class_path: str) -> type:
        """
        Load a plugin class from a module path.

        Args:
            class_path: Full module path to the class (e.g., 'module.submodule.ClassName')

        Returns:
            The loaded class
        """
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    @staticmethod
    def load_emitters(config: List[Dict[str, Any]]) -> List[Emitter]:
        """
        Load emitter instances from configuration.

        Args:
            config: List of emitter configurations

        Returns:
            List of instantiated emitters
        """
        emitters = []
        for emitter_config in config:
            plugin_class = PluginLoader.load_plugin_class(emitter_config["type"])
            plugin_config = emitter_config.get("config", {})
            emitter = plugin_class(plugin_config)
            emitters.append(emitter)
        return emitters

    @staticmethod
    def load_transformers(config: List[Dict[str, Any]]) -> List[Transformer]:
        """
        Load transformer instances from configuration.

        Args:
            config: List of transformer configurations

        Returns:
            List of instantiated transformers
        """
        transformers = []
        for transformer_config in config:
            plugin_class = PluginLoader.load_plugin_class(transformer_config["type"])
            plugin_config = transformer_config.get("config", {})
            transformer = plugin_class(plugin_config)
            transformers.append(transformer)
        return transformers

    @staticmethod
    def load_filters(config: List[Dict[str, Any]]) -> List[Filter]:
        """
        Load filter instances from configuration.

        Args:
            config: List of filter configurations

        Returns:
            List of instantiated filters
        """
        filters = []
        for filter_config in config:
            plugin_class = PluginLoader.load_plugin_class(filter_config["type"])
            plugin_config = filter_config.get("config", {})
            filter_instance = plugin_class(plugin_config)
            filters.append(filter_instance)
        return filters
