"""
Базовый класс плагина для Expotion.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path

from flask import Flask


class ExpotionPlugin(ABC):
    """
    Базовый абстрактный класс для всех Expotion плагинов.
    
    Атрибуты:
        name: Уникальное имя плагина
        version: Версия плагина
        description: Описание плагина
        author: Автор плагина
        dependencies: Список зависимостей от других плагинов
        default_config: Настройки по умолчанию
    """
    
    name: str = "base-plugin"
    version: str = "0.0.0"
    description: str = "Base plugin"
    author: str = ""
    dependencies: List[str] = []
    default_config: Dict[str, Any] = {}
    
    def __init__(self):
        self._app: Optional[Flask] = None
        self._enabled: bool = True
        self._base_path: Path = Path(__file__).parent
    
    @property
    def app(self) -> Optional[Flask]:
        """Возвращает экземпляр Flask приложения."""
        return self._app
    
    @property
    def enabled(self) -> bool:
        """Возвращает True, если плагин включен."""
        return self._enabled
    
    @property
    def base_path(self) -> Path:
        """Базовый путь плагина для доступа к ресурсам."""
        return self._base_path
    
    @abstractmethod
    def init_app(self, app: Flask) -> None:
        """
        Инициализирует плагин с Flask приложением.
        
        Args:
            app: Экземпляр Flask приложения
        """
        pass
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Настраивает плагин."""
        pass
    
    def on_load(self) -> None:
        """Вызывается при загрузке плагина (до init_app)."""
        pass
    
    def on_unload(self) -> None:
        """Вызывается при выгрузке плагина."""
        pass
    
    def get_menu_items(self) -> List[Dict[str, str]]:
        """Возвращает пункты меню для навигации."""
        return []
    
    def get_admin_views(self) -> List[Any]:
        """Возвращает административные представления."""
        return []
    
    def get_cli_commands(self) -> List[Any]:
        """Возвращает CLI команды для Flask."""
        return []
    
    def healthcheck(self) -> Dict[str, Any]:
        """Проверка состояния плагина."""
        return {"status": "ok", "plugin": self.name, "version": self.version}
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, version={self.version})>"

