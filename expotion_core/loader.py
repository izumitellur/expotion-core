"""
Загрузчик плагинов для Expotion.

Поддерживает загрузку плагинов через:
1. Entry points (pip пакеты)
2. Локальные папки (для разработки)
"""
import importlib
import importlib.metadata
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Type

from flask import Flask

from .plugin import ExpotionPlugin

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "expotion.plugins"


class PluginLoader:
    """Загрузчик и менеджер плагинов для Flask приложения."""
    
    def __init__(
        self,
        app: Optional[Flask] = None,
        plugins_dir: Optional[Path] = None
    ):
        self._app = app
        self._plugins: Dict[str, ExpotionPlugin] = {}
        self._plugins_dir = plugins_dir
        self._disabled_plugins: List[str] = []
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """Инициализирует загрузчик с Flask приложением."""
        self._app = app
        
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['expotion_loader'] = self
        
        self._disabled_plugins = app.config.get('DISABLED_PLUGINS', [])
        
        if self._plugins_dir is None:
            self._plugins_dir = app.config.get('PLUGINS_DIR')
        
        @app.context_processor
        def inject_plugins():
            return {
                'expotion_plugins': self.get_all_plugins(),
                'expotion_menu_items': self.get_all_menu_items()
            }
    
    @property
    def plugins(self) -> Dict[str, ExpotionPlugin]:
        """Возвращает словарь всех загруженных плагинов."""
        return self._plugins.copy()
    
    def load_all(self) -> None:
        """Загружает все плагины."""
        logger.info("🔌 Expotion: Загрузка плагинов...")
        
        self._load_from_entry_points()
        
        if self._plugins_dir:
            self._load_from_directory()
        
        self._init_all_plugins()
        
        logger.info(f"✅ Expotion: Загружено плагинов: {len(self._plugins)}")
    
    def _load_from_entry_points(self) -> None:
        """Загружает плагины из entry points."""
        try:
            entry_points = importlib.metadata.entry_points()
            
            if hasattr(entry_points, 'select'):
                eps = entry_points.select(group=ENTRY_POINT_GROUP)
            else:
                eps = entry_points.get(ENTRY_POINT_GROUP, [])
            
            for ep in eps:
                try:
                    plugin_class = ep.load()
                    self._register_plugin_class(plugin_class, source=f"pip:{ep.name}")
                except Exception as e:
                    logger.error(f"❌ Ошибка загрузки плагина {ep.name}: {e}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить entry points: {e}")
    
    def _load_from_directory(self) -> None:
        """Загружает плагины из локальной директории."""
        if not self._plugins_dir or not Path(self._plugins_dir).exists():
            return
        
        plugins_path = Path(self._plugins_dir)
        
        for plugin_path in plugins_path.iterdir():
            if not plugin_path.is_dir():
                continue
            if plugin_path.name.startswith('_') or plugin_path.name.startswith('.'):
                continue
            
            plugin_module = plugin_path / "plugin.py"
            if not plugin_module.exists():
                plugin_module = plugin_path / "__init__.py"
            
            if not plugin_module.exists():
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{plugin_path.name}",
                    plugin_module
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) 
                            and issubclass(attr, ExpotionPlugin) 
                            and attr is not ExpotionPlugin):
                            self._register_plugin_class(
                                attr, 
                                source=f"local:{plugin_path.name}"
                            )
                            break
                            
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки плагина {plugin_path.name}: {e}")
    
    def _register_plugin_class(
        self, 
        plugin_class: Type[ExpotionPlugin],
        source: str = "unknown"
    ) -> None:
        """Регистрирует класс плагина."""
        try:
            plugin = plugin_class()
            
            if plugin.name in self._disabled_plugins:
                logger.info(f"⏸️ Плагин {plugin.name} отключен")
                return
            
            if plugin.name in self._plugins:
                logger.warning(f"⚠️ Плагин {plugin.name} уже загружен")
                return
            
            plugin.on_load()
            self._plugins[plugin.name] = plugin
            logger.info(f"📦 Загружен: {plugin.name} v{plugin.version} [{source}]")
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания плагина: {e}")
    
    def _init_all_plugins(self) -> None:
        """Инициализирует все загруженные плагины."""
        if not self._app:
            return
        
        sorted_plugins = self._sort_by_dependencies()
        
        for plugin in sorted_plugins:
            try:
                plugin._app = self._app
                plugin.init_app(self._app)
                logger.info(f"✅ Инициализирован: {plugin.name}")
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации {plugin.name}: {e}")
                plugin._enabled = False
    
    def _sort_by_dependencies(self) -> List[ExpotionPlugin]:
        """Сортирует плагины по зависимостям."""
        result = []
        visited = set()
        
        def visit(name: str):
            if name in visited:
                return
            visited.add(name)
            
            plugin = self._plugins.get(name)
            if plugin:
                for dep in plugin.dependencies:
                    if dep in self._plugins:
                        visit(dep)
                result.append(plugin)
        
        for name in self._plugins:
            visit(name)
        
        return result
    
    def get_plugin(self, name: str) -> Optional[ExpotionPlugin]:
        """Возвращает плагин по имени."""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> List[ExpotionPlugin]:
        """Возвращает список всех активных плагинов."""
        return [p for p in self._plugins.values() if p.enabled]
    
    def get_all_menu_items(self) -> List[Dict[str, str]]:
        """Собирает пункты меню со всех плагинов."""
        items = []
        for plugin in self.get_all_plugins():
            items.extend(plugin.get_menu_items())
        return items
    
    def healthcheck(self) -> Dict[str, Any]:
        """Проверка состояния всех плагинов."""
        results = {}
        for name, plugin in self._plugins.items():
            try:
                results[name] = plugin.healthcheck()
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
        return results
    
    def unload_plugin(self, name: str) -> bool:
        """Выгружает плагин по имени."""
        plugin = self._plugins.get(name)
        if plugin:
            try:
                plugin.on_unload()
                plugin._enabled = False
                del self._plugins[name]
                logger.info(f"🔌 Плагин {name} выгружен")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка выгрузки {name}: {e}")
        return False

