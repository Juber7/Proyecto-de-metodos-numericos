from flask import Flask, render_template, request
import sympy as sp
import numpy as np
import matplotlib
matplotlib.use('Agg') # Esto evita que la gráfica intente abrirse en una ventana de Windows y bloquee el servidor
import matplotlib.pyplot as plt
import io
import base64
import cmath
import math
import re
from sympy.parsing.latex import parse_latex

app = Flask(__name__)

# ==========================================
# MÉTODO 1: BISECCIÓN (BLINDADO)
# ==========================================
def metodo_biseccion(latex_str, xl, xu, tol, max_iter):
    if not latex_str or latex_str.strip() == "":
        return {
            "error": True, "titulo": "🛑 Ecuación vacía",
            "mensaje": "No se recibió ninguna ecuación.", "consejo": "Usa la pizarra virtual para escribir tu f(x)."
        }
    
    try:
        # Limpieza y parseo de LaTeX
        latex_limpio = latex_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        funcion_simbolica = parse_latex(latex_limpio).subs(sp.Symbol('e'), sp.E)
        
        simbolos_usados = [s for s in funcion_simbolica.free_symbols if str(s) not in ['e', 'pi']]

        if len(simbolos_usados) > 1: return {"error": True, "titulo": "🛑 Demasiadas Variables", "mensaje": f"Detectamos: {simbolos_usados}.", "consejo": "Bisección solo soporta 1 variable."}
        if len(simbolos_usados) == 0: return {"error": True, "titulo": "🛑 Sin Variable", "mensaje": "La ecuación no tiene ninguna incógnita."}

        variable_dinamica = simbolos_usados[0]
        f = sp.lambdify(variable_dinamica, funcion_simbolica, 'numpy')

        
        #aqui validamos si se puede evaluar los limites en la funcion,por culquier error
        try:
            fxl = float(f(xl))
            fxu = float(f(xu))
        except (ValueError, TypeError, ZeroDivisionError):
            return {
                "error": True, "titulo": "🛑 Error de Dominio Matemático",
                "mensaje": f"No se puede evaluar la función en el intervalo [{xl}, {xu}].", 
                "consejo": "Asegúrate de no estar dividiendo por cero o sacando raíces cuadradas/logaritmos de números negativos en esos límites."
            }

    except Exception as err:
        return {"error": True, "titulo": "🛑 Error de Sintaxis", "mensaje": str(err), "consejo": "Revisa la escritura de tu fórmula."}

    # aqui aplicamos el teorema de bolzano, las condiciones,practicamente
    # se revisa si la funcion en ese intervalo tiene raizo cambia de signo
    if fxl * fxu > 0:
        return {
            "error": True, "titulo": "⚠️ Intervalo Inválido (Sin cambio de signo)",
            "mensaje": f"Evaluamos tus límites y obtuvimos f({xl}) = {round(fxl, 5)} y f({xu}) = {round(fxu, 5)}. Ambos tienen el mismo signo.",
            "consejo": "Para que la bisección funcione, la curva debe cruzar el eje X. Un límite debe ser positivo y el otro negativo."
        }
    #pero validaos esto por si encontramos una raiz
    elif fxl * fxu == 0:
        raiz_exacta = xl if fxl == 0 else xu
        return {
            "error": True, "titulo": "🎯 ¡Raíz encontrada al instante!",
            "mensaje": f"Uno de tus límites ya es la raíz exacta: {raiz_exacta}", 
            "consejo": "Intenta con otro intervalo si estás buscando una raíz diferente en la curva."
        }

    resultados = []
    xr_anterior = 0
    xl_original, xu_original = xl, xu

    # === CICLO ITERATIVO ===
    for i in range(1, max_iter + 1):
        xr = (xl + xu) / 2
        
        try:
            fxr = float(f(xr))
        except:
            return {"error": True, "titulo": "🛑 Discontinuidad detectada", "mensaje": f"La función falló al evaluar en el punto medio xr = {xr}.", "consejo": "Revisa que tu función sea continua en este intervalo."}
        
        ea = abs((xr - xr_anterior) / xr) * 100 if (xr != 0 and i > 1) else 100
        
        resultados.append({
            "iteracion": i, "xl": round(xl, 8), "xu": round(xu, 8), "xr": round(xr, 8),
            "fxl": round(fxl, 8), "fxr": round(fxr, 8), "ea": round(ea, 8) if i > 1 else "---"
        })

        if i > 1 and ea < tol:
            break

        # Reemplazo de límites
        if fxl * fxr < 0:
            xu = xr
        elif fxl * fxr > 0:
            xl = xr
            fxl = fxr # Actualizamos fxl para la siguiente iteración
        else:
            break # fxr es exactamente 0
            
        xr_anterior = xr

    # === GENERAR LA GRÁFICA ===
    margen = (xu_original - xl_original) * 0.5
    if margen == 0: margen = 2
    x_vals = np.linspace(xl_original - margen, xu_original + margen, 200)
    
    try:
        y_vals = f(x_vals)
        if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
    except:
        y_vals = np.zeros_like(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'f({variable_dinamica})', color='#0d6efd', linewidth=2)
    plt.axhline(0, color='black', linewidth=1) 
    
    plt.axvline(xl_original, color='orange', linestyle='--', label='xl inicial')
    plt.axvline(xu_original, color='purple', linestyle='--', label='xu inicial')
    plt.plot(xr, 0, 'ro', markersize=8, label=f'Raíz ({round(xr, 8)})')
    
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
        "raiz": round(xr, 8),
        "convergencia": "Lineal O(n) - El error se reduce a la mitad en cada paso.",
        "grafica": grafica_url
    }

