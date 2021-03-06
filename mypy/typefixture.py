"""Fixture used in type-related test cases.

It contains class TypeInfos and Type objects.
"""

from typing import List

from mypy.types import (
    TypeVar, AnyType, Void, ErrorType, NoneTyp, Instance, Callable, TypeVarDef,
    BasicTypes
)
from mypy.nodes import (
    TypeInfo, TypeDef, Block, ARG_POS, ARG_OPT, ARG_STAR, SymbolTable
)


class TypeFixture:
    """Helper class that is used as a fixture in type-related unit tests.

    The members are initialized to contain various type-related values.
    """
    
    def __init__(self):
        # Type variables

        self.t = TypeVar('T', 1)    # T`1 (type variable)
        self.tf = TypeVar('T', -1)  # T`-1 (type variable)
        self.tf2 = TypeVar('T', -2) # T`-2 (type variable)
        self.s = TypeVar('S', 2)    # S`2 (type variable)
        self.s1 = TypeVar('S', 1)   # S`1 (type variable)
        self.sf = TypeVar('S', -2)  # S`-2 (type variable)
        self.sf1 = TypeVar('S', -1) # S`-1 (type variable)

        # Simple types

        self.anyt = AnyType()
        self.void = Void()
        self.err = ErrorType()
        self.nonet = NoneTyp()

        # Abstract class TypeInfos

        # class F
        self.fi = make_type_info('F', is_abstract=True)

        # class F2
        self.f2i = make_type_info('F2', is_abstract=True)

        # class F3(F)
        self.f3i = make_type_info('F3', is_abstract=True, mro=[self.fi])

        # Class TypeInfos

        self.oi = make_type_info('builtins.object')         # class object
        self.std_tuplei = make_type_info('builtins.tuple')  # class tuple
        self.type_typei = make_type_info('builtins.type')   # class type
        self.std_functioni = make_type_info('std::Function') # Function TODO
        self.ai = make_type_info('A', mro=[self.oi])        # class A
        self.bi = make_type_info('B', mro=[self.ai])        # class B(A)
        self.ci = make_type_info('C', mro=[self.ai])        # class C(A)
        self.di = make_type_info('D', mro=[self.oi])        # class D

        # class E(F)
        self.ei = make_type_info('E', mro=[self.fi, self.oi])

        # class E2(F2, F)
        self.e2i = make_type_info('E2', mro=[self.f2i, self.fi, self.oi])

        # class E3(F, F2)
        self.e3i = make_type_info('E3', mro=[self.fi, self.f2i, self.oi])

        # Generic class TypeInfos

        # G[T]
        self.gi = make_type_info('G', mro=[self.oi], typevars=['T'])
        # G2[T]
        self.g2i = make_type_info('G2', mro=[self.oi], typevars=['T'])
        # H[S, T]
        self.hi = make_type_info('H', mro=[self.oi], typevars=['S', 'T'])
        # GS[T, S] <: G[S]
        self.gsi = make_type_info('GS', mro=[self.gi, self.oi],
                                  typevars=['T', 'S'],
                                  bases=[Instance(self.gi, [self.s])])
        # GS2[S] <: G[S]
        self.gs2i = make_type_info('GS2', mro=[self.gi, self.oi],
                                   typevars=['S'],
                                   bases=[Instance(self.gi, [self.s1])])
        # list[T]
        self.std_listi = make_type_info('builtins.list', mro=[self.oi],
                                        typevars=['T'])

        # Instance types

        self.o = Instance(self.oi, [])                       # object
        self.std_tuple = Instance(self.std_tuplei, [])       # tuple
        self.type_type = Instance(self.type_typei, [])         # type
        self.std_function = Instance(self.std_functioni, []) # function TODO
        self.a = Instance(self.ai, [])          # A
        self.b = Instance(self.bi, [])          # B
        self.c = Instance(self.ci, [])          # C
        self.d = Instance(self.di, [])          # D

        self.e = Instance(self.ei, [])          # E
        self.e2 = Instance(self.e2i, [])        # E2
        self.e3 = Instance(self.e3i, [])        # E3

        self.f = Instance(self.fi, [])          # F
        self.f2 = Instance(self.f2i, [])        # F2
        self.f3 = Instance(self.f3i, [])        # F3

        # Generic instance types

        self.ga = Instance(self.gi, [self.a])        # G[A]
        self.gb = Instance(self.gi, [self.b])        # G[B]
        self.go = Instance(self.gi, [self.o])        # G[object]
        self.gt = Instance(self.gi, [self.t])        # G[T`1]
        self.gtf = Instance(self.gi, [self.tf])      # G[T`-1]
        self.gtf2 = Instance(self.gi, [self.tf2])    # G[T`-2]
        self.gs = Instance(self.gi, [self.s])        # G[S]
        self.gdyn = Instance(self.gi, [self.anyt])    # G[Any]

        self.g2a = Instance(self.g2i, [self.a])      # G2[A]

        self.gsab = Instance(self.gsi, [self.a, self.b])  # GS[A, B]
        self.gsba = Instance(self.gsi, [self.b, self.a])  # GS[B, A]

        self.gs2a = Instance(self.gs2i, [self.a])    # GS2[A]

        self.hab = Instance(self.hi, [self.a, self.b])    # H[A, B]
        self.haa = Instance(self.hi, [self.a, self.a])    # H[A, A]
        self.hbb = Instance(self.hi, [self.b, self.b])    # H[B, B]
        self.hts = Instance(self.hi, [self.t, self.s])    # H[T, S]

        self.lsta = Instance(self.std_listi, [self.a])  # List[A]
        self.lstb = Instance(self.std_listi, [self.b])  # List[B]

        # Basic types
        self.basic = BasicTypes(self.o, self.type_type, self.std_tuple,
                                self.std_function)
    
    # Helper methods
    
    def callable(self, *a):
        """callable(a1, ..., an, r) constructs a callable with argument types
        a1, ... an and return type r.
        """
        return Callable(a[:-1], [ARG_POS] * (len(a) - 1),
                        [None] * (len(a) - 1), a[-1], False)
    
    def callable_type(self, *a):
        """callable_type(a1, ..., an, r) constructs a callable with
        argument types a1, ... an and return type r, and which
        represents a type.
        """
        return Callable(a[:-1], [ARG_POS] * (len(a) - 1),
                        [None] * (len(a) - 1), a[-1], True)
    
    def callable_default(self, min_args, *a):
        """callable_default(min_args, a1, ..., an, r) constructs a
        callable with argument types a1, ... an and return type r,
        with min_args mandatory fixed arguments.
        """
        n = len(a) - 1
        return Callable(a[:-1],
                        [ARG_POS] * min_args + [ARG_OPT] * (n - min_args),
                        [None]  * n,
                        a[-1], False)
    
    def callable_var_arg(self, min_args, *a):
        """callable_var_arg(min_args, a1, ..., an, r) constructs a callable
        with argument types a1, ... *an and return type r.
        """
        n = len(a) - 1
        return Callable(a[:-1],
                        [ARG_POS] * min_args +
                        [ARG_OPT] * (n - 1 - min_args) +
                        [ARG_STAR], [None] * n,
                        a[-1], False)


