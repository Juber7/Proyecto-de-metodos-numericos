
# 🧮 Proyecto de Métodos Numéricos

Aplicación web interactiva desarrollada en Python (Flask) para resolver ecuaciones no lineales y calcular series de Taylor. Incluye evaluación simbólica de funciones matematicas, cálculo de errores, tablas iterativas y generación de gráficas dinámicas.

## 🛠️ Tecnologías Utilizadas
* **Backend:** Python, Flask
* **Motor Matemático:** SymPy (Cálculo simbólico y derivadas), NumPy
* **Gráficas:** Matplotlib
* **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2

---

## 🚀 Guía de Instalación para el Equipo

Para correr este proyecto en tu computadora local, sigue estos pasos al pie de la letra:

### 1. Clonar el repositorio
Abre tu terminal y clona este proyecto (o descárgalo como ZIP y descomprímelo):
```bash
git clone https://github.com/Juber7/Proyecto-de-metodos-numericos.git
cd nombre-de-tu-carpeta
```

### 2. Crear entorno virtual
En la carpeta donde bajaste el proyecto
```bash
python -m venv venv
.\venv\Scripts\activate <- (para activar el entorno virtual)
```
### 3. Instalar las librerias necesarias
En la terminal (powershell)
```bash
pip install Flask sympy numpy matplotlib gunicorn
```

Y para correr el servidor
```bash
python home.py
```
## 📂 Estructura del Proyecto
home.py: Archivo principal con las rutas de Flask y la lógica de los métodos numéricos.

* **templates/:** Contiene las vistas HTML.

* **base.html:** Plantilla maestra con la barra de navegación lateral.

* **index.html:** Pantalla de bienvenida.

* **biseccion.html:** Vista de la calculadora del método de bisección.

* **_resultados.html:** Plantilla parcial reutilizable para mostrar tablas y gráficas.

* **.gitignore:** Archivos y carpetas que Git no debe subir (como venv/).