# ==========================================
# MÉTODO 2: REGLA FALSA (FALSA POSICIÓN)
# ==========================================
def metodo_falsa_posicion(latex_str, xl, xu, tol, max_iter):
    if not latex_str or latex_str.strip() == "":
        return {
            "error": True, "titulo": "🛑 Ecuación vacía",
            "mensaje": "No se recibió ninguna ecuación.", "consejo": "Escribe tu f(x) en la pizarra virtual."
        }
    
    try:
        # 1. Limpieza y Traducción LaTeX a SymPy
        latex_limpio = latex_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        funcion_simbolica = parse_latex(latex_limpio).subs(sp.Symbol('e'), sp.E)
        
        # 2. Detección de Variable Dinámica
        simbolos_usados = [s for s in funcion_simbolica.free_symbols if str(s) not in ['e', 'pi']]
        if len(simbolos_usados) > 1: return {"error": True, "titulo": "🛑 Demasiadas Variables", "mensaje": f"Detectamos: {simbolos_usados}."}
        if len(simbolos_usados) == 0: return {"error": True, "titulo": "🛑 Sin Variable", "mensaje": "La ecuación no tiene incógnita."}

        variable_dinamica = simbolos_usados[0]
        f = sp.lambdify(variable_dinamica, funcion_simbolica, 'numpy')

        # 3. Prueba de fuego en los límites
        xl_original, xu_original = xl, xu
        fxl = float(f(xl))
        fxu = float(f(xu))

    except Exception as err:
        return {"error": True, "titulo": "🛑 Error Matemático", "mensaje": str(err)}

    # === Validación de Bolzano ===
    if fxl * fxu >= 0:
        return {
            "error": True, "titulo": "⚠️ Intervalo Inválido",
            "mensaje": f"f({xl}) = {round(fxl, 5)} y f({xu}) = {round(fxu, 5)}. Mismo signo.",
            "consejo": "Regla Falsa requiere que la función cruce el eje X entre xl y xu."
        }

    resultados = []
    xr_anterior = 0

    # === Ciclo de Regla Falsa ===
    for i in range(1, max_iter + 1):
        fxl = f(xl)
        fxu = f(xu)
        
        if fxl - fxu == 0: break

        # Fórmula de Regla Falsa (Intersección de la secante)
        xr = xu - (fxu * (xl - xu)) / (fxl - fxu)
        fxr = f(xr)

        ea = abs((xr - xr_anterior) / xr) * 100 if i > 1 else 100

        resultados.append({
            "iteracion": i, "xl": round(xl, 8), "xu": round(xu, 8), "xr": round(xr, 8),
            "fxl": round(fxl, 8), "fxr": round(fxr, 8), "ea": round(ea, 8) if i > 1 else "---"
        })

        if i > 1 and ea < tol: break

        # Reemplazo de límites
        if fxl * fxr < 0:
            xu = xr
        else:
            xl = xr
        
        xr_anterior = xr

    # === Gráfica ===
    margen = (xu_original - xl_original) * 0.5
    x_vals = np.linspace(xl_original - margen - 1, xu_original + margen + 1, 200)
    y_vals = f(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'f({variable_dinamica})', color='#198754', linewidth=2) 
    plt.axhline(0, color='black', linewidth=1) 
    plt.axvline(xl_original, color='orange', linestyle='--', label='xl inicial')
    plt.axvline(xu_original, color='purple', linestyle='--', label='xu inicial')
    plt.plot(xr, 0, 'ro', markersize=8, label=f'Raíz ({round(xr, 8)})')
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend(); plt.tight_layout()

    img = io.BytesIO(); plt.savefig(img, format='png', transparent=True); img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8'); plt.close()

    return {
        "resultados": resultados, "raiz": round(xr, 8),
        "convergencia": f"Lineal - Variable: '{variable_dinamica}'.", "grafica": grafica_url
    }
def metodo_newton_raphson(latex_str, x0, tol, max_iter):
    if not latex_str or latex_str.strip() == "":
        return {
            "error": True, "titulo": "🛑 Ecuación vacía",
            "mensaje": "No se recibió ninguna ecuación.", "consejo": "Escribe tu f(x) en la pizarra virtual."
        }

    try:
        # 1. Limpieza y traducción a SymPy
        latex_limpio = latex_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        funcion_simbolica = parse_latex(latex_limpio).subs(sp.Symbol('e'), sp.E)

        # 2. Detección de variable dinámica
        simbolos_usados = [s for s in funcion_simbolica.free_symbols if str(s) not in ['e', 'pi']]

        if len(simbolos_usados) > 1:
            return {"error": True, "titulo": "🛑 Demasiadas Variables", "mensaje": f"Detectamos: {simbolos_usados}."}
        if len(simbolos_usados) == 0:
            return {"error": True, "titulo": "🛑 Sin Variable", "mensaje": "La ecuación no tiene incógnita."}

        variable_dinamica = simbolos_usados[0]

        # 3. Derivada analítica automática
        derivada_simbolica = sp.diff(funcion_simbolica, variable_dinamica)

        f = sp.lambdify(variable_dinamica, funcion_simbolica, 'numpy')
        df = sp.lambdify(variable_dinamica, derivada_simbolica, 'numpy')

        # Prueba de fuego numérica
        float(f(x0))
        float(df(x0))

    except Exception as err:
        return {"error": True, "titulo": "🛑 Error Matemático", "mensaje": str(err)}

    resultados = []
    xi = float(x0)

    # 4. Ciclo de Newton-Raphson
    for i in range(1, max_iter + 1):
        try:
            fxi = float(f(xi))
            dfxi = float(df(xi))
        except:
            return {"error": True, "titulo": "🚀 Divergencia", "mensaje": "Los números se volvieron demasiado grandes o complejos."}

        if dfxi == 0:
            return {"error": True, "titulo": "⚠️ Derivada Cero", "mensaje": "La pendiente es horizontal. El método no puede avanzar.", "consejo": "Prueba con otro x0."}

        # Fórmula de Newton-Raphson: xi+1 = xi - f(xi)/f'(xi)
        x_siguiente = xi - (fxi / dfxi)
        ea = abs((x_siguiente - xi) / x_siguiente) * 100 if x_siguiente != 0 else 100

        resultados.append({
            "iteracion": i, "xi": round(xi, 8), "fxi": round(fxi, 8),
            "dfxi": round(dfxi, 8), "x_siguiente": round(x_siguiente, 8),
            "ea": round(ea, 8) if i > 1 else "---"
        })

        if i > 1 and ea < tol:
            xi = x_siguiente
            break
        xi = x_siguiente

    # 5. Gráfica
    margen = abs(xi - float(x0)) + 2
    x_vals = np.linspace(min(float(x0), xi) - margen, max(float(x0), xi) + margen, 200)
    try:
        y_vals = f(x_vals)
        if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
    except: y_vals = np.zeros_like(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'f({variable_dinamica})', color='#dc3545', linewidth=2)
    plt.axhline(0, color='black', linewidth=1)
    plt.axvline(float(x0), color='orange', linestyle='--', label='x0 inicial')
    plt.plot(xi, 0, 'go', markersize=8, label=f'Raíz ({round(xi, 8)})')
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend(); plt.tight_layout()

    img = io.BytesIO(); plt.savefig(img, format='png', transparent=True); img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8'); plt.close()

    return {
        "tipo": "abierto", "resultados": resultados, "raiz": round(xi, 8),
        "convergencia": f"Cuadrática O(n²) - Variable: '{variable_dinamica}'.", "grafica": grafica_url
    }
    
