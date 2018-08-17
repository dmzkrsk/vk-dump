from functools import reduce
from importlib import import_module
from operator import or_
import logging


logger = logging.getLogger()


class ModuleCache:
    def __init__(self, modules):
        loaded_modules = set()

        for module in modules:
            logger.info('Loading plugin %s', module)
            loaded_modules.add(import_module(f'modules.{module}'))

        self.modules = loaded_modules
        self.scope = reduce(or_, (m.SCOPE for m in loaded_modules), 0)

    def __bool__(self):
        return bool(self.modules)

    def __iter__(self):
        return iter(self.modules)
