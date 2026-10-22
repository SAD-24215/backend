import importlib
import pkgutil
from fastapi import FastAPI


def auto_register_routers(app: FastAPI):
    for _, feature_name, is_pkg in pkgutil.iter_modules(__path__):
        if is_pkg:
            try:
                module = importlib.import_module(f"{__name__}.{feature_name}.route")
            except ModuleNotFoundError:
                continue

            if hasattr(module, "router"):
                app.include_router(module.router)