from fractions import Fraction
import os
import subprocess
from enum import Enum

# ===================== COLORES =====================
class Colors:
    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    GREEN   = '\033[92m'
    BLUE    = '\033[94m'
    YELLOW  = '\033[93m'
    CYAN    = '\033[96m'
    RED     = '\033[91m'
    MAGENTA = '\033[95m'


# ===================== RESULTADO DEL SISTEMA =====================
class TipoSistema(Enum):
    UNICA_SOLUCION     = "única solución"
    SIN_SOLUCION       = "sin solución (inconsistente)"
    INFINITAS_SOLUCIONES = "infinitas soluciones (dependiente)"


class ResultadoGaussJordan:
    """Encapsula el resultado completo de una ejecución de Gauss-Jordan."""

    def __init__(self, tipo: TipoSistema, A_inicial, A_final=None, logger=None, solucion=None):
        self.tipo      = tipo
        self.A_inicial = A_inicial   # copia de la matriz original sin modificar
        self.A_final   = A_final
        self.logger    = logger
        self.solucion  = solucion    # lista de Fraction o None


# ===================== LOGGER =====================
class StepLogger:
    """Registra cada paso del proceso para exportación posterior."""

    def __init__(self):
        self.steps = []

    def add(self, title: str, matrix, operation: str = None):
        self.steps.append({
            'title':     title,
            'matrix':    [row[:] for row in matrix],
            'operation': operation,
        })


# ===================== PRESENTACIÓN =====================
def _calc_cell_width(rows) -> int:
    max_len = max(len(str(val)) for row in rows for val in row)
    return max(max_len, 4)


def print_matrix(mat, step: int = 0, title: str = "Matriz") -> None:
    """Imprime la matriz aumentada con alineación y separador visual."""
    print(f"\n{Colors.CYAN}{title} - Paso {step}:{Colors.RESET}")
    cw     = _calc_cell_width(mat)
    n_cols = len(mat[0])
    for row in mat:
        coef = " ".join(f"{str(val):>{cw}}" for val in row[:-1])
        last = f"{str(row[-1]):>{cw}}"
        print(f"    [ {coef} | {last} ]")
    print("    " + "-" * (2 + (cw + 1) * (n_cols - 1) + 2 + cw + 2))
    print()


def print_elimination_detail(fila_k, fila_i, multiplicador_elim, k: int, i: int, paso: int) -> None:
    """
    Muestra el detalle visual de una operación de eliminación.
    Solo imprime — no modifica ninguna matriz.
    """
    operation = f"Fila {k+1} = Fila {k+1} + [({multiplicador_elim}) * Fila {i+1}]"
    print(f"\n{Colors.YELLOW}Paso {paso}: {operation}{Colors.RESET}")

    n_cols    = len(fila_k)
    nueva_fila = [fila_k[j] + multiplicador_elim * fila_i[j] for j in range(n_cols)]
    fila_mult  = [multiplicador_elim * fila_i[j]             for j in range(n_cols)]

    todos = list(fila_k) + list(fila_i) + fila_mult + nueva_fila
    cw    = max(max(len(str(v)) for v in todos), 4)

    label1 = f"        Fila {k+1} ="
    label2 = f"{multiplicador_elim} * Fila {i+1} ="
    max_label = max(len(label1), len(label2))
    label1 = label1.rjust(max_label)
    label2 = label2.rjust(max_label)

    bracket_width = 2 + (cw + 1) * (n_cols - 1) + 2 + cw + 2

    def fmt_row(vals):
        coef = " ".join(f"{str(v):>{cw}}" for v in vals[:-1])
        last = f"{str(vals[-1]):>{cw}}"
        return f"[ {coef} | {last} ]"

    indent = "  "
    print(f"{indent}{label1} {fmt_row(fila_k)}")
    print(f"{indent}{label2} {fmt_row(fila_mult)}")
    print(f"{indent}{' ' * max_label} {'-' * bracket_width}")
    print(f"{indent}{label1} {fmt_row(nueva_fila)}")
    print("-" * (max_label + bracket_width + 8))
    print()


