#!/usr/bin/env python3
"""
AIOS Configuration Validator
Validates prod.yaml for field completeness, path existence, and cron expression validity.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, List, Tuple

def validate_cron_expression(expr: str) -> Tuple[bool, str]:
    """Validate cron expression format."""
    parts = expr.split()
    if len(parts) != 5:
        return False, f"Invalid cron format (expected 5 fields, got {len(parts)})"
    
    # Basic validation for each field
    ranges = [
        (0, 59, "minute"),
        (0, 23, "hour"),
        (1, 31, "day"),
        (1, 12, "month"),
        (0, 6, "weekday")
    ]
    
    for i, (min_val, max_val, name) in enumerate(ranges):
        part = parts[i]
        if part == "*":
            continue
        if part.startswith("*/"):
            try:
                step = int(part[2:])
                if step <= 0:
                    return False, f"Invalid step value in {name}: {step}"
            except ValueError:
                return False, f"Invalid step format in {name}: {part}"
        else:
            try:
                val = int(part)
                if not (min_val <= val <= max_val):
                    return False, f"Value out of range for {name}: {val} (expected {min_val}-{max_val})"
            except ValueError:
                return False, f"Invalid value in {name}: {part}"
    
    return True, "OK"

def validate_paths(config: Dict) -> List[str]:
    """Validate that required paths exist."""
    errors = []
    
    # Check workspace
    workspace = config.get("core", {}).get("workspace")
    if workspace:
        if not Path(workspace).exists():
            errors.append(f"Workspace path does not exist: {workspace}")
    else:
        errors.append("Missing core.workspace")
    
    # Check storage path (parent directory should exist)
    storage_path = config.get("storage", {}).get("path")
    if storage_path:
        parent = Path(storage_path).parent
        if not parent.exists():
            errors.append(f"Storage parent directory does not exist: {parent}")
    else:
        errors.append("Missing storage.path")
    
    # Check backup path
    backup_path = config.get("storage", {}).get("backup", {}).get("path")
    if backup_path:
        if not Path(backup_path).exists():
            errors.append(f"Backup path does not exist: {backup_path}")
    
    return errors

def validate_required_fields(config: Dict) -> List[str]:
    """Validate that all required fields are present."""
    errors = []
    
    required = [
        ("version", str),
        ("environment", str),
        ("core.workspace", str),
        ("core.log_level", str),
        ("models.default", str),
        ("models.api_key_env", str),
        ("agents.max_concurrent", int),
        ("queue.max_pending", int),
        ("self_improving.enabled", bool),
        ("quality_gates.L0.enabled", bool),
        ("monitoring.health_check_interval", int),
        ("storage.backend", str),
        ("storage.path", str),
        ("cron.heartbeat.schedule", str),
        ("cost_control.daily_limit", (int, float)),
    ]
    
    for field_path, expected_type in required:
        parts = field_path.split(".")
        value = config
        try:
            for part in parts:
                value = value[part]
            if not isinstance(value, expected_type):
                errors.append(f"Field {field_path} has wrong type (expected {expected_type.__name__}, got {type(value).__name__})")
        except (KeyError, TypeError):
            errors.append(f"Missing required field: {field_path}")
    
    return errors

def validate_cron_jobs(config: Dict) -> List[str]:
    """Validate all cron job schedules."""
    errors = []
    
    cron_jobs = config.get("cron", {})
    for job_name, job_config in cron_jobs.items():
        if isinstance(job_config, dict) and "schedule" in job_config:
            schedule = job_config["schedule"]
            valid, msg = validate_cron_expression(schedule)
            if not valid:
                errors.append(f"Invalid cron schedule for {job_name}: {msg}")
    
    return errors

def validate_config(config_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate AIOS configuration file.
    Returns: (is_valid, errors, warnings)
    """
    errors = []
    warnings = []
    
    # Load config
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        return False, [f"Failed to load config: {e}"], []
    
    # Run validations
    errors.extend(validate_required_fields(config))
    errors.extend(validate_paths(config))
    errors.extend(validate_cron_jobs(config))
    
    # Warnings (non-critical)
    if config.get("models", {}).get("thinking", {}).get("enabled"):
        warnings.append("Thinking mode is enabled (may increase costs)")
    
    if config.get("self_improving", {}).get("auto_apply"):
        warnings.append("Self-improving auto_apply is enabled (risky in production)")
    
    if config.get("features", {}).get("experimental_agents"):
        warnings.append("Experimental agents are enabled")
    
    is_valid = len(errors) == 0
    return is_valid, errors, warnings

def main():
    config_path = r"C:\Users\A\.openclaw\workspace\aios\config\prod.yaml"
    
    print("=" * 60)
    print("AIOS Configuration Validator")
    print("=" * 60)
    print(f"Config: {config_path}\n")
    
    is_valid, errors, warnings = validate_config(config_path)
    
    if errors:
        print("[X] ERRORS:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print()
    
    if warnings:
        print("[!] WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
        print()
    
    if is_valid:
        print("[OK] Configuration is valid!")
        return 0
    else:
        print(f"[X] Configuration has {len(errors)} error(s)")
        return 1

if __name__ == "__main__":
    exit(main())
