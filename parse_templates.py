import pathlib
import re
from dataclasses import dataclass
from typing import Dict, List, Union, Tuple, Any
from resources import ResourceBundle

Token = Union[str, int]

@dataclass
class TransformTemplate:
    name: str
    inputs: Dict[str, int]
    outputs: Dict[str, int]

    def scaled_inputs(self, k: int) -> ResourceBundle:
        """Return ResourceBundle of inputs × k."""
        return ResourceBundle({r: q * k for r, q in self.inputs.items()})

    def scaled_outputs(self, k: int) -> ResourceBundle:
        """Return ResourceBundle of outputs × k."""
        return ResourceBundle({r: q * k for r, q in self.outputs.items()})

    def max_scale(self, stock: ResourceBundle) -> int:
        """Largest integer k such that k·inputs ≤ current stock."""
        if not self.inputs:
            return 0
        return min(stock.quantity(r) // q for r, q in self.inputs.items())

    @staticmethod
    def from_lisp(ast: List[Any]) -> 'TransformTemplate':
        # ast format: ['TRANSFORM', 'C', ['INPUTS', ['Res1', q1], ...], ['OUTPUTS', [...]]]
        if len(ast) < 4 or ast[0].upper() != 'TRANSFORM':
            raise ValueError("AST is not a TRANSFORM node")
        inputs = {}
        outputs = {}
        for section in ast[2:]:
            if not isinstance(section, list) or len(section) < 2:
                continue
            header = section[0].upper()
            for entry in section[1:]:
                if isinstance(entry, list) and len(entry) == 2:
                    res, qty = entry
                    try:
                        qty_int = int(qty)
                    except ValueError:
                        raise ValueError(f"Quantity for resource {res} is not an integer: {qty}")
                    if header == 'INPUTS':
                        inputs[res] = qty_int
                    elif header == 'OUTPUTS':
                        outputs[res] = qty_int

        derived_name = None
        for res_name in outputs:
            if res_name != "Population" and not res_name.endswith("Waste"):
                derived_name = res_name
                break
        if derived_name is None:
            # fallback: use the dummy ast[1] or first output key
            derived_name = ast[1] if isinstance(ast[1], str) else next(iter(outputs), "TRANSFORM")
        return TransformTemplate(
            name=derived_name,
            inputs=inputs,
            outputs=outputs
        )


def tokenize(text: str) -> List[str]:
    """
    Tokenize a Lisp-like string into parentheses and atoms.
    """
    # Add spaces around parentheses, then split
    spaced = re.sub(r"([()])", r" \1 ", text)
    tokens = spaced.split()
    return tokens


def parse_tokens(tokens: List[str], pos: int = 0) -> Tuple[Union[List[Any], Token], int]:
    """
    Recursively parse tokens into nested lists.
    Returns (AST_node, next_position).
    """
    if pos >= len(tokens):
        raise ValueError("Unexpected end of token stream")

    token = tokens[pos]
    if token == '(':
        ast: List[Any] = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ')':
            node, pos = parse_tokens(tokens, pos)
            ast.append(node)
        if pos >= len(tokens):
            raise ValueError("Missing closing parenthesis")
        pos += 1  # skip ')'
        return ast, pos

    elif token == ')':
        raise ValueError(f"Unexpected closing parenthesis at position {pos}")

    else:
        # Atom: try int, else string
        try:
            return int(token), pos + 1
        except ValueError:
            return token, pos + 1


def parse_lisp(text: str) -> List[Any]:
    """
    Parse a full Lisp-like document into a list of ASTs.
    """
    tokens = tokenize(text)
    asts: List[Any] = []
    pos = 0
    while pos < len(tokens):
        node, pos = parse_tokens(tokens, pos)
        asts.append(node)
    return asts


def load_templates(file_path: Union[str, pathlib.Path]) -> Dict[str, TransformTemplate]:
    """
    Load all TRANSFORM templates from a file.

    Returns a dict mapping template name to TransformTemplate objects.
    """
    path = pathlib.Path(file_path)
    text = path.read_text()
    asts = parse_lisp(text)
    templates: Dict[str, TransformTemplate] = {}
    for ast in asts:
        if isinstance(ast, list) and len(ast) > 0 and isinstance(ast[0], str) and ast[0].upper() == 'TRANSFORM':
            tpl = TransformTemplate.from_lisp(ast)
            templates[tpl.name] = tpl
    return templates


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Parse TRANSFORM templates from a Lisp file.')
    parser.add_argument('input', help='Path to the transform templates file')
    parser.add_argument('-o', '--output', help='Optional output file to list parsed templates')
    args = parser.parse_args()

    templates = load_templates(args.input)
    for name, tpl in templates.items():
        print(f"Template: {name}")
        print(f"  Inputs: {tpl.inputs}")
        print(f"  Outputs: {tpl.outputs}\n")

    if args.output:
        out_path = pathlib.Path(args.output)
        with out_path.open('w') as f:
            for tpl in templates.values():
                f.write(f"{tpl.name}: inputs={tpl.inputs}, outputs={tpl.outputs}\n")
