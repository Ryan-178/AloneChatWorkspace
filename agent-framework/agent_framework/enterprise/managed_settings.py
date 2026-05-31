"""
Managed settings that load from macOS plist, Windows Registry, or YAML file
Enterprise policies can be deployed through system configuration
"""
from __future__ import annotations
import os
import platform
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


_MANAGED_SETTINGS_CACHE: Dict[str, Any] = {}


def _get_platform() -> str:
    return platform.system().lower()


class ManagedSettings:
    """
    Loads managed settings from platform-specific sources:
    - macOS: /Library/Preferences/, ~/Library/Preferences/ plist files
    - Windows: HKLM\\Software\\, HKCU\\Software\\ Registry keys
    - Fallback: YAML/JSON file in /etc/alonechat/ or ~/.alonechat/
    """

    PREFERENCES_DOMAIN = "com.alonechat"

    def __init__(self, domain: Optional[str] = None):
        if domain:
            self.domain = domain
        else:
            self.domain = self.PREFERENCES_DOMAIN
        self.platform = _get_platform()
        self._settings: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.platform == "darwin":
            self._load_macos_plist()
        elif self.platform == "windows":
            self._load_windows_registry()
        self._load_fallback_file()

    def _load_macos_plist(self):
        try:
            import subprocess
            plist_paths = [
                Path(f"/Library/Preferences/{self.domain}.plist"),
                Path(Path.home(), f"Library/Preferences/{self.domain}.plist"),
            ]
            for plist_path in plist_paths:
                if plist_path.exists():
                    result = subprocess.run(
                        ["plutil", "-p", str(plist_path)],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        import plistlib
                        with open(plist_path, "rb") as f:
                            data = plistlib.load(f)
                            if isinstance(data, dict):
                                self._settings.update(data)
            result = subprocess.run(
                ["defaults", "read", self.domain],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "=" in line:
                        parts = line.split("=", 1)
                        key = parts[0].strip().strip(";").strip()
                        val = parts[1].strip().strip(";").strip()
                        if key:
                            self._settings[key] = val
        except Exception:
            pass

    def _load_windows_registry(self):
        try:
            import winreg
            hklm_path = f"Software\\{self.domain}"
            hkcu_path = f"Software\\{self.domain}"

            for root, subkey in [(winreg.HKEY_LOCAL_MACHINE, hklm_path),
                                 (winreg.HKEY_CURRENT_USER, hkcu_path)]:
                try:
                    with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ) as key:
                        i = 0
                        while True:
                            try:
                                name, value, _ = winreg.EnumValue(key, i)
                                if isinstance(value, str):
                                    self._settings[name] = value
                                elif isinstance(value, int):
                                    self._settings[name] = value
                                elif isinstance(value, bytes):
                                    self._settings[name] = value.decode("utf-8", errors="replace")
                                i += 1
                            except OSError:
                                break
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
        except ImportError:
            pass
        except Exception:
            pass

    def _load_fallback_file(self):
        fallback_paths = [
            Path(f"/etc/{self.domain}/managed.json"),
            Path(f"/etc/{self.domain}/managed.yaml"),
            Path(Path.home(), f".{self.domain}", "managed.json"),
            Path(Path.home(), f".{self.domain}", "managed.yaml"),
        ]

        for fpath in fallback_paths:
            if fpath.exists():
                try:
                    if fpath.suffix == ".json":
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                self._settings.update(data)
                    elif fpath.suffix in (".yaml", ".yml"):
                        import yaml
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f) or {}
                            if isinstance(data, dict):
                                self._settings.update(data)
                except Exception:
                    pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        return dict(self._settings)

    def __contains__(self, key: str) -> bool:
        return key in self._settings

    def __getitem__(self, key: str) -> Any:
        return self._settings[key]

    def __repr__(self) -> str:
        return f"ManagedSettings(domain={self.domain}, platform={self.platform}, keys={len(self._settings)})"
