from __future__ import annotations
from random import random, randint, sample, choice
from copy import deepcopy
from typing import (
    Any,
    Union,
    Callable,
    Optional,
    Mapping,
    Iterable,
    Sequence,
    Dict,
    List,
    Set,
)

from evolver.exceptions import InvalidRegexError
from evolver.helpers import first_nested
from evolver.wrappers import RxWrapperSet, RxWrapper
from evolver.types import RxTypeSet, RxType, CharSets
from evolver.config import (
    RAND,
    P_MODIFIER,
    P_EXTEND,
    SUPPRESS_ROOT_CHARS,
    NodeSpec,
    RxSpec,
)


class RxNode:
    def __init__(
        self,
        char_set: CharSets,
        wrapper: RxWrapper,
        children: Sequence[RxNode],
        is_child: bool,
    ) -> None:
        self.name: str = wrapper.name
        self.modifier: Optional[RxNode] = None
        self.assertion: Optional[RxNode] = None
        self.children: Sequence[RxNode] = children
        self.rxtype: RxType = wrapper.rxtype
        self.display_function: Callable = wrapper.display_function
        self.compile_function: Callable = wrapper.compile_function
        self.is_child: bool = is_child
        self.strip_child_mods: bool = wrapper.strip_child_mods
        self.strip_mod: bool = False
        self.char_sets: CharSets = char_set

        for child in self.children:
            if self.strip_child_mods:
                child.strip_mod = True

    def __repr__(self) -> str:
        out = f"{self.name}"
        if self.modifier:
            out += f":<{self.modifier}>"
        if self.children:
            out += f"{str(self.children)}"
        return out

    def set_assertion(self, assertion: RxNode) -> None:
        self.assertion = assertion

    def set_modifier(self, modifier: RxNode) -> None:
        self.modifier = modifier

    def display(self) -> str:
        out = ""

        if self.assertion and not self.strip_mod:
            out += self.assertion.display()

        if self.children:
            out += self.display_function(self, self.children)

        else:
            out += self.display_function(self)
        # print('- ', self.name, self.rxtype)

        if self.modifier and not self.strip_mod:
            out += self.modifier.display()

        return out

    def compile(
        self,
        compiled_node: Optional[str] = None,
        compiled_children: Optional[List[str]] = None,
    ) -> str:
        args: list = [self]

        if self.children:
            args.append(self.children)

        if self.rxtype.is_type_name("mod"):
            args.append(compiled_node)

        if self.rxtype.is_type_name("mmod"):
            args.append(compiled_children)

        res: str = self.compile_function(*args)

        if self.modifier and not self.strip_mod:
            res = self.modifier.compile(
                res, [child.compile() for child in self.children]
            )
        return res

    def mutate(self, node_factory: RxNodeFactory, prob_change: float) -> RxNode:
        if random() < prob_change:
            return node_factory.make_random_node(
                type_name=self.rxtype.name, is_child=self.is_child
            )
        else:
            new_children = []
            for child in self.children:
                new_children.append(child.mutate(node_factory, prob_change))

            new_node = deepcopy(self)
            new_node.children = new_children
            return new_node


