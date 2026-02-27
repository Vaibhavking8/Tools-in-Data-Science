import os
import ast
import importlib
import inspect
import typing

SCRIPTS_DIR = "scripts"

# override map for common factory functions -> return type
RETURN_TYPE_OVERRIDES = {
    ("pandas", "DataFrame"): lambda: importlib.import_module("pandas").DataFrame,
    ("pandas", "read_csv"): lambda: importlib.import_module("pandas").DataFrame,
    ("pandas", "read_excel"): lambda: importlib.import_module("pandas").DataFrame,
    ("requests", "get"): lambda: importlib.import_module("requests.models").Response,
    ("requests", "post"): lambda: importlib.import_module("requests.models").Response,
    ("json", "loads"): lambda: dict,
    ("json", "load"): lambda: dict,
    ("json", "dumps"): lambda: str,
    ("json", "dump"): lambda: type(None),
}


def infer_type(node, imports, var_types):
    """Try to infer a runtime object/type for an AST node."""
    # name references
    if isinstance(node, ast.Name):
        if node.id in var_types:
            return var_types[node.id]
        if node.id in imports:
            try:
                return importlib.import_module(imports[node.id])
            except ImportError:
                return None
        return None

    # attribute chain: resolve step by step
    if isinstance(node, ast.Attribute):
        base = infer_type(node.value, imports, var_types)
        if base is None:
            return None
        try:
            return getattr(base, node.attr)
        except Exception:
            return None

    # subscript expressions propagate the container type
    if isinstance(node, ast.Subscript):
        return infer_type(node.value, imports, var_types)

    # binary operations: assume result has same type as left operand when known
    if isinstance(node, ast.BinOp):
        left_type = infer_type(node.left, imports, var_types)
        if left_type is not None:
            return left_type
        return infer_type(node.right, imports, var_types)

    # function call: try to get return type override or class
    if isinstance(node, ast.Call):
        # builtin open returns concrete file object type (TextIOWrapper etc)
        if isinstance(node.func, ast.Name) and node.func.id == 'open':
            try:
                # create a temporary file object to inspect its type without writing
                import tempfile
                f = open(tempfile.gettempdir()+"/temp.txt", 'w')
                t = type(f)
                f.close()
                return t
            except Exception:
                import io
                return getattr(io, 'TextIOWrapper', None)
        # handle dict.get with literal default separately
        if isinstance(node.func, ast.Attribute):
            base = infer_type(node.func.value, imports, var_types)
            if base is dict and node.func.attr == 'get':
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Dict):
                    return dict
        func_obj = infer_type(node.func, imports, var_types)
        # if we have override mapping
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            module_alias = node.func.value.id
            func_name = node.func.attr
            if module_alias in imports:
                key = (imports[module_alias], func_name)
                if key in RETURN_TYPE_OVERRIDES:
                    try:
                        return RETURN_TYPE_OVERRIDES[key]()
                    except Exception:
                        pass
        # if func_obj is a class, calling it returns instance -> return class
        if inspect.isclass(func_obj):
            return func_obj
        # handle common pandas methods by propagating DataFrame type
        try:
            import pandas as _pd
            df_type = _pd.DataFrame
            ser_type = _pd.Series
        except Exception:
            df_type = None
            ser_type = None
        if isinstance(node.func, ast.Attribute) and df_type is not None:
            base = infer_type(node.func.value, imports, var_types)
            if base is df_type or base is ser_type or (inspect.isclass(base) and df_type is not None and issubclass(base, df_type)):
                return df_type
        # special case: built-in method bound to a class (e.g. datetime.strptime)
        if hasattr(func_obj, "__self__") and isinstance(func_obj.__self__, type):
            return func_obj.__self__
        # if function has return type hint
        try:
            hints = typing.get_type_hints(func_obj)
            ret = hints.get('return')
            if isinstance(ret, type):
                return ret
        except Exception:
            pass
        return None

    return None


class ValidityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = {}
        self.var_types = {}
        self.invalid = False
        self.reason = None

    def visit_Import(self, node):
        for alias in node.names:
            self.imports[alias.asname or alias.name] = alias.name

    def visit_ImportFrom(self, node):
        module = node.module
        for alias in node.names:
            name = alias.asname or alias.name
            # bind imported name to the actual object (module or attribute)
            try:
                mod = importlib.import_module(module)
                attr = getattr(mod, alias.name)
                self.var_types[name] = attr
            except Exception:
                # ignore failures, still record mapping to module name
                self.imports[name] = module
            else:
                # store object directly so infer_type can pick it up
                self.var_types[name] = attr

    def visit_Assign(self, node):
        # only simple name targets
        for target in node.targets:
            if isinstance(target, ast.Name):
                inferred = infer_type(node.value, self.imports, self.var_types)
                if inferred is not None:
                    # store type or object
                    if inspect.isclass(inferred) or inspect.ismodule(inferred) or isinstance(inferred, type):
                        self.var_types[target.id] = inferred
                    else:
                        # if it's an instance, record its type
                        self.var_types[target.id] = type(inferred)
        self.generic_visit(node)

    def visit_Call(self, node):
        # check the call's function attribute validity
        # check for simple function call names first
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            # if not a builtin, not imported, and not a variable we know, it's invalid
            try:
                import builtins as _builtins
                is_builtin = func_name in dir(_builtins)
            except Exception:
                is_builtin = False
            if func_name not in self.imports and func_name not in self.var_types and not is_builtin:
                self.invalid = True
                self.reason = f"call to unknown function or class '{func_name}'"
        if isinstance(node.func, ast.Attribute):
            base_obj = infer_type(node.func.value, self.imports, self.var_types)
            if base_obj is not None:
                if not hasattr(base_obj, node.func.attr):
                    self.invalid = True
                    self.reason = f"object of type {base_obj} has no attribute '{node.func.attr}'"
            else:
                # base unknown; try basic module-level resolve if it's a Name
                if isinstance(node.func.value, ast.Name) and node.func.value.id in self.imports:
                    module_name = self.imports[node.func.value.id]
                    try:
                        module = importlib.import_module(module_name)
                        if not hasattr(module, node.func.attr):
                            self.invalid = True
                            self.reason = f"module '{module_name}' has no attribute '{node.func.attr}'"
                    except Exception:
                        pass
                # otherwise we can't determine, leave as is
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # catch plain attribute access (e.g. response.status_code)
        base_obj = infer_type(node.value, self.imports, self.var_types)
        if base_obj is not None:
            if not hasattr(base_obj, node.attr):
                self.invalid = True
                self.reason = f"object of type {base_obj} has no attribute '{node.attr}'"
        # unknown base: can't verify
        self.generic_visit(node)

    def visit_With(self, node):
        # infer types for variables bound by context managers
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                inferred = infer_type(item.context_expr, self.imports, self.var_types)
                if inferred is not None:
                    self.var_types[item.optional_vars.id] = inferred
        self.generic_visit(node)


def script_is_valid(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    visitor = ValidityVisitor()
    visitor.visit(tree)
    return not visitor.invalid


def check_script(filepath):
    """Return (valid, reason)"""
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    try:
        tree = ast.parse(code)
    except SyntaxError as se:
        return False, f"syntax error: {se}"
    visitor = ValidityVisitor()
    visitor.visit(tree)
    return (not visitor.invalid, visitor.reason)


if __name__ == "__main__":
    for filename in os.listdir(SCRIPTS_DIR):
        path = os.path.join(SCRIPTS_DIR, filename)

        if script_is_valid(path):
            print(f"✅ Found the real script: {filename}")
            # stop after first valid file
            break
