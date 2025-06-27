# optimizacion.py

import pulp
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# Se eliminan webbrowser y Timer, ya que no son necesarios para el despliegue en Vercel
# y la lógica de robustez se centra en la API.

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# --- AÑADIDO: Constantes de configuración para límites de seguridad ---
# Se definen límites para evitar que solicitudes con datos masivos puedan
# degradar el rendimiento del servidor o causar un consumo excesivo de memoria.
MAX_AULAS = 200
MAX_GRUPOS = 200
MAX_HORARIOS = 50
MAX_CAPACIDAD = 1000
MAX_TAMANO_GRUPO = 1000


@app.route('/')
def home():
    return render_template('index.html')


# La función de optimización no necesita cambios, ya que ahora las validaciones
# se hacen antes de llamarla.
def resolver_asignacion(datos_aulas, datos_grupos, datos_horarios, datos_parametros):
    # (El código interno de esta función permanece igual)
    aulas_cap = [a['capacidad'] for a in datos_aulas]
    grupos_est = [g['tamano'] for g in datos_grupos]
    horarios_str = [h for h in datos_horarios]

    delta_porcentaje = datos_parametros.get('delta', 0.20)
    lambda_penalizacion = datos_parametros.get('lambda', 1.0)

    I = range(len(datos_grupos))
    J = range(len(datos_aulas))
    T = range(len(horarios_str))

    modelo = pulp.LpProblem("Asignacion_Aulas_Web", pulp.LpMaximize)

    x = pulp.LpVariable.dicts("x", (I, J, T), cat=pulp.LpBinary)
    U = pulp.LpVariable.dicts("U", (I, J, T), lowBound=0, cat=pulp.LpContinuous)

    estudiantes_asignados = pulp.lpSum(grupos_est[i] * x[i][j][t] for i in I for j in J for t in T)
    penalizacion_total = pulp.lpSum(lambda_penalizacion * U[i][j][t] for i in I for j in J for t in T)
    modelo += estudiantes_asignados - penalizacion_total, "PuntajeTotal"

    for i in I:
        modelo += pulp.lpSum(x[i][j][t] for j in J for t in T) == 1, f"AsigUnica_{i}"
    for j in J:
        for t in T:
            modelo += pulp.lpSum(x[i][j][t] for i in I) <= 1, f"OcupAula_{j}_{t}"
    for i in I:
        for j in J:
            for t in T:
                modelo += grupos_est[i] * x[i][j][t] <= aulas_cap[j] * x[i][j][t], f"Capacidad_{i}_{j}_{t}"
    for i in I:
        for j in J:
            for t in T:
                capacidad_aula = aulas_cap[j]
                estudiantes_grupo = grupos_est[i]
                umbral_absoluto = delta_porcentaje * capacidad_aula
                modelo += U[i][j][t] >= (capacidad_aula - estudiantes_grupo - umbral_absoluto) * x[i][j][
                    t], f"Penalizacion_{i}_{j}_{t}"

    modelo.solve()

    resultados = []
    valor_objetivo = None
    if pulp.LpStatus[modelo.status] == 'Optimal':
        valor_objetivo = pulp.value(modelo.objective)
        for i in I:
            for j in J:
                for t in T:
                    if pulp.value(x[i][j][t]) > 0.99:
                        nombre_grupo = datos_grupos[i]['nombre']
                        nombre_aula = datos_aulas[j]['nombre']
                        horario = horarios_str[t]
                        resultado = f"{nombre_grupo} -> {nombre_aula} -> {horario}"
                        resultados.append(resultado)

    return {"estado": pulp.LpStatus[modelo.status], "valor_objetivo": valor_objetivo, "resultados": resultados}


