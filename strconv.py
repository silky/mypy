import alore
import re
from util import dump_tagged, short_type
from os import separator
from string import int_to_str


# Visitor for converting a Node to a human-readable string.
#
# For example, an MypyFile node from program "1" is converted into
# something like this:
#   MypyFile:1(
#     fnam
#     ExpressionStmt:1(
#       IntExpr(1)))
class StrConv(NodeVisitor<str>):
    # Convert an array of items to a multiline pretty-printed string. The tag
    # is produced from the type name of obj and its line number. See
    # util::DumpTagged for a description of the nodes argument.
    def dump(self, nodes, obj):
        return dump_tagged(nodes, short_type(obj) + ':' + str(obj.line))
    
    # Return an array in a format suitable for dump() that represents the
    # arguments and the body of a function. The caller can then decorate the
    # array with information specific to methods, global functions or
    # anonymous functions.
    def func_helper(self, o):
        a = []
        if o.args != []:
            a.append(alore.pair('Args', o.args))
        if o.typ is not None:
            a.append(o.typ)
        for i in o.init:
            if i is not None:
                a.append(alore.pair('Init', o.init))
                break
        if o.var_arg is not None:
            a.append(alore.pair('VarArg', [o.var_arg]))
        if o.dict_var_arg is not None:
            a.append(alore.pair('DictVarArg', [o.dict_var_arg]))
        a.append(o.body)
        return a
    
    
    # Top-level structures
    #---------------------
    
    
    def visit_mypy_file(self, o):
        a = [o.defs]
        if o.is_bom:
            a.insert(0, 'BOM')
        # Omit path to special file with name "main". This is used to simplify
        # test case descriptions; the file "main" is used by default in many test
        # cases.
        if o.path is not None and o.path != 'main':
            # Insert path. Normalize directory separators to / to unify test case
            # output in all platforms.
            a.insert(0, o.path.replace(separator, '/'))
        return self.dump(a, o)
    
    def visit_import(self, o):
        a = []
        for id, as_id in o.ids:
            a.append('{} : {}'.format(id, as_id))
        return 'Import:{}({})'.format(o.line, ', '.join(a))
    
    def visit_import_from(self, o):
        a = []
        for name, as_name in o.names:
            a.append('{} : {}'.format(name, as_name))
        return 'ImportFrom:{}({}, [{}])'.format(o.line, o.id, ', '.join(a))
    
    def visit_import_all(self, o):
        return 'ImportAll:{}({})'.format(o.line, o.id)
    
    
    # Definitions
    #------------
    
    
    def visit_func_def(self, o):
        a = self.func_helper(o)
        a.insert(0, o.name)
        if o.max_pos != -1:
            a.insert(1, 'MaxPos({})'.format(o.max_pos))
        return self.dump(a, o)
    
    def visit_overloaded_func_def(self, o):
        a = o.items[:]
        if o.typ is not None:
            a.insert(0, o.typ)
        return self.dump(a, o)
    
    def visit_type_def(self, o):
        a = [o.name, o.defs.body]
        # Display base types unless they are implicitly just builtins.object (in
        # this case there is no representation).
        if len(o.base_types) > 1 or (len(o.base_types) == 1 and o.base_types[0].repr is not None):
            a.insert(1, alore.pair('BaseType', o.base_types))
        if o.type_vars is not None:
            a.insert(1, alore.pair('TypeVars', o.type_vars.items))
        if o.is_interface:
            a.insert(1, 'Interface')
        return self.dump(a, o)
    
    def visit_var_def(self, o):
        a = []
        for n, t in o.items:
            a.append('Var({})'.format(n.name))
            a.append('Type({})'.format(t))
        if o.init is not None:
            a.append(o.init)
        return self.dump(a, o)
    
    def visit_var(self, o):
        l = ''
        # Add :nil line number tag if no line number is specified to remain
        # compatible with old test case descriptions that assume this.
        if o.line < 0:
            l = ':nil'
        return 'Var' + l + '(' + o.name + ')'
    
    def visit_global_decl(self, o):
        return self.dump([o.names], o)
    
    def visit_decorator(self, o):
        return self.dump([o.decorator, o.func], o)
    
    def visit_annotation(self, o):
        return 'Type:{}({})'.format(o.line, o.typ)
    
    
    # Statements
    #-----------
    
    
    def visit_block(self, o):
        return self.dump(o.body, o)
    
    def visit_expression_stmt(self, o):
        return self.dump([o.expr], o)
    
    def visit_assignment_stmt(self, o):
        return self.dump([alore.pair('Lvalues', o.lvalues), o.rvalue], o)
    
    def visit_operator_assignment_stmt(self, o):
        return self.dump([o.op, o.lvalue, o.rvalue], o)
    
    def visit_while_stmt(self, o):
        a = [o.expr, o.body]
        if o.else_body is not None:
            a.append(alore.pair('Else', o.else_body.body))
        return self.dump(a, o)
    
    def visit_for_stmt(self, o):
        a = [o.index]
        if o.types != [None] * len(o.types):
            a += o.types
        a.extend([o.expr, o.body])
        if o.else_body is not None:
            a.append(alore.pair('Else', o.else_body.body))
        return self.dump(a, o)
    
    def visit_return_stmt(self, o):
        return self.dump([o.expr], o)
    
    def visit_if_stmt(self, o):
        a = []
        for i in range(len(o.expr)):
            a.append(alore.pair('If', [o.expr[i]]))
            a.append(alore.pair('Then', o.body[i].body))
        
        if o.else_body is None:
            return self.dump(a, o)
        else:
            return self.dump([a, alore.pair('Else', o.else_body.body)], o)
    
    def visit_break_stmt(self, o):
        return self.dump([], o)
    
    def visit_continue_stmt(self, o):
        return self.dump([], o)
    
    def visit_pass_stmt(self, o):
        return self.dump([], o)
    
    def visit_raise_stmt(self, o):
        return self.dump([o.expr, o.from_expr], o)
    
    def visit_assert_stmt(self, o):
        return self.dump([o.expr], o)
    
    def visit_yield_stmt(self, o):
        return self.dump([o.expr], o)
    
    def visit_del_stmt(self, o):
        return self.dump([o.expr], o)
    
    def visit_try_stmt(self, o):
        a = [o.body]
        
        for i in range(len(o.vars)):
            a.append(o.types[i])
            if o.vars[i] is not None:
                a.append(o.vars[i])
            a.append(o.handlers[i])
        
        if o.else_body is not None:
            a.append(alore.pair('Else', o.else_body.body))
        if o.finally_body is not None:
            a.append(alore.pair('Finally', o.finally_body.body))
        
        return self.dump(a, o)
    
    def visit_with_stmt(self, o):
        a = []
        for i in range(len(o.expr)):
            a.append(alore.pair('Expr', [o.expr[i]]))
            if o.name[i] is not None:
                a.append(alore.pair('Name', [o.name[i]]))
        return self.dump(a + [o.body], o)
    
    
    # Expressions
    #------------
    
    
    # Simple expressions
    
    def visit_int_expr(self, o):
        return 'IntExpr({})'.format(o.value)
    
    def visit_str_expr(self, o):
        return 'StrExpr({})'.format(self.str_repr(o.value))
    
    def str_repr(self, s):
        s = re.sub(s, '\\\u[0-9a-fA-F]{4}', xxx_def (m):
            return '\\' + m.group(0)
        )
        return re.sub(s, '[^\\x20-\\x7e]', xxx_def (m):
            return '\u{}'.format(int_to_str(ord(m.group(0)), 16, 4))
        )
    
    def visit_float_expr(self, o):
        return 'FloatExpr({})'.format(o.value)
    
    def visit_paren_expr(self, o):
        return self.dump([o.expr], o)
    
    def visit_name_expr(self, o):
        return short_type(o) + '(' + self.pretty_name(o.name, o.kind, o.full_name, o.is_def) + ')'
    
    def pretty_name(self, name, kind, full_name, is_def):
        n = name
        if is_def:
            n += '*'
        if kind == GDEF or (full_name != name and full_name is not None):
            # Append fully qualified name for global references.
            n += ' [{}]'.format(full_name)
        elif kind == LDEF:
            # Add tag to signify a local reference.
            n += ' [l]'
        elif kind == MDEF:
            # Add tag to signify a member reference.
            n += ' [m]'
        return n
    
    def visit_member_expr(self, o):
        return self.dump([o.expr, self.pretty_name(o.name, o.kind, o.full_name, o.is_def)], o)
    
    def visit_call_expr(self, o):
        a = [o.callee, alore.pair('Args', o.args)]
        if o.is_var_arg:
            a.append('VarArg')
        if o.dict_var_arg is not None:
            a.append(alore.pair('DictVarArg', [o.dict_var_arg]))
        for n, v in o.keyword_args:
            a.append(alore.pair('KwArgs', [n, v]))
        return self.dump(a, o)
    
    def visit_op_expr(self, o):
        return self.dump([o.op, o.left, o.right], o)
    
    def visit_cast_expr(self, o):
        return self.dump([o.expr, o.typ], o)
    
    def visit_unary_expr(self, o):
        return self.dump([o.op, o.expr], o)
    
    def visit_list_expr(self, o):
        a = o.items[:]
        if o.typ is not None:
            a.insert(0, alore.pair('Type', [o.typ]))
        return self.dump(a, o)
    
    def visit_dict_expr(self, o):
        a = o.items[:]
        if o.key_type is not None:
            a.insert(0, alore.pair('ValueType', [o.value_type]))
            a.insert(0, alore.pair('KeyType', [o.key_type]))
        return self.dump(a, o)
    
    def visit_set_expr(self, o):
        return self.dump(o.items, o)
    
    def visit_tuple_expr(self, o):
        a = o.items[:]
        if o.types is not None:
            a.insert(0, alore.pair('Type', o.types))
        return self.dump(a, o)
    
    def visit_index_expr(self, o):
        return self.dump([o.base, o.index], o)
    
    def visit_super_expr(self, o):
        return self.dump([o.name], o)
    
    def visit_type_application(self, o):
        return self.dump([o.expr, alore.pair('Types', o.types)], o)
    
    def visit_func_expr(self, o):
        a = self.func_helper(o)
        return self.dump(a, o)
    
    def visit_generator_expr(self, o):
        # FIX types
        return self.dump([o.left_expr, o.index, o.right_expr, o.condition], o)
    
    def visit_list_comprehension(self, o):
        return self.dump([o.generator], o)
    
    def visit_conditional_expr(self, o):
        return self.dump([o.cond, o.if_expr, o.else_expr], o)
    
    def visit_slice_expr(self, o):
        a = [o.begin_index, o.end_index, o.stride]
        if a[0] is None:
            a[0] = '<empty>'
        if a[1] is None:
            a[1] = '<empty>'
        return self.dump(a, o)
    
    def visit_coerce_expr(self, o):
        return self.dump([o.expr, alore.pair('Types', [o.target_type, o.source_type])], o)
    
    def visit_type_expr(self, o):
        return self.dump([str(o.typ)], o)
    
    # These are for convenience. These node types are not defined in the parser
    # module.
    def visit_filter_node(self, o):
        pass