from flask import Flask, request, jsonify
from models_productos import db, Producto
import os
import asyncio
from nats.aio.client import Client as NATS
from dotenv import load_dotenv
import json
import pybreaker

load_dotenv()

# Configuración del Flask y la base de datos
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI1')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=5)

async def publish_product_to_nats(product_data):
    try:
        nc = NATS()
        await nc.connect(servers=[os.getenv('NATS_SERVER_URL', 'nats://localhost:4222')])
        await nc.publish("products.updated", product_data.encode())
        print(f"Mensaje publicado: {product_data}")
        await nc.close()
    except Exception as e:
        print(f"Error al conectar con NATS: {str(e)}")
        raise  

@app.route('/productos', methods=['POST'])
def crear_producto():
    data = request.json
    if 'nombre' not in data or 'descripcion' not in data:
        return jsonify({"mensaje": "Datos incompletos"}), 400
    
    nuevo_producto = Producto(nombre=data['nombre'], descripcion=data['descripcion'])
    db.session.add(nuevo_producto)
    db.session.commit()

    product_data = json.dumps({"id": nuevo_producto.id, "nombre": nuevo_producto.nombre})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        breaker.call(loop.run_until_complete, publish_product_to_nats(product_data))
    except pybreaker.CircuitBreakerError:
        return jsonify({"mensaje": "Servicio no disponible, por favor intenta más tarde"}), 503
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return jsonify({"mensaje": "Error interno"}), 500
    finally:
        loop.close()

    return jsonify({"mensaje": "Producto creado", "id": nuevo_producto.id}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)