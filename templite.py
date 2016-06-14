import re


class TempliteSyntaxError(ValueError):
    """Raise when a template has a syntax error"""

class CodeBuilder(object):
    """Build source code conveniently"""

    def __init__(self, indent=0):
        self.code = []
        self.indent_level = indent

    def __str__(self):
        return ''.join(str(c) for c in self.code)

    def add_line(self, line):
        """Add a line of source to the code

        Indentation and newline will be added for you, dont't provide them

        """
        self.code.extend([' ' * self.indent_level, line, '\n'])

    def add_section(self):
        """Add a section, a sub-CodeBuilder"""
        section = CodeBuilder(self.indent_level)
        self.code.append(section)
        return section

    INDENT_STEP = 4 # PEP8 standard
    def indent(self):
        """Increases the current indent for following lines."""
        self.indent_level += self.INDENT_STEP

    def dedent(self): 
        """Decreases the current indent for following lines."""
        self.indent_level -= self.INDENT_STEP

    def get_globals(self):
        """Excute the code, and return dict of globals it defines"""
        # Check that the caller really finished all the blocks they started
        assert self.indent_level == 0
        # Get the Pythn source as a sing string
        python_source = str(self)
        # Execute the source, defining glabals, and return them
        global_namespace = {}
        exec(python_source, global_namespace)
        return global_namespace


class Templite(object):
    """
    A simple template renderer, for a nano-subset of Django syntax

    """

    def __init__(self, text, *contexts):
        """Construct a Templite with give 'text'.
        
        'contexts' are dictionaries of values to use for future renderings.
        These are good for filters and global values.
        """

        self.context = {}
        for context in contexts:
            self.context.update(context)

        self.all_vars = set()
        self.loop_vars = set()

        code = CodeBuilder()

        code.add_line('def render_function(context, do_dots):')
        code.indent()
        vars_code = code.add_section()
        code.add_line('result = []')
        code.add_line('append_result = result.append')
        code.add_line('extend_result = result.extend')
        code.add_line('to_str = str')

        buffered = []
        def flush_output():
            """Force 'buffered' to the code builder"""
            if len(buffered) == 1:
                code.add_line("append_result({0})".format(buffered[0]))
            elif len(buffered) > 1:
                code.add_line('extend_result([{0}])'.format(", ".join(buffered)))

            del buffered[:]

        ops_stack = []
        # split the text to form a list of tokens
        tokens = re.split(r"(?s)({{.*?}}|{%.*?}|{#.*?})", text)

        for token in tokens:
            if token.startswith('{#'):
                # Comment: ignore it and move on
                continue
            elif token.startswith('{{'):
                expr = self._expr_code(token[2:-2].strip())
                buffered.append('to_str({0})'.format(expr))
            elif token.startswith('{%'):
                # Action tag: split into words and parse further
                flush_output()
                words = token[2:-2].strip().split()
                if words[0] == 'if':
                    if len(words) != 2:
                        self._syntax_error('Don\'t understand if', token)
                    ops_stack.append('if')
                    code.add_line('if {0}'.format(words[1]))
                    code.indent()
                elif words[0] == 'for':
                    # Loop: iterate over expression result
                    if len(words) != 4 and words[2] != 'in':
                        self._syntax_error('Don\'t understand for', token)
                    ops_stack.append('for')
                    self._variable(words[1], self.loop_vars)
                    code.add_line(
                        'for c_{0} in {1}:'.format(words[1], self._expr_code(words[3]))
                    )
                    code.indent()
                elif words[0].startswith('end'):
                    # Endsomething
                    if len(words) != 1:
                        self._syntax_error('Don\'t understand end', tokens)
                    end_what = words[0][3:]
                    if not ops_stack:
                        self._syntax_error('Too many ends', token)
                    start_what = ops_stack.pop()
                    if start_what != end_what:
                        self._syntax_error('Missing end tag', token)
                    code.dedent()
                else:
                    self._syntax_error('Don\'t understand tag', tokens)
            else:
                if token:
                    buffered.append(repr(token))
        if ops_stack:
            self._syntax_error('Unmatched action tag', ops_stack[-1])

        flush_output()

        for var_name in self.all_vars - self.loop_vars:
            vars_code.add_line('c_{0} = context[\'{1}\']'.format(var_name, var_name))

        code.add_line('return \'\'.join(result)')
        code.dedent()
        self._render_function = code.get_globals()['render_function']

    def _expr_code(self, expr):
        """Generate a python expression for 'expr'"""
        if '|' in expr:
            pipes = expr.split('|')
            code = self._expr_code(pipes[0])
            for func in pipes[1:]:
                self._variable(func, self.all_vars)
                code = 'c_{0}({1})'.format(func, code)
        elif '.' in expr:
            dots = expr.split('.')
            code = self._expr_code(dots[0])
            args = ', '.join(repr(d) for d in dots[1:])
            code = 'do_dots({0}, {1})'.format(code, args)
        else:
            self._variable(expr, self.all_vars)
            code = 'c_{0}'.format(expr)
        return code

    def _syntax_error(self, msg, thing):
        """Raise a syntax error using 'msg', and showing 'thins'."""
        raise TempliteSyntaxError('{0}: {1}'.format(msg, thing))

    def _variable(self, name, vars_set):
        """Track that 'name' is used as variable.

        Adds the name to 'vars_set', a set of variable names.

        Raise an syntax error if 'name' if not a valid name.

        """
        if not re.match(r'[_a-zA-Z][_a-zA-Z0-9]*$', name):
            self._synctax_error('Not a valid name', name)
        vars_set.add(name)

    def render(self, context=None):
        """Render this template by applying it to 'context'

        'context' is a dictionary of values to use in this rendering

        """

        # Make the complete context we'll use
        render_context = dict(self.context)
        if context:
            render_context.update(context)
        return self._render_function(render_context, self._do_dots)

    def _do_dots(self, value, *dots):
        for dot in dots:
            try:
                value = getattr(value, dot)
            except AttributeError:
                value = value[dot]
            if callable(value):
                value = value()
        return value




