# ==========================================
# MÉTODO 4: SECANTE (ACTUALIZADO)
# ==========================================
def metodo_secante(latex_str, x0, x1, tol, max_iter):
    if not latex_str or latex_str.strip() == "":
        return {
            "error": True, "titulo": "🛑 Ecuación vacía",
            "mensaje": "No se recibió ninguna ecuación.", "consejo": "Usa la pizarra virtual."
        }

    try:
        # 1. Limpieza y traducción a SymPy
        latex_limpio = latex_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        funcion_simbolica = parse_latex(latex_limpio).subs(sp.Symbol('e'), sp.E)

        # 2. Detección de variable dinámica
        simbolos_usados = [s for s in funcion_simbolica.free_symbols if str(s) not in ['e', 'pi']]

        if len(simbolos_usados) > 1: return {"error": True, "titulo": "🛑 Demasiadas Variables", "mensaje": f"Detectamos: {simbolos_usados}."}
        if len(simbolos_usados) == 0: return {"error": True, "titulo": "🛑 Sin Variable", "mensaje": "La ecuación no tiene incógnita."}

        variable_dinamica = simbolos_usados[0]
        f = sp.lambdify(variable_dinamica, funcion_simbolica, 'numpy')

        # Evaluación inicial de los dos puntos
        fx0 = float(f(x0))
        fx1 = float(f(x1))

    except Exception as err:
        return {"error": True, "titulo": "🛑 Error Matemático", "mensaje": str(err)}

    resultados = []
    x_previo = float(x0)
    x_actual = float(x1)

    # 3. Ciclo de la Secante
    for i in range(1, max_iter + 1):
        try:
            fx_previo = float(f(x_previo))
            fx_actual = float(f(x_actual))
        except:
            return {"error": True, "titulo": "🚀 Divergencia", "mensaje": "La función generó valores demasiado grandes o complejos."}

        # Evitar división por cero si f(x_previo) y f(x_actual) son iguales (Línea horizontal)
        if fx_previo - fx_actual == 0:
            return {"error": True, "titulo": "⚠️ División por Cero", "mensaje": "La recta secante se volvió horizontal y no cruzará el eje X.", "consejo": "Intenta con otros valores iniciales."}

        # Fórmula de la Secante
        x_siguiente = x_actual - (fx_actual * (x_previo - x_actual)) / (fx_previo - fx_actual)
        
        ea = abs((x_siguiente - x_actual) / x_siguiente) * 100 if x_siguiente != 0 else 100

        resultados.append({
            "iteracion": i, "x_previo": round(x_previo, 8), "x_actual": round(x_actual, 8),
            "fx_actual": round(fx_actual, 8), "x_siguiente": round(x_siguiente, 8),
            "ea": round(ea, 8) if i > 1 else "---"
        })

        if ea < tol:
            x_actual = x_siguiente
            break
        
        # Desplazamiento para la siguiente iteración
        x_previo = x_actual
        x_actual = x_siguiente

    # 4. Gráfica
    margen = abs(x_actual - float(x0)) + 2
    x_vals = np.linspace(min(float(x0), float(x1), x_actual) - margen, max(float(x0), float(x1), x_actual) + margen, 200)
    
    try:
        y_vals = f(x_vals)
        if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
        y_vals = np.clip(y_vals, -100, 100) # Evitar que la gráfica se deforme
    except: y_vals = np.zeros_like(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'f({variable_dinamica})', color='#0dcaf0', linewidth=2)
    plt.axhline(0, color='black', linewidth=1)
    
    # Dibujamos los dos puntos iniciales
    plt.axvline(float(x0), color='orange', linestyle=':', label='x0 inicial')
    plt.axvline(float(x1), color='purple', linestyle=':', label='x1 inicial')
    plt.plot(x_actual, 0, 'go', markersize=8, label=f'Raíz ({round(x_actual, 8)})')
    
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend(); plt.tight_layout()

    img = io.BytesIO(); plt.savefig(img, format='png', transparent=True); img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8'); plt.close()

    return {
        "tipo": "secante", "resultados": resultados, "raiz": round(x_actual, 8),
        "convergencia": f"Superlineal (Aprox. 1.618) - Variable: '{variable_dinamica}'.", "grafica": grafica_url
    }
    

# ==========================================
# MÉTODO 5: SERIE DE TAYLOR 
# ==========================================
def metodo_taylor(latex_str, x0, x_eval, n_terminos):
    if not latex_str or latex_str.strip() == "":
        return {"error": True, "titulo": "🛑 Ecuación vacía", "mensaje": "Escribe tu f(x) en la pizarra."}

    try:
        # Limpieza y Traducción a SymPy
        latex_limpio = latex_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        f_simbolica = parse_latex(latex_limpio).subs(sp.Symbol('e'), sp.E)

        # Detectar variable
        simbolos_usados = [s for s in f_simbolica.free_symbols if str(s) not in ['e', 'pi']]
        if len(simbolos_usados) > 1: return {"error": True, "titulo": "🛑 Demasiadas Variables", "mensaje": f"Detectamos: {simbolos_usados}."}
        x = simbolos_usados[0] if len(simbolos_usados) == 1 else sp.Symbol('x')
        
        # Valor verdadero
        f_lambdify = sp.lambdify(x, f_simbolica, 'numpy')
        valor_verdadero = float(f_lambdify(x_eval))

    except Exception as err:
        return {"error": True, "titulo": "🛑 Error Matemático", "mensaje": str(err)}

    resultados = []
    aprox_actual = 0
    polinomio_taylor = 0

    # Ciclo de Taylor
    for i in range(n_terminos):
        if i == 0:
            derivada = f_simbolica
        else:
            derivada = sp.diff(f_simbolica, x, i)
        
        try:
            derivada_evaluada = float(derivada.subs(x, x0))
        except:
            return {"error": True, "titulo": "⚠️ Discontinuidad", "mensaje": f"No se puede evaluar la derivada de orden {i} en el centro."}
        
        # Fórmula de Taylor
        termino_valor = (derivada_evaluada / math.factorial(i)) * ((x_eval - x0) ** i)
        termino_simbolico = (derivada.subs(x, x0) / math.factorial(i)) * ((x - x0) ** i)
        
        aprox_actual += termino_valor
        polinomio_taylor += termino_simbolico
        
        et = abs((valor_verdadero - aprox_actual) / valor_verdadero) * 100 if valor_verdadero != 0 else abs(valor_verdadero - aprox_actual)
        
        # Estética visual de la derivada para la tabla
        derivada_bonita = str(derivada).replace('**', '^').replace('*', '·').replace('sqrt', '√')

        resultados.append({
            "orden": i,
            "derivada": derivada_bonita,
            "derivada_evaluada": round(derivada_evaluada, 8),
            "termino_calculado": round(termino_valor, 8),
            "aproximacion": round(aprox_actual, 8),
            "et": round(et, 8) if i > 0 else "---"
        })

    # Gráfica
    margen = abs(x_eval - x0) + 2
    x_vals = np.linspace(min(x0, x_eval) - margen, max(x0, x_eval) + margen, 200)
    
    try:
        y_vals_f = f_lambdify(x_vals)
        if isinstance(y_vals_f, (int, float)): y_vals_f = np.full_like(x_vals, y_vals_f)
        
        p_lambdify = sp.lambdify(x, polinomio_taylor, 'numpy')
        y_vals_p = p_lambdify(x_vals)
        if isinstance(y_vals_p, (int, float)): y_vals_p = np.full_like(x_vals, y_vals_p)
        
        y_min, y_max = np.min(y_vals_f) - 5, np.max(y_vals_f) + 5
        y_vals_p = np.clip(y_vals_p, y_min - 10, y_max + 10)
    except: 
        y_vals_f = np.zeros_like(x_vals)
        y_vals_p = np.zeros_like(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals_f, label=f'Original f({x})', color='#0d6efd', linewidth=2)
    plt.plot(x_vals, y_vals_p, label=f'Taylor (Orden {n_terminos-1})', color='#ffc107', linestyle='--', linewidth=2)
    plt.axvline(x0, color='gray', linestyle=':', label=f'Centro x0={x0}')
    plt.plot(x_eval, valor_verdadero, 'bo', markersize=6, label='Valor Real')
    plt.plot(x_eval, aprox_actual, 'yo', markersize=6, label='Aproximación')
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend(); plt.tight_layout()

    img = io.BytesIO(); plt.savefig(img, format='png', transparent=True); img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8'); plt.close()

    polinomio_str = str(polinomio_taylor).replace('**', '^').replace('*', '·').replace('sqrt', '√')

    return {
        "tipo": "taylor", 
        "resultados": resultados, 
        "valor_verdadero": round(valor_verdadero, 8),
        "aprox_final": round(aprox_actual, 8),
        "polinomio_final": polinomio_str,
        "grafica": grafica_url
    }


    
