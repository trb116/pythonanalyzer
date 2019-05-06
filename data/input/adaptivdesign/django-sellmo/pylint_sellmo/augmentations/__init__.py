from pylint.checkers.base import BasicErrorChecker
from pylint_plugin_utils import suppress_message

from astroid import scoped_nodes


def is_load_function(node):
    if node.decorators is not None:
        return any(
            decorator.func.name == 'load'
            for decorator in node.decorators.nodes
            if isinstance(decorator, scoped_nodes.CallFunc)
                and hasattr(decorator.func, 'name'))
    return False


def apply_augmentations(linter):
    suppress_message(linter, BasicErrorChecker.visit_function, 'E0102', is_load_function)
