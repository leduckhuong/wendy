#!/usr/bin/env python3
"""
Configuration validation script for Wendy system
Run this before starting services to ensure configuration is valid.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_validator import ConfigValidator

def main():
    """Validate configuration and exit with appropriate code"""
    print("🔍 Validating Wendy configuration...")

    # Check if config files exist
    config_files = [
        'listener/config.ini',
        'reader/config.ini'
    ]

    for config_file in config_files:
        if not os.path.exists(config_file):
            print(f"❌ Configuration file not found: {config_file}")
            print("   Please copy config.ini.default to config.ini and update with your values")
            return 1

    # Validate listener config
    print("\n📡 Validating listener configuration...")
    listener_validator = ConfigValidator('listener/config.ini')
    is_valid, errors, warnings = listener_validator.validate_config()

    if errors:
        print("❌ Listener configuration errors:")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("⚠️  Listener configuration warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if not is_valid:
        return 1

    # Validate reader config
    print("\n📖 Validating reader configuration...")
    reader_validator = ConfigValidator('reader/config.ini')
    is_valid, errors, warnings = reader_validator.validate_config()

    if errors:
        print("❌ Reader configuration errors:")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("⚠️  Reader configuration warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if not is_valid:
        return 1

    print("\n✅ All configurations are valid!")
    print("🚀 You can now start the services safely.")
    return 0

if __name__ == '__main__':
    exit(main())
