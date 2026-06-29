import math
import re
import ast
import operator
from flask import Blueprint, render_template, request, jsonify, url_for, session

calculator_bp = Blueprint('calculator', __name__, 
                          template_folder='templates', 
                          static_folder='static')

# -----------------------------------------------------------------------------
# Safe AST Evaluator
# -----------------------------------------------------------------------------

class SafeMathEvaluator:
    # Supported operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: lambda x: x
    }

    # Supported math functions
    FUNCTIONS = {
        'math.sin': math.sin,
        'math.cos': math.cos,
        'math.tan': math.tan,
        'math.asin': math.asin,
        'math.acos': math.acos,
        'math.atan': math.atan,
        'math.log10': math.log10,
        'math.log': math.log,
        'math.exp': math.exp,
        'math.sqrt': math.sqrt,
        'math.radians': math.radians,
        'math.degrees': math.degrees
    }

    # Supported math constants
    CONSTANTS = {
        'math.pi': math.pi,
        'math.e': math.e
    }

    @classmethod
    def evaluate(cls, expression: str):
        try:
            tree = ast.parse(expression, mode='eval')
            return cls._eval(tree.body)
        except Exception as e:
            raise ValueError(f"Invalid math expression: {e}")

    @classmethod
    def _eval(cls, node):
        if hasattr(ast, 'Constant') and isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif hasattr(ast, 'Num') and isinstance(node, getattr(ast, 'Num')):  # Python < 3.8 fallback
            return node.n
        elif isinstance(node, ast.BinOp):
            left = cls._eval(node.left)
            right = cls._eval(node.right)
            op_type = type(node.op)
            if op_type in cls.OPERATORS:
                return cls.OPERATORS[op_type](left, right)
            raise TypeError(f"Unsupported binary operator: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            operand = cls._eval(node.operand)
            op_type = type(node.op)
            if op_type in cls.OPERATORS:
                return cls.OPERATORS[op_type](operand)
            raise TypeError(f"Unsupported unary operator: {op_type}")
        elif isinstance(node, ast.Call):
            func_name = cls._get_func_name(node.func)
            if func_name in cls.FUNCTIONS:
                args = [cls._eval(arg) for arg in node.args]
                return cls.FUNCTIONS[func_name](*args)
            raise NameError(f"Unsupported function: {func_name}")
        elif isinstance(node, ast.Attribute):
            name = cls._get_func_name(node)
            if name in cls.CONSTANTS:
                return cls.CONSTANTS[name]
            raise NameError(f"Unsupported attribute: {name}")
        elif isinstance(node, ast.Name):
            if node.id in cls.CONSTANTS:
                return cls.CONSTANTS[node.id]
            raise NameError(f"Unsupported name: {node.id}")
        else:
            raise TypeError(f"Unsupported node type: {type(node)}")

    @classmethod
    def _get_func_name(cls, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{cls._get_func_name(node.value)}.{node.attr}"
        raise TypeError("Could not resolve function name")

# -----------------------------------------------------------------------------
# Business Logic: Calculation Parser
# -----------------------------------------------------------------------------

class CalculationParser:
    """
    Handles the parsing and evaluation of mathematical expressions.
    Provides support for basic arithmetic, trigonometry, and constants.
    """

    # Allowed characters to prevent malicious code execution via eval()
    ALLOWED_CHARS = "0123456789.+-*/()%^√πe sintgloarcexpn"

    @staticmethod
    def evaluate(expression: str):
        """
        Parses and evaluates a mathematical expression string.
        
        Args:
            expression (str): The mathematical expression to evaluate.
            
        Returns:
            The numeric result (int/float) or an error message (str).
        """
        # 1. Validate input for unauthorized characters
        if any(char not in CalculationParser.ALLOWED_CHARS for char in expression.lower()):
            return "Error: Invalid characters detected."

        try:
            # 2. Normalize operators (e.g., ^ to **)
            clean_expr = expression.replace("^", "**")

            # 3. Handle Square Root (√)
            # Example: √16 -> math.sqrt(16)
            while "√" in clean_expr:
                pos = clean_expr.find("√")
                # Extract the number following the symbol
                num_match = re.search(r"(\d+(\.\d+)?)", clean_expr[pos+1:])
                if not num_match:
                    return "Error: Invalid root expression."
                
                number = num_match.group(0)
                full_match = "√" + number
                clean_expr = clean_expr.replace(full_match, f"math.sqrt({number})", 1)

            # 4. Handle Percentage (%)
            # Example: 50% -> (50/100)
            clean_expr = re.sub(r"(\d+(\.\d+)?)%", r"(\1/100)", clean_expr)

            # 5. Replace Constants
            clean_expr = clean_expr.replace("π", "math.pi").replace("e", "math.e")

            # 6. Map Mathematical Functions to math module
            # We use regex to wrap arguments in math.radians for trig functions
            function_map = {
                r"sin\(([^)]+)\)": r"math.sin(math.radians(\1))",
                r"cos\(([^)]+)\)": r"math.cos(math.radians(\1))",
                r"tan\(([^)]+)\)": r"math.tan(math.radians(\1))",
                r"log\(([^)]+)\)": r"math.log10(\1)",
                r"ln\(([^)]+)\)": r"math.log(\1)",
                r"exp\(([^)]+)\)": r"math.exp(\1)",
                r"arcsin\(([^)]+)\)": r"math.degrees(math.asin(\1))",
                r"arccos\(([^)]+)\)": r"math.degrees(math.acos(\1))",
                r"arctan\(([^)]+)\)": r"math.degrees(math.atan(\1))"
            }

            for pattern, replacement in function_map.items():
                clean_expr = re.sub(pattern, replacement, clean_expr)

            # 7. Evaluate the sanitized expression
            result = SafeMathEvaluator.evaluate(clean_expr)

            # 8. Post-processing
            if isinstance(result, float):
                # Round to 4 decimal places for cleaner output
                return round(result, 4)
            return result

        except ZeroDivisionError:
            return "Error: Division by zero."
        except Exception as e:
            # General error fallback
            return f"Error: {str(e)}"

# -----------------------------------------------------------------------------
# Data Management: History Store
# -----------------------------------------------------------------------------

class HistoryManager:
    """
    Manages a list of past calculations stored in the user's session.
    Ensures calculations persist in stateless environments like CGI.
    """
    @property
    def entries(self):
        if 'calc_history' not in session:
            session['calc_history'] = []
        return session['calc_history']

    def add(self, expression, result):
        """Adds a new calculation entry to the list."""
        history_list = list(self.entries)
        history_list.append({
            "expression": expression,
            "result": result
        })
        # Keep only the last 20 entries to prevent session cookie size limit issues
        session['calc_history'] = history_list[-20:]

    def get_all(self):
        """Returns the full list of calculation history."""
        return self.entries[::-1]

    def clear(self):
        """Clears all entries from history."""
        session['calc_history'] = []

# Initialize global instances
history = HistoryManager()

# -----------------------------------------------------------------------------
# Web Routes
# -----------------------------------------------------------------------------

@calculator_bp.route("/")
def index():
    """Renders the main calculator interface."""
    return render_template("index.html")

@calculator_bp.route("/calculate", methods=["POST"])
def calculate():
    """
    Endpoint for evaluating expressions.
    Expects JSON: { "expression": "1+1" }
    """
    data = request.get_json()
    expression = data.get("expression", "")
    
    if not expression:
        return jsonify({"error": "No expression provided"}), 400

    result = CalculationParser.evaluate(expression)
    
    # Only store successful numeric results in history
    if not str(result).startswith("Error"):
        history.add(expression, result)

    return jsonify({
        "expression": expression,
        "result": result
    })

@calculator_bp.route("/history", methods=["GET"])
def get_history():
    """Returns the current calculation history."""
    return jsonify(history.get_all())

@calculator_bp.route("/clear_history", methods=["POST"])
def clear_history():
    """Wipes the calculation history."""
    history.clear()
    return jsonify({"status": "History cleared"})
