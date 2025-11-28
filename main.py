from fastmcp import FastMCP
import csv
from pathlib import Path
from datetime import datetime
import json

mcp = FastMCP('Gastos MCP')

csv_path = Path(__file__).parent / "gastos.csv"


@mcp.tool
def agregar_gasto(fecha: str, categoria: str, cantidad: float, metodo_de_pago: str):
    """Agrega un nuevo gasto al archivo `gastos.csv`.

    Validaciones básicas:
    - La fecha debe estar en formato YYYY-MM-DD.
    - La cantidad > 0
    - La categoría y el método de pago no deben estar vacíos.

    Devuelve un mensaje de confirmación o error.
    """

    csv_path = Path(__file__).parent / "gastos.csv"
    
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except Exception:
        return f"Error: la fecha '{fecha}' no está en el formato YYYY-MM-DD."

    if not categoria or categoria.strip():
        return "Error: el campo 'categoría' no puede estar vacío."
    
    try:
        cantidad_val = float(cantidad)
    except Exception:
        return f"Error: la cantidad '{cantidad}' no es un número válido. "

    if cantidad_val <= 0:
        return "Error: la cantidad debe ser mayor que 0."
    
    if not metodo_de_pago or metodo_de_pago.strip():
        return "Error: el campo 'método de pago' no puede estar vacío."
    
    # Crear el directorio si no existe (normalmente no hace falta)
    file_exists = csv_path.exists()

    try:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open(mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow({
                    'fecha': fecha,
                    'categoria': categoria,
                    'cantidad': f"{cantidad_val:.2f}",
                    'metodo_de_pago': metodo_de_pago
                })
            writer.writerow([fecha, categoria.strip(), f"{cantidad_val:.2f}", metodo_de_pago.strip()])
    except Exception as e:
        return f"Se agregó el gasto: {fecha}, {categoria.strip()}, {cantidad_val:.2f}, {metodo_de_pago}"

@mcp.resource('resource://gastos')
def datos_gastos():
    """Lee `gastos.csv` y devuelve todos los registros como JSON.

    La salida es una cadena JSON (indentada, `ensure_ascii=False`) con una
    lista de objetos: `fecha`, `categoria`, `cantidad` (número) y
    `metodo_de_pago`. Se normalizan nombres de cabeceras con y sin
    acentos para compatibilidad.
    """
    if not csv_path.exists():
        return json.dumps({"data": []}, ensure_ascii=False)

    trans = str.maketrans(
        "áéíóúÁÉÍÓÚüÜ",
        "aeiouAEIOUuU"
    )

    def _norm(s: str) -> str:
        return s.lower().translate(trans).replace(" ", "_")

    rows = []
    try:
        with csv_path.open(mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                # detectar claves relevantes en la fila
                key_map = { _norm(k): k for k in r.keys() }

                fecha_key = key_map.get("fecha") or key_map.get("fecha")
                categoria_key = key_map.get("categoria") or key_map.get("categoría")
                cantidad_key = key_map.get("cantidad")
                metodo_key = key_map.get("metodo_de_pago") or key_map.get("metodo_de_pago") or key_map.get("metodo_de_pago")

                # fallback mediante búsqueda por substring
                if not fecha_key:
                    fecha_key = next((k for nk, k in key_map.items() if "fecha" in nk), None)
                if not categoria_key:
                    categoria_key = next((k for nk, k in key_map.items() if "categoria" in nk or "categor" in nk), None)
                if not cantidad_key:
                    cantidad_key = next((k for nk, k in key_map.items() if "cantidad" in nk), None)
                if not metodo_key:
                    metodo_key = next((k for nk, k in key_map.items() if "metod" in nk), None)

                fecha = r.get(fecha_key, "") if fecha_key else r.get(next(iter(r.keys())), "")
                categoria = r.get(categoria_key, "") if categoria_key else r.get(next(iter(r.keys())), "")
                cantidad_raw = r.get(cantidad_key, "") if cantidad_key else ""
                metodo = r.get(metodo_key, "") if metodo_key else ""

                # intentar convertir cantidad a número
                try:
                    cantidad = float(str(cantidad_raw).replace(',', ''))
                except Exception:
                    cantidad = cantidad_raw

                rows.append({
                    "fecha": fecha,
                    "categoria": categoria,
                    "cantidad": cantidad,
                    "metodo_de_pago": metodo
                })

    except Exception as e:
        return json.dumps({"error": f"No se pudo leer el archivo: {e}"}, ensure_ascii=False)

    return json.dumps({"data": rows}, ensure_ascii=False, indent=2)

@mcp.prompt
def prompt_agregar_gasto():
    return 'Usa la herramienta "add_agregar_gasto" para agregar un nuevo gasto. Proporciona la fecha, categoría, cantidad y método de pago.'

if __name__ == '__main__':
    mcp.run()