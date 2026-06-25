# Kirchhoff · Gauss-Jordan

Solver de sistemas de ecuaciones lineales NxN por el método de Gauss-Jordan,
con fracciones exactas. Diseñado para resolver sistemas de mallas por Kirchhoff
en circuitos eléctricos.

## Cómo desplegar en Render (paso a paso)

### 1. Sube el proyecto a GitHub

1. Crea un repositorio nuevo en https://github.com/new
   - Nombre sugerido: `kirchhoff-gauss-jordan`
   - Visibilidad: Public o Private (ambas funcionan en Render)

2. En tu computadora, abre una terminal en la carpeta del proyecto y ejecuta:

```bash
git init
git add .
git commit -m "primer commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/kirchhoff-gauss-jordan.git
git push -u origin main
```

### 2. Despliega en Render

1. Ve a https://render.com y crea una cuenta (gratuita)
2. Haz clic en **New +** → **Web Service**
3. Conecta tu cuenta de GitHub cuando te lo pida
4. Selecciona el repositorio `kirchhoff-gauss-jordan`
5. Render detectará automáticamente el `render.yaml` y rellenará los campos
6. Haz clic en **Create Web Service**
7. Espera ~2 minutos a que termine el build

### 3. Accede desde tu iPhone

Render te dará una URL del tipo:
```
https://kirchhoff-gauss-jordan.onrender.com
```

Ábrela en Safari. Para agregarla a tu pantalla de inicio:
1. Toca el ícono de compartir (cuadro con flecha hacia arriba)
2. Selecciona **Agregar a pantalla de inicio**
3. La app aparecerá como ícono nativo en tu iPhone

---

## Uso

- Selecciona el tamaño del sistema (2×2 hasta 5×5)
- Nombra tus variables (por defecto I₁, I₂, ...)
- Ingresa los coeficientes de la matriz aumentada [A | b]
  - Acepta enteros: `10`, `-4`
  - Fracciones: `1/2`, `-3/4`
  - Decimales: `0.5`
- Toca **Resolver →**
- Expande **Ver desarrollo paso a paso** para ver cada operación

## Estructura del proyecto

```
kirchhoff/
├── app.py              # Backend Flask
├── gauss_jordan.py     # Algoritmo Gauss-Jordan con Fraction
├── templates/
│   └── index.html      # Interfaz web (mobile-first)
├── requirements.txt    # Dependencias Python
├── render.yaml         # Configuración de despliegue
└── README.md
```

## Correr localmente

```bash
pip install flask
python app.py
# Abre http://localhost:5000
```
