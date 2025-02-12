import pytest
from unittest.mock import patch, Mock
import requests
from crewai.cli.provider import fetch_provider_data, get_provider_data
from crewai.cli.constants import JSON_URL, PROVIDERS, MODELS

def test_fetch_provider_data_timeout():
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout
        result = fetch_provider_data('/tmp/cache.json')
        assert result is None

def test_fetch_provider_data_wrong_content_type():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.headers = {'content-type': 'text/plain'}
        mock_get.return_value = mock_response
        result = fetch_provider_data('/tmp/cache.json')
        assert result is None

def test_get_provider_data_fallback():
    with patch('crewai.cli.provider.load_provider_data') as mock_load:
        mock_load.return_value = None
        result = get_provider_data()
        assert result is not None
        assert all(provider.lower() in result for provider in PROVIDERS)
        # Verify that each provider has its models from MODELS
        for provider in PROVIDERS:
            assert result[provider.lower()] == MODELS.get(provider.lower(), [])