# ==========================================
# MÉTODO 6: PUNTO FIJO (CON DESPEJE AUTOMÁTICO)
# ==========================================
def metodo_punto_fijo(latex_fx_str, x0, tol, max_iter):
    if not latex_fx_str or latex_fx_str.strip() == "":
        return {
            "error": True, "titulo": "🛑 Ecuación f(x) vacía",
            "mensaje": "No se recibió ninguna ecuación.", "consejo": "Escribe tu función f(x) original."
        }
    
    try:
        latex_limpio = latex_fx_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        f_simbolica = parse_latex(latex_limpio).subs(sp.Symbol('e'), sp.E)
        
        simbolos_usados = [s for s in f_simbolica.free_symbols if str(s) not in ['e', 'pi']]

        if len(simbolos_usados) > 1: return {"error": True, "titulo": "🛑 Demasiadas Variables", "mensaje": f"Detectamos: {simbolos_usados}.", "consejo": "Punto Fijo solo soporta 1 variable."}
        if len(simbolos_usados) == 0: return {"error": True, "titulo": "🛑 Sin Variable", "mensaje": "La ecuación no tiene ninguna incógnita."}

        variable_dinamica = simbolos_usados[0]
        x = variable_dinamica
        
        # === GENERADOR AUTOMÁTICO DE DESPEJES g(x) ===
        posibles_g = [x + f_simbolica, x - f_simbolica]
        
        terminos = sp.Add.make_args(f_simbolica)
        for t in terminos:
            if t.has(x):
                resto = f_simbolica - t
                y = sp.Symbol('y_temp')
                try:
                    sub_despejes = sp.solve(t - y, x)
                    for sol in sub_despejes:
                        posibles_g.append(sol.subs(y, -resto))
                except: pass

        # === EVALUADOR DE CONVERGENCIA ===
        g_ganadora = None
        menor_derivada = float('inf')
        
        for g_expr in posibles_g:
            try:
                dg_expr = sp.diff(g_expr, x)
                dg_func = sp.lambdify(x, dg_expr, 'numpy')
                valor_derivada = abs(float(dg_func(x0)))
                
                # Elegimos la g(x) cuya derivada sea menor a 1
                if valor_derivada < 1 and valor_derivada < menor_derivada:
                    menor_derivada = valor_derivada
                    g_ganadora = g_expr
            except: continue

        if g_ganadora is None:
            return {
                "error": True, "titulo": "🛑 Divergencia Inevitable",
                "mensaje": f"Se generaron {len(posibles_g)} despejes posibles, pero NINGUNO converge en el punto x0 = {x0}.",
                "consejo": "El álgebra tiene un límite. Intenta con un valor inicial (x0) más cercano a la raíz real."
            }

        g = sp.lambdify(x, g_ganadora, 'numpy') 
        g_str_legible = str(g_ganadora).replace('**', '^')
        diagnostico = f"¡Despeje Automático Exitoso! g({x}) = {g_str_legible}. Convergencia garantizada: |g'({x0})| = {round(menor_derivada, 5)} < 1."

    except Exception as err:
        return {"error": True, "titulo": "🛑 Error Matemático", "mensaje": str(err), "consejo": "Revisa tu sintaxis."}

    # === CICLO ITERATIVO ===
    resultados = []
    xi = float(x0)
    diverge = False

    for i in range(1, max_iter + 1):
        try:
            gxi = float(g(xi))
        except: return {"error": True, "titulo": "🛑 Raíz Compleja", "mensaje": "El despeje topó con números imaginarios.", "consejo": "Cambia el x0."}
        
        if abs(gxi) > 1e6:
            diverge = True
            break

        ea = abs((gxi - xi) / gxi) * 100 if gxi != 0 else 100
        resultados.append({"iteracion": i, "xi": round(xi, 8), "gxi": round(gxi, 8), "ea": round(ea, 8) if i > 1 else "---"})

        if i > 1 and ea < tol:
            xi = gxi
            break
        xi = gxi

    if diverge: return {"error": True, "titulo": "🚀 Divergencia", "mensaje": "Divergencia numérica.", "consejo": "Prueba otra semilla."}

    # === GENERAR LA GRÁFICA ===
    margen = abs(xi - float(x0)) + 2
    x_min = min(float(x0), xi) - margen
    x_max = max(float(x0), xi) - margen if max(float(x0), xi) == min(float(x0), xi) else max(float(x0), xi) + margen
    
    x_vals = np.linspace(x_min, x_max, 200)
    x_vals = np.where(x_vals == 0, 1e-10, x_vals) 
    
    try:
        y_vals_g = g(x_vals)
        if isinstance(y_vals_g, (int, float)): y_vals_g = np.full_like(x_vals, y_vals_g)
    except: y_vals_g = np.zeros_like(x_vals)

    plt.figure(figsize=(8, 5))
    plt.plot(x_vals, y_vals_g, label=f'g({variable_dinamica}) ganadora', color='#6f42c1', linewidth=2) 
    plt.plot(x_vals, x_vals, label=f'y = {variable_dinamica}', color='gray', linestyle='--', linewidth=1.5) 
    plt.axhline(0, color='black', linewidth=1) 
    plt.axvline(float(x0), color='orange', linestyle=':', label=f'{variable_dinamica}0 inicial')
    plt.plot(xi, xi, 'ro', markersize=8, label=f'Raíz ({round(xi, 8)})') 
    
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend()
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png', transparent=True)
    img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return {
        "tipo": "punto_fijo", "resultados": resultados, "raiz": round(xi, 8),
        "convergencia": diagnostico, "grafica": grafica_url
    }
    
