from dataclasses import dataclass, field
from uuid import uuid4

BLOCKS: tuple = ("root", "n1", "n2", "n4", "n5", "n6", "n7")
# BLOCKS = ("root", "div", "p", "b", "strong", "i", "ul", "ol", "span")
PRINT_SHIFT = 2


@dataclass
class Node:
    name: str = "string"
    text: str = ""
    start_tag: str = ""
    end_tag: str = ""
    self_length: int = 0
    children: list["Node"] = field(default_factory=list)
    children_length: int = 0
    total_length: int = 0
    level: int = 0
    parent: "Node" = None

    def is_splittable(self) -> bool:
        return len(self.children) > 0 and self.name in BLOCKS

    def own_len_w_parents(self):
        """Recursive function to calculate total_length of
        node's self_length and its parent's self_length"""

        if self.parent is None or self.parent.name == "root":
            return self.self_length
        return self.parent.own_len_w_parents() + self.self_length

    def add_child(self, node: "Node"):
        """Function to add a child Node"""

        self.children.append(node)
        node.level = self.level + 1
        node.parent = self

    def calculate_total_length(self):
        """Recursive function to calculate total_length of
        each node in the tree"""

        self.self_length += (self.level - 1) * PRINT_SHIFT
        if not self.children:
            """Base case"""
            self.total_length = self.self_length
            return self.total_length

        for child in self.children:
            self.children_length += child.calculate_total_length()

        self.total_length = self.self_length + self.children_length

        return self.total_length

    def print_tree_simple(self):
        print(
            " " * self.level * PRINT_SHIFT,
            self.name,
            "<=",
            self.parent.name if self.parent else "None",
        )
        for child in self.children:
            child.print_tree_simple()

    def print_tree(self):
        """Recursive function to output the tree of nodes
        starting from root node"""

        if self.name == "string":
            print(" " * (self.level - 1) * PRINT_SHIFT, self.text)
            return

        if self.name != "root":
            print(" " * (self.level - 1) * PRINT_SHIFT, self.start_tag)

        for child in self.children:
            child.print_tree()

        if self.name != "root":
            print(" " * (self.level - 1) * PRINT_SHIFT, self.end_tag)


@dataclass
class Fragment:
    uuid: str = field(default_factory=uuid4)
    total_length: int = 0
    lst: list = field(default_factory=list)

    def get_node_parents(self, node: Node):
        lst = []
        while node.parent:
            lst.append(node.parent)
            node = node.parent
        return lst

    def add_node(self, node: Node):
        if node.name == "root":
            return
        if node.parent.name != "root" and not self.lst:
            parents = list(reversed(self.get_node_parents(node)))
            for parent in parents:
                if parent.name == "root":
                    continue
                self.lst.append(parent)
                self.total_length += parent.self_length

        self.lst.append(node)
        self.total_length += node.self_length

    def add_node_w_children(self, node: Node):
        self.add_node(node)

        if not node.children:
            return

        for child in node.children:
            self.add_node_w_children(child)

    def print_tree(self):
        """
        Function that creates list of open tags
        strings and closing tags
        for each node in the tree for output
        """

        closing_tags = []
        result = []
        level = -1  # shift level to -1 b of root

        for node in self.lst:
            node.level -= 1  # shift level by -1
            if node.level <= level and closing_tags:
                # if there is jump to left means
                # we need to close tags
                diff = level - node.level  # count number of closing tags
                for i in range(diff):
                    end_tag = closing_tags.pop()
                    if end_tag:
                        result.append(
                            " " * (level - i - 1) * PRINT_SHIFT + end_tag
                        )
            if node.start_tag:
                result.append(" " * node.level * PRINT_SHIFT + node.start_tag)
            if node.text:
                result.append(" " * node.level * PRINT_SHIFT + node.text)
            if node.end_tag:
                closing_tags.append(node.end_tag)
            level = node.level

        if closing_tags:
            # if there are some closing tags left
            length = len(closing_tags) - 1
            for tag in list(reversed(closing_tags)):
                result.append(" " * length * PRINT_SHIFT + tag)
                length -= 1

        yield from result


@dataclass
class FragmentList:
    lst: list = field(default_factory=list[Fragment])
    current_fragment: Fragment = field(default_factory=Fragment)
    length: int = 0
    max_len: int = 0

    def __post_init__(self):
        self.lst.append(Fragment())
        self.current_fragment = self.lst[-1]

    def split_tree(self, node: Node):
        """
        Main function where magic happens
        tree of nodes is split into fragments
        """

        self.current_fragment = self.lst[-1]
        left_space = self.max_len - self.current_fragment.total_length

        if node.total_length <= left_space:
            if node.children:
                self.current_fragment.add_node_w_children(node)
            else:
                self.current_fragment.add_node(node)

        if node.self_length > self.max_len:
            raise ValueError(
                f"Node {node.start_tag}{node.end_tag} is too long for fragment: {node.self_length} > {self.max_len}"
            )

        elif not node.is_splittable() and node.total_length > left_space:
            if not node.own_len_w_parents() <= self.max_len:
                raise ValueError(
                    f"Unsplittable Node {node.name} too long with its parents: {node.own_len_w_parents()} > {self.max_len}"
                )
            new_fragment = Fragment()
            self.lst.append(new_fragment)
            if node.children:
                new_fragment.add_node_w_children(node)
            else:
                new_fragment.add_node(node)

        elif node.is_splittable() and node.total_length > left_space:
            if node.self_length > left_space:
                if not node.own_len_w_parents() <= self.max_len:
                    raise ValueError(
                        f"Splittable Block Node {node.start_tag}{node.end_tag} too long with its parents: {node.own_len_w_parents()} > {self.max_len}"
                    )
                new_fragment = Fragment()
                self.lst.append(new_fragment)
                self.current_fragment = new_fragment
            self.current_fragment.add_node(node)

            for child in node.children:
                self.split_tree(child)
