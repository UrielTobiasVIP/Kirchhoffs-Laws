from flask import Flask, request, jsonify, render_template
from fractions import Fraction
from gauss_jordan import gauss_jordan, TipoSistema

app = Flask(__name__)


def parse_fraction(value: str) -> Fraction:
    """Convierte string a Fraction. Acepta enteros, decimales y fracciones a/b."""
    value = value.strip()
    if not value:
        raise ValueError("Celda vacía")
    if '/' in value:
        parts = value.split('/')
        if len(parts) != 2:
            raise ValueError(f"Fracción inválida: {value}")
        num, den = int(parts[0]), int(parts[1])
        if den == 0:
            raise ValueError("Denominador cero")
        return Fraction(num, den)
    # Soporte para decimales: convertir a fracción exacta
    return Fraction(value).limit_denominator(10000)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/solve', methods=['POST'])
def solve():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Sin datos'}), 400

    try:
        n = int(data.get('n', 4))
        if n < 2 or n > 8:
            return jsonify({'error': 'El tamaño debe ser entre 2 y 8'}), 400

        raw = data.get('matrix', [])
        if len(raw) != n or any(len(row) != n + 1 for row in raw):
            return jsonify({'error': f'La matriz debe ser {n}x{n+1}'}), 400

        # Parsear a Fraction
        A = []
        for i, row in enumerate(raw):
            fila = []
            for j, val in enumerate(row):
                try:
                    fila.append(parse_fraction(str(val)))
                except Exception as e:
                    col_label = 'b' if j == n else f'a{i+1}{j+1}'
                    return jsonify({'error': f'Valor inválido en {col_label}: {e}'}), 400
            A.append(fila)

        resultado = gauss_jordan(A, verbose=False)

        # Construir respuesta
        response = {
            'tipo': resultado.tipo.value,
            'es_unica': resultado.tipo == TipoSistema.UNICA_SOLUCION,
        }

        if resultado.tipo == TipoSistema.UNICA_SOLUCION:
            response['solucion'] = [
                {
                    'fraccion': str(f),
                    'decimal': f'{float(f):.6f}',
                    'es_entera': f.denominator == 1,
                }
                for f in resultado.solucion
            ]

        # Pasos del logger
        pasos = []
        for step in resultado.logger.steps:
            mat_str = []
            for row in step['matrix']:
                mat_str.append([str(v) for v in row])
            pasos.append({
                'titulo':    step['title'],
                'operacion': step.get('operation') or '',
                'matriz':    mat_str,
            })
        response['pasos'] = pasos
        response['n'] = n

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
