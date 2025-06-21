# optimizacion.py

import pulp
from flask import Flask, jsonify, render_template, request # Importamos 'request'
from flask_cors import CORS
import webbrowser
from threading import Timer

# --- Creamos la aplicación Flask ---
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# --- Ruta para servir la página web ---
@app.route('/')
def home():
    return render_template('index.html')

# --- La lógica de optimización ahora recibe los datos como parámetros ---
def resolver_asignacion(datos_aulas, datos_grupos, datos_parametros):
    # 1. PROCESAR LOS DATOS RECIBIDOS
    grupos_data = {item['nombre']: item['tamano'] for item in datos_grupos}
    aulas_data = {item['nombre']: item['capacidad'] for item in datos_aulas}
    
    # Horarios (por ahora siguen fijos, pero podrían hacerse dinámicos)
    horarios = [
        '07:00-09:15', '09:15-11:30', '11:30-13:45',
        '14:00-16:15', '16:15-18:30', '18:30-20:45'
    ]
    
    delta_porcentaje = datos_parametros.get('delta', 0.20)
    lambda_penalizacion = datos_parametros.get('lambda', 1.0)

    nombres_grupos = list(grupos_data.keys())
    nombres_aulas = list(aulas_data.keys())

    # 2. CREAR EL MODELO
    modelo = pulp.LpProblem("Asignacion_Aulas_Optima", pulp.LpMaximize)

    # 3. DEFINIR LAS VARIABLES
    indices_posibles = [
        (i, j, t) for i in nombres_grupos for j in nombres_aulas for t in horarios
        if grupos_data[i] <= aulas_data[j]
    ]
    x = pulp.LpVariable.dicts("asignacion", indices_posibles, cat='LpBinary')
    U = pulp.LpVariable.dicts("subutilizacion_penalizable", indices_posibles, lowBound=0, cat='Continuous')

    # 4. DEFINIR FUNCIÓN OBJETIVO
    total_estudiantes_asignados = pulp.lpSum(x[i, j, t] * grupos_data[i] for i, j, t in indices_posibles)
    penalizacion_total = pulp.lpSum(U[i, j, t] * lambda_penalizacion for i, j, t in indices_posibles)
    modelo += total_estudiantes_asignados - penalizacion_total, "Maximizar_Estudiantes_Menos_Penalizacion"

    # 5. DEFINIR RESTRICCIONES
    for i in nombres_grupos:
        modelo += (pulp.lpSum(x[i, j, t] for j in nombres_aulas for t in horarios if (i, j, t) in indices_posibles) == 1,
                   f"Asignacion_Unica_Grupo_{i}")
    for j in nombres_aulas:
        for t in horarios:
            modelo += (pulp.lpSum(x[i, j, t] for i in nombres_grupos if (i, j, t) in indices_posibles) <= 1,
                       f"Un_Grupo_Por_Aula_Horario_{j}_{t.replace(':', '').replace('-', '_')}")
    for i, j, t in indices_posibles:
        umbral_tolerancia = aulas_data[j] * delta_porcentaje
        espacio_excedente = aulas_data[j] - grupos_data[i] - umbral_tolerancia
        modelo += (U[i, j, t] >= x[i, j, t] * espacio_excedente,
                   f"Penalizacion_Subutilizacion_{i}_{j}_{t.replace(':', '').replace('-', '_')}")

    # 6. RESOLVER EL MODELO
    modelo.solve()

    # 7. PREPARAR LOS RESULTADOS
    resultados = []
    valor_objetivo = None
    if pulp.LpStatus[modelo.status] == 'Optimal':
        valor_objetivo = pulp.value(modelo.objective)
        for i, j, t in indices_posibles:
            if x[(i, j, t)].varValue == 1:
                resultado = f"Asignado: {i} -> Aula: {j} -> Horario: {t}"
                resultados.append(resultado)
    else:
        resultados.append("No se encontró una solución óptima.")
        
    return {"estado": pulp.LpStatus[modelo.status], "valor_objetivo": valor_objetivo, "resultados": resultados}

# --- Punto de entrada de la API ---
@app.route('/solve', methods=['POST'])
def solve_endpoint():
    try:
        # Obtenemos los datos JSON enviados desde el navegador
        datos_entrada = request.get_json()
        
        # Validamos que los datos necesarios estén presentes
        if not datos_entrada or 'aulas' not in datos_entrada or 'grupos' not in datos_entrada:
            raise ValueError("Los datos de entrada (aulas, grupos) son inválidos.")

        # Llamamos a la función de resolución con los datos recibidos
        solucion = resolver_asignacion(
            datos_entrada['aulas'], 
            datos_entrada['grupos'], 
            datos_entrada.get('parametros', {})
        )
        return jsonify(solucion)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Lógica para iniciar el servidor y abrir el navegador ---
def abrir_navegador():
      webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, abrir_navegador).start()
    app.run(port=5000, debug=False) # Se recomienda debug=False para un uso normal