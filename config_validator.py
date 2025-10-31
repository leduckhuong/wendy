"""
Configuration validator for Wendy Telegram Data Collection System
Validates config files and provides environment management.
"""

import os
import configparser
from typing import Dict, List, Tuple
from pathlib import Path

class ConfigValidator:
    """Validates configuration files and provides environment management"""

    REQUIRED_SECTIONS = {
        'LOGGING': ['LOG_FILE_RUN', 'LOG_FILE_ERROR'],
        'SESSION': ['SESSION_DIR'],
        'HISTORY': ['HISTORY_DOWNLOADED_FILE'],
        'STORAGE': ['STORAGE_DIR'],
        'DIST': ['DIST_DIR'],
        'EXTRACT': ['EXTRACT_DIR'],
        'WHITELIST': ['WHITELIST_FILE_TYPES'],
        'RULES': ['DATA_RULES'],
        'TELE_API_1': ['APP_ID', 'HASH_ID', 'PHONE', 'USERNAME'],
        'TELE_API_2': ['APP_ID', 'HASH_ID', 'PHONE', 'USERNAME']
    }

    OPTIONAL_SECTIONS = ['ELASTIC_API', 'MONGO_API']

    def __init__(self, config_path: str = 'config.ini'):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_config(self) -> Tuple[bool, List[str], List[str]]:
        """Validate configuration file"""
        try:
            self.config.read(self.config_path)
        except Exception as e:
            self.errors.append(f'Failed to read config file: {e}')
            return False, self.errors, self.warnings

        # Check required sections and keys
        for section, keys in self.REQUIRED_SECTIONS.items():
            if not self.config.has_section(section):
                self.errors.append(f'Missing required section: [{section}]')
                continue

            for key in keys:
                if not self.config.has_option(section, key):
                    self.errors.append(f'Missing required key: [{section}]{key}')
                elif not self.config.get(section, key).strip():
                    self.errors.append(f'Empty value for: [{section}]{key}')

        # Validate paths
        self._validate_paths()

        # Validate API credentials
        self._validate_api_credentials()

        # Validate file extensions
        self._validate_file_extensions()

        # Check rules file
        self._validate_rules_file()

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_paths(self):
        """Validate directory and file paths"""
        paths_to_check = [
            ('SESSION', 'SESSION_DIR'),
            ('STORAGE', 'STORAGE_DIR'),
            ('DIST', 'DIST_DIR'),
            ('EXTRACT', 'EXTRACT_DIR'),
            ('HISTORY', 'HISTORY_DOWNLOADED_FILE'),
            ('LOGGING', 'LOG_FILE_RUN'),
            ('LOGGING', 'LOG_FILE_ERROR')
        ]

        for section, key in paths_to_check:
            if self.config.has_option(section, key):
                path = self.config.get(section, key)
                if not path.startswith('../') and not path.startswith('./'):
                    # Create directories if they don't exist
                    try:
                        Path(path).mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        self.warnings.append(f'Cannot create directory {path}: {e}')

    def _validate_api_credentials(self):
        """Validate Telegram API credentials"""
        for api_section in ['TELE_API_1', 'TELE_API_2']:
            if self.config.has_section(api_section):
                app_id = self.config.get(api_section, 'APP_ID', fallback='')
                hash_id = self.config.get(api_section, 'HASH_ID', fallback='')
                phone = self.config.get(api_section, 'PHONE', fallback='')

                # Basic validation
                if not app_id.isdigit():
                    self.errors.append(f'Invalid APP_ID in [{api_section}]: must be numeric')

                if len(hash_id) != 32:
                    self.errors.append(f'Invalid HASH_ID in [{api_section}]: must be 32 characters')

                if not phone.startswith('+'):
                    self.warnings.append(f'Phone number in [{api_section}] should start with +')

    def _validate_file_extensions(self):
        """Validate file extension whitelist"""
        if self.config.has_option('WHITELIST', 'WHITELIST_FILE_TYPES'):
            extensions = self.config.get('WHITELIST', 'WHITELIST_FILE_TYPES')
            if not extensions.strip():
                self.warnings.append('WHITELIST_FILE_TYPES is empty - no files will be processed')
            else:
                # Should be a Python list-like string
                if not extensions.startswith('[') or not extensions.endswith(']'):
                    self.errors.append('WHITELIST_FILE_TYPES must be a Python list format: ["ext1","ext2"]')

    def _validate_rules_file(self):
        """Validate rules configuration file"""
        if self.config.has_option('RULES', 'DATA_RULES'):
            rules_path = self.config.get('RULES', 'DATA_RULES')
            if not os.path.exists(rules_path):
                self.errors.append(f'Rules file not found: {rules_path}')
            else:
                try:
                    import yaml
                    with open(rules_path, 'r') as f:
                        rules = yaml.safe_load(f)
                    if 'line_rules' not in rules:
                        self.errors.append(f'Rules file missing "line_rules" key: {rules_path}')
                except Exception as e:
                    self.errors.append(f'Invalid rules file {rules_path}: {e}')

    def create_default_config(self, output_path: str = 'config.ini.default'):
        """Create a default configuration file"""
        default_config = configparser.ConfigParser()

        # Add all sections with default values
        default_config.add_section('LOGGING')
        default_config.set('LOGGING', 'LOG_FILE_RUN', './logs/run.log')
        default_config.set('LOGGING', 'LOG_FILE_ERROR', './logs/error.log')

        default_config.add_section('SESSION')
        default_config.set('SESSION', 'SESSION_DIR', './sessions')

        default_config.add_section('HISTORY')
        default_config.set('HISTORY', 'HISTORY_DOWNLOADED_FILE', './history_downloaded.txt')

        default_config.add_section('STORAGE')
        default_config.set('STORAGE', 'STORAGE_DIR', '../storage')

        default_config.add_section('DIST')
        default_config.set('DIST', 'DIST_DIR', '../dist')

        default_config.add_section('EXTRACT')
        default_config.set('EXTRACT', 'EXTRACT_DIR', '../extract')

        default_config.add_section('WHITELIST')
        default_config.set('WHITELIST', 'WHITELIST_FILE_TYPES', '[".zip",".rar",".tar",".gz",".7z",".xlsx",".csv",".txt"]')

        default_config.add_section('RULES')
        default_config.set('RULES', 'DATA_RULES', '../rules/rules.yaml')

        default_config.add_section('TELE_API_1')
        default_config.set('TELE_API_1', 'APP_ID', 'YOUR_APP_ID_1')
        default_config.set('TELE_API_1', 'HASH_ID', 'YOUR_API_HASH_1')
        default_config.set('TELE_API_1', 'PHONE', '+1234567890')
        default_config.set('TELE_API_1', 'USERNAME', '@your_bot_username_1')

        default_config.add_section('TELE_API_2')
        default_config.set('TELE_API_2', 'APP_ID', 'YOUR_APP_ID_2')
        default_config.set('TELE_API_2', 'HASH_ID', 'YOUR_API_HASH_2')
        default_config.set('TELE_API_2', 'PHONE', '+0987654321')
        default_config.set('TELE_API_2', 'USERNAME', '@your_bot_username_2')

        try:
            with open(output_path, 'w') as f:
                f.write('; ########### DEFAULT CONFIGURATION\n')
                f.write('; Copy this file to config.ini and update with your values\n\n')
                default_config.write(f)
            print(f'Default config created: {output_path}')
        except Exception as e:
            print(f'Failed to create default config: {e}')

def main():
    """CLI interface for config validation"""
    import sys

    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = 'config.ini'

    validator = ConfigValidator(config_path)
    is_valid, errors, warnings = validator.validate_config()

    if errors:
        print('❌ Configuration Errors:')
        for error in errors:
            print(f'  - {error}')

    if warnings:
        print('⚠️  Configuration Warnings:')
        for warning in warnings:
            print(f'  - {warning}')

    if is_valid:
        print('✅ Configuration is valid')
        return 0
    else:
        print('❌ Configuration is invalid')
        return 1

if __name__ == '__main__':
    exit(main())
