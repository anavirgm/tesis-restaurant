from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re
import os

app = Flask(__name__)

# Configuración de la clave secreta
app.secret_key = os.environ.get('SECRET_KEY', 'tu_clave_secreta')

# Configuración de la base de datos MySQL en Clever Cloud
db_user = 'utoxyrvuz8fbadhw'
db_password = 'FjgB1gcbXmC4i50ze7UI'
db_host = 'bdqjuxpj0akcxmtxeigj-mysql.services.clever-cloud.com'
db_name = 'bdqjuxpj0akcxmtxeigj'
db_port = '3306'
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Definir modelos para cada tabla
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    rol = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Guardar contraseña en texto plano (no recomendado)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class Mesa(db.Model):
    __tablename__ = 'mesas'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, unique=True, nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='libre')
    comensales = db.Column(db.Integer, nullable=False, default=0)  # Número de comensales actuales
    max_comensales = db.Column(db.Integer, nullable=False)  # Máximo de comensales permitidos

class Extra(db.Model):
    __tablename__ = 'extras'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class PlatoExtras(db.Model):
    __tablename__ = 'plato_extras'
    id = db.Column(db.Integer, primary_key=True)
    plato_id = db.Column(db.Integer, db.ForeignKey('menu.id', ondelete='CASCADE'))
    extra_id = db.Column(db.Integer, db.ForeignKey('extras.id', ondelete='CASCADE'))

    plato = db.relationship('Plato', backref='plato_extras')
    extra = db.relationship('Extra', backref='plato_extras')

class Plato(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=True)
    precio = db.Column(db.Float, nullable=False)
    extras = db.Column(db.String(200), nullable=True)
    imagen = db.Column(db.String(200), nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    categoria = db.relationship('Categoria', backref=db.backref('platos', lazy=True))

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(50), nullable=False)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesas.id', ondelete='CASCADE'), nullable=True)  # Si no es del restaurante, puede ser None
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now)
    ubicacion = db.Column(db.String(200), nullable=True)  # Nueva columna para almacenar la dirección del cliente

    # Relación con el modelo Usuario
    usuario = db.relationship('Usuario', backref='pedidos')
    

class Factura(db.Model):
    __tablename__ = 'facturas'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    pagado = db.Column(db.Boolean, default=False)

    # Relación con Pedido
    pedido = db.relationship('Pedido', backref='facturas')

class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedidos'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    extras = db.Column(db.String(200), nullable=True)

    # Relación con el modelo Plato (Menu)
    menu = db.relationship('Plato', backref='detalle_pedidos')
# Ruta principal redirige a login
@app.route('/')
def index():
    return redirect(url_for('login'))

# Función de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cedula = request.form['cedula']
        password = request.form['password']
        
        # Consulta a la base de datos para encontrar al usuario por cédula
        user = Usuario.query.filter_by(cedula=cedula).first()
        
        # Verifica si el usuario existe y si la contraseña es correcta
        if user and user.password == password:
            # Guardar información del usuario en la sesión
            session['user_id'] = user.id          # ID del usuario
            session['user_role'] = user.rol        # Rol del usuario (usuario, empleado, administrador)
            session['user_name'] = user.nombre      # Nombre del usuario
            
            # Redirigir al dashboard
            return redirect(url_for('dashboard'))
        else:
            # Mensaje de error si las credenciales son incorrectas
            flash('Cédula o contraseña incorrectos.')

    return render_template('login.html')

# Cerrar sesión
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

def iniciar_sesion(usuario):
    session['user_id'] = usuario.id  # Almacenar el ID del usuario en la sesión
    print(f"Usuario {usuario.nombre} ha iniciado sesión.")

# Gestionar mesas
@app.route('/mesas')
def mesas():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    mesas = Mesa.query.all()
    return render_template('mesas.html', mesas=mesas)

