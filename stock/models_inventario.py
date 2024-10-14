from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Inventario(db.Model):
    __tablename__ = 'inventario'

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Inventario {self.producto_id}: {self.cantidad}>'