class InterfaceTypeFixture(TypeFixture):
    """Extension of TypeFixture that contains additional generic
    interface types."""
    
    def __init__(self):
        super().__init__()
        # GF[T]
        self.gfi = make_type_info('GF', typevars=['T'], is_abstract=True)
    
        # M1 <: GF[A]
        self.m1i = make_type_info('M1',
                                  is_abstract=True,
                                  mro=[self.gfi, self.oi],
                                  bases=[Instance(self.gfi, [self.a])])

        self.gfa = Instance(self.gfi, [self.a]) # GF[A]
        self.gfb = Instance(self.gfi, [self.b]) # GF[B]

        self.m1 = Instance(self.m1i, []) # M1


def make_type_info(name: str,
                   is_abstract: bool = False,
                   mro: List[TypeInfo] = None,
                   bases: List[Instance] = None,
                   typevars: List[str] = None) -> TypeInfo:
    """Make a TypeInfo suitable for use in unit tests."""
    
    type_def = TypeDef(name, Block([]), None, [])
    type_def.fullname = name
    
    if typevars:
        v = [] # type: List[TypeVarDef]
        id = 1
        for n in typevars:
            v.append(TypeVarDef(n, id, None))
            id += 1
        type_def.type_vars = v
    
    info = TypeInfo(SymbolTable(), type_def)
    if mro is None:
        mro = []
    info.mro = [info] + mro
    if bases is None:
        if mro:
            # By default, assume that there is a single non-generic base.
            bases = [Instance(mro[0], [])]
        else:
            bases = []
    info.bases = bases
    
    return info
