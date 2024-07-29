from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import json
import openai

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necesario para manejar sesiones

# Cargar el archivo JSON con las fallas
with open('fallas.json', encoding='utf-8') as f:
    fallas_data = json.load(f)

def obtener_respuesta(pregunta):
    if not pregunta.strip():
        return {"mensaje": "Por favor, ingrese una pregunta válida."}

    # Buscar la pregunta en el JSON de fallas
    for falla in fallas_data:
        try:
            if pregunta.lower() in falla['descripcion_falla']['descripcion_problema'].lower():
                # Crear una respuesta conversacional con formato mejorado
                operador = falla['informacion_operador']['nombre_operador']
                puesto = falla['informacion_operador']['puesto']
                descripcion = falla['descripcion_falla']['descripcion_problema']
                acciones = "\n- ".join(falla['acciones_tomadas']['acciones_tomadas_solucion_problema'])
                resultado = falla['acciones_tomadas']['resultados']
                comentarios = falla['acciones_tomadas']['comentarios_adicionales'] if falla['acciones_tomadas']['comentarios_adicionales'] != 'N/A' else 'No hay comentarios adicionales.'

                mensaje = (
                    f"El operador {operador} ({puesto}) reportó el siguiente problema: {descripcion}.\n\n"
                    f"Para solucionar este problema, se realizaron las siguientes acciones:\n"
                    f"- {acciones}\n\n"
                    f"El resultado de estas acciones fue: {resultado}.\n\n"
                    f"Comentarios adicionales: {comentarios}."
                )
                return {"mensaje": mensaje}
        except KeyError as e:
            print(f"KeyError: {e} en {falla}")

    # Si no se encuentra, utilizar OpenAI como respaldo
    ejemplos = ""
    for falla in fallas_data:
        try:
            operador = falla['informacion_operador']['nombre_operador']
            puesto = falla['informacion_operador']['puesto']
            descripcion = falla['descripcion_falla']['descripcion_problema']
            acciones = "\n- ".join(falla['acciones_tomadas']['acciones_tomadas_solucion_problema'])
            resultado = falla['acciones_tomadas']['resultados']
            comentarios = falla['acciones_tomadas']['comentarios_adicionales'] if falla['acciones_tomadas']['comentarios_adicionales'] != 'N/A' else 'No hay comentarios adicionales.'

            ejemplos += (
                f"Problema: {descripcion}\n"
                f"Operador: {operador} ({puesto})\n\n"
                f"Acciones tomadas:\n- {acciones}\n\n"
                f"Resultado: {resultado}\n\n"
                f"Comentarios: {comentarios}\n\n"
            )
        except KeyError as e:
            print(f"KeyError: {e} en {falla}")

    prompt = f"{ejemplos}Pregunta: {pregunta}\nRespuesta:"

    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Actúa como un asistente experto en la resolución de fallas de máquinas. Responde de manera conversacional, estructurada y detallada, evitando respuestas muy extensas o pegadas."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        return {"mensaje": respuesta.choices[0].message['content'].strip()}
    except Exception as e:
        return {"mensaje": f"Error al obtener respuesta de OpenAI: {str(e)}"}

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        with open('usuarios.json', encoding='utf-8') as f:
            usuarios = json.load(f)

        for usuario in usuarios:
            if usuario['username'] == username and usuario['password'] == password:
                session['username'] = username
                return redirect(url_for('index'))

        return "Nombre de usuario o contraseña incorrectos", 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/consultar', methods=['POST'])
def consultar():
    data = request.get_json()
    if not data or 'pregunta' not in data:
        return jsonify({'respuesta': 'Pregunta inválida o no proporcionada'}), 400

    pregunta = data.get('pregunta', '').strip()
    if not pregunta:
        return jsonify({'respuesta': 'Por favor, ingrese una pregunta válida.'}), 400

    respuesta = obtener_respuesta(pregunta)
    return jsonify({'respuesta': respuesta['mensaje']})

if __name__ == '__main__':
    app.run(debug=True)