@app.route('/editar_mesa/<int:mesa_id>', methods=['POST'])
def editar_mesa(mesa_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    mesa = Mesa.query.get_or_404(mesa_id)
    
    # Actualizar solo el estado y los comensales
    mesa.comensales = request.form.get('comensales')
    mesa.estado = request.form.get('estado')

    db.session.commit()
    flash('Mesa actualizada exitosamente')
    return redirect(url_for('mesas'))

@app.route('/eliminar_mesa/<int:mesa_id>', methods=['POST'])
def eliminar_mesa(mesa_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    mesa = Mesa.query.get_or_404(mesa_id)
    db.session.delete(mesa)
    db.session.commit()
    flash('Mesa eliminada exitosamente')
    return redirect(url_for('mesas_admin'))

@app.route('/mesas_admin', methods=['GET', 'POST'])
def mesas_admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Agregar nueva mesa
        numero = request.form.get('numero')
        max_comensales = request.form.get('max_comensales')
        estado = request.form.get('estado', 'libre')  # Estado por defecto
        nueva_mesa = Mesa(numero=numero, max_comensales=max_comensales, estado=estado, comensales=0)
        
        db.session.add(nueva_mesa)
        db.session.commit()
        flash('Mesa agregada exitosamente')
        return redirect(url_for('mesas_admin'))

    mesas = Mesa.query.all()
    return render_template('mesas_admin.html', mesas=mesas)

def procesar_creacion_pedido(estado, mesa_id):
    # Obtener el ID del usuario desde la sesión
    usuario_id = session.get('user_id')

    if not usuario_id:
        print("Error: No se pudo obtener el usuario logueado.")
        return

    # Llamar a la función crear_pedido con el usuario_id correcto
    crear_pedido(estado, mesa_id, usuario_id)

def crear_pedido(estado, mesa_id, usuario_id):
    mesa = Mesa.query.get(mesa_id)  # Verificar si la mesa existe
    if not mesa:
        print(f"Error: la mesa con id {mesa_id} no existe.")
        return  # No intentamos crear el pedido si no hay mesa

    # Crear el nuevo pedido
    nuevo_pedido = Pedido(
        estado=estado,
        mesa_id=mesa_id,
        usuario_id=usuario_id,
        fecha=datetime.now()
    )
    
    db.session.add(nuevo_pedido)
    try:
        db.session.commit()
        print("Pedido creado con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear el pedido: {e}")

def procesar_verificacion_creacion_pedido(estado, mesa_id):
    # Obtener el ID del usuario desde la sesión
    usuario_id = session.get('user_id')

    if not usuario_id:
        print("Error: No se pudo obtener el usuario logueado.")
        return

    # Llamar a la función verificar_y_crear_pedido con el usuario_id correcto
    verificar_y_crear_pedido(estado, mesa_id, usuario_id)

def verificar_y_crear_pedido(estado, mesa_id, usuario_id=None, ubicacion=None):
    usuario = Usuario.query.get(usuario_id)

    if usuario:
        # Si el rol del usuario es "empleado" o "administrador"
        if usuario.rol in ["empleado", "administrador"]:
            ubicacion = None  # No se requiere ubicación, ya que es un pedido en el restaurante
        else:
            # Verificar que se proporcione una ubicación para clientes que no están en el restaurante
            if not ubicacion:
                print("Error: Se requiere una ubicación para pedidos fuera del restaurante.")
                return

    # Crear el nuevo pedido
    nuevo_pedido = Pedido(
        estado=estado,
        mesa_id=mesa_id if usuario.rol in ["empleado", "administrador"] else None,  # Si no es empleado/admin, mesa_id es None
        usuario_id=usuario_id,
        fecha=datetime.now(),
        ubicacion=ubicacion
    )

    db.session.add(nuevo_pedido)
    try:
        db.session.commit()
        print("Pedido creado con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear el pedido: {e}")
        
def obtener_pedidos():
    pedidos = Pedido.query.all()
    for pedido in pedidos:
        print(f"Pedido ID: {pedido.id}, Estado: {pedido.estado}, Mesa: {pedido.mesa_id}, Fecha: {pedido.fecha}, Usuario ID: {pedido.usuario_id}")

def crear_usuario(nombre, correo):
    nuevo_usuario = Usuario(
        nombre=nombre,
        correo=correo
    )
    db.session.add(nuevo_usuario)
    try:
        db.session.commit()
        print(f"Usuario {nombre} creado con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear el usuario: {e}")

@app.route('/mesas/<int:mesa_id>/cambiar_estado')
def cambiar_estado(mesa_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    mesa = Mesa.query.get_or_404(mesa_id)
    mesa.estado = 'ocupada' if mesa.estado == 'libre' else 'libre'
    db.session.commit()
    return redirect(url_for('mesas'))

# Gestionar menú (cliente)
@app.route('/menu_cliente')
def menu_cliente():
    categoria_id = request.args.get('categoria_id', None)  # Obtener el id de la categoría seleccionada
    
    if categoria_id:
        platos = Plato.query.filter_by(categoria_id=categoria_id).all()
    else:
        platos = Plato.query.all()  # Mostrar todos los platos si no se selecciona ninguna categoría

    categorias = Categoria.query.all()  # Cargar todas las categorías
    return render_template('menu_cliente.html', platos=platos, categorias=categorias)

# Inicializar carrito de compras en la sesión
@app.before_request
def inicializar_carrito():
    if 'carrito' not in session:
        session['carrito'] = []


@app.route('/agregar_carrito', methods=['POST'])
def agregar_carrito():
    plato_id = request.form.get('plato_id')
    cantidad = int(request.form.get(f'cantidad_{plato_id}', 1))

    # Obtener el plato de la base de datos
    plato = Plato.query.get(plato_id)

    if plato:
        # Obtener los extras seleccionados (puede ser una lista)
        extras_seleccionados = request.form.getlist(f'extras_{plato_id}')

        # Crear el item del carrito
        item = {
            'id': plato.id,
            'nombre': plato.nombre,
            'cantidad': cantidad,
            'precio_unitario': plato.precio,
            'precio_total': plato.precio * cantidad,
            'extras': extras_seleccionados  # Guardar los extras seleccionados
        }

        # Manejar el carrito dentro de la sesión
        if 'carrito' not in session:
            session['carrito'] = []

        # Agregar el item al carrito
        session['carrito'].append(item)
        session.modified = True

    return redirect(url_for('menu_cliente'))

# Finalizar compra
@app.route('/finalizar_compra', methods=['POST'])
def finalizar_compra():
    if not session.get('carrito'):
        flash('El carrito está vacío.')
        return redirect(url_for('menu_cliente'))

    # Obtener el ID del usuario desde la sesión
    usuario_id = session.get('user_id')

    if not usuario_id:
        flash('Error: No se pudo obtener el usuario logueado.')
        return redirect(url_for('menu_cliente'))

    # Verificar si el usuario es cliente
    usuario = Usuario.query.get(usuario_id)
    if usuario.rol not in ["empleado", "administrador"]:
        # Redirigir al módulo de simulación de pago
        return redirect(url_for('simulacion_pago'))

    # Si es empleado o administrador, proceder directamente
    return crear_y_procesar_pedido(usuario_id, None)  # Sin ubicación

@app.route('/ingresar_direccion', methods=['GET', 'POST'])
def ingresar_direccion():
    if request.method == 'POST':
        direccion = request.form.get('direccion')

        if not direccion:
            flash('Por favor ingresa una dirección válida.')
            return render_template('ingresar_direccion.html')

        # Obtener el ID del usuario desde la sesión
        usuario_id = session.get('user_id')

        # Procesar el pedido con la dirección ingresada
        return crear_y_procesar_pedido(usuario_id, direccion)

    return render_template('ingresar_direccion.html')

def crear_y_procesar_pedido(usuario_id, ubicacion=None):
    # Crear nuevo pedido
    nuevo_pedido = Pedido(
        mesa_id=None if ubicacion else 1,  # Si hay ubicación, no hay mesa (pedido fuera del restaurante)
        estado='pendiente',
        usuario_id=usuario_id,
        ubicacion=ubicacion,
        fecha=datetime.now()
    )
    db.session.add(nuevo_pedido)
    db.session.commit()

    # Crear detalle de pedido para cada plato en el carrito
    total = 0
    for item in session['carrito']:
        extras = ', '.join(item['extras']) if item.get('extras') else None

        detalle = DetallePedido(
            pedido_id=nuevo_pedido.id,
            menu_id=item['id'],
            cantidad=item['cantidad'],
            precio_unitario=item['precio_unitario'],
            extras=extras  # Guardar los extras seleccionados como string
        )
        total += item['precio_total']
        db.session.add(detalle)

    # Crear factura
    nueva_factura = Factura(
        pedido_id=nuevo_pedido.id,
        total=total,
        pagado=False
    )
    db.session.add(nueva_factura)
    db.session.commit()

    # Vaciar el carrito
    session['carrito'] = []
    session.modified = True

    flash('Compra realizada exitosamente.')
    return redirect(url_for('historial'))

@app.route('/detalle_pedido/<int:pedido_id>')
def detalle_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # Verificar que el pedido pertenece al usuario actual
    if pedido.usuario_id != session.get('user_id'):
        return redirect(url_for('historial'))

    detalles = DetallePedido.query.filter_by(pedido_id=pedido_id).all()

    return render_template('detalle_pedido.html', pedido=pedido, detalles=detalles)

@app.route('/simulacion_pago', methods=['GET', 'POST'])
def simulacion_pago():
    if request.method == 'POST':
        metodo_pago = request.form.get('metodo_pago')

        if metodo_pago == 'tarjeta':
            numero_tarjeta = request.form.get('numero_tarjeta')
            nombre_tarjeta = request.form.get('nombre_tarjeta')
            vencimiento = request.form.get('vencimiento')
            cvv = request.form.get('cvv')

            # Validaciones básicas
            if not numero_tarjeta or len(numero_tarjeta) != 16 or not numero_tarjeta.isdigit():
                flash('Número de tarjeta inválido (16 dígitos requeridos).')
                return redirect(url_for('simulacion_pago'))
            if not nombre_tarjeta:
                flash('Nombre en la tarjeta requerido.')
                return redirect(url_for('simulacion_pago'))
            if not vencimiento or not re.match(r'(0[1-9]|1[0-2])/[0-9]{2}', vencimiento):
                flash('Fecha de vencimiento inválida (formato MM/YY).')
                return redirect(url_for('simulacion_pago'))
            if not cvv or len(cvv) not in [3, 4] or not cvv.isdigit():
                flash('CVV inválido (3-4 dígitos requeridos).')
                return redirect(url_for('simulacion_pago'))

        elif metodo_pago == 'transferencia':
            numero_referencia = request.form.get('numero_referencia')
            if not numero_referencia or not numero_referencia.isdigit():
                flash('Número de referencia inválido.')
                return redirect(url_for('simulacion_pago'))

        else:
            flash('Método de pago no válido.')
            return redirect(url_for('simulacion_pago'))

        # Redirigir al módulo de dirección tras el pago
        flash('Pago simulado con éxito. Por favor, ingresa tu dirección.')
        return redirect(url_for('ingresar_direccion'))

    # Mostrar el carrito en el formulario de pago
    carrito = session.get('carrito', [])
    total = sum(item['precio_total'] for item in carrito)

    return render_template('simulacion_pago.html', carrito=carrito, total=total)

@app.route('/historial')
def historial():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Asegurarse de que solo los usuarios tengan acceso al historial
    if session['user_role'] in ['administrador', 'empleado']:
        return redirect(url_for('dashboard'))  # O redirigir a cualquier otra página

    pedidos = Pedido.query.filter_by(usuario_id=session['user_id']).all()
    pedidos_detallados = []
    
    for pedido in pedidos:
        detalles = DetallePedido.query.filter_by(pedido_id=pedido.id).all()
        detalles_comida = []
        
        for detalle in detalles:
            comida = Plato.query.get(detalle.menu_id)
            extras = []
            if detalle.extras:  # Verifica si hay extras
                extras = detalle.extras.split(',')  # Asumiendo que extras se guarda como cadena separada por comas
            
            detalles_comida.append({
                'nombre_plato': comida.nombre,
                'cantidad': detalle.cantidad,
                'extras': extras  # Ahora se pasa como lista
            })

        factura = Factura.query.filter_by(pedido_id=pedido.id).first()

        # Actualizar factura a "pagado" si el usuario no es administrador ni empleado
        if session['user_role'] not in ['administrador', 'empleado'] and not factura.pagado:
            factura.pagado = True
            db.session.commit()  # Guardar el cambio en la base de datos

        pedidos_detallados.append({
            'pedido': pedido,
            'detalles_comida': detalles_comida,
            'factura': factura
        })

    return render_template('historial.html', pedidos=pedidos_detallados)

# Gestionar menú (administrador)
@app.route('/menu_admin')
def menu_admin():
    if 'user_role' not in session or session['user_role'] != 'administrador':
        return redirect(url_for('login'))
    platos = Plato.query.all()
    categorias = Categoria.query.all()  # Agrega esta línea para obtener las categorías
    return render_template('menu_admin.html', platos=platos, categorias=categorias)  # Incluye las categorías en la renderización

# Agregar plato (administrador)
@app.route('/menu/agregar', methods=['GET', 'POST'])
def agregar_plato():
    if 'user_role' not in session or session['user_role'] != 'administrador':
        return redirect(url_for('login'))

    categorias = Categoria.query.all()

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = float(request.form['precio'])
        categoria_id = request.form['categoria_id']

        # Crear y guardar el plato
        nuevo_plato = Plato(
            nombre=nombre, descripcion=descripcion, precio=precio, categoria_id=categoria_id
        )
        db.session.add(nuevo_plato)
        db.session.commit()

        # Procesar los extras añadidos en el formulario
        extras_nuevos = request.form.getlist('extras')
        for extra_nombre in extras_nuevos:
            if extra_nombre.strip():  # Verifica que no esté vacío
                extra = Extra(nombre=extra_nombre.strip())
                db.session.add(extra)
                db.session.commit()

                # Relacionar el extra con el plato
                plato_extra = PlatoExtras(plato_id=nuevo_plato.id, extra_id=extra.id)
                db.session.add(plato_extra)

        db.session.commit()
        flash('Plato y extras agregados exitosamente.')
        return redirect(url_for('menu_admin'))

    return render_template('agregar_plato.html', categorias=categorias)
# Editar plato
@app.route('/menu/editar/<int:plato_id>', methods=['GET', 'POST'])
def editar_plato(plato_id):
    if 'user_role' not in session or session['user_role'] != 'administrador':
        return redirect(url_for('login'))

    plato = Plato.query.get_or_404(plato_id)
    categorias = Categoria.query.all()
    extras = Extra.query.all()

    if request.method == 'POST':
        plato.nombre = request.form['nombre']
        plato.descripcion = request.form['descripcion']
        plato.precio = float(request.form['precio'])
        plato.categoria_id = int(request.form['categoria_id'])

        PlatoExtras.query.filter_by(plato_id=plato.id).delete()

        for extra_id in request.form.getlist('extras'):
            plato_extra = PlatoExtras(plato_id=plato.id, extra_id=int(extra_id))
            db.session.add(plato_extra)

        db.session.commit()
        flash('Plato actualizado exitosamente.')
        return redirect(url_for('menu_admin'))

    return render_template('editar_plato.html', plato=plato, categorias=categorias, extras=extras)

# Eliminar plato
@app.route('/menu/eliminar/<int:plato_id>', methods=['POST'])
def eliminar_plato(plato_id):
    if 'user_role' not in session or session['user_role'] != 'administrador':
        return redirect(url_for('login'))

    plato = Plato.query.get_or_404(plato_id)
    db.session.delete(plato)
    db.session.commit()

    flash('Plato eliminado exitosamente.')
    return redirect(url_for('menu_admin'))

@app.route('/marcar_listo/<int:pedido_id>', methods=['POST'])
def marcar_listo(pedido_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Obtener el pedido por ID
    pedido = Pedido.query.get_or_404(pedido_id)

    # Cambiar el estado del pedido a "listo"
    pedido.estado = 'listo'
    
    db.session.commit()

    return redirect(url_for('cocina'))

@app.route('/marcar_pagado/<int:factura_id>', methods=['POST'])
def marcar_pagado(factura_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Obtener la factura por ID
    factura = Factura.query.get_or_404(factura_id)

    # Cambiar el estado de la factura a pagado
    factura.pagado = True
    
    db.session.commit()

    return redirect(url_for('facturacion'))

# Función para la cocina
@app.route('/cocina')
def cocina():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    pedidos = Pedido.query.all()
    pedidos_detallados = []
    
    for pedido in pedidos:
        detalles = DetallePedido.query.filter_by(pedido_id=pedido.id).all()
        detalles_comida = []
        
        for detalle in detalles:
            comida = Plato.query.get(detalle.menu_id)
            extras = []
            if detalle.extras:  # Verifica si hay extras
                extras = detalle.extras.split(',')
            
            detalles_comida.append({
                'nombre_plato': comida.nombre,
                'cantidad': detalle.cantidad,
                'extras': extras  # Ahora se pasa como lista
            })
        
        pedidos_detallados.append({
            'pedido': pedido,
            'detalles_comida': detalles_comida
        })

    return render_template('cocina.html', pedidos=pedidos_detallados)

# Función para la facturación
@app.route('/facturacion')
def facturacion():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    facturas = Factura.query.all()
    facturas_detalladas = []
    
    for factura in facturas:
        pedido = factura.pedido
        detalles = DetallePedido.query.filter_by(pedido_id=pedido.id).all()
        detalles_comida = []
        
        for detalle in detalles:
            comida = Plato.query.get(detalle.menu_id)
            extras = []
            if detalle.extras:  # Verifica si hay extras
                extras = detalle.extras.split(',')
                
            detalles_comida.append({
                'nombre_plato': comida.nombre,
                'cantidad': detalle.cantidad,
                'extras': extras  # Ahora se pasa como lista
            })
        
        facturas_detalladas.append({
            'factura': factura,
            'detalles_comida': detalles_comida
        })

    return render_template('facturacion.html', facturas=facturas_detalladas)
@app.route('/borrar_pedido/<int:pedido_id>', methods=['POST'])
def borrar_pedido(pedido_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Obtener el pedido por ID
    pedido = Pedido.query.get_or_404(pedido_id)

    # Borrar el pedido
    db.session.delete(pedido)
    db.session.commit()

    return redirect(url_for('cocina'))

@app.route('/borrar_factura/<int:factura_id>', methods=['POST'])
def borrar_factura(factura_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Obtener la factura por ID
    factura = Factura.query.get_or_404(factura_id)

    # Borrar la factura
    db.session.delete(factura)
    db.session.commit()

    return redirect(url_for('facturacion'))

# Función para la configuración
@app.route('/configuracion')
def configuracion():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('configuracion.html')

@app.route('/usuarios')
def gestionar_usuarios():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuarios = Usuario.query.all()  # Obtener todos los usuarios
    return render_template('gestionar_usuarios.html', usuarios=usuarios)

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        nuevo_rol = request.form.get('rol')
        usuario.rol = nuevo_rol
        db.session.commit()
        return redirect(url_for('gestionar_usuarios'))
    
    return render_template('editar_usuario.html', usuario=usuario)

@app.route('/cuenta', methods=['GET', 'POST'])
def cuenta():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener los datos del usuario logueado
    usuario = Usuario.query.get(session['user_id'])
    
    if request.method == 'POST':
        nuevo_email = request.form.get('email')
        nueva_password = request.form.get('password')
        
        # Validaciones básicas
        if nuevo_email:
            usuario.email = nuevo_email
        if nueva_password:
            usuario.password = nueva_password  # Recuerda usar hash para la contraseña
        
        db.session.commit()
        return redirect(url_for('cuenta'))  # Recargar la página después de editar
    
    return render_template('cuenta.html', usuario=usuario)

@app.route('/resumen')
def resumen():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener todas las categorías
    categorias = Categoria.query.all()

    resumen_categoria = []
    
    # Para cada categoría, obtener el plato más popular
    for categoria in categorias:
        # Consulta para obtener el plato más vendido de esta categoría
        plato_mas_vendido = db.session.query(
            Plato.nombre, 
            db.func.sum(DetallePedido.cantidad).label('total_vendido')
        ).join(DetallePedido, Plato.id == DetallePedido.menu_id
        ).filter(Plato.categoria_id == categoria.id
        ).group_by(Plato.id
        ).order_by(db.desc('total_vendido')
        ).first()

        # Añadir el resultado al resumen
        resumen_categoria.append({
            'categoria': categoria.nombre,
            'plato_mas_vendido': plato_mas_vendido[0] if plato_mas_vendido else "Ninguno",
            'cantidad_vendida': plato_mas_vendido[1] if plato_mas_vendido else 0
        })

    return render_template('resumen.html', resumen_categoria=resumen_categoria)

# Vista para gestionar categorías
@app.route('/categorias')
def categorias():
    if 'user_role' not in session or session['user_role'] != 'administrador':
        return redirect(url_for('login'))
    categorias = Categoria.query.all()
    return render_template('categorias.html', categorias=categorias)

# Agregar una nueva categoría
@app.route('/categorias/agregar', methods=['GET', 'POST'])
def agregar_categoria():
    if 'user_role' not in session or session['user_role'] != 'administrador':
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        nueva_categoria = Categoria(nombre=nombre)
        db.session.add(nueva_categoria)
        db.session.commit()
        flash('Categoría agregada exitosamente.')
        return redirect(url_for('categorias'))

    return render_template('agregar_categoria.html')

# Editar una categoría existente
@app.route('/categorias/editar/<int:categoria_id>', methods=['GET', 'POST'])
def editar_categoria(categoria_id):
    if 'user_role' not in session or session['user_role'] != 'administrador':
        return redirect(url_for('login'))

    categoria = Categoria.query.get_or_404(categoria_id)

    if request.method == 'POST':
        categoria.nombre = request.form['nombre']
        db.session.commit()
        flash('Categoría actualizada exitosamente.')
        return redirect(url_for('menu_admin'))  # Cambia esto para redirigir a menu_admin

    return render_template('editar_categoria.html', categoria=categoria)

# Eliminar una categoría
@app.route('/categorias/eliminar/<int:categoria_id>', methods=['POST'])
def eliminar_categoria(categoria_id):
    if 'user_role' not in session or session['user_role'] != 'administrador':
        return redirect(url_for('login'))

    categoria = Categoria.query.get_or_404(categoria_id)
    db.session.delete(categoria)
    db.session.commit()
    flash('Categoría eliminada exitosamente.')
    return redirect(url_for('categorias'))

# Prueba de conexión a la base de datos
@app.route('/prueba_db')
def prueba_db():
    try:
        db.session.execute('SELECT 1')
        return "Conexión a la base de datos exitosa."
    except Exception as e:
        return f"Error al conectar a la base de datos: {e}"

if __name__ == '__main__':
    app.run(debug=True)