# ==========================================
# MÉTODO 6: HORNER (EVALUACIÓN POLINOMIAL)
# ==========================================
def metodo_horner(latex_str, x0):
    if not latex_str or latex_str.strip() == "":
        return {"error": True, "titulo": "🛑 Polinomio vacío", "mensaje": "Escribe tu polinomio en la pizarra."}

    try:
        # 1. Limpieza bestial
        latex_limpio = latex_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        f_latex = parse_latex(latex_limpio)
        # Forzamos la expansión para destruir cualquier formato oculto
        f_simbolica = sp.expand(sp.sympify(str(f_latex))) 

        # 2. Variable dinámica
        simbolos_usados = [s for s in f_simbolica.free_symbols if str(s) not in ['e', 'pi']]
        if len(simbolos_usados) > 1: return {"error": True, "titulo": "🛑 Demasiadas Variables", "mensaje": f"Detectamos: {simbolos_usados}."}
        x = simbolos_usados[0] if len(simbolos_usados) == 1 else sp.Symbol('x')

        
        # Sacamos el grado máximo de la ecuación. Si esto falla, es porque metieron un seno o un logaritmo.
        try:
            grado_maximo = sp.degree(f_simbolica, gen=x)
            if str(grado_maximo) == 'oo' or str(grado_maximo) == '-oo': # Si tira infinito, no es polinomio
                raise ValueError()
        except:
            return {"error": True, "titulo": "⚠️ Función Inválida", "mensaje": "Esto no parece un polinomio. Horner solo acepta cosas como x^3 - 2x + 1."}

        # Armamos la lista de coeficientes manualmente (del grado mayor al 0)
        coeficientes = []
        for i in range(int(grado_maximo), -1, -1):
            if i == 0:
                # El término independiente (el número solo) se saca evaluando x=0
                coef = f_simbolica.subs(x, 0)
            else:
                # Le arrancamos el número que acompaña a la x^i
                coef = f_simbolica.coeff(x, i)
            
            coeficientes.append(float(coef))

    except Exception as err:
        return {"error": True, "titulo": "🛑 Error Matemático", "mensaje": f"Detalle técnico: {str(err)}"}

    # ==========================================
    # LA DIVISIÓN SINTÉTICA PURA Y DURA
    # ==========================================
    resultados = []
    
    # El primer número baja directo
    b_actual = coeficientes[0] 

    resultados.append({
        "grado": int(grado_maximo),
        "a": round(b_actual, 8),
        "operacion": "---",
        "b": round(b_actual, 8)
    })

    # Bucle de multiplicar por x0 y sumar
    for i in range(1, len(coeficientes)):
        a_actual = coeficientes[i]
        
        operacion_val = b_actual * float(x0)
        b_nuevo = a_actual + operacion_val

        resultados.append({
            "grado": int(grado_maximo) - i,
            "a": round(a_actual, 8),
            "operacion": round(operacion_val, 8),
            "b": round(b_nuevo, 8)
        })
        b_actual = b_nuevo

    # El último valor calculado es nuestra respuesta
    residuo = b_actual

    # ==========================================
    # GRÁFICA MATPLOTLIB
    # ==========================================
    margen = 3
    x_vals = np.linspace(float(x0) - margen, float(x0) + margen, 200)
    try:
        f_lambdify = sp.lambdify(x, f_simbolica, 'numpy')
        y_vals = f_lambdify(x_vals)
        if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
    except:
        y_vals = np.zeros_like(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'P({x})', color='#fd7e14', linewidth=2)
    plt.axhline(0, color='black', linewidth=1)
    
    plt.plot(float(x0), residuo, 'ro', markersize=8, label=f'P({x0}) = {round(residuo, 5)}')
    plt.axvline(float(x0), color='gray', linestyle=':')
    
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend(); plt.tight_layout()

    img = io.BytesIO(); plt.savefig(img, format='png', transparent=True); img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8'); plt.close()

    return {
        "tipo": "horner",
        "resultados": resultados,
        "raiz": round(residuo, 8),
        "convergencia": "Evaluación por División Sintética.",
        "grafica": grafica_url
    }
# ==========================================
# MÉTODO 8: HORNER-NEWTON (BIRGE-VIETA)
# ==========================================
def metodo_horner_newton(latex_str, x0, tol, max_iter):
    if not latex_str or latex_str.strip() == "":
        return {"error": True, "titulo": "🛑 Polinomio vacío", "mensaje": "Escribe tu polinomio."}

    try:
        # 1. Limpieza bestial (igual que Horner normal)
        latex_limpio = latex_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        f_latex = parse_latex(latex_limpio)
        f_simbolica = sp.expand(sp.sympify(str(f_latex))) 

        x = [s for s in f_simbolica.free_symbols if str(s) not in ['e', 'pi']][0] if f_simbolica.free_symbols else sp.Symbol('x')

        # Extraemos coeficientes a lo bruto
        grado_maximo = sp.degree(f_simbolica, gen=x)
        if str(grado_maximo) in ['oo', '-oo']: raise ValueError()

        coef_originales = []
        for i in range(int(grado_maximo), -1, -1):
            coef = f_simbolica.subs(x, 0) if i == 0 else f_simbolica.coeff(x, i)
            coef_originales.append(float(coef))

    except Exception as err:
        return {"error": True, "titulo": "⚠️ Función Inválida", "mensaje": "Asegúrate de ingresar un polinomio válido."}

    resultados = []
    xi = float(x0)
    
    # === MINIFUNCIÓN: Hace una división sintética rápida ===
    def hacer_horner(coefs, valor_x):
        b = coefs[0]
        nuevos_coefs = [b]
        for i in range(1, len(coefs)):
            b = coefs[i] + b * valor_x
            nuevos_coefs.append(b)
        # Retornamos el residuo y los coeficientes sobrantes (el cociente)
        return b, nuevos_coefs[:-1] 

    # 2. Ciclo de Búsqueda de la Raíz
    for i in range(1, max_iter + 1):
        # Horner 1: Evaluamos el polinomio para sacar P(xi)
        pxi, coef_q = hacer_horner(coef_originales, xi)
        
        # Horner 2: Evaluamos el cociente para sacar P'(xi)
        dpxi, _ = hacer_horner(coef_q, xi)

        if dpxi == 0:
            return {"error": True, "titulo": "⚠️ División por Cero", "mensaje": "La derivada se hizo cero (recta horizontal)."}

        # Newton-Raphson aplicado
        x_siguiente = xi - (pxi / dpxi)
        
        ea = abs((x_siguiente - xi) / x_siguiente) * 100 if x_siguiente != 0 else 100

        # Guardamos usando las variables que tu _resultados.html ya espera
        resultados.append({
            "iteracion": i,
            "xi": round(xi, 8),
            "pxi": round(pxi, 8),
            "dpxi": round(dpxi, 8),
            "x_siguiente": round(x_siguiente, 8),
            "ea": round(ea, 8) if i > 1 else "---"
        })

        if ea < tol:
            xi = x_siguiente
            break
        
        xi = x_siguiente

    # 3. Gráfica
    margen = abs(xi - float(x0)) + 2
    x_vals = np.linspace(min(float(x0), xi) - margen, max(float(x0), xi) + margen, 200)
    try:
        f_lambdify = sp.lambdify(x, f_simbolica, 'numpy')
        y_vals = f_lambdify(x_vals)
        if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
        y_vals = np.clip(y_vals, -100, 100) # Evita deformaciones
    except: y_vals = np.zeros_like(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'P({x})', color='#20c997', linewidth=2)
    plt.axhline(0, color='black', linewidth=1)
    plt.plot(xi, 0, 'go', markersize=8, label=f'Raíz ({round(xi, 5)})')
    plt.axvline(float(x0), color='orange', linestyle=':', label='x0 inicial')
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend(); plt.tight_layout()

    img = io.BytesIO(); plt.savefig(img, format='png', transparent=True); img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8'); plt.close()

    return {
        "tipo": "horner_newton",
        "resultados": resultados,
        "raiz": round(xi, 8),
        "convergencia": "Cuadrática (Newton apoyado por doble Horner).",
        "grafica": grafica_url
    }

    # Función auxiliar para hacer la división sintética rápida
    def division_sintetica(coeficientes, valor_x):
        b = [float(coeficientes[0])]
        for j in range(1, len(coeficientes)):
            b.append(float(coeficientes[j]) + b[-1] * valor_x)
        return b[-1], b[:-1] # Retorna (Residuo, Coeficientes del Cociente)

    resultados = []
    xi = float(x0)

    for i in range(1, max_iter + 1):
        # Horner 1: Sacamos P(xi) y el polinomio cociente Q(x)
        pxi, q_coeffs = division_sintetica(coeffs, xi)
        
        # Horner 2: Evaluamos el cociente Q(x) para sacar la derivada P'(xi)
        dpxi, _ = division_sintetica(q_coeffs, xi)
        
        if dpxi == 0:
            return {
                "error": True,
                "titulo": "⚠️ Derivada Cero (Línea Horizontal)",
                "mensaje": f"En la iteración {i}, la segunda división sintética (derivada) dio 0.",
                "consejo": "El método falla porque genera división por cero. Intenta con un x0 diferente."
            }

        # Fórmula de Newton usando los residuos de Horner
        x_siguiente = xi - (pxi / dpxi)
        
        ea = abs((x_siguiente - xi) / x_siguiente) * 100 if x_siguiente != 0 else 100

        resultados.append({
            "iteracion": i,
            "xi": round(xi, 8),
            "pxi": round(pxi, 8),
            "dpxi": round(dpxi, 8),
            "x_siguiente": round(x_siguiente, 8),
            "ea": round(ea, 8) if i > 1 else "---"
        })

        if i > 1 and ea < tol:
            xi = x_siguiente
            break
            
        xi = x_siguiente

    # === GENERAR LA GRÁFICA ===
    margen = abs(xi - x0) * 0.5 if abs(xi - x0) > 0 else 2
    x_min = min(x0, xi) - margen
    x_max = max(x0, xi) + margen
    
    x_vals = np.linspace(x_min, x_max, 200)
    y_vals = f_numpy(x_vals)

    altura_maxima = max(abs(f_numpy(x_min)), abs(f_numpy(x_max))) * 3
    y_vals = np.clip(y_vals, -altura_maxima, altura_maxima)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'P(x)', color='#20c997', linewidth=2) # Color Teal
    plt.axhline(0, color='black', linewidth=1) 
    
    plt.axvline(x0, color='orange', linestyle='--', label='x0 inicial')
    plt.plot(xi, 0, 'go', markersize=8, label=f'Raíz ({round(xi, 8)})') 
    
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend()
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png', transparent=True)
    img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return {
        "tipo": "horner_newton", 
        "resultados": resultados, 
        "raiz": round(xi, 8),
        "convergencia": "Cuadrática O(n²) usando Doble División Sintética.",
        "grafica": grafica_url
    }
    
def metodo_muller(latex_str, x0, x1, x2, tol, max_iter):
    if not latex_str or latex_str.strip() == "":
        return {"error": True, "titulo": "🛑 Función vacía", "mensaje": "Escribe tu f(x)."}

    try:
        # 1. Limpieza a lo bruto (tu técnica infalible)
        latex_limpio = latex_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        f_latex = parse_latex(latex_limpio)
        f_simbolica = sp.expand(sp.sympify(str(f_latex)))

        simbolos_usados = [s for s in f_simbolica.free_symbols if str(s) not in ['e', 'pi']]
        if len(simbolos_usados) > 1: return {"error": True, "titulo": "🛑 Demasiadas Variables", "mensaje": f"Detectamos: {simbolos_usados}."}
        x = simbolos_usados[0] if len(simbolos_usados) == 1 else sp.Symbol('x')

    except Exception as err:
        return {"error": True, "titulo": "🛑 Error Matemático", "mensaje": f"Detalle: {str(err)}"}

    resultados = []
    
    # Muller trabaja mejor si forzamos a que todo sea "complex" desde el inicio
    cx0, cx1, cx2 = complex(x0), complex(x1), complex(x2)

    # Minifunción para evaluar la fórmula y forzar el resultado a complejo
    def evaluar(val):
        return complex(f_simbolica.subs(x, val).evalf())

    # 2. Ciclo de Muller
    for i in range(1, max_iter + 1):
        try:
            f0 = evaluar(cx0)
            f1 = evaluar(cx1)
            f2 = evaluar(cx2)

            # Distancias
            h0 = cx1 - cx0
            h1 = cx2 - cx1
            
            if h0 == 0 or h1 == 0:
                return {"error": True, "titulo": "⚠️ Estancamiento", "mensaje": "Los puntos colapsaron. Intenta con otros valores iniciales."}

            # Diferencias divididas
            d0 = (f1 - f0) / h0
            d1 = (f2 - f1) / h1

            # Coeficientes de la parábola
            a = (d1 - d0) / (h1 + h0)
            b = a * h1 + d1
            c = f2

            # El corazón de Muller: la raíz cuadrada que puede dar números imaginarios
            discriminante = cmath.sqrt(b**2 - 4*a*c)

            # Muller exige elegir el signo que haga el denominador más GRANDE para no dividir entre cero
            den_mas = b + discriminante
            den_menos = b - discriminante
            den = den_mas if abs(den_mas) >= abs(den_menos) else den_menos

            if den == 0:
                return {"error": True, "titulo": "⚠️ Denominador Cero", "mensaje": "El denominador de Muller se hizo cero."}

            # Calculamos la nueva raíz
            dx = -2 * c / den
            xr = cx2 + dx

            # Calculamos el error (usamos abs() que saca la magnitud real)
            ea = abs((xr - cx2) / xr) * 100 if xr != 0 else 100

            # Formateador visual: si la parte imaginaria es 0, lo muestra como número normal
            def fmt(num):
                if abs(num.imag) < 1e-8: return round(num.real, 6)
                return f"{round(num.real, 4)} + {round(num.imag, 4)}i".replace("+ -", "- ")

            resultados.append({
                "iteracion": i,
                "x0": fmt(cx0),
                "x1": fmt(cx1),
                "x2": fmt(cx2),
                "xr": fmt(xr),
                "fxr": fmt(evaluar(xr)),
                "ea": round(ea, 6) if i > 1 else "---"
            })

            if ea < tol:
                break
            
            # Recorremos los puntos
            cx0, cx1, cx2 = cx1, cx2, xr

        except Exception as e:
            return {"error": True, "titulo": "🛑 Error de Iteración", "mensaje": str(e)}

    # Extraemos la raíz final para mostrar
    raiz_mostrar = fmt(xr)
    es_compleja = abs(xr.imag) > 1e-8

    # 3. Gráfica
    margen = 3
    x_vals = np.linspace(cx2.real - margen, cx2.real + margen, 200)
    try:
        f_lambdify = sp.lambdify(x, f_simbolica, 'numpy')
        y_vals = f_lambdify(x_vals)
        if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
        y_vals = np.clip(y_vals, -100, 100)
    except: y_vals = np.zeros_like(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'f({x})', color='#dc3545', linewidth=2)
    plt.axhline(0, color='black', linewidth=1)
    
    if es_compleja:
        plt.plot(xr.real, 0, 'rx', markersize=10, label='Raíz Compleja (Proyectada)')
    else:
        plt.plot(xr.real, 0, 'go', markersize=8, label=f'Raíz Real ({raiz_mostrar})')
        
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend(); plt.tight_layout()

    img = io.BytesIO(); plt.savefig(img, format='png', transparent=True); img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8'); plt.close()

    return {
        "tipo": "muller",
        "resultados": resultados,
        "raiz": raiz_mostrar,
        "convergencia": "Raíces Complejas e Imaginarias",
        "grafica": grafica_url
    }
    
def metodo_bairstow(latex_str, r0, s0, tol, max_iter):
    if not latex_str or latex_str.strip() == "":
        return {"error": True, "titulo": "🛑 Polinomio vacío", "mensaje": "Escribe tu polinomio."}

    try:
        # 1. Limpieza bestial
        latex_limpio = latex_str.replace(r'\mathrm{e}', 'e').replace(r'\exponentialE', 'e').replace(r'\cdot', '*').lower()
        f_latex = parse_latex(latex_limpio)
        f_simbolica = sp.expand(sp.sympify(str(f_latex)))

        simbolos_usados = [s for s in f_simbolica.free_symbols if str(s) not in ['e', 'pi']]
        if len(simbolos_usados) > 1: return {"error": True, "titulo": "🛑 Demasiadas Variables", "mensaje": f"Detectamos: {simbolos_usados}."}
        x = simbolos_usados[0] if len(simbolos_usados) == 1 else sp.Symbol('x')

        # === EXTRACCIÓN A LO BRUTO ===
        grado_maximo = sp.degree(f_simbolica, gen=x)
        if str(grado_maximo) in ['oo', '-oo']: raise ValueError()
        if grado_maximo < 3:
            return {"error": True, "titulo": "⚠️ Grado Insuficiente", "mensaje": "Bairstow es para polinomios grandes. Escribe uno de grado 3 o mayor (ej. x^3 - 2x^2 + 1)."}

        # Coeficientes ordenados del grado mayor al independiente (a_n, a_{n-1}, ..., a_0)
        a = []
        for i in range(int(grado_maximo), -1, -1):
            coef = f_simbolica.subs(x, 0) if i == 0 else f_simbolica.coeff(x, i)
            a.append(float(coef))

    except Exception as err:
        return {"error": True, "titulo": "🛑 Error Matemático", "mensaje": "Asegúrate de ingresar un polinomio válido."}

    resultados = []
    n = len(a) - 1
    r = float(r0)
    s = float(s0)

    b = [0] * (n + 1)
    c = [0] * (n + 1)

    # 2. Ciclo de Bairstow (Doble división sintética)
    for iteracion in range(1, max_iter + 1):
        # Primera división sintética (Arreglo b)
        b[0] = a[0]
        b[1] = a[1] + r * b[0]
        for i in range(2, n + 1):
            b[i] = a[i] + r * b[i-1] + s * b[i-2]

        # Segunda división sintética (Arreglo c)
        c[0] = b[0]
        c[1] = b[1] + r * c[0]
        for i in range(2, n): # Se calcula solo hasta n-1
            c[i] = b[i] + r * c[i-1] + s * c[i-2]

        # Resolver sistema de ecuaciones para deltas
        det = c[n-2] * c[n-2] - c[n-1] * c[n-3]
        if det == 0:
            return {"error": True, "titulo": "⚠️ Determinante Cero", "mensaje": "El sistema colapsó. Intenta con otros valores de r0 y s0."}

        dr = (-b[n-1] * c[n-2] + b[n] * c[n-3]) / det
        ds = (-b[n] * c[n-2] + b[n-1] * c[n-1]) / det

        r += dr
        s += ds

        # Error máximo entre r y s
        ear = abs(dr / r) * 100 if r != 0 else 100
        eas = abs(ds / s) * 100 if s != 0 else 100
        ea = max(ear, eas)

        resultados.append({
            "iteracion": iteracion,
            "r": round(r, 6),
            "s": round(s, 6),
            "ea": round(ea, 6)
        })

        if ea < tol: break

    # 3. Calculamos las dos raíces encontradas por el factor cuadrático (x^2 - rx - s = 0)
    D = r**2 + 4*s
    x1 = (r + cmath.sqrt(D)) / 2
    x2 = (r - cmath.sqrt(D)) / 2

    def fmt_root(num):
        if abs(num.imag) < 1e-8: return f"{round(num.real, 4)}"
        return f"{round(num.real, 4)} {round(num.imag, 4):+}i"

    raiz_mostrar = f"x₁ = {fmt_root(x1)} &nbsp; | &nbsp; x₂ = {fmt_root(x2)}"

    # 4. Gráfica Visual
    margen = 3
    centro_x = x1.real if abs(x1.imag) < 1e-8 else 0
    x_vals = np.linspace(centro_x - margen, centro_x + margen, 200)
    try:
        f_lambdify = sp.lambdify(x, f_simbolica, 'numpy')
        y_vals = f_lambdify(x_vals)
        if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
        y_vals = np.clip(y_vals, -100, 100)
    except: y_vals = np.zeros_like(x_vals)

    plt.figure(figsize=(8, 4))
    plt.plot(x_vals, y_vals, label=f'P({x})', color='#6f42c1', linewidth=2)
    plt.axhline(0, color='black', linewidth=1)
    
    # Dibujar las raíces solo si son reales
    if abs(x1.imag) < 1e-8: plt.plot(x1.real, 0, 'go', markersize=8, label='Raíz x₁')
    if abs(x2.imag) < 1e-8: plt.plot(x2.real, 0, 'yo', markersize=8, label='Raíz x₂')
    
    plt.grid(color='gray', linestyle=':', linewidth=0.5)
    plt.legend(); plt.tight_layout()

    img = io.BytesIO(); plt.savefig(img, format='png', transparent=True); img.seek(0)
    grafica_url = base64.b64encode(img.getvalue()).decode('utf8'); plt.close()

    return {
        "tipo": "bairstow",
        "resultados": resultados,
        "raiz": raiz_mostrar, # Usamos formato HTML limpio para que el front lo pinte bonito
        "convergencia": "Extracción de un factor cuadrático.",
        "grafica": grafica_url
    }

