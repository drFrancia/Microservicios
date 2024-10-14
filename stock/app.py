from flask import Flask, jsonify
from models_inventario import db, Inventario
import os
from dotenv import load_dotenv
from nats.aio.client import Client as NATS
import asyncio
import json
import threading

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI2')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

async def message_handler(msg):
    try:
        data = json.loads(msg.data.decode())
        producto_id = data['id']
        nombre = data['nombre']
        print(f"Producto recibido: ID = {producto_id}, Nombre = {nombre}")
        
        with app.app_context():
            inventario = Inventario.query.filter_by(producto_id=producto_id).first()
            if not inventario:
                inventario = Inventario(producto_id=producto_id, cantidad=0)
                db.session.add(inventario)
            db.session.commit()
        
    except Exception as e:
        print(f"Error procesando mensaje: {str(e)}")

@app.route('/inventario/<int:producto_id>', methods=['GET'])
def obtener_inventario(producto_id):
    inventario = Inventario.query.filter_by(producto_id=producto_id).first()
    if inventario:
        return jsonify({"producto_id": producto_id, "cantidad": inventario.cantidad}), 200
    else:
        return jsonify({"mensaje": "Producto no encontrado"}), 404

async def run_nats():
    nc = NATS()
    await nc.connect(os.getenv('NATS_SERVER_URL', 'nats://localhost:4222'))
    await nc.subscribe("products.updated", cb=message_handler)
    print("Esperando mensajes...")
    
    while True:
        await asyncio.sleep(1)

def run_nats_forever():
    asyncio.run(run_nats())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    nats_thread = threading.Thread(target=run_nats_forever)
    nats_thread.start()
    
    app.run(host='0.0.0.0', port=5001, debug=True)