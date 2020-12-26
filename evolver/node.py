from __future__ import annotations
from random import random, randint, sample, choice
from typing import Any, Union, Callable, Optional, Iterable, Sequence, Dict, List, Set
from copy import deepcopy

from evolver.config import RAND, P_MODIFIER, P_EXTEND, SUPPRESS_ROOT_CHARS
from evolver.exceptions import InvalidRegexError
from evolver.helpers import Singleton
from evolver.wrappers import RxWrapper
from evolver.types import RxType


NodeSpec = Dict[str, Union[str, "NodeSpec", List["NodeSpec"]]]
RxSpec = List[Union[str, "RxSpec", List["RxSpec"]]]


def first_nested(values: List[Any]):
    if not values:
        raise ValueError("list is empty")

    if isinstance(values, list):
        return first_nested(values[0])
    return values


def parse_rxspec(rxspec: RxSpec) -> NodeSpec:
    if not isinstance(rxspec, list):
        rxspec = [rxspec]

    node_spec = {"rw_name": rxspec[0]}
    for spec in rxspec[1:]:
        if RxWrapper.wrapper_is_type(first_nested(spec), "mod"):
            node_spec["modifier"] = parse_rxspec(spec)

        else:
            node_spec["children"] = [parse_rxspec(child) for child in spec]

    return node_spec


@Singleton
class RxNodeFactory:
    @staticmethod
    def instance():
        raise AttributeError(
            "FOR RESOLVING PYLINT DECORATOR ISSUE, SHOULD NOT BE REACHED"
        )

    def __init__(self) -> None:
        self.omit_types: Set[str] = set()
        self.omit_wrappers: Set[str] = set()

    def set_omit(
        self,
        types: Optional[Union[str, Iterable[str]]] = None,
        wrappers: Optional[Union[str, Iterable[str]]] = None,
    ) -> None:

        if types and not isinstance(set, types):
            types = set(types)
        self.omit_types = types or set()

        if wrappers and not isinstance(list, wrappers):
            wrappers = set(wrappers)
        self.omit_wrappers = wrappers or set()

    def clear_omit(self, types: bool = False, wrappers: bool = False) -> None:
        if not (types and wrappers):
            self.clear_omit(types=True, wrappers=True)

        types and self.omit_types.clear()
        wrappers and self.omit_wrappers.clear()

    def make_node(
        self,
        rw_name: Optional[str] = None,
        children: Optional[List[NodeSpec]] = RAND,
        modifier: Optional[NodeSpec] = None,
        rw: Optional[RxWrapper] = None,
        is_child: Optional[bool] = False,
        strict_type_match: Optional[bool] = False,
    ) -> RxNode:
        """
        children format: [{'rw_name': regex_wrapper_name, 'children': [<children>]})]
        modifier format: {'rw_name': <modifier_name>, 'children': <children>, 'modifier': <modifier>}
        """

        if not rw:
            if not rw_name:
                raise ValueError("must provide regex wrapper object or name")

            rw = RxWrapper.get_wrapper(rw_name)

        child_nodes = []
        if rw.child_count != 0:
            if children == RAND:
                child_types = list(
                    filter(
                        lambda type_name: not RxType.is_one_of(
                            type_name, self.omit_types
                        ),
                        rw.child_types,
                    )
                )

                if rw.uniform_child_types:
                    child_types = sample(rw.child_types, 1)
                child_nodes = [
                    self.make_random_node(choice(child_types), is_child=True)
                    for i in range(rw.get_child_count())
                ]
            else:
                for child in children:
                    child_nodes.append(self.make_node(**child, is_child=True))

        node = RxNode(rw, child_nodes, is_child)
        if rw.is_modifiable:
            if modifier == RAND:
                # print("- ", node.name)
                # print("- ", rw.name)
                # print("- ", rw.re_type)
                # print("- ", rw.re_type.is_type_name("mod"))

                # if wrapper is not a modifier, build a modifier. Otherwise, build mod-modifier.
                mod_type = "mmod" if rw.re_type.is_type_name("mod") else "mod"
                # print("- ", mod_type)
                # if mod_type (to make) is mod, then don't build an mmod
                # omit_types += ["mmod"] if mod_type == "mod" else []
                # print(">> ", omit_types)
                if mod_type not in self.omit_types:
                    modifier = self.make_random_node(mod_type, strict_typing=True)
                    node.set_modifier(modifier)
                # print("-- ", modifier)
            elif modifier:
                modifier = self.make_node(**modifier)
                node.set_modifier(modifier)

        return node

    def make_random_node(
        self,
        type_name: Optional[str] = "re",
        is_child: Optional[bool] = False,
        prob_modifier: Optional[float] = P_MODIFIER,
        strict_typing: Optional[bool] = False,
    ) -> RxNode:
        re_type = RxType.get_type(type_name)

        # filter RxWrapper.wrappers with items that match re_type
        filtered_wrappers = list(
            filter(
                lambda rw: rw.re_type.is_type(re_type, strict=strict_typing),
                RxWrapper.wrappers.values(),
            )
        )

        # filter out types specified for omission in node generation
        for omit in self.omit_types:
            omit_type = RxType.get_type(omit)
            filtered_wrappers = list(
                filter(lambda rw: not rw.re_type.is_type(omit_type), filtered_wrappers)
            )

        # filter out characters if is root node and suppression parameter specified
        if not is_child and SUPPRESS_ROOT_CHARS:
            filtered_wrappers = list(
                filter(
                    lambda rw: not rw.re_type.is_type(RxType.get_type("printable")),
                    filtered_wrappers,
                )
            )

        # filter out wrappers specified for omission in node generation
        for omit in self.omit_wrappers:
            filtered_wrappers = list(
                filter(lambda rw: rw.name != omit, filtered_wrappers)
            )

        rw = choice(filtered_wrappers)
        modifier = None
        if rw.is_modifiable and random() < prob_modifier:
            modifier = RAND

        return self.make_node(
            rw=rw,
            modifier=modifier,
            is_child=is_child,
        )


@Singleton
class RxNode:
    def __init__(
        self, wrapper: RxWrapper, children: Sequence[RxNode], is_child: bool
    ) -> None:
        self.name: str = wrapper.name
        self.modifier: RxNode = None
        self.assertion: RxNode = None
        self.children: Sequence[RxNode] = children
        self.rxtype: RxType = wrapper.rxtype
        self.display_function: Callable = wrapper.display_function
        self.compile_function: Callable = wrapper.compile_function
        self.is_child: bool = is_child
        self.strip_child_mods: bool = wrapper.strip_child_mods
        self.strip_mod: bool = False

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
            out += self.display_function(self.children)

        else:
            out += self.display_function()
        # print('- ', self.name, self.re_type)

        if self.modifier and not self.strip_mod:
            out += self.modifier.display()

        return out

    def compile(
        self,
        compiled_node: Optional[str] = None,
        compiled_children: Optional[List[str]] = None,
    ) -> str:
        args = []

        if self.children:
            args.append(self.children)

        if self.rxtype.is_type_name("mod"):
            args.append(compiled_node)

        if self.rxtype.is_type_name("mmod"):
            args.append(compiled_children)

        res = self.compile_function(*args)

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


@Singleton
class RxNodeSetFactory:
    @staticmethod
    def instance():
        raise AttributeError(
            "FOR RESOLVING PYLINT DECORATOR ISSUE, SHOULD NOT BE REACHED"
        )

    def __init__(self) -> None:
        self.node_factory: RxNodeFactory = RxNodeFactory.instance()

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
            parse_rxspec(rxspec) for rxspec in regex_specification
        ]
        return RxNodeSet([self.node_factory.make_node(**spec) for spec in node_specs])

    def random_node_set(self, prob_extend: Optional[float] = P_EXTEND) -> RxNodeSet:
        nodes: List[RxNode] = [self.node_factory.make_random_node()]
        while random() < prob_extend:
            nodes.append(self.node_factory.make_random_node())
        return RxNodeSet(nodes)


class RxNodeSet:
    def __init__(self, nodes: Sequence[RxNode]) -> None:
        self.node_factory: RxNodeFactory = RxNodeFactory.instance()
        self.nodes: Sequence = nodes

    def __repr__(self) -> str:
        return ", ".join([str(node) for node in self.nodes])

    def display(self) -> str:
        return "".join([node.display() for node in self.nodes])

    def compile(self) -> str:
        try:
            return "".join([node.compile() for node in self.nodes])
        except InvalidRegexError as e:
            print(f"{self.display()} is an invalid regex")
            print(e)
            return None
        except:
            raise

    def mutate(self, prob_change: float) -> RxNodeSet:
        new_nodes = [node.mutate(self.node_factory, prob_change) for node in self.nodes]
        if random() < prob_change:
            ix = randint(0, len(new_nodes) - 1)
            if random() < 0.5 and len(new_nodes) > 1:
                new_nodes = new_nodes[:ix] + new_nodes[ix + 1 :]
            else:
                new_nodes = (
                    new_nodes[:ix]
                    + [self.node_factory.make_random_node()]
                    + new_nodes[ix:]
                )
        return RxNodeSet(new_nodes)

    def crossover(self, node_set: RxNodeSet, probswap: float) -> RxNodeSet:
        new_nodes = self.nodes
        if random() < probswap:
            max_len = max([len(self.nodes), len(node_set.nodes)])
            cuts = sorted([randint(0, max_len), randint(0, max_len)])
            new_nodes = (
                self.nodes[: cuts[0]]
                + node_set.nodes[cuts[0] : cuts[1]]
                + self.nodes[cuts[1] :]
            )
        return RxNodeSet([deepcopy(node) for node in new_nodes])