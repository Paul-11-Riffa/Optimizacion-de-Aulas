// /static/app.js - VERSIÓN FINAL COMENTADA

/**
 * =====================================================================================
 * FUNCIONES PARA MANEJAR LA INTERFAZ DE USUARIO (UI)
 * Estas funciones se encargan de crear y eliminar elementos dinámicamente en la página.
 * =====================================================================================
 */

/**
 * Genera las secciones de entrada para cada piso según el número que el usuario especifique.
 * Se activa al cargar la página y cada vez que el usuario cambia el valor del input "Número de Pisos".
 */
function generarSeccionesPisos() {
    // Obtiene el contenedor principal donde se añadirán las secciones de los pisos.
    const container = document.getElementById('aulas-por-piso-container');
    // Lee el valor del input, lo convierte a un número entero.
    const numPisos = parseInt(document.getElementById('numPisos').value, 10);
    // Limpia el contenido previo para no duplicar secciones si se vuelve a llamar.
    container.innerHTML = '';

    // Solo procede si el número de pisos es mayor que cero.
    if (numPisos > 0) {
        // Bucle que se repite una vez por cada piso.
        for (let i = 1; i <= numPisos; i++) {
            // Crea un nuevo elemento <div> para la sección del piso.
            const pisoSection = document.createElement('div');
            // Le asigna una clase para poder aplicarle estilos CSS.
            pisoSection.className = 'piso-section';
            // Inserta el HTML necesario para la tabla de aulas y el botón de añadir.
            // Se usan plantillas de texto (template literals) para construir el HTML fácilmente.
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
            // Añade la sección del piso recién creada al contenedor principal.
            container.appendChild(pisoSection);
        }
    }
}

/**
 * Agrega una nueva fila a la tabla de aulas de un piso específico.
 * @param {string} tableId - El ID de la tabla a la que se añadirá la fila.
 * @param {number} pisoNum - El número del piso, para generar un nombre de aula predeterminado.
 */
function agregarFilaAula(tableId, pisoNum) {
    // Selecciona el cuerpo (tbody) de la tabla específica.
    const tableBody = document.querySelector(`#${tableId} tbody`);
    // Cuenta cuántas filas ya existen para generar un nombre único.
    const numAulasActual = tableBody.rows.length;
    // Inserta una nueva fila vacía en la tabla.
    const newRow = tableBody.insertRow();
    // Genera un nombre de aula predeterminado (ej: P1_Aula_1).
    const nombreAulaPredeterminado = `P${pisoNum}_Aula_${numAulasActual + 1}`;

    // Rellena la nueva fila con las celdas (td) y los inputs correspondientes.
    newRow.innerHTML = `
      <td><input type="text" value="${nombreAulaPredeterminado}" /></td>
      <td><input type="number" placeholder="Ej: 45" min="1" /></td>
      <td><button class="remove-btn" onclick="eliminarFila(this)">Eliminar</button></td>
    `;
}

/**
 * Agrega una nueva fila a la tabla de grupos de estudiantes.
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
 * Agrega una nueva fila a la tabla de horarios disponibles.
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
 * Elimina la fila (tr) que contiene el botón que fue presionado.
 * @param {HTMLElement} button - El botón "Eliminar" que fue clickeado.
 */
function eliminarFila(button) {
    // .closest('tr') busca el ancestro <tr> más cercano al botón y lo elimina.
    button.closest("tr").remove();
}

/**
 * Actualiza el texto que muestra el valor actual de un slider.
 * Se llama cada vez que el usuario mueve el manejador del slider.
 * @param {HTMLInputElement} slider - El elemento input de tipo "range" que cambió.
 */
function updateSliderValue(slider) {
    // Construye el ID del elemento <span> que muestra el valor (ej: 'delta-value').
    const displayId = `${slider.id}-value`;
    const display = document.getElementById(displayId);
    // Si el elemento existe, actualiza su contenido.
    if (display) {
        // Añade un '%' al final si es el slider de 'delta'.
        display.textContent = slider.id === 'delta' ? `${slider.value}%` : slider.value;
    }
}

/**
 * =====================================================================================
 * LÓGICA PRINCIPAL DE LA APLICACIÓN
 * Se encarga de la inicialización y de la comunicación con el backend.
 * =====================================================================================
 */

// --- INICIALIZACIÓN DE LA PÁGINA ---
// Este evento se dispara cuando todo el HTML ha sido cargado y parseado por el navegador.
document.addEventListener('DOMContentLoaded', () => {
    // 1. Genera las secciones de pisos iniciales (basado en el valor por defecto del input).
    generarSeccionesPisos();

    // 2. Inicializa los valores visuales de los sliders para que muestren su valor por defecto al cargar.
    updateSliderValue(document.getElementById('delta'));
    updateSliderValue(document.getElementById('lambda'));
});

// --- MANEJO DEL EVENTO DE RESOLVER ---
// Se añade un "escuchador de eventos" al botón "Resolver". El código dentro se ejecutará cada vez que se haga clic.
// --- MODIFICACIÓN: Event listener del botón "Resolver" mejorado ---
document.getElementById("solveBtn").addEventListener("click", () => {

    // --- 1. PREPARACIÓN DE LA UI PARA LA CARGA ---
    const solveButton = document.getElementById("solveBtn");
    const resultsDiv = document.getElementById("results");

    // Deshabilita el botón para prevenir clics múltiples
    solveButton.disabled = true;
    solveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...'; // Feedback visual

    // Limpia los resultados anteriores
    resultsDiv.textContent = "Recolectando y validando datos...";
    resultsDiv.className = 'results-feedback'; // Clase para estilo neutro

    // --- 2. RECOLECCIÓN Y VALIDACIÓN DE DATOS EN EL CLIENTE ---

    // (Las funciones de recolección ahora incluyen validación más estricta)
    function recolectarAulas() {
        const aulas = [];
        document.querySelectorAll('.piso-section tbody tr').forEach(row => {
            const nombreInput = row.querySelector('input[type="text"]');
            const capacidadInput = row.querySelector('input[type="number"]');

            const nombre = nombreInput.value.trim();
            const capacidad = parseInt(capacidadInput.value, 10);

            // Se añade el aula solo si tiene nombre y una capacidad numérica y positiva
            if (nombre && !isNaN(capacidad) && capacidad > 0) {
                aulas.push({nombre, capacidad});
            }
        });
        return aulas;
    }

    function recolectarGrupos() {
        const data = [];
        document.querySelectorAll('#grupos-table tbody tr').forEach(row => {
            const nombreInput = row.querySelector('input[type="text"]');
            const tamanoInput = row.querySelector('input[type="number"]');

            const nombre = nombreInput.value.trim();
            const tamano = parseInt(tamanoInput.value, 10);

            if (nombre && !isNaN(tamano) && tamano > 0) {
                data.push({nombre, tamano});
            }
        });
        return data;
    }

    function recolectarHorarios() {
        const data = [];
        document.querySelectorAll('#horarios-table tbody tr').forEach(row => {
            const input = row.querySelector("input[type='text']");
            const horario = input.value.trim();
            if (horario) {
                data.push(horario);
            }
        });
        return data;
    }

    const aulas = recolectarAulas();
    const grupos = recolectarGrupos();
    const horarios = recolectarHorarios();
    const parametros = {
        delta: parseFloat(document.getElementById("delta").value) / 100,
        lambda: parseFloat(document.getElementById("lambda").value),
    };

    // Validación en el cliente para dar feedback rápido
    if (aulas.length === 0 || grupos.length === 0 || horarios.length === 0) {
        resultsDiv.textContent = "Error: Debes definir al menos un aula, un grupo y un horario con datos válidos.";
        resultsDiv.className = 'results-feedback error'; // Clase para estilo de error

        // Reactiva el botón si hay un error de validación
        solveButton.disabled = false;
        solveButton.innerHTML = 'Resolver con Python';
        return;
    }

    const payload = {aulas, grupos, horarios, parametros};

    // --- 3. LLAMADA A LA API CON FETCH ---
    fetch("/solve", { // Ruta relativa para funcionar en cualquier entorno
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload),
    })
    .then(async (response) => {
        // --- MODIFICACIÓN: Mejor manejo de respuestas de error de la API ---
        const responseData = await response.json();
        if (!response.ok) {
            // Si la respuesta no es 2xx, construye un error con el mensaje del backend
            const error = new Error(responseData.error || 'Ocurrió un error desconocido');
            error.status = response.status;
            throw error;
        }
        return responseData;
    })
    .then((data) => {
        // --- 4. RENDERIZADO DE RESULTADOS EXITOSOS ---
        resultsDiv.className = 'results-feedback success'; // Clase para estilo de éxito
        let output = `<strong>Estado:</strong> ${data.estado}\n`;
        if (data.valor_objetivo !== null) {
            output += `<strong>Valor Objetivo (Z):</strong> ${data.valor_objetivo.toFixed(2)}\n\n`;
        }
        output += "<strong>--- Asignaciones Óptimas ---</strong>\n";
        output += data.resultados.length > 0 ? data.resultados.join("\n") : "No se encontraron asignaciones.";

        // Usamos innerHTML para que las etiquetas <strong> se rendericen
        resultsDiv.innerHTML = output.replace(/\n/g, '<br>');
    })
    .catch((error) => {
        // --- 5. MANEJO DE ERRORES (de red o de la API) ---
        console.error("Error en la solicitud:", error);
        resultsDiv.className = 'results-feedback error';
        resultsDiv.textContent = `Error: ${error.message}`;
    })
    .finally(() => {
        // --- 6. RESTAURACIÓN DE LA UI ---
        // Este bloque se ejecuta siempre, tanto si la petición tuvo éxito como si falló.
        solveButton.disabled = false; // Reactiva el botón
        solveButton.innerHTML = 'Resolver con Python';
    });
});