# Rutas denavegación
@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/biseccion', methods=['GET', 'POST'])
def biseccion():
    datos = None
    if request.method == 'POST':
        
        funcion = request.form['ecuacion_latex']
        
        xl = float(request.form['xl'])
        xu = float(request.form['xu'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
        datos = metodo_biseccion(funcion, xl, xu, tol, max_iter)
        
    return render_template('biseccion.html', datos=datos)

@app.route('/falsa_posicion', methods=['GET', 'POST'])
def falsa_posicion():
    datos = None
    if request.method == 'POST':
        # Leemos la pizarra virtual
        funcion = request.form['ecuacion_latex']
        xl = float(request.form['xl'])
        xu = float(request.form['xu'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
        datos = metodo_falsa_posicion(funcion, xl, xu, tol, max_iter)
        
    return render_template('falsa_posicion.html', datos=datos)


@app.route('/newton', methods=['GET', 'POST'])
def newton():
    datos = None
    if request.method == 'POST':

        funcion = request.form['ecuacion_latex']
        x0 = float(request.form['x0'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
        datos = metodo_newton_raphson(funcion, x0, tol, max_iter)
        
    return render_template('newton.html', datos=datos)

@app.route('/secante', methods=['GET', 'POST'])
def secante():
    datos = None
    if request.method == 'POST':
        # Leemos la pizarra virtual
        funcion = request.form['ecuacion_latex']
        x0 = float(request.form['x0'])
        x1 = float(request.form['x1'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
        datos = metodo_secante(funcion, x0, x1, tol, max_iter)
        
    return render_template('secante.html', datos=datos)

@app.route('/taylor', methods=['GET', 'POST'])
def taylor():
    datos = None
    if request.method == 'POST':
        
        funcion = request.form['ecuacion_latex']
        
        
        x0 = float(request.form['x0'])
        x_eval = float(request.form['x_eval'])
        n_terminos = int(request.form['n_terminos'])
        
        datos = metodo_taylor(funcion, x0, x_eval, n_terminos)
        
    return render_template('taylor.html', datos=datos)

@app.route('/punto_fijo', methods=['GET', 'POST'])
def punto_fijo():
    datos = None
    if request.method == 'POST':
       
        funcion = request.form['ecuacion_latex'] 
        
        x0 = float(request.form['x0'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
  
        datos = metodo_punto_fijo(funcion, x0, tol, max_iter)
        
    return render_template('punto_fijo.html', datos=datos)

@app.route('/horner', methods=['GET', 'POST'])
def horner():
    datos = None
    if request.method == 'POST':
   
        funcion = request.form['ecuacion_latex']
        
        
        x0 = float(request.form['x0'])
        
        datos = metodo_horner(funcion, x0)
        
    return render_template('horner.html', datos=datos)

@app.route('/horner_newton', methods=['GET', 'POST'])
def horner_newton():
    datos = None
    if request.method == 'POST':
        funcion = request.form['ecuacion_latex']
        x0 = float(request.form['x0'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
        datos = metodo_horner_newton(funcion, x0, tol, max_iter)
        
    return render_template('horner_newton.html', datos=datos)

@app.route('/muller', methods=['GET', 'POST'])
def muller():
    datos = None
    if request.method == 'POST':
        funcion = request.form['ecuacion_latex']
        x0 = float(request.form['x0'])
        x1 = float(request.form['x1'])
        x2 = float(request.form['x2'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
        datos = metodo_muller(funcion, x0, x1, x2, tol, max_iter)
        
    return render_template('muller.html', datos=datos)

@app.route('/bairstow', methods=['GET', 'POST'])
def bairstow():
    datos = None
    if request.method == 'POST':
        funcion = request.form['ecuacion_latex']
        r0 = float(request.form['r0'])
        s0 = float(request.form['s0'])
        tol = float(request.form['tol'])
        max_iter = int(request.form['max_iter'])
        
        datos = metodo_bairstow(funcion, r0, s0, tol, max_iter)
        
    return render_template('bairstow.html', datos=datos)
if __name__ == '__main__':
    app.run(debug=True)