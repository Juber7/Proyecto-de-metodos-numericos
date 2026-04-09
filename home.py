from flask import Flask, render_template, request
import sympy as sp
import numpy as np
import matplotlib
matplotlib.use('Agg') # Esto evita que la gráfica intente abrirse en una ventana de Windows y bloquee el servidor
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

def metodo_biseccion(funcion_str, xl, xu, tol, max_iter):
    # 1. Limpieza y traducción de la función
    funcion_str = funcion_str.replace('^', '**')   # Arregla el problema del exponente
    funcion_str = funcion_str.replace('ln', 'log') # Arregla el problema del logaritmo natural
    
    # 2. Preparar la función matemática
    x = sp.Symbol('x')
    try:
        funcion_simbolica = sp.sympify(funcion_str)
        f = sp.lambdify(x, funcion_simbolica, 'numpy') 
    except Exception as e:
        return {"error": "Error al leer la función. Asegúrate de usar 'x' como variable."}

    # ... (el resto del código sigue exactamente igual)

    # 2. Validar que exista un cambio de signo (condición de bisección)
    fxl = f(xl)
    fxu = f(xu)
    
    if fxl * fxu >= 0:
        return {
            "error": True,
            "titulo": "⚠️ Intervalo sin cambio de signo",
            "mensaje": f"Evaluamos tus límites y obtuvimos f({xl}) = {round(fxl, 4)} y f({xu}) = {round(fxu, 4)}. Como ambos resultados tienen el mismo signo, la curva no cruza el cero (eje X) en este tramo.",
            "consejo": "Para que la bisección funcione, un resultado debe ser positivo y el otro negativo. ¡Intenta con otros valores para xl y xu!"
        }

    resultados = []
    xr_anterior = 0

    # 3. Ciclo iterativo
    for i in range(1, max_iter + 1):
        xr = (xl + xu) / 2
        fxl = f(xl)
        fxr = f(xr)
        
        # Calcular el error aproximado (salvo en la primera iteración)
        ea = abs((xr - xr_anterior) / xr) * 100 if i > 1 else 100
        
        # Guardamos los datos de esta iteración para la tabla
        resultados.append({
            "iteracion": i,
            "xl": round(xl, 4),
            "xu": round(xu, 4),
            "xr": round(xr, 4),
            "fxl": round(fxl, 4),
            "fxr": round(fxr, 4),
            "ea": round(ea, 4) if i > 1 else "---"
        })

        # Criterio de parada por tolerancia
        if i > 1 and ea < tol:
            break

        # Reasignar límites
        if fxl * fxr < 0:
            xu = xr
        elif fxl * fxr > 0:
            xl = xr
        else:
            break # Encontramos la raíz exacta
            
        xr_anterior = xr
        
        # ... (Aquí termina el ciclo for de la bisección)

    # === GENERAR LA GRÁFICA ===
    # Creamos un arreglo de puntos X para dibujar la curva
    margen = (xu - xl) * 0.5 if 'xu_original' in locals() else 2
    x_vals = np.linspace(xl - margen, xu + margen, 200)
    y_vals = f(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'f(x)', color='#0d6efd', linewidth=2)
    plt.axhline(0, color='black', linewidth=1) # Eje X
    
    # Dibujar los límites y la raíz
    plt.axvline(xl, color='orange', linestyle='--', label='xl final')
    plt.axvline(xu, color='purple', linestyle='--', label='xu final')
    plt.plot(xr, 0, 'ro', markersize=8, label=f'Raíz ({round(xr, 4)})')
    
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend()
    plt.tight_layout()

    # Convertir la gráfica a una imagen base64 para enviarla al HTML
    img = io.BytesIO()
    plt.savefig(img, format='png', transparent=True)
    img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return {
        "resultados": resultados, 
        "raiz": round(xr, 4),
        "convergencia": "Lineal O(n) - El error se reduce a la mitad por iteración.",
        "grafica": grafica_url
    }

    return {"resultados": resultados, "raiz": round(xr, 4)}

# ==========================================
# MÉTODO 2: REGLA FALSA (FALSA POSICIÓN)
# ==========================================
def metodo_falsa_posicion(funcion_str, xl, xu, tol, max_iter):
    funcion_str = funcion_str.replace('^', '**').replace('ln', 'log')
    x = sp.Symbol('x')
    
    try:
        funcion_simbolica = sp.sympify(funcion_str)
        f = sp.lambdify(x, funcion_simbolica, 'numpy') 
    except Exception as e:
        return {"error": True, "titulo": "Error Matemático", "mensaje": "No se pudo leer la función.", "consejo": "Asegúrate de usar 'x' como variable."}

    xl_original = xl
    xu_original = xu
    fxl = f(xl)
    fxu = f(xu)
    
    if fxl * fxu >= 0:
        return {
            "error": True,
            "titulo": "⚠️ Intervalo sin cambio de signo",
            "mensaje": f"Evaluamos tus límites y obtuvimos f({xl}) = {round(fxl, 4)} y f({xu}) = {round(fxu, 4)}. Mismo signo.",
            "consejo": "Para la Regla Falsa, un resultado debe ser positivo y el otro negativo."
        }

    resultados = []
    xr_anterior = 0

    for i in range(1, max_iter + 1):
        fxl = f(xl)
        fxu = f(xu)
        
        # Evitar división por cero por si la línea se vuelve horizontal
        if fxl - fxu == 0:
            break

        # LA NUEVA FÓRMULA DE REGLA FALSA
        xr = xu - (fxu * (xl - xu)) / (fxl - fxu)
        fxr = f(xr)

        ea = abs((xr - xr_anterior) / xr) * 100 if i > 1 else 100

        resultados.append({
            "iteracion": i,
            "xl": round(xl, 4),
            "xu": round(xu, 4),
            "xr": round(xr, 4),
            "fxl": round(fxl, 4),
            "fxr": round(fxr, 4),
            "ea": round(ea, 4) if i > 1 else "---"
        })

        if i > 1 and ea < tol:
            break

        # Reemplazo de límites (igual que bisección)
        if fxl * fxr < 0:
            xu = xr
        elif fxl * fxr > 0:
            xl = xr
        else:
            break

        xr_anterior = xr

    # GENERAR LA GRÁFICA
    margen = (xu_original - xl_original) * 0.5
    x_vals = np.linspace(xl_original - margen, xu_original + margen, 200)
    y_vals = f(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'f(x)', color='#198754', linewidth=2) # En verde para distinguirlo
    plt.axhline(0, color='black', linewidth=1) 
    
    plt.axvline(xl_original, color='orange', linestyle='--', label='xl inicial')
    plt.axvline(xu_original, color='purple', linestyle='--', label='xu inicial')
    plt.plot(xr, 0, 'ro', markersize=8, label=f'Raíz ({round(xr, 4)})')
    
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend()
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png', transparent=True)
    img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return {
        "resultados": resultados, 
        "raiz": round(xr, 4),
        "convergencia": "Lineal (Suele ser más rápida que Bisección).",
        "grafica": grafica_url
    }

# Ruta 1: Pantalla de inicio
@app.route('/')
def inicio():
    return render_template('index.html')

# Ruta 2: Calculadora de Bisección
@app.route('/biseccion', methods=['GET', 'POST'])
def biseccion():
    datos = None
    if request.method == 'POST':
        funcion = request.form['funcion']
        xl = float(request.form['xl'])
        xu = float(request.form['xu'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
        datos = metodo_biseccion(funcion, xl, xu, tol, max_iter)
        
    return render_template('biseccion.html', datos=datos)

# RUTA PARA LA PÁGINA DE REGLA FALSA
@app.route('/falsa_posicion', methods=['GET', 'POST'])
def falsa_posicion():
    datos = None
    if request.method == 'POST':
        funcion = request.form['funcion']
        xl = float(request.form['xl'])
        xu = float(request.form['xu'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
        datos = metodo_falsa_posicion(funcion, xl, xu, tol, max_iter)
        
    return render_template('falsa_posicion.html', datos=datos)

if __name__ == '__main__':
    app.run(debug=True)