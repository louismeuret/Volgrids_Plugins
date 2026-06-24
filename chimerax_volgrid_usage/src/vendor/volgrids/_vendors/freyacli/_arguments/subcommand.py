import volgrids._vendors.freyacli as fy

# //////////////////////////////////////////////////////////////////////////////
class Subcommand:
    def __init__(self, name: str, parent: "Subcommand|None"):
        self.name = name
        self.parent: "Subcommand|None" = parent
        self.children: dict[str, "Subcommand"] = {}
        self.depth = 0 if self.is_root() else parent.depth + 1
        self.help_str: fy.HelpStr = fy.HelpStr()

        self.rules: dict[str, fy.ArgumentRule] = {}
        self.rules_posit: list[fy.ArgumentRule] = []
        self.rules_flags: list[fy.ArgumentRule] = []

        self._children_names: list[str] = [] # children names sorted in order of definition


    # --------------------------------------------------------------------------
    def __repr__(self):
        values = ','.join('' if v is None else str(v) for v in self.iter_sorted_children())
        return f"Subcommand({self.depth}:{self.name}){{{values if values else ''}}}"


    # --------------------------------------------------------------------------
    def __getitem__(self, name: str) -> "Subcommand":
        return self.get_child(name)


    # --------------------------------------------------------------------------
    def add_child(self, name: str) -> "Subcommand":
        self._assert_unique_child(name)
        child = Subcommand(name, self)
        self.children[name] = child
        self._children_names.append(name)
        return child


    # --------------------------------------------------------------------------
    def get_child(self, name: str) -> "Subcommand":
        if name not in self.children:
            raise fy.FreyaSyntaxError(f"Branch '{name}' is not defined in the CLI rules.")
        return self.children[name]


    # --------------------------------------------------------------------------
    def add_rule(self, rule: fy.ArgumentRule):
        if rule.name in self.rules:
            raise fy.FreyaSyntaxError(f"Duplicate definition of '{rule}'.")

        self.rules[rule.name] = rule
        lst = self.rules_posit if rule.is_positional else self.rules_flags
        lst.append(rule)


    # --------------------------------------------------------------------------
    def is_root(self) -> bool: return self.parent is None
    def is_leaf(self) -> bool: return not self.children


    # --------------------------------------------------------------------------
    def iter_sorted_children(self):
        return (self.children[name] for name in self._children_names)


    # --------------------------------------------------------------------------
    def get_args_with_flag(self, flag: str, short_name: bool) -> list[fy.ArgumentRule]:
        """List of rules returned is ensured to contain between 0 and 1 elements."""
        matches = list(filter(
            lambda rule: flag == rule.flag_short if short_name else flag == rule.flag_long,
            self.rules_flags
        ))
        if len(matches) > 1:
            raise fy.FreyaSyntaxError(f"Multiple rules with the same flag: '{flag}'.")
        return matches


    # --------------------------------------------------------------------------
    def get_path_to_root(self) -> list[str]:
        path = []
        node = self
        while node:
            if node.parent is None: break
            path.append(node.name)
            node = node.parent
        return path[::-1]


    # --------------------------------------------------------------------------
    def str_help_long(self, py_name: str) -> str:
        return '\n'.join((
            self._get_usage_str(py_name),
            self.help_str.nl_surround(),
            self._get_str_leaf_arguments() if self.is_leaf() \
                else self._get_str_subcommands(),
        ))


    # --------------------------------------------------------------------------
    def _get_usage_str(self, py_name: str) -> str:
        path_to_root = [py_name] + self.get_path_to_root()
        preffix = "    " + ' '.join(path_to_root)

        usage_posits = ' '.join(
            rule.get_usage_str_positional() for rule in self.rules_posit
        )
        if usage_posits: usage_posits += ' '

        if self.is_leaf():
            ### [NOTE] options isn't currently supported for non-leaf nodes
            return f"{preffix} {usage_posits}{fy.Color.green('[options...]')}"

        return f"{preffix} {fy.Color.magenta('COMMAND')} ..."


    # --------------------------------------------------------------------------
    def _get_str_subcommands(self) -> str:
        max_name_len = max(map(len, self._children_names))
        width_name = len(fy.HelpStr.pad_name("", max_name_len))
        width_desc = max(1, fy.WIDTH_TERMINAL - width_name)

        rows_commands = '\n'.join((
            fy.Color.magenta(fy.HelpStr.pad_name(child.name, max_name_len)) +\
                child.help_str.wrapped_text(width_name, width_desc)
            for child in self.iter_sorted_children()
        ))

        return '\n'.join((
            fy.Color.magenta("commands:", bright = False),
            "    The following subcommands are available:",
            "",
            rows_commands,
        ))


    # --------------------------------------------------------------------------
    def _get_str_leaf_arguments(self) -> str:
        return '\n'.join((
            self._get_str_leaf_posits(),
            self._get_str_leaf_flags(),
        ))


    # --------------------------------------------------------------------------
    def _get_str_leaf_posits(self) -> str:
        if not self.rules_posit: return ""

        rows_posits = '\n'.join((
            rule.get_help_string_description()
            for rule in self.rules_posit
        ))
        return '\n'.join((
            fy.Color.blue("positional arguments:", bright = False),
            rows_posits, "",
        ))


    # --------------------------------------------------------------------------
    def _get_str_leaf_flags(self) -> str:
        if not self.rules_flags: return ""

        rows_flags = '\n'.join((
            rule.get_help_string_description()
            for rule in self.rules_flags
        ))
        return '\n'.join((
            fy.Color.green("options:", bright = False),
            rows_flags, "",
        ))


    # --------------------------------------------------------------------------
    def _assert_unique_child(self, name: str):
        if name in self.children:
            raise fy.FreyaSyntaxError(f"Duplicate child branch '{name}' specified inside the same branch.")


# //////////////////////////////////////////////////////////////////////////////
