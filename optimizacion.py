# optimizacion.py

import pulp
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# Ya no necesitamos webbrowser ni Timer, porque Vercel maneja el servidor.

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)


@app.route('/')
def home():
    return render_template('index.html')


def resolver_asignacion(datos_aulas, datos_grupos, datos_horarios, datos_parametros):
    # La lógica de optimización (que ya funciona) no necesita cambios.
    # ... (todo tu código de optimización va aquí sin cambios) ...
    aulas_lista = datos_aulas
    grupos_lista = datos_grupos
    aulas_cap = [a['capacidad'] for a in aulas_lista]
    grupos_est = [g['tamano'] for g in grupos_lista]

    if datos_horarios and len(datos_horarios) > 0:
        horarios_str = datos_horarios
    else:
        horarios_str = ['07:00-09:15', '09:15-11:30', '11:30-13:45']

    delta_porcentaje = datos_parametros.get('delta', 0.20)
    lambda_penalizacion = datos_parametros.get('lambda', 1.0)

    I = range(len(grupos_lista))
    J = range(len(aulas_lista))
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
                        resultado = f"Asignado: {nombre_grupo} -> Aula: {nombre_aula} -> Horario: {horario}"
                        resultados.append(resultado)
    else:
        resultados.append("No se encontró una solución óptima para los datos proporcionados.")

    return {"estado": pulp.LpStatus[modelo.status], "valor_objetivo": valor_objetivo, "resultados": resultados}


@app.route('/solve', methods=['POST'])
def solve_endpoint():
    try:
        datos_entrada = request.get_json()
        if not datos_entrada or 'aulas' not in datos_entrada or 'grupos' not in datos_entrada:
            raise ValueError("Los datos de entrada (aulas, grupos) son inválidos.")

        solucion = resolver_asignacion(
            datos_entrada['aulas'],
            datos_entrada['grupos'],
            datos_entrada.get('horarios', []),
            datos_entrada.get('parametros', {})
        )
        return jsonify(solucion)
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

# --- ELIMINAMOS ESTA SECCIÓN ---
# Vercel se encarga de iniciar el servidor, por lo que este bloque ya no es necesario.
# if __name__ == '__main__':
#     Timer(1, abrir_navegador).start()
#     app.run(port=5000, debug=False)
# --- FIN DE LA ELIMINACIÓN ---
