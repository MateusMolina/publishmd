"""Test configuration loading and validation."""

import pytest
import yaml
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.config import ConfigLoader, PluginLoader
from publishmd.base import Transformer, Filter


class MockTransformer(Transformer):
    def transform(self, file_path, copied_files):
        pass


class MockFilter(Filter):
    def filter(self, files):
        return files


class TestConfigLoader:
    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_data = {
            "transformers": [
                {"name": "test_transformer", "type": "test.module.TestTransformer", "config": {}}
            ],
        }
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)
            config = ConfigLoader.load_config(config_path)
            assert config == config_data

    def test_load_nonexistent_config(self):
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_config("nonexistent.yaml")

    def test_validate_valid_transformer_config(self):
        config = {"transformers": [{"name": "test", "type": "test.module.Test"}]}
        ConfigLoader.validate_config(config)

    def test_validate_valid_filter_config(self):
        config = {"filters": [{"name": "test", "type": "test.module.Test"}]}
        ConfigLoader.validate_config(config)

    def test_validate_empty_config(self):
        with pytest.raises(ValueError, match="must contain at least one of: transformers, filters"):
            ConfigLoader.validate_config({})

    def test_validate_invalid_transformers_format(self):
        config = {"transformers": "not a list"}
        with pytest.raises(ValueError, match="'transformers' must be a list"):
            ConfigLoader.validate_config(config)

    def test_validate_missing_transformer_name(self):
        config = {"transformers": [{"type": "test.module.Test"}]}
        with pytest.raises(ValueError, match="must have a 'name'"):
            ConfigLoader.validate_config(config)

    def test_validate_missing_transformer_type(self):
        config = {"transformers": [{"name": "test"}]}
        with pytest.raises(ValueError, match="must have a 'type'"):
            ConfigLoader.validate_config(config)


class TestPluginLoader:
    def test_load_plugin_class(self):
        cls = PluginLoader.load_plugin_class("pathlib.Path")
        assert cls == Path

    def test_load_plugin_class_invalid(self):
        with pytest.raises((ModuleNotFoundError, AttributeError)):
            PluginLoader.load_plugin_class("nonexistent.module.Class")

    def test_load_transformers(self):
        config = [{"name": "mock_transformer", "type": "tests.test_config.MockTransformer", "config": {"test": "value"}}]
        transformers = PluginLoader.load_transformers(config)
        assert len(transformers) == 1
        assert isinstance(transformers[0], MockTransformer)
        assert transformers[0].config == {"test": "value"}

    def test_load_filters(self):
        config = [{"name": "mock_filter", "type": "tests.test_config.MockFilter", "config": {}}]
        filters = PluginLoader.load_filters(config)
        assert len(filters) == 1
        assert isinstance(filters[0], MockFilter)
