import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS


# Configurar la conexión a la base de datos SQLite
DATABASE = 'inventario.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Crear la tabla 'pasajes' si no existe
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pasajes (
            codigo INTEGER PRIMARY KEY,
            destino TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio REAL NOT NULL
        ) ''')
    conn.commit()
    cursor.close()
    conn.close()

# Verificar si la base de datos existe, si no, crearla y crear la tabla
def create_database():
    conn = sqlite3.connect(DATABASE)
    conn.close()
    create_table()

# Programa principal
# Crear la base de datos y la tabla si no existen
create_database()

class Pasaje:
    # Definimos el constructor e inicializamos los atributos de instancia
    def __init__(self, codigo, destino, cantidad, precio):
        self.codigo = codigo           # Código 
        self.destino = destino         # Destino
        self.cantidad = cantidad       # Cantidad disponible (stock)
        self.precio = precio           # Precio 

    # Este método permite modificar un pasaje.
    def modificar(self, nuevo_destino, nueva_cantidad, nuevo_precio):
        self.destino = nuevo_destino          # Modifica la destino
        self.cantidad = nueva_cantidad        # Modifica la cantidad
        self.precio = nuevo_precio            # Modifica el precio

class Inventario:
    # Definimos el constructor e inicializamos los atributos de instancia
    def __init__(self):
        self.conexion = get_db_connection()
        self.cursor = self.conexion.cursor()

    # Este método permite crear objetos de la clase "Pasaje" y agregarlos al inventario.
    def agregar_pasaje(self, codigo, destino, cantidad, precio):
        pasaje_existente = self.consultar_pasaje(codigo)
        if pasaje_existente:
            return jsonify({'message': 'Ya existe un pasaje con ese código.'}), 400
        nuevo_pasaje = Pasaje(codigo, destino, cantidad, precio)
        sql = f'INSERT INTO pasajes VALUES ({codigo}, "{destino}", {cantidad}, {precio});'
        self.cursor.execute(sql)
        self.conexion.commit()
        return jsonify({'message': 'Pasaje agregado correctamente.'}), 200


    # Este método permite consultar datos de pasajes que están en el inventario
    # Devuelve el pasaje correspondiente al código proporcionado o False si no existe.
    def consultar_pasaje (self, codigo):
        sql = f'SELECT * FROM pasajes WHERE codigo = {codigo};'
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        if row:
            codigo, destino, cantidad, precio = row
            return Pasaje(codigo, destino, cantidad, precio)
        return None


    # Este método permite modificar datos de pasajes que están en el inventario
    # Utiliza el método consultar_pasaje del inventario y modificar del pasaje.
    def modificar_pasaje(self, codigo, nuevo_destino, nueva_cantidad, nuevo_precio):
        pasaje = self.consultar_pasaje(codigo)
        if pasaje:
            pasaje.modificar(nuevo_destino, nueva_cantidad, nuevo_precio)
            sql = f'UPDATE pasajes SET destino = "{nuevo_destino}", cantidad = {nueva_cantidad}, precio = {nuevo_precio} WHERE codigo = {codigo};' 
            self.cursor.execute(sql)
            self.conexion.commit()
            return jsonify({'message': 'Pasaje modificado correctamente.'}), 200
        return jsonify({'message': 'Pasaje no encontrado.'}), 404
     
     # Este método imprime en la terminal una lista con los datos de los pasajes que figuran en el inventario.
    def listar_pasajes(self):
        self.cursor.execute("SELECT * FROM pasajes")
        rows = self.cursor.fetchall()
        pasajes = []
        for row in rows:
            codigo, destino, cantidad, precio = row
            pasaje = {'codigo': codigo, 'destino': destino, 'cantidad': cantidad, 'precio': precio}
            pasajes.append(pasaje)
        return jsonify(pasajes), 200

    # Este método elimina el pasaje indicado por codigo de la lista mantenida en el inventario.
    def eliminar_pasaje(self, codigo):
        sql = f'DELETE FROM pasajes WHERE codigo = {codigo};' 
        self.cursor.execute(sql)
        if self.cursor.rowcount > 0:
            self.conexion.commit()
            return jsonify({'message': 'Pasaje eliminado correctamente.'}), 200
        return jsonify({'message': 'Pasaje no encontrado.'}), 404

  
class Carrito:
    # Definimos el constructor e inicializamos los atributos de instancia
    def __init__(self):
        self.conexion = get_db_connection()
        self.cursor = self.conexion.cursor()
        self.items = []

    # Este método permite agregar pasajes del inventario al carrito.
    def agregar(self, codigo, cantidad, inventario):
        pasaje = inventario.consultar_pasaje(codigo)
        if pasaje is None:
            return jsonify({'message': 'El pasaje no existe.'}), 404
        if pasaje.cantidad < cantidad:
            return jsonify({'message': 'Cantidad en stock insuficiente.'}), 400

        for item in self.items:
            if item.codigo == codigo:
                item.cantidad += cantidad
                sql = f'UPDATE Pasajes SET cantidad = cantidad - {cantidad}  WHERE codigo = {codigo};'
                self.cursor.execute(sql)
                self.conexion.commit()
                return jsonify({'message': 'Pasaje agregado al carrito correctamente.'}), 200

        nuevo_item = Pasaje(codigo, pasaje.destino, cantidad, pasaje.precio)
        self.items.append(nuevo_item)
        sql = f'UPDATE pasajes SET cantidad = cantidad - {cantidad}  WHERE codigo = {codigo};'
        self.cursor.execute(sql)
        self.conexion.commit()
        return jsonify({'message': 'Pasaje agregado al carrito correctamente.'}), 200


    # Este método quita unidades de un elemento del carrito, o lo elimina.
    def quitar(self, codigo, cantidad, inventario):
        for item in self.items:
            if item.codigo == codigo:
                if cantidad > item.cantidad:
                    return jsonify({'message': 'Cantidad a quitar mayor a la cantidad en el carrito.'}), 400
                item.cantidad -= cantidad
                if item.cantidad == 0:
                    self.items.remove(item)
                sql = f'UPDATE pasajes SET cantidad = cantidad + {cantidad} WHERE codigo = {codigo};'
                self.cursor.execute(sql)
                self.conexion.commit()
                return jsonify({'message': 'Pasaje quitado del carrito correctamente.'}), 200
        return jsonify({'message': 'El pasaje no se encuentra en el carrito.'}), 404
    
    def mostrar(self):
        pasajes_carrito = []
        for item in self.items:
            pasaje = {'codigo': item.codigo, 'destino': item.destino, 'cantidad': item.cantidad, 'precio': item.precio}
            pasajes_carrito.append(pasaje)
        return jsonify(pasajes_carrito), 200

app = Flask(__name__)
CORS(app)

carrito = Carrito()         # Instanciamos un carrito
inventario = Inventario()   # Instanciamos un inventario

# Ruta para obtener los datos de un pasaje según su código
@app.route('/pasajes/<int:codigo>', methods=['GET'])
def obtener_pasaje(codigo):
    pasaje = inventario.consultar_pasaje(codigo)
    if pasaje:
        return jsonify({
            'codigo': pasaje.codigo,
            'destino': pasaje.destino,
            'cantidad': pasaje.cantidad,
            'precio': pasaje.precio
        }), 200
    return jsonify({'message': 'Pasaje no encontrado.'}), 404

# Ruta para obtener el index
@app.route('/')
def index():
    return 'API de Inventario'

# Ruta para obtener la lista de pasajes del inventario
@app.route('/pasajes', methods=['GET'])
def obtener_pasajes():
    return inventario.listar_pasajes()

# Ruta para agregar un pasaje al inventario
@app.route('/pasajes', methods=['POST'])
def agregar_pasaje():
    codigo = request.json.get('codigo')
    destino = request.json.get('destino')
    cantidad = request.json.get('cantidad')
    precio = request.json.get('precio')
    return inventario.agregar_pasaje(codigo, destino, cantidad, precio)

# Ruta para modificar un pasaje del inventario
@app.route('/pasajes/<int:codigo>', methods=['PUT'])
def modificar_pasaje(codigo):
    nuevo_destino = request.json.get('destino')
    nueva_cantidad = request.json.get('cantidad')
    nuevo_precio = request.json.get('precio')
    return inventario.modificar_pasaje(codigo, nuevo_destino, nueva_cantidad, nuevo_precio)

# Ruta para eliminar un pasaje del inventario
@app.route('/pasajes/<int:codigo>', methods=['DELETE'])
def eliminar_pasaje(codigo):
    return inventario.eliminar_pasaje(codigo)

# Ruta para agregar un pasaje al carrito
@app.route('/carrito', methods=['POST'])
def agregar_carrito():
    codigo = request.json.get('codigo')
    cantidad = request.json.get('cantidad')
    inventario = Inventario()
    return carrito.agregar(codigo, cantidad, inventario)

# Ruta para quitar un pasaje del carrito
@app.route('/carrito', methods=['DELETE'])
def quitar_carrito():
    codigo = request.json.get('codigo')
    cantidad = request.json.get('cantidad')
    inventario = Inventario()
    return carrito.quitar(codigo, cantidad, inventario)

# Ruta para obtener el contenido del carrito
@app.route('/carrito', methods=['GET'])
def obtener_carrito():
    return carrito.mostrar()

# Finalmente, si estamos ejecutando este archivo, lanzamos app.
if __name__ == '__main__':
    app.run()
