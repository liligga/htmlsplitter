import click
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString

from tree import FragmentList, Node, Fragment, BLOCKS


MAX_LEN = 4096


def extract_tags(element):
    if not isinstance(element, Tag):
        return "", ""

    start_tag = str(element).split(">")[0] + ">"

    if element.name in ("area", "img", "br", "hr", "input", "meta", "link"):
        return start_tag, ""

    end_tag = f"</{element.name}>"

    return start_tag, end_tag


def create_node_from_element(element):
    node = None
    if isinstance(element, Tag):
        start_tag, end_tag = extract_tags(element)
        self_length = len(start_tag) + len(end_tag)
        node = Node(
            name=element.name,
            self_length=self_length,
            start_tag=start_tag,
            end_tag=end_tag,
        )
    if isinstance(element, NavigableString):
        text = str(element).strip()
        node = Node(
            name="string",
            text=text,
            self_length=len(text),
        )
    return node


def traverse_soup(parent: Node, elements: BeautifulSoup):
    if type(elements) is not list:
        elements = [elements]

    for element in elements:
        if element.name and (
            element.name == "script" or element.name == "style"
        ):
            continue
        if element.encode("utf-8").strip() == b"":
            continue

        new_node = create_node_from_element(element)
        parent.add_child(new_node)
        if isinstance(element, Tag):
            traverse_soup(new_node, element.contents)


def split_message(tree: Node, max_len: int):
    fragments = FragmentList(max_len=max_len)
    fragments.split_tree(tree)
    print(
        f"Total {len(fragments.lst)} fragments with {sum(f.total_length for f in fragments.lst)} bytes"
    )
    for fragment in fragments.lst:
        yield fragment


@click.command()
@click.option("--max-len", default=MAX_LEN, help="max length of the response")
@click.argument("file")
def main(file: str, max_len: int):
    f = open(file, "r")
    soup = BeautifulSoup(f.read().replace("\n", ""), "html.parser")
    f.close()
    tree = Node("root", 0)
    traverse_soup(tree, soup.contents)

    tree.calculate_total_length()
    tree.print_tree_simple()

    for ind, fragment in enumerate(split_message(tree, max_len), start=1):
        print(f"==== Fragment {ind} Length {fragment.total_length} chars ====")
        for node in fragment.print_tree():
            print(node)


if __name__ == "__main__":
    main()