# ===================== ENTRADA DE DATOS =====================
def fraction_input(prompt: str) -> Fraction:
    """Lee un número entero o fracción desde consola, con reintento ante errores."""
    while True:
        try:
            val = input(prompt).strip()
            if '/' in val:
                parts = val.split('/')
                if len(parts) != 2:
                    raise ValueError("Fracción inválida")
                num, den = int(parts[0]), int(parts[1])
                if den == 0:
                    raise ZeroDivisionError("El denominador no puede ser cero")
                return Fraction(num, den)
            return Fraction(val)
        except (ValueError, ZeroDivisionError) as e:
            print(f"   Error: {e}. Ingrese número o fracción (ej: 1/2, 3, -4/5)")


def input_matrix(n: int) -> list:
    """Solicita al usuario una matriz aumentada NxN+1."""
    print(f"\n{Colors.BOLD}Ingrese la matriz aumentada ({n}x{n+1}):{Colors.RESET}")
    A = []
    for i in range(n):
        print(f"\nFila {i+1}:")
        fila = []
        for j in range(n + 1):
            etiqueta = f"b{i+1}" if j == n else f"a{i+1}{j+1}"
            fila.append(fraction_input(f"   {etiqueta} = "))
        A.append(fila)
    return A


# ===================== ALGORITMO GAUSS-JORDAN =====================
def gauss_jordan(A_input: list, verbose: bool = True) -> ResultadoGaussJordan:
    """
    Resuelve un sistema de ecuaciones lineales NxN por el método de Gauss-Jordan.

    Parámetros
    ----------
    A_input : list[list[Fraction]]
        Matriz aumentada NxN+1. No se modifica (se trabaja sobre una copia).
    verbose : bool
        Si True, imprime cada paso en consola.

    Retorna
    -------
    ResultadoGaussJordan con tipo, matriz inicial, matriz final, logger y solución.
    """
    # Validación básica
    n = len(A_input)
    if n == 0 or any(len(row) != n + 1 for row in A_input):
        raise ValueError(f"La matriz debe ser NxN+1. Se recibió una forma inválida.")

    # Copia profunda para no alterar la entrada
    A         = [[Fraction(v) for v in row] for row in A_input]
    A_inicial = [[Fraction(v) for v in row] for row in A_input]
    logger    = StepLogger()

    logger.add("Matriz Inicial", A)
    if verbose:
        print_matrix(A, 0, "Matriz Inicial")

    paso = 1

    for i in range(n):
        # ── Pivoteo parcial ──────────────────────────────────────────────────
        max_row = max(range(i, n), key=lambda k: abs(A[k][i]))
        if max_row != i:
            A[i], A[max_row] = A[max_row], A[i]
            if verbose:
                print(f"\n{Colors.BLUE}Paso {paso}: Intercambio fila {i+1} ↔ {max_row+1}{Colors.RESET}")
                print_matrix(A, paso, "Después de intercambio")
            logger.add(f"Paso {paso}: Intercambio fila {i+1} ↔ {max_row+1}", A)
            paso += 1

        # ── Detección de sistema singular ────────────────────────────────────
        if A[i][i] == 0:
            # Verificar si la fila es 0|b con b≠0 → sin solución
            # o 0|0 → infinitas soluciones
            tipo = (
                TipoSistema.SIN_SOLUCION
                if A[i][n] != 0
                else TipoSistema.INFINITAS_SOLUCIONES
            )
            if verbose:
                print(f"\n{Colors.RED}❌ Sistema {tipo.value}.{Colors.RESET}")
            return ResultadoGaussJordan(tipo, A_inicial, A, logger, solucion=None)

        # ── Normalización ────────────────────────────────────────────────────
        pivote       = A[i][i]
        multiplicador = Fraction(1, 1) / pivote
        A[i]         = [A[i][j] * multiplicador for j in range(n + 1)]

        if verbose:
            print(f"\n{Colors.BLUE}Paso {paso}: Fila {i+1} = Fila {i+1} * ({multiplicador}){Colors.RESET}")
            print_matrix(A, paso, "Después de normalizar")
        logger.add(f"Paso {paso}: Normalizar Fila {i+1}", A)
        paso += 1

        # ── Eliminación ──────────────────────────────────────────────────────
        for k in range(n):
            if k == i:
                continue
            factor           = A[k][i]
            multiplicador_elim = -factor
            if factor == 0:
                continue  # ya es cero, no hay nada que eliminar

            # Presentación (solo lee A[k] y A[i], no los modifica)
            if verbose:
                print_elimination_detail(A[k], A[i], multiplicador_elim, k, i, paso)

            # Modificación de la fila (separado de la presentación)
            A[k] = [A[k][j] + multiplicador_elim * A[i][j] for j in range(n + 1)]

            operation = f"Fila {k+1} = Fila {k+1} + [({multiplicador_elim}) * Fila {i+1}]"
            logger.add(f"Paso {paso}: {operation}", A, operation)
            paso += 1

    solucion = [A[i][n] for i in range(n)]
    return ResultadoGaussJordan(TipoSistema.UNICA_SOLUCION, A_inicial, A, logger, solucion)


