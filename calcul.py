import tkinter as tk
from tkinter import messagebox, simpledialog
import ast
import math
import operator
import statistics
import re

# Casio fx-991ES PLUS-inspired educational calculator.
# This is an original Python/Tkinter recreation, not an official Casio product.

BG = "#d8d9d4"
KEY = "#f1f2ec"
DARK = "#202522"
BLUE = "#52677f"
ORANGE = "#b56a24"
SCREEN = "#b8d0c7"

BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}
UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


class SafeMath:
    """Evaluate a restricted set of mathematical expressions without eval()."""

    def __init__(self, calculator):
        self.calculator = calculator

    def _functions(self):
        calc = self.calculator

        def angle(x):
            return math.radians(x) if calc.degrees else x

        def inverse_angle(x):
            value = math.asin(x)
            return math.degrees(value) if calc.degrees else value

        def inverse_cos(x):
            value = math.acos(x)
            return math.degrees(value) if calc.degrees else value

        def inverse_tan(x):
            value = math.atan(x)
            return math.degrees(value) if calc.degrees else value

        def factorial(x):
            if not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0 or int(x) != x:
                raise ValueError("Factorial requires a non-negative whole number.")
            return math.factorial(int(x))

        def npr(n, r):
            n, r = int(n), int(r)
            if n < 0 or r < 0 or r > n:
                raise ValueError("nPr requires whole numbers with 0 <= r <= n.")
            return math.factorial(n) // math.factorial(n - r)

        def ncr(n, r):
            n, r = int(n), int(r)
            if n < 0 or r < 0 or r > n:
                raise ValueError("nCr requires whole numbers with 0 <= r <= n.")
            return math.comb(n, r)

        return {
            "sqrt": math.sqrt,
            "sin": lambda x: math.sin(angle(x)),
            "cos": lambda x: math.cos(angle(x)),
            "tan": lambda x: math.tan(angle(x)),
            "asin": inverse_angle,
            "acos": inverse_cos,
            "atan": inverse_tan,
            "log": math.log10,
            "log10": math.log10,
            "ln": math.log,
            "log2": math.log2,
            "abs": abs,
            "exp": math.exp,
            "factorial": factorial,
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "floor": math.floor,
            "ceil": math.ceil,
            "nPr": npr,
            "nCr": ncr,
        }

    def evaluate(self, expression):
        expression = expression.strip()
        if not expression:
            raise ValueError("Enter a calculation first.")
        expression = (expression.replace("π", "pi").replace("×", "*")
                      .replace("÷", "/").replace("−", "-").replace("^", "**"))
        # Convert simple postfix factorials, e.g. 5! or (3+2)!.
        expression = re.sub(r"(?<![A-Za-z_])([0-9]+(?:\.[0-9]+)?)!", r"factorial(\1)", expression)
        functions = self._functions()
        constants = {
            "pi": math.pi,
            "e": math.e,
            "Ans": self.calculator.ans,
            "ans": self.calculator.ans,
            "M": self.calculator.memory,
        }
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise ValueError("Check the expression. You may have missed a number, operator, or bracket.") from exc

        def walk(node):
            if isinstance(node, ast.Expression):
                return walk(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return node.value
            if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
                left, right = walk(node.left), walk(node.right)
                if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                    raise ValueError("Exponent is too large for this calculator.")
                return BIN_OPS[type(node.op)](left, right)
            if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
                return UNARY_OPS[type(node.op)](walk(node.operand))
            if isinstance(node, ast.Name) and node.id in constants:
                return constants[node.id]
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in functions and not node.keywords):
                args = [walk(arg) for arg in node.args]
                return functions[node.func.id](*args)
            raise ValueError("Unsupported expression. Use the calculator's mathematical functions.")

        return walk(tree)


class ScientificCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Scientific Calculator - fx-991ES PLUS Style")
        # Fit the entire calculator to the available desktop height.
        # The previous fixed 800 px height could hide the bottom keys on laptops.
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = min(540, max(430, screen_w - 50))
        win_h = min(700, max(540, screen_h - 100))
        x = max(0, (screen_w - win_w) // 2)
        y = max(0, (screen_h - win_h) // 2)
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.minsize(430, 540)
        self.root.configure(bg=BG)
        self.expression = tk.StringVar()
        self.status = tk.StringVar(value="DEG  |  SCIENTIFIC CALCULATOR")
        self.degrees = True
        self.ans = 0
        self.memory = 0
        self.shift = False
        self.engine = SafeMath(self)
        self._build()
        self.root.bind("<Return>", lambda _event: self.calculate())
        self.root.bind("<KP_Enter>", lambda _event: self.calculate())
        self.root.bind("<Escape>", lambda _event: self.clear())
        self.root.bind("<BackSpace>", lambda _event: self.delete())

    def _build(self):
        top = tk.Frame(self.root, bg=BG, padx=12, pady=5)
        top.pack(fill="x")
        tk.Label(top, text="CASIO", font=("Arial", 18, "bold"), bg=BG, fg="#313832").pack(anchor="w")
        tk.Label(top, text="fx-991ES PLUS  |  NATURAL-V.P.A.M.", font=("Arial", 9, "bold"), bg=BG, fg="#3d6c58").pack(anchor="w")
        tk.Label(top, text="TWO WAY POWER  •  SCIENTIFIC", font=("Arial", 7), bg=BG, fg="#4c514d").pack(anchor="e")

        frame = tk.Frame(self.root, bg="#a9b1a9", padx=5, pady=5, relief="sunken", bd=2)
        frame.pack(fill="x", padx=14, pady=(0, 5))
        tk.Label(frame, textvariable=self.status, anchor="w", bg=SCREEN, fg="#345248", font=("Consolas", 8), padx=7).pack(fill="x")
        self.display = tk.Entry(frame, textvariable=self.expression, justify="right", font=("Consolas", 18), bg=SCREEN, fg="#182b26", relief="flat", bd=0, insertbackground="#182b26")
        self.display.pack(fill="x", ipady=7, padx=4, pady=(2, 3))

        pad = tk.Frame(self.root, bg=BG, padx=9, pady=1)
        pad.pack(fill="both", expand=True)
        layout = [
            [("SHIFT", self.toggle_shift, BLUE), ("ALPHA", self.alpha_info, BLUE), ("REPLAY", self.replay, BLUE), ("DRG", self.toggle_angle, BLUE), ("ON", self.clear, BLUE)],
            [("CALC", self.calculate, DARK), ("∫ / d/dx", self.advanced_calculus, DARK), ("x⁻¹", lambda: self.insert("**(-1)"), DARK), ("log□", lambda: self.insert("log("), DARK), ("ln", lambda: self.insert("ln("), DARK)],
            [("a/b", lambda: self.insert("/"), DARK), ("√", lambda: self.insert("sqrt("), DARK), ("x²", lambda: self.insert("**2"), DARK), ("xʸ", lambda: self.insert("**"), DARK), ("log", lambda: self.insert("log("), DARK)],
            [("(−)", lambda: self.insert("-"), DARK), ("hyp", self.hyperbolic_info, DARK), ("sin", lambda: self.trig("sin"), DARK), ("cos", lambda: self.trig("cos"), DARK), ("tan", lambda: self.trig("tan"), DARK)],
            [("x!", lambda: self.insert("factorial("), DARK), ("nPr", lambda: self.insert("nPr("), DARK), ("nCr", lambda: self.insert("nCr("), DARK), ("π", lambda: self.insert("pi"), DARK), ("e", lambda: self.insert("e"), DARK)],
            [("RCL", self.recall_memory, DARK), ("ENG", self.engineering, DARK), ("(", lambda: self.insert("("), DARK), (")", lambda: self.insert(")"), DARK), ("M+", self.memory_add, DARK)],
            [("7", lambda: self.insert("7"), KEY), ("8", lambda: self.insert("8"), KEY), ("9", lambda: self.insert("9"), KEY), ("DEL", self.delete, ORANGE), ("AC", self.clear, ORANGE)],
            [("4", lambda: self.insert("4"), KEY), ("5", lambda: self.insert("5"), KEY), ("6", lambda: self.insert("6"), KEY), ("×", lambda: self.insert("*"), KEY), ("÷", lambda: self.insert("/"), KEY)],
            [("1", lambda: self.insert("1"), KEY), ("2", lambda: self.insert("2"), KEY), ("3", lambda: self.insert("3"), KEY), ("+", lambda: self.insert("+"), KEY), ("−", lambda: self.insert("-"), KEY)],
            [("0", lambda: self.insert("0"), KEY), (".", lambda: self.insert("."), KEY), ("EXP", lambda: self.insert("*10**"), KEY), ("Ans", lambda: self.insert("Ans"), KEY), ("=", self.calculate, BLUE)],
            [("SOLVE", self.solve_dialog, BLUE), ("MATRIX", self.matrix_dialog, BLUE), ("STAT", self.stats_dialog, BLUE), ("BASE", self.base_dialog, BLUE), ("M−", self.memory_subtract, DARK)],
        ]
        for r, row in enumerate(layout):
            pad.grid_rowconfigure(r, weight=1, uniform="row")
            for c, (label, command, color) in enumerate(row):
                pad.grid_columnconfigure(c, weight=1, uniform="col")
                fg = "white" if color in (DARK, BLUE, ORANGE) else "#242824"
                button = tk.Button(pad, text=label, command=command, bg=color, fg=fg,
                                   activebackground="#d0d4ce", activeforeground="#111111",
                                   font=("Arial", 9 if len(label) > 4 else 11, "bold"),
                                   relief="raised", bd=1, cursor="hand2")
                button.grid(row=r, column=c, sticky="nsew", padx=2, pady=2, ipadx=0, ipady=1)
        tk.Label(self.root, text="Enter = calculate  •  Esc = clear  •  sin(30), sqrt(144), 5!", bg=BG, fg="#555b55", font=("Arial", 7)).pack(pady=(1, 4))

    def insert(self, text):
        self.display.focus_set()
        try:
            start, end = self.display.index(tk.SEL_FIRST), self.display.index(tk.SEL_LAST)
            self.display.delete(start, end)
            self.display.insert(start, text)
        except tk.TclError:
            self.display.insert(self.display.index(tk.INSERT), text)
        self.shift = False

    def clear(self):
        self.expression.set("")
        self.status.set(("DEG" if self.degrees else "RAD") + "  |  SCIENTIFIC CALCULATOR")
        self.display.focus_set()

    def delete(self):
        try:
            start, end = self.display.index(tk.SEL_FIRST), self.display.index(tk.SEL_LAST)
            self.display.delete(start, end)
        except tk.TclError:
            pos = self.display.index(tk.INSERT)
            if pos > 0:
                self.display.delete(pos - 1, pos)

    @staticmethod
    def format_result(result):
        if isinstance(result, float):
            if not math.isfinite(result):
                raise ValueError("Result is not finite.")
            if abs(result) < 1e-12:
                result = 0.0
            if abs(result - round(result)) < 1e-10 and abs(result) < 1e14:
                return str(int(round(result)))
            return f"{result:.12g}"
        return str(result)

    def calculate(self):
        expr = self.expression.get().strip()
        if not expr:
            return
        try:
            result = self.engine.evaluate(expr)
            self.ans = result
            self.expression.set(self.format_result(result))
            self.status.set("ANSWER SAVED TO Ans  |  " + ("DEG" if self.degrees else "RAD"))
            self.display.icursor(tk.END)
        except ZeroDivisionError:
            messagebox.showerror("Math Error", "You cannot divide by zero.")
        except (ValueError, TypeError, OverflowError) as exc:
            messagebox.showerror("Calculation Error", str(exc) or "Please check the expression.")
        except Exception:
            messagebox.showerror("Input Error", "Please check the expression and try again.")

    def trig(self, name):
        if self.shift:
            self.insert({"sin": "asin(", "cos": "acos(", "tan": "atan("}[name])
            self.shift = False
        else:
            self.insert(name + "(")

    def toggle_angle(self):
        self.degrees = not self.degrees
        self.status.set(("DEG" if self.degrees else "RAD") + "  |  SCIENTIFIC CALCULATOR")

    def toggle_shift(self):
        self.shift = not self.shift
        self.status.set("SHIFT ON: sin/cos/tan become inverse functions" if self.shift else ("DEG" if self.degrees else "RAD") + "  |  SCIENTIFIC CALCULATOR")

    def alpha_info(self):
        messagebox.showinfo("ALPHA", "Use π, e, Ans and M for constants, previous answer and memory.")

    def hyperbolic_info(self):
        messagebox.showinfo("Hyperbolic functions", "Type one of these into the display:\nsinh(1)\ncosh(1)\ntanh(1)")

    def replay(self):
        self.display.icursor(tk.END)
        self.display.focus_set()

    def _eval_x(self, expression, x):
        expression = re.sub(r"\bx\b", f"({repr(float(x))})", expression)
        return self.engine.evaluate(expression)

    def memory_add(self):
        try:
            self.memory += self.engine.evaluate(self.expression.get())
            self.status.set(f"M = {self.format_result(self.memory)}")
        except Exception as exc:
            messagebox.showerror("Memory", f"Enter a valid expression first.\n{exc}")

    def memory_subtract(self):
        try:
            self.memory -= self.engine.evaluate(self.expression.get())
            self.status.set(f"M = {self.format_result(self.memory)}")
        except Exception as exc:
            messagebox.showerror("Memory", f"Enter a valid expression first.\n{exc}")

    def recall_memory(self):
        self.insert("M")

    def engineering(self):
        try:
            value = float(self.engine.evaluate(self.expression.get()))
            exponent = int(math.floor(math.log10(abs(value)) / 3) * 3) if value else 0
            self.expression.set(f"{value / (10 ** exponent):.10g}*10**{exponent}")
        except Exception as exc:
            messagebox.showerror("Engineering notation", str(exc))

    def advanced_calculus(self):
        choice = simpledialog.askstring("Calculus", "Type INTEGRAL or DERIVATIVE:")
        if not choice:
            return
        if choice.strip().lower().startswith("i"):
            self.integral_dialog()
        elif choice.strip().lower().startswith("d"):
            self.derivative_dialog()
        else:
            messagebox.showinfo("Calculus", "Please enter INTEGRAL or DERIVATIVE.")

    def solve_dialog(self):
        kind = simpledialog.askinteger("Equation solver", "Choose 1 for a*x + b = 0, or 2 for a*x² + b*x + c = 0:", minvalue=1, maxvalue=2)
        if kind is None:
            return
        try:
            a = simpledialog.askfloat("Equation solver", "Coefficient a:")
            if a is None: return
            b = simpledialog.askfloat("Equation solver", "Coefficient b:")
            if b is None: return
            if kind == 1:
                if a == 0: raise ValueError("Coefficient a cannot be zero.")
                messagebox.showinfo("Solution", f"x = {self.format_result(-b / a)}")
            else:
                c = simpledialog.askfloat("Equation solver", "Coefficient c:")
                if c is None: return
                if a == 0: raise ValueError("For a quadratic equation, coefficient a cannot be zero.")
                disc = b*b - 4*a*c
                if disc < 0:
                    root = math.sqrt(-disc)
                    x1 = complex(-b / (2*a), root / (2*a))
                    x2 = complex(-b / (2*a), -root / (2*a))
                    messagebox.showinfo("Solutions", f"x1 = {x1}\nx2 = {x2}")
                else:
                    x1, x2 = (-b + math.sqrt(disc)) / (2*a), (-b - math.sqrt(disc)) / (2*a)
                    messagebox.showinfo("Solutions", f"x1 = {self.format_result(x1)}\nx2 = {self.format_result(x2)}")
        except Exception as exc:
            messagebox.showerror("Equation solver", str(exc))

    def integral_dialog(self):
        expression = simpledialog.askstring("Numerical integration", "Enter f(x), for example x**2 or sin(x):")
        if not expression: return
        lo = simpledialog.askfloat("Numerical integration", "Lower limit:")
        if lo is None: return
        hi = simpledialog.askfloat("Numerical integration", "Upper limit:")
        if hi is None: return
        try:
            n = 4000
            h = (hi - lo) / n
            total = self._eval_x(expression, lo) + self._eval_x(expression, hi)
            for i in range(1, n):
                total += (4 if i % 2 else 2) * self._eval_x(expression, lo + i*h)
            result = total * h / 3
            self.ans = result
            messagebox.showinfo("Integral result", f"Numerical result ≈ {result:.12g}\n(Simpson's rule)")
        except Exception as exc:
            messagebox.showerror("Integration error", str(exc))

    def derivative_dialog(self):
        expression = simpledialog.askstring("Numerical derivative", "Enter f(x), for example x**2:")
        if not expression: return
        x = simpledialog.askfloat("Numerical derivative", "Calculate f'(x) at x =")
        if x is None: return
        try:
            h = 1e-5 * max(1, abs(x))
            result = (self._eval_x(expression, x+h) - self._eval_x(expression, x-h)) / (2*h)
            self.ans = result
            messagebox.showinfo("Derivative result", f"f'({x}) ≈ {result:.12g}")
        except Exception as exc:
            messagebox.showerror("Derivative error", str(exc))

    def matrix_dialog(self):
        try:
            raw_a = simpledialog.askstring("Matrix A", "Enter four values for 2×2 matrix A, comma-separated:")
            if not raw_a: return
            raw_b = simpledialog.askstring("Matrix B", "Enter four values for 2×2 matrix B, comma-separated:")
            if not raw_b: return
            A = [float(v.strip()) for v in raw_a.split(",")]
            B = [float(v.strip()) for v in raw_b.split(",")]
            if len(A) != 4 or len(B) != 4:
                raise ValueError("Enter exactly four values for each matrix.")
            op = simpledialog.askstring("Matrix operation", "Choose +, -, *, detA, or invA:")
            if not op: return
            if op in ("+", "-"):
                values = [x+y if op == "+" else x-y for x, y in zip(A, B)]
            elif op == "*":
                values = [A[0]*B[0]+A[1]*B[2], A[0]*B[1]+A[1]*B[3], A[2]*B[0]+A[3]*B[2], A[2]*B[1]+A[3]*B[3]]
            elif op.lower() == "deta":
                messagebox.showinfo("Matrix result", f"det(A) = {A[0]*A[3]-A[1]*A[2]}")
                return
            elif op.lower() == "inva":
                det = A[0]*A[3]-A[1]*A[2]
                if det == 0: raise ValueError("Matrix A has no inverse because its determinant is zero.")
                values = [A[3]/det, -A[1]/det, -A[2]/det, A[0]/det]
            else:
                raise ValueError("Choose +, -, *, detA, or invA.")
            messagebox.showinfo("Matrix result", f"[[{values[0]:g}, {values[1]:g}],\n [{values[2]:g}, {values[3]:g}]]")
        except Exception as exc:
            messagebox.showerror("Matrix error", str(exc))

    def stats_dialog(self):
        raw = simpledialog.askstring("Statistics", "Enter numbers separated by commas:")
        if not raw: return
        try:
            values = [float(v.strip()) for v in raw.split(",")]
            if not values: return
            lines = [f"Count = {len(values)}", f"Sum = {sum(values)}", f"Mean = {statistics.mean(values)}", f"Median = {statistics.median(values)}", f"Minimum = {min(values)}", f"Maximum = {max(values)}"]
            if len(values) > 1:
                lines += [f"Sample SD = {statistics.stdev(values)}", f"Population SD = {statistics.pstdev(values)}"]
            messagebox.showinfo("Statistics results", "\n".join(lines))
        except Exception as exc:
            messagebox.showerror("Statistics error", str(exc))

    def base_dialog(self):
        raw = simpledialog.askstring("Base conversion", "Enter an integer in decimal (base 10):")
        if raw is None: return
        try:
            value = int(raw.strip())
            sign = "-" if value < 0 else ""
            value = abs(value)
            messagebox.showinfo("Base conversion", f"DEC: {sign}{value}\nBIN: {sign}{bin(value)[2:]}\nOCT: {sign}{oct(value)[2:]}\nHEX: {sign}{hex(value)[2:].upper()}")
        except Exception as exc:
            messagebox.showerror("Base conversion", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    app = ScientificCalculator(root)
    root.mainloop()
