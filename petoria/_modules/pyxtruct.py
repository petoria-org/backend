import ast


def get_type(annotation):
    if annotation is None:
        return "Any"
    return ast.unparse(annotation)  # Python 3.9+


def build_tree(node, indent=0):
    stree = ""  # str of the tree (output)

    prefix = " " * indent

    # ----- FUNCTIONS -----
    if isinstance(node, ast.FunctionDef):
        args = []
        for arg in node.args.args:
            arg_type = get_type(arg.annotation)
            args.append(f"{arg.arg}: {arg_type}")

        ret_type = get_type(node.returns)
        stree += f"{prefix}Function: {node.name}({', '.join(args)}) -> {ret_type}\n"

    # ----- CLASSES -----
    elif isinstance(node, ast.ClassDef):
        bases = [ast.unparse(base) for base in node.bases] or ["object"]
        bases_str = ", ".join(bases)
        stree += f"{prefix}Class: {node.name}({bases_str})\n"

        # Class variables
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                var_name = item.target.id  # pylance catches some error but the code works
                var_type = get_type(item.annotation)
                stree += f"{prefix}  Class Var: {var_name}: {var_type}\n"

            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        stree += f"{prefix}  Class Var: {target.id}: Any\n"

    # ----- WALK CHILDREN -----
    for child in ast.iter_child_nodes(node):
        stree += build_tree(child, indent + 1)
    return stree


def file_tree(path):
    with open(path, 'r') as file:
        tree = ast.parse(file.read())
    return build_tree(tree)


if __name__ == '__main__':
    import sys
    path = sys.argv[1]
    with open(path, "r") as f:
        tree = ast.parse(f.read())
    print(path)
    print(build_tree(tree))