@app.route('/solve', methods=['POST'])
def solve_endpoint():
    try:
        datos_entrada = request.get_json()

        # --- MODIFICACIÓN: Bloque de validación exhaustiva ---
        if not datos_entrada:
            return jsonify({"error": "No se recibieron datos en la solicitud."}), 400

        # --- Validación de Aulas ---
        aulas_validadas = []
        if 'aulas' not in datos_entrada or not isinstance(datos_entrada['aulas'], list):
            return jsonify({"error": "El campo 'aulas' es inválido o no existe."}), 400
        if len(datos_entrada['aulas']) > MAX_AULAS:
            return jsonify({"error": f"Se exedió el número máximo de aulas permitidas ({MAX_AULAS})."}), 400
        for aula in datos_entrada['aulas']:
            nombre = aula.get('nombre', '').strip()
            capacidad = aula.get('capacidad')
            if not nombre: continue  # Ignora aulas sin nombre
            if not isinstance(capacidad, int) or not (0 < capacidad <= MAX_CAPACIDAD):
                return jsonify({
                                   "error": f"La capacidad del aula '{nombre}' debe ser un número entero positivo menor o igual a {MAX_CAPACIDAD}."}), 400
            aulas_validadas.append({'nombre': nombre, 'capacidad': capacidad})

        # --- Validación de Grupos ---
        grupos_validados = []
        if 'grupos' not in datos_entrada or not isinstance(datos_entrada['grupos'], list):
            return jsonify({"error": "El campo 'grupos' es inválido o no existe."}), 400
        if len(datos_entrada['grupos']) > MAX_GRUPOS:
            return jsonify({"error": f"Se exedió el número máximo de grupos permitidos ({MAX_GRUPOS})."}), 400
        for grupo in datos_entrada['grupos']:
            nombre = grupo.get('nombre', '').strip()
            tamano = grupo.get('tamano')
            if not nombre: continue  # Ignora grupos sin nombre
            if not isinstance(tamano, int) or not (0 < tamano <= MAX_TAMANO_GRUPO):
                return jsonify({
                                   "error": f"El tamaño del grupo '{nombre}' debe ser un número entero positivo menor o igual a {MAX_TAMANO_GRUPO}."}), 400
            grupos_validados.append({'nombre': nombre, 'tamano': tamano})

        # --- Validación de Horarios ---
        horarios_validados = []
        if 'horarios' not in datos_entrada or not isinstance(datos_entrada['horarios'], list):
            return jsonify({"error": "El campo 'horarios' es inválido o no existe."}), 400
        if len(datos_entrada['horarios']) > MAX_HORARIOS:
            return jsonify({"error": f"Se exedió el número máximo de horarios permitidos ({MAX_HORARIOS})."}), 400
        for horario in datos_entrada['horarios']:
            if isinstance(horario, str) and horario.strip():
                horarios_validados.append(horario.strip())

        # --- Verificación final de que hay datos suficientes para resolver ---
        if not aulas_validadas or not grupos_validados or not horarios_validados:
            return jsonify(
                {"error": "Se requieren datos válidos de al menos un aula, un grupo y un horario para proceder."}), 400

        # --- Validación de Parámetros ---
        parametros = datos_entrada.get('parametros', {})
        if not isinstance(parametros, dict):
            return jsonify({"error": "El campo 'parametros' debe ser un objeto."}), 400
        # --- FIN DEL BLOQUE DE VALIDACIÓN ---

        # Se llama a la función de optimización solo con los datos ya limpios y validados
        solucion = resolver_asignacion(
            aulas_validadas,
            grupos_validados,
            horarios_validados,
            parametros
        )
        return jsonify(solucion)

    except Exception as e:
        # Este error captura cualquier otra cosa inesperada, como un JSON mal formado.
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500


if __name__ == '__main__':
    # La lógica para abrir el navegador se puede mantener para desarrollo local.
    import webbrowser
    from threading import Timer
    def abrir_navegador():
        webbrowser.open_new('http://127.0.0.1:5000/')
    Timer(1, abrir_navegador).start()
    app.run(port=5000, debug=False)