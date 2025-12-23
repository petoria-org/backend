import ast


def get_type(annotation):
    if annotation is None:
        return "Any"
    return ast.unparse(annotation)  # Python 3.9+


def print_tree(node, indent=0):
    prefix = " " * indent

    # ----- FUNCTIONS -----
    if isinstance(node, ast.FunctionDef):
        args = []
        for arg in node.args.args:
            arg_type = get_type(arg.annotation)
            args.append(f"{arg.arg}: {arg_type}")

        ret_type = get_type(node.returns)
        print(f"{prefix}Function: {node.name}({', '.join(args)}) -> {ret_type}")

    # ----- CLASSES -----
    elif isinstance(node, ast.ClassDef):
        bases = [ast.unparse(base) for base in node.bases] or ["object"]
        bases_str = ", ".join(bases)
        print(f"{prefix}Class: {node.name}({bases_str})")

        # Class variables
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                var_name = item.target.id
                var_type = get_type(item.annotation)
                print(f"{prefix}  Class Var: {var_name}: {var_type}")

            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        print(f"{prefix}  Class Var: {target.id}: Any")

    # ----- WALK CHILDREN -----
    for child in ast.iter_child_nodes(node):
        print_tree(child, indent + 1)


path = input("Path: ")
with open(path, "r") as f:
    tree = ast.parse(f.read())
print(path)
print_tree(tree)