class RxNodeFactory:
    def __init__(self, printable_subset: Optional[Iterable[str]]) -> None:
        self.omit_types: Set[str] = set()
        self.omit_wrappers: Set[str] = set()
        self._rxtypes = RxTypeSet()
        self._char_sets = CharSets(self._rxtypes)
        self._rxwrappers = RxWrapperSet(self._char_sets, printable_subset)

    def set_omit(
        self,
        types: Optional[Union[str, Iterable[str]]] = None,
        wrappers: Optional[Union[str, Iterable[str]]] = None,
    ) -> None:

        if types and not isinstance(types, set):
            types = set(types)
        self.omit_types = types or set()

        if wrappers and not isinstance(wrappers, set):
            wrappers = set(wrappers)
        self.omit_wrappers = wrappers or set()

    def clear_omit(self, types: bool = False, wrappers: bool = False) -> None:
        if not (types and wrappers):
            self.clear_omit(types=True, wrappers=True)

        if types:
            self.omit_types.clear()
        if wrappers:
            self.omit_wrappers.clear()

    def parse_rxspec(self, rxspec: RxSpec) -> NodeSpec:
        if not isinstance(rxspec, list):
            rxspec = [rxspec]

        node_spec = {"rw_name": rxspec[0]}
        for spec in rxspec[1:]:
            if self._rxwrappers.wrapper_is_type(first_nested(spec), "mod"):
                node_spec["modifier"] = self.parse_rxspec(spec)

            else:
                node_spec["children"] = [self.parse_rxspec(child) for child in spec]

        return node_spec

    def make_node(
        self,
        rw_name: Optional[str] = None,
        children: Union[List[NodeSpec], int] = RAND,
        modifier: Optional[Union[NodeSpec, int]] = None,
        rxwrapper: Optional[RxWrapper] = None,
        is_child: bool = False,
        strict_type_match: bool = False,
    ) -> RxNode:
        """
        children format: [{'rw_name': regex_wrapper_name, 'children': [<children>]})]
        modifier format: {'rw_name': <modifier_name>, 'children': <children>, 'modifier': <modifier>}
        """

        if not rxwrapper:
            if not rw_name:
                raise ValueError("must provide regex wrapper object or name")

            rxwrapper = self._rxwrappers[rw_name]

        child_nodes: List[RxNode] = []
        if rxwrapper.child_count != 0:
            if children == RAND:
                child_types: List[str] = list(
                    filter(
                        lambda type_name: not self._rxtypes.is_one_of(
                            type_name, self.omit_types
                        ),
                        rxwrapper.child_types,
                    )
                )

                if rxwrapper.uniform_child_types:
                    child_types = sample(rxwrapper.child_types, 1)
                child_nodes = [
                    self.make_random_node(choice(child_types), is_child=True)
                    for i in range(rxwrapper.get_child_count())
                ]
            else:
                for child in children:
                    child_nodes.append(self.make_node(**child, is_child=True))

        node: RxNode = RxNode(self._char_sets, rxwrapper, child_nodes, is_child)
        if rxwrapper.is_modifiable:
            if modifier == RAND:
                # print("- ", node.name)
                # print("- ", rxwrapper.name)
                # print("- ", rxwrapper.rxtype)
                # print("- ", rxwrapper.rxtype.is_type_name("mod"))

                # if wrapper is not a modifier, build a modifier. Otherwise, build mod-modifier.
                mod_type: str = (
                    "mmod" if rxwrapper.rxtype.is_type_name("mod") else "mod"
                )
                # print("- ", mod_type)
                # if mod_type (to make) is mod, then don't build an mmod
                # omit_types += ["mmod"] if mod_type == "mod" else []
                # print(">> ", omit_types)
                if mod_type not in self.omit_types:
                    modifier_node: RxNode = self.make_random_node(
                        mod_type, strict_typing=True
                    )
                    node.set_modifier(modifier_node)
                # print("-- ", modifier)
            elif modifier:
                modifier_node: RxNode = self.make_node(**modifier)
                node.set_modifier(modifier_node)

        return node

    def make_random_node(
        self,
        type_name: str = "re",
        is_child: bool = False,
        prob_modifier: float = P_MODIFIER,
        strict_typing: bool = False,
    ) -> RxNode:
        rxtype: RxType = self._rxtypes[type_name]

        # filter RxWrapper.wrappers with items that match rxtype
        filtered_wrappers: List[RxWrapper] = list(
            filter(
                lambda rxwrapper: rxwrapper.rxtype.is_type(
                    rxtype, strict=strict_typing
                ),
                self._rxwrappers.all(),
            )
        )

        # filter out types specified for omission in node generation
        for omit in self.omit_types:
            omit_type: RxType = self._rxtypes[omit]
            filtered_wrappers = list(
                filter(
                    lambda rxwrapper: not rxwrapper.rxtype.is_type(omit_type),
                    filtered_wrappers,
                )
            )

        # filter out characters if is root node and suppression parameter specified
        if not is_child and SUPPRESS_ROOT_CHARS:
            filtered_wrappers = list(
                filter(
                    lambda rxwrapper: not rxwrapper.rxtype.is_type(
                        self._rxtypes["printable"]
                    ),
                    filtered_wrappers,
                )
            )

        # filter out wrappers specified for omission in node generation
        for omit in self.omit_wrappers:
            filtered_wrappers = list(
                filter(lambda rxwrapper: rxwrapper.name != omit, filtered_wrappers)
            )

        rxwrapper: RxWrapper = choice(filtered_wrappers)
        modifier: Optional[int] = None
        if rxwrapper.is_modifiable and random() < prob_modifier:
            modifier = RAND

        return self.make_node(
            rxwrapper=rxwrapper,
            modifier=modifier,
            is_child=is_child,
        )