# ===================== EXPORTACIÓN =====================
def _matrix_to_latex(mat) -> str:
    """Convierte una matriz a filas LaTeX de bmatrix."""
    n = len(mat[0]) - 1
    lines = ""
    for row in mat:
        coefs = " & ".join(str(row[j]) for j in range(n))
        lines += f"  {coefs} & \\Bigg| & {row[n]} \\\\\n"
    return lines


def generate_latex(resultado: ResultadoGaussJordan) -> str:
    """Genera el documento LaTeX completo a partir de un ResultadoGaussJordan."""
    n = len(resultado.A_inicial)

    latex = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{geometry}
\usepackage{booktabs}
\usepackage{xcolor}
\geometry{margin=2.5cm}
"""
    latex += f"\n\\title{{\\textbf{{Resolución por Gauss-Jordan ({n}x{n})}}}}\n"
    latex += r"""\author{}
\date{\today}
\begin{document}
\maketitle

\section{Matriz Inicial}
\[
\begin{bmatrix}
"""
    latex += _matrix_to_latex(resultado.A_inicial)
    latex += r"""\end{bmatrix}
\]

\section{Proceso Paso a Paso}
"""
    for step in resultado.logger.steps:
        latex += f"\n\\subsection*{{{step['title']}}}\n"
        if step.get('operation'):
            latex += f"\\textbf{{Operación:}} {step['operation']}\n\n"
        latex += "\\[\n\\begin{bmatrix}\n"
        latex += _matrix_to_latex(step['matrix'])
        latex += "\\end{bmatrix}\n\\]\n"

    latex += "\n\\section{Resultado}\n"
    if resultado.tipo == TipoSistema.UNICA_SOLUCION:
        latex += "\\begin{align*}\n"
        for idx, frac in enumerate(resultado.solucion):
            latex += f"  x_{{{idx+1}}} &= {frac} \\\\[6pt]\n"
        latex += "\\end{align*}\n"
    else:
        latex += f"El sistema no tiene solución única: \\textbf{{{resultado.tipo.value}}}.\n"

    latex += "\n\\end{document}\n"
    return latex


def save_files(resultado: ResultadoGaussJordan, output_text: str, choice: str) -> None:
    """
    Guarda los archivos de salida según la opción elegida.

    choice:
        '1' → solo TXT
        '2' → TXT + LaTeX
        '3' → TXT + LaTeX + PDF
    """
    n    = len(resultado.A_inicial)
    base = f"Gauss_Jordan_{n}x{n}"

    # TXT siempre
    txt_path = f"{base}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(output_text)
    print(f"{Colors.GREEN}✅ TXT guardado: {txt_path}{Colors.RESET}")

    if choice in ('2', '3'):
        tex_path = f"{base}.tex"
        latex_code = generate_latex(resultado)
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
        print(f"{Colors.GREEN}✅ LaTeX guardado: {tex_path}{Colors.RESET}")

        if choice == '3':
            try:
                print(f"{Colors.YELLOW}Compilando PDF...{Colors.RESET}")
                subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', tex_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                pdf_path = f"{base}.pdf"
                if os.path.exists(pdf_path):
                    print(f"{Colors.GREEN}✅ PDF generado: {pdf_path}{Colors.RESET}")
                else:
                    print(f"{Colors.YELLOW}⚠️  pdflatex no generó el PDF.{Colors.RESET}")
            except FileNotFoundError:
                print(f"{Colors.YELLOW}⚠️  pdflatex no está instalado.{Colors.RESET}")


# ===================== MAIN =====================
def main() -> None:
    output_lines = []

    def log(msg: str = ""):
        """Acumula texto para el TXT y lo imprime al mismo tiempo."""
        print(msg)
        # Guardamos sin códigos ANSI para el archivo de texto
        import re
        output_lines.append(re.sub(r'\033\[[0-9;]*m', '', msg))

    log(f"{Colors.BOLD}{Colors.BLUE}=== Gauss-Jordan NxN con Fracciones Exactas ==={Colors.RESET}")

    # ── Tamaño del sistema ───────────────────────────────────────────────────
    while True:
        try:
            n = int(input("\n¿Tamaño del sistema NxN? (ej: 3 para 3x3, 4 para 4x4): ").strip())
            if n < 2:
                print("   El tamaño mínimo es 2.")
                continue
            break
        except ValueError:
            print("   Error: ingrese un número entero.")

    # ── Modo de entrada ──────────────────────────────────────────────────────
    usar_ejemplo = input("¿Usar ejemplo predefinido? (s/n): ").strip().lower() == 's'

    EJEMPLOS = {
        2: [
            [Fraction(2),  Fraction(1),  Fraction(5)],
            [Fraction(1),  Fraction(-1), Fraction(1)],
        ],
        3: [
            [Fraction(2),  Fraction(1),  Fraction(-1), Fraction(8)],
            [Fraction(-3), Fraction(-1), Fraction(2),  Fraction(-11)],
            [Fraction(-2), Fraction(1),  Fraction(2),  Fraction(-3)],
        ],
        4: [
            [Fraction(10), Fraction(-4), Fraction(1), Fraction(0),  Fraction(-5)],
            [Fraction(-4), Fraction(9),  Fraction(0), Fraction(-3), Fraction(23)],
            [Fraction(1),  Fraction(0),  Fraction(5), Fraction(2),  Fraction(5)],
            [Fraction(0),  Fraction(-3), Fraction(2), Fraction(6),  Fraction(-3)],
        ],
    }

    if usar_ejemplo:
        if n in EJEMPLOS:
            A_input = EJEMPLOS[n]
            print(f"{Colors.GREEN}Usando ejemplo predefinido {n}x{n}.{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}No hay ejemplo predefinido para {n}x{n}. Ingrese la matriz manualmente.{Colors.RESET}")
            A_input = input_matrix(n)
    else:
        A_input = input_matrix(n)

    # ── Ejecución del algoritmo ──────────────────────────────────────────────
    resultado = gauss_jordan(A_input, verbose=True)

    # ── Mostrar resultado ────────────────────────────────────────────────────
    if resultado.tipo == TipoSistema.UNICA_SOLUCION:
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎯 SOLUCIÓN FINAL{Colors.RESET}")
        print("=" * 70)
        for idx, frac in enumerate(resultado.solucion):
            print(f"  x{idx+1} = {str(frac):>20}   ≈   {float(frac):.10f}")
    else:
        print(f"\n{Colors.RED}❌ El sistema tiene {resultado.tipo.value}.{Colors.RESET}")

    # ── Capturar salida acumulada para el TXT ────────────────────────────────
    # (La salida fue impresa en tiempo real; output_lines fue rellenado en paralelo)
    # Para el TXT usamos la salida visible que ya se imprimió.
    import io, sys
    # Reconstruimos el texto desde output_lines (ya sin ANSI)
    output_text = "\n".join(output_lines)

    # ── Guardar archivos ─────────────────────────────────────────────────────
    print(f"\n{Colors.MAGENTA}¿Guardar archivos?{Colors.RESET}")
    print("  1. Solo TXT")
    print("  2. TXT + LaTeX")
    print("  3. TXT + LaTeX + PDF")
    print("  0. No guardar")
    choice = input("Opción (0-3): ").strip()

    if choice in ('1', '2', '3'):
        save_files(resultado, output_text, choice)

    print(f"\n{Colors.BOLD}{Colors.GREEN}¡Listo!{Colors.RESET}")


if __name__ == "__main__":
    main()
