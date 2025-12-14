"""
Expotion Core - ядро плагинной системы для Flask.

Пример:
    from flask import Flask
    from expotion_core import PluginLoader, ExpotionPlugin
    
    app = Flask(__name__)
    loader = PluginLoader(app)
    loader.load_all()
"""
from .plugin import ExpotionPlugin
from .loader import PluginLoader

__version__ = "1.0.0"
__all__ = ["ExpotionPlugin", "PluginLoader"]