class RxNodeSet:
    def __init__(self, nodes: List[RxNode], node_factory: RxNodeFactory) -> None:
        self.node_factory: RxNodeFactory = node_factory
        self.nodes: List = nodes

    def __repr__(self) -> str:
        return ", ".join([str(node) for node in self.nodes])

    def display(self) -> str:
        return "".join([node.display() for node in self.nodes])

    def compile(self) -> Optional[str]:
        try:
            return "".join([node.compile() for node in self.nodes])
        except InvalidRegexError as e:
            print(f"{self.display()} is an invalid regex")
            print(e)
            return None
        except:
            raise

    def mutate(self, prob_change: float) -> RxNodeSet:
        new_nodes: List[RxNode] = [
            node.mutate(self.node_factory, prob_change) for node in self.nodes
        ]
        if random() < prob_change:
            ix: int = randint(0, len(new_nodes) - 1)
            if random() < 0.5 and len(new_nodes) > 1:
                new_nodes = new_nodes[:ix] + new_nodes[ix + 1 :]
            else:
                new_nodes = (
                    new_nodes[:ix]
                    + [self.node_factory.make_random_node()]
                    + new_nodes[ix:]
                )
        return RxNodeSet(new_nodes, self.node_factory)

    def crossover(self, node_set: RxNodeSet, probswap: float) -> RxNodeSet:
        new_nodes: List[RxNode] = self.nodes
        if random() < probswap:
            max_len: int = max([len(self.nodes), len(node_set.nodes)])
            cuts: List[int] = sorted([randint(0, max_len), randint(0, max_len)])
            new_nodes = (
                self.nodes[: cuts[0]]
                + node_set.nodes[cuts[0] : cuts[1]]
                + self.nodes[cuts[1] :]
            )
        return RxNodeSet([deepcopy(node) for node in new_nodes], self.node_factory)


class RxNodeSetFactory:
    def __init__(self, printable_subset: Optional[Iterable[str]] = None) -> None:
        self.node_factory: RxNodeFactory = RxNodeFactory(printable_subset)

    def set_omit(
        self,
        types: Optional[Union[str, Iterable[str]]] = None,
        wrappers: Optional[Union[str, Iterable[str]]] = None,
    ):
        self.node_factory.set_omit(types, wrappers)

    def clear_omit(self, types: bool = False, wrappers: bool = False) -> None:
        self.node_factory.clear_omit(types, wrappers)

    def make_node_set(self, regex_specification: RxSpec) -> RxNodeSet:
        """
        format: [
            'name_1',
            ['<name_2>', <modifier>]
            ['<name_3>', [<child_1>]],
            ['<name_4>', [<child_1>, <child_2>]],
            ['<name_5>', [<child_1>], <modifier>],
            ['<name_6>', <modifier>, [<child_1>]],
            ['<name_7>', [<modifier>, [<child_1>]], [<child_1>]],
            ['<name_8>', [[<child_1>, [<sub_child_1>, <sub_child_2>]], <child_2>]]
        ]
        """

        node_specs: List[NodeSpec] = [
            self.node_factory.parse_rxspec(rxspec) for rxspec in regex_specification
        ]
        return RxNodeSet(
            [self.node_factory.make_node(**spec) for spec in node_specs],
            self.node_factory,
        )

    def random_node_set(self, prob_extend: float = P_EXTEND) -> RxNodeSet:
        nodes: List[RxNode] = [self.node_factory.make_random_node()]
        while random() < prob_extend:
            nodes.append(self.node_factory.make_random_node())
        return RxNodeSet(nodes, self.node_factory)
