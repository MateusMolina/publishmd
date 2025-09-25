"""Test configuration loading and validation."""

import pytest
import yaml
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.config import ConfigLoader, PluginLoader
from publishmd.base import Emitter, Transformer


class MockEmitter(Emitter):
    def emit(self, input_dir, output_dir):
        return []


class MockTransformer(Transformer):
    def transform(self, file_path, emitted_files):
        pass


class TestConfigLoader:
    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_data = {
            "emitters": [
                {
                    "name": "test_emitter",
                    "type": "test.module.TestEmitter",
                    "config": {},
                }
            ],
            "transformers": [
                {
                    "name": "test_transformer",
                    "type": "test.module.TestTransformer",
                    "config": {},
                }
            ],
        }

        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)

            config = ConfigLoader.load_config(config_path)
            assert config == config_data

    def test_load_nonexistent_config(self):
        """Test loading a non-existent configuration file."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_config("nonexistent.yaml")

    def test_validate_valid_config(self):
        """Test validating a valid configuration."""
        config = {"emitters": [{"name": "test", "type": "test.module.Test"}]}

        # Should not raise any exception
        ConfigLoader.validate_config(config)

    def test_validate_empty_config(self):
        """Test validating an empty configuration."""
        with pytest.raises(
            ValueError,
            match="must contain at least one of: emitters, transformers, filters",
        ):
            ConfigLoader.validate_config({})

    def test_validate_invalid_emitters_format(self):
        """Test validating configuration with invalid emitters format."""
        config = {"emitters": "not a list"}

        with pytest.raises(ValueError, match="'emitters' must be a list"):
            ConfigLoader.validate_config(config)

    def test_validate_missing_emitter_name(self):
        """Test validating configuration with missing emitter name."""
        config = {"emitters": [{"type": "test.module.Test"}]}

        with pytest.raises(ValueError, match="must have a 'name'"):
            ConfigLoader.validate_config(config)

    def test_validate_missing_emitter_type(self):
        """Test validating configuration with missing emitter type."""
        config = {"emitters": [{"name": "test"}]}

        with pytest.raises(ValueError, match="must have a 'type'"):
            ConfigLoader.validate_config(config)


class TestPluginLoader:
    def test_load_plugin_class(self):
        """Test loading a plugin class from module path."""
        # Test with built-in class
        cls = PluginLoader.load_plugin_class("pathlib.Path")
        assert cls == Path

    def test_load_plugin_class_invalid(self):
        """Test loading an invalid plugin class."""
        with pytest.raises((ModuleNotFoundError, AttributeError)):
            PluginLoader.load_plugin_class("nonexistent.module.Class")

    def test_load_emitters(self):
        """Test loading emitters from configuration."""
        # Use mock emitter for testing
        config = [
            {
                "name": "mock_emitter",
                "type": "tests.test_config.MockEmitter",
                "config": {"test": "value"},
            }
        ]

        emitters = PluginLoader.load_emitters(config)
        assert len(emitters) == 1
        assert isinstance(emitters[0], MockEmitter)
        assert emitters[0].config == {"test": "value"}

    def test_load_transformers(self):
        """Test loading transformers from configuration."""
        config = [
            {
                "name": "mock_transformer",
                "type": "tests.test_config.MockTransformer",
                "config": {"test": "value"},
            }
        ]

        transformers = PluginLoader.load_transformers(config)
        assert len(transformers) == 1
        assert isinstance(transformers[0], MockTransformer)
        assert transformers[0].config == {"test": "value"}
