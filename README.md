# Expotion Core

Ядро плагинной системы для Flask приложений.

## Установка

```bash
pip install expotion-core

# или из GitHub
pip install git+https://github.com/your-username/expotion-core.git
```

## Использование

```python
from flask import Flask
from expotion_core import PluginLoader

app = Flask(__name__)

loader = PluginLoader(app)
loader.load_all()  # Автоматически найдёт все expotion-* плагины

if __name__ == "__main__":
    app.run()
```

## Создание плагина

```python
from expotion_core import ExpotionPlugin
from flask import Blueprint

class MyPlugin(ExpotionPlugin):
    name = "my-plugin"
    version = "1.0.0"
    
    def init_app(self, app):
        bp = Blueprint('my_plugin', __name__, url_prefix='/my')
        app.register_blueprint(bp)
```

## pyproject.toml плагина

```toml
[project.entry-points."expotion.plugins"]
my-plugin = "expotion_my_plugin:MyPlugin"
```

