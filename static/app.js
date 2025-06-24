/**
 * Genera las secciones de entrada para cada piso.
 */
function generarSeccionesPisos() {
    const container = document.getElementById('aulas-por-piso-container');
    const numPisos = parseInt(document.getElementById('numPisos').value, 10);
    container.innerHTML = '';

    if (numPisos > 0) {
        for (let i = 1; i <= numPisos; i++) {
            const pisoSection = document.createElement('div');
            pisoSection.className = 'piso-section';
            pisoSection.innerHTML = `
          <h4>Piso ${i}</h4>
          <table id="aulas-piso-${i}-table">
            <thead>
              <tr>
                <th>Nombre del Aula</th>
                <th>Capacidad</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
          <button type="button" onclick="agregarFilaAula('aulas-piso-${i}-table', ${i})">
            Añadir Aula al Piso ${i}
          </button>
        `;
            container.appendChild(pisoSection);
        }
    }
}

/**
 * Agrega una fila de aula a la tabla de un piso específico.
 */
function agregarFilaAula(tableId, pisoNum) {
    const tableBody = document.querySelector(`#${tableId} tbody`);
    const numAulasActual = tableBody.rows.length;
    const newRow = tableBody.insertRow();
    const nombreAulaPredeterminado = `P${pisoNum}_Aula_${numAulasActual + 1}`;

    newRow.innerHTML = `
      <td><input type="text" value="${nombreAulaPredeterminado}" /></td>
      <td><input type="number" placeholder="Ej: 45" min="1" /></td>
      <td><button class="remove-btn" onclick="eliminarFila(this)">Eliminar</button></td>
    `;
}

/**
 * Agrega una fila a la tabla de grupos.
 */
function agregarFilaGrupo() {
    const tableBody = document.querySelector(`#grupos-table tbody`);
    const newRow = tableBody.insertRow();
    newRow.innerHTML = `
      <td><input type="text" placeholder="Ej: Cálculo I" /></td>
      <td><input type="number" placeholder="Ej: 35" min="1" /></td>
      <td><button class="remove-btn" onclick="eliminarFila(this)">Eliminar</button></td>
    `;
}

/**
 * NUEVA FUNCIÓN para agregar una fila a la tabla de horarios.
 */
function agregarFilaHorario() {
    const tableBody = document.querySelector(`#horarios-table tbody`);
    const newRow = tableBody.insertRow();
    newRow.innerHTML = `
      <td><input type="text" placeholder="Ej: 14:00-16:15" /></td>
      <td><button class="remove-btn" onclick="eliminarFila(this)">Eliminar</button></td>
    `;
}


/**
 * Elimina la fila más cercana al botón presionado.
 */
function eliminarFila(button) {
    button.closest("tr").remove();
}

// --- LÓGICA PARA RESOLVER (MODIFICADA PARA ENVIAR HORARIOS) ---
document.getElementById("solveBtn").addEventListener("click", () => {
    const resultsDiv = document.getElementById("results");
    resultsDiv.textContent = "Recolectando datos y enviando a Python...";

    function recolectarAulas() {
        const aulas = [];
        const sections = document.querySelectorAll('.piso-section');
        sections.forEach(section => {
            const rows = section.querySelectorAll("tbody tr");
            rows.forEach(row => {
                const inputs = row.querySelectorAll("input");
                const nombre = inputs[0].value;
                const capacidad = parseInt(inputs[1].value, 10);
                if (nombre && capacidad > 0) {
                    aulas.push({nombre, capacidad});
                }
            });
        });
        return aulas;
    }

    function recolectarGrupos() {
        const data = [];
        const rows = document.querySelectorAll(`#grupos-table tbody tr`);
        rows.forEach((row) => {
            const inputs = row.querySelectorAll("input");
            const nombre = inputs[0].value;
            const tamano = parseInt(inputs[1].value, 10);
            if (nombre && tamano > 0) {
                data.push({nombre, tamano});
            }
        });
        return data;
    }

    /**
     * NUEVA FUNCIÓN para recolectar los horarios del usuario.
     */
    function recolectarHorarios() {
        const data = [];
        const rows = document.querySelectorAll(`#horarios-table tbody tr`);
        rows.forEach((row) => {
            const input = row.querySelector("input");
            const horario = input.value.trim();
            if (horario) { // Solo añade si no está vacío
                data.push(horario);
            }
        });
        return data;
    }


    const aulas = recolectarAulas();
    const grupos = recolectarGrupos();
    const horarios = recolectarHorarios(); // <-- Obtenemos los horarios personalizados
    const parametros = {
        delta: parseFloat(document.getElementById("delta").value) / 100,
        lambda: parseFloat(document.getElementById("lambda").value),
    };

    // Verificamos que todos los datos necesarios estén presentes
    if (aulas.length === 0 || grupos.length === 0 || horarios.length === 0) {
        resultsDiv.textContent = "Error: Debes definir al menos un aula, un grupo y un horario.";
        return;
    }

    // Añadimos los horarios al payload que se envía al servidor
    const payload = {aulas, grupos, horarios, parametros};
    resultsDiv.textContent = "Procesando... El servidor de Python está calculando la solución.";

    fetch("http://127.0.0.1:5000/solve", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
    })
        .then((response) => response.ok ? response.json() : Promise.reject(response))
        .then((data) => {
            if (data.error) {
                throw new Error(data.error);
            }
            let output = `Estado de la Solución: ${data.estado}\n`;
            if (data.valor_objetivo !== null) {
                output += `Valor de la Función Objetivo (Z): ${data.valor_objetivo.toFixed(2)}\n\n`;
            }
            output += "--- Asignaciones Óptimas ---\n";
            output += data.resultados.length > 0 ? data.resultados.join("\n") : "No se encontraron asignaciones.";
            resultsDiv.textContent = output;
        })
        .catch((error) => {
            console.error("Error:", error);
            resultsDiv.textContent = `Error al procesar la solicitud. Asegúrate de que el script 'optimizacion.py' se está ejecutando.\n\nDetalles: ${error.message || 'Error de red.'}`;
        });
});

document.addEventListener('DOMContentLoaded', generarSeccionesPisos);
