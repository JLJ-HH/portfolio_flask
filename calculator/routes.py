import math
import re
from flask import Blueprint, render_template, request, jsonify, url_for

calculator_bp = Blueprint('calculator', __name__, 
                          template_folder='templates', 
                          static_folder='static')

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
            # Note: eval() is used for simplicity but with strict character filtering
            result = eval(clean_expr, {"__builtins__": {}}, {"math": math})

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
    Manages a simple in-memory list of past calculations.
    """
    def __init__(self):
        self.entries = []

    def add(self, expression, result):
        """Adds a new calculation entry to the list."""
        self.entries.append({
            "expression": expression,
            "result": result
        })

    def get_all(self):
        """Returns the full list of calculation history."""
        return self.entries[::-1]  # Return reversed for 'newest first'

    def clear(self):
        """Clears all entries from history."""
        self.entries = []

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
