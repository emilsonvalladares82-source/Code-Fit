import os
import logging
from contextlib import contextmanager
from datetime import date
from functools import wraps
import psycopg2
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from flask import Flask,render_template,request,redirect,url_for,session,flash,jsonify,abort
from werkzeug.security import generate_password_hash,check_password_hash
load_dotenv()
app=Flask(__name__);app.secret_key=os.getenv('FLASK_SECRET_KEY','change-me')
logging.basicConfig(level=logging.INFO)
DATABASE_URL=os.getenv('DATABASE_URL')

def db():
    if not DATABASE_URL:
        raise RuntimeError('DATABASE_URL no está configurada.')
    return psycopg2.connect(DATABASE_URL)

@contextmanager
def db_cursor(dictionary=False):
    connection = None
    cursor = None
    try:
        connection = db()
        cursor = connection.cursor(cursor_factory=RealDictCursor) if dictionary else connection.cursor()
        yield connection, cursor
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

def setup():
    c = None
    q = None
    try:
        c=db();q=c.cursor()
        q.execute("""CREATE TABLE IF NOT EXISTS usuarios(id SERIAL PRIMARY KEY,nombre VARCHAR(100) NOT NULL,correo VARCHAR(150) NOT NULL UNIQUE,contraseña VARCHAR(255) NOT NULL,edad INT NULL,peso DECIMAL(6,2) NULL,altura DECIMAL(4,2) NULL,objetivo VARCHAR(50) DEFAULT 'mejorar_condicion',nivel VARCHAR(30) DEFAULT 'principiante',dias_disponibles VARCHAR(255) DEFAULT '',minutos_disponibles INT DEFAULT 30,fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        q.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='usuarios'");cols={x[0] for x in q.fetchall()}
        for n,t in {'edad':'INT NULL','peso':'DECIMAL(6,2) NULL','altura':'DECIMAL(4,2) NULL','objetivo':"VARCHAR(50) DEFAULT 'mejorar_condicion'",'nivel':"VARCHAR(30) DEFAULT 'principiante'",'dias_disponibles':"VARCHAR(255) DEFAULT ''",'minutos_disponibles':'INT DEFAULT 30'}.items():
            if n not in cols:q.execute(f'ALTER TABLE usuarios ADD COLUMN {n} {t}')
        q.execute("SELECT data_type FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='usuarios' AND column_name='dias_disponibles'");days_type=q.fetchone()[0]
        if days_type not in ('character varying','text'):q.execute("ALTER TABLE usuarios ALTER COLUMN dias_disponibles TYPE VARCHAR(255)")
        q.execute("""CREATE TABLE IF NOT EXISTS ejercicios(id SERIAL PRIMARY KEY,nombre VARCHAR(120) NOT NULL,categoria VARCHAR(60) NOT NULL,dificultad VARCHAR(30) NOT NULL,descripcion TEXT NOT NULL,duracion VARCHAR(40) DEFAULT '',equipo VARCHAR(120) DEFAULT 'Sin equipo')""")
        q.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='ejercicios'");exercise_cols={x[0] for x in q.fetchall()}
        for n,t in {'dificultad':"VARCHAR(30) NOT NULL DEFAULT 'Principiante'",'duracion':"VARCHAR(40) DEFAULT ''",'equipo':"VARCHAR(120) DEFAULT 'Sin equipo'"}.items():
            if n not in exercise_cols:q.execute(f'ALTER TABLE ejercicios ADD COLUMN {n} {t}')
        q.execute("""CREATE TABLE IF NOT EXISTS rutinas(id SERIAL PRIMARY KEY,nombre VARCHAR(120) NOT NULL,objetivo VARCHAR(50) NOT NULL,nivel VARCHAR(30) NOT NULL,duracion INT NOT NULL DEFAULT 30,descripcion TEXT NOT NULL)""")
        q.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='rutinas'");routine_cols={x[0] for x in q.fetchall()}
        if 'duracion' not in routine_cols:q.execute("ALTER TABLE rutinas ADD COLUMN duracion INT NOT NULL DEFAULT 30")
        if 'descripcion' not in routine_cols:q.execute("ALTER TABLE rutinas ADD COLUMN descripcion TEXT NOT NULL DEFAULT ''")
        q.execute("""CREATE TABLE IF NOT EXISTS rutina_ejercicios(id SERIAL PRIMARY KEY,rutina_id INT NOT NULL,ejercicio_id INT NOT NULL,series INT DEFAULT 3,repeticiones VARCHAR(40) DEFAULT '10-12',orden INT DEFAULT 1,FOREIGN KEY(rutina_id) REFERENCES rutinas(id) ON DELETE CASCADE,FOREIGN KEY(ejercicio_id) REFERENCES ejercicios(id) ON DELETE CASCADE)""")
        q.execute("SELECT column_name FROM information_schema.columns WHERE table_schema=current_schema() AND table_name='rutina_ejercicios'");link_cols={x[0] for x in q.fetchall()}
        if 'orden' not in link_cols:q.execute("ALTER TABLE rutina_ejercicios ADD COLUMN orden INT DEFAULT 1")
        q.execute("""CREATE TABLE IF NOT EXISTS progreso(id SERIAL PRIMARY KEY,usuario_id INT NOT NULL,fecha DATE NOT NULL,peso DECIMAL(6,2) NULL,minutos INT DEFAULT 0,entrenamiento VARCHAR(150) DEFAULT '',notas TEXT,FOREIGN KEY(usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE)""")
        q.execute('SELECT COUNT(*) FROM ejercicios')
        if q.fetchone()[0]==0:
            ex=[('Sentadilla','Piernas','Principiante','Trabaja piernas y glúteos con movimiento controlado.','3 x 10-12','Sin equipo'),('Flexiones','Pecho','Principiante','Trabaja pecho, hombros y tríceps.','3 x 8-12','Sin equipo'),('Puente de glúteos','Glúteos','Principiante','Eleva la cadera de forma controlada.','3 x 12-15','Sin equipo'),('Plancha','Core','Principiante','Mantén el cuerpo alineado y activa el abdomen.','3 x 20-40 s','Sin equipo'),('Zancadas','Piernas','Intermedio','Alterna las piernas y controla el descenso.','3 x 10 por pierna','Sin equipo'),('Mountain climbers','Cardio','Intermedio','Alterna rodillas hacia el pecho desde plancha.','3 x 30 s','Sin equipo'),('Remo con mochila','Espalda','Intermedio','Remo con mochila ligera y espalda neutra.','3 x 10-12','Mochila'),('Sentadilla con salto','Cardio','Intermedio','Sentadilla con salto y aterrizaje suave.','3 x 8-10','Sin equipo'),('Bird-dog','Core','Principiante','Extiende brazo y pierna contrarios manteniendo estabilidad.','3 x 8 por lado','Sin equipo'),('Elevaciones de talones','Pantorrillas','Principiante','Eleva y baja talones lentamente.','3 x 15','Sin equipo')]
            q.executemany('INSERT INTO ejercicios(nombre,categoria,dificultad,descripcion,duracion,equipo) VALUES(%s,%s,%s,%s,%s,%s)',ex)
        q.execute('SELECT COUNT(*) FROM rutinas')
        if q.fetchone()[0]==0:
            rs=[('Inicio Activo','mejorar_condicion','principiante',25,'Rutina corta para comenzar y crear constancia.'),('Base Fuerza','ganar_fuerza','principiante',35,'Entrenamiento general con peso corporal.'),('Cardio Inicial','bajar_peso','principiante',30,'Circuito moderado para aumentar actividad.'),('Masa y Fuerza','ganar_peso','intermedio',45,'Rutina general de fuerza.'),('Condición Pro','mejorar_condicion','intermedio',45,'Fuerza y cardio para nivel intermedio.')]
            q.executemany('INSERT INTO rutinas(nombre,objetivo,nivel,duracion,descripcion) VALUES(%s,%s,%s,%s,%s)',rs);q.execute('SELECT id,nombre FROM ejercicios');ex={n:i for i,n in q.fetchall()};q.execute('SELECT id,nombre FROM rutinas');rt={n:i for i,n in q.fetchall()}
            links=[('Inicio Activo','Sentadilla',3,'10-12',1),('Inicio Activo','Flexiones',3,'8-12',2),('Inicio Activo','Puente de glúteos',3,'12-15',3),('Inicio Activo','Plancha',3,'20-40 s',4),('Base Fuerza','Sentadilla',3,'10-12',1),('Base Fuerza','Flexiones',3,'8-12',2),('Base Fuerza','Zancadas',3,'10 por pierna',3),('Base Fuerza','Plancha',3,'30-45 s',4),('Cardio Inicial','Mountain climbers',3,'30 s',1),('Cardio Inicial','Sentadilla',3,'12',2),('Cardio Inicial','Bird-dog',3,'8 por lado',3),('Cardio Inicial','Elevaciones de talones',3,'15',4),('Masa y Fuerza','Sentadilla',4,'8-12',1),('Masa y Fuerza','Flexiones',4,'8-12',2),('Masa y Fuerza','Remo con mochila',4,'10-12',3),('Masa y Fuerza','Zancadas',3,'10 por pierna',4),('Condición Pro','Zancadas',3,'10 por pierna',1),('Condición Pro','Flexiones',3,'10-15',2),('Condición Pro','Mountain climbers',3,'40 s',3),('Condición Pro','Plancha',3,'40-60 s',4)]
            q.executemany('INSERT INTO rutina_ejercicios(rutina_id,ejercicio_id,series,repeticiones,orden) VALUES(%s,%s,%s,%s,%s)',[(rt[r],ex[e],s,rep,o) for r,e,s,rep,o in links])
        c.commit();q.close();c.close();return True
    except Error as e:print('PostgreSQL:',e);return False
    finally:
        if q is not None:
            q.close()
        if c is not None:
            c.close()

def req(f):
    @wraps(f)
    def w(*a,**kw):
        if 'usuario_id' not in session:return redirect(url_for('login'))
        if user() is None:
            session.clear()
            flash('Tu sesión ya no es válida. Inicia sesión nuevamente.','error')
            return redirect(url_for('login'))
        return f(*a,**kw)
    return w

def user():
    with db_cursor(dictionary=True) as (c,q):
        q.execute('SELECT * FROM usuarios WHERE id=%s',(session['usuario_id'],));return q.fetchone()

def imc(w,h):
    try:
        w=float(w);h=float(h)
        if w<=0 or h<=0:return None,'Valores inválidos'
        v=round(w/(h*h),2)
        if v < 18.5:
            clasificacion = 'Falta ganar peso'
        elif v <= 24.9:
            clasificacion = 'Rango normal'
        elif v <= 29.9:
            clasificacion = 'Sobrepeso'
        else:
            clasificacion = 'Obesidad'
        return v,clasificacion
    except:return None,'Valores inválidos'

def obj(x):return {'bajar_peso':'bajar de peso','ganar_peso':'ganar peso','mejorar_condicion':'mejorar tu condición física','ganar_fuerza':'ganar fuerza'}.get(x,'mejorar tu condición física')

def local_ai(m,u):
    return f"Hola {u['nombre']}. Mientras configuras tu clave de OpenAI, puedo orientarte de forma básica: tu objetivo es {obj(u.get('objetivo'))}, tu nivel es {u.get('nivel') or 'principiante'} y dispones de unos {u.get('minutos_disponibles') or 30} minutos. Sobre tu mensaje ({m}), prueba una sesión adaptada a ese tiempo y detente si aparece dolor."

def ai(m,u):
    key=os.getenv('OPENAI_API_KEY','').strip()
    if not key:return local_ai(m,u)
    try:
        from openai import OpenAI
        client=OpenAI(api_key=key)
        system_prompt = """1. Actua como un entrenador experto, empatico y muy profesional.
2. Tu objetivo principal es resolver dudas y adaptar las rutinas especificamente para usuarios principiantes, pero tambien para otros usuarios.
3. Utiliza un tono profesional, empatico, motivador y alentador.
4. Responde de forma ultra-concisa, directa y al grano. Limita estrictamente la respuesta a lo que la persona acaba de preguntar en su ultimo mensaje.
5. No generes introducciones largas, resúmenes innecesarios ni repitas la rutina completa si no te la han solicitado expresamente.
6. Solo haz referencia o recuerda informacion de mensajes anteriores si la persona pregunta explicitamente por algo discutido antes, por ejemplo: "¿Que me dijiste sobre las sentadillas?". Si no lo solicita, concentrate unicamente en el mensaje actual.
7. Para usuarios principiantes, usa frases muy breves, claras y faciles de digerir. Evita la fatiga de lectura y los tecnicismos complejos.
8. Adapta tus recomendaciones al objetivo, nivel, dias y tiempo disponible de la persona."""

    
        
        profile=(
            f"Nombre: {u.get('nombre') or 'sin indicar'}\n"
            f"Edad: {u.get('edad') or 'sin indicar'}\n"
            f"Peso: {u.get('peso') or 'sin indicar'} kg\n"
            f"Altura: {u.get('altura') or 'sin indicar'} m\n"
            f"Objetivo: {obj(u.get('objetivo'))}\n"
            f"Nivel: {u.get('nivel') or 'principiante'}\n"
            f"Días disponibles: {u.get('dias_disponibles') or 'sin indicar'}\n"
            f"Minutos disponibles: {u.get('minutos_disponibles') or 30}"
        )
        response=client.responses.create(
            model=os.getenv('OPENAI_MODEL','gpt-5.6-luna'),
            instructions=system_prompt,
            input=f"Perfil de la persona:\n{profile}\n\nMensaje actual:\n{m}",
        )
        reply=response.output_text.strip()
        return reply or local_ai(m,u)
    except Exception as e:print('AI fallback:',e);return local_ai(m,u)

@app.route('/')
def home():return redirect(url_for('dashboard' if 'usuario_id' in session else 'login'))
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        correo = request.form.get('correo', '').strip().lower()
        with db_cursor(dictionary=True) as (c,q):
            q.execute(
                'SELECT * FROM usuarios WHERE correo=%s',
                (correo,)
            )
            u = q.fetchone()
        if u and check_password_hash(u['contraseña'],request.form.get('contraseña','')):session['usuario_id']=u['id'];return redirect(url_for('imc_page'))
        flash('Correo o contraseña incorrectos.','error')
    return render_template('login.html')
@app.route('/registro',methods=['GET','POST'])
def registro():
    if request.method=='POST':
        n=request.form.get('nombre','').strip();e=request.form.get('correo','').strip().lower();p=request.form.get('contraseña','');p2=request.form.get('confirmar','')
        if not n or not e or len(p)<6:flash('Completa los campos y usa al menos 6 caracteres.','error')
        elif p!=p2:flash('Las contraseñas no coinciden.','error')
        else:
            try:
                with db_cursor() as (c,q):
                    q.execute('INSERT INTO usuarios(nombre,correo,contraseña) VALUES(%s,%s,%s)',(n,e,generate_password_hash(p)));c.commit()
                flash('Cuenta creada correctamente.','success');return redirect(url_for('login'))
            except Error:flash('No se pudo crear la cuenta; quizá el correo ya existe.','error')
    return render_template('registro.html')
@app.route('/logout')
def logout():session.clear();return redirect(url_for('login'))
@app.route('/imc',methods=['GET','POST'])
@req
def imc_page():
    u=user();r=clasificacion=None
    if request.method=='POST':
        w=request.form.get('peso');h=request.form.get('altura');r,clasificacion=imc(w,h)
        if r:
            with db_cursor() as (c,q):
                q.execute('UPDATE usuarios SET peso=%s,altura=%s WHERE id=%s',(float(w),float(h),u['id']));c.commit()
            u=user()
    return render_template('imc.html',user=u,result=r,category=clasificacion)
@app.route('/dashboard')
@req
def dashboard():
    u=user();r,clasificacion=imc(u.get('peso'),u.get('altura'))
    with db_cursor(dictionary=True) as (c,q):
        q.execute('SELECT * FROM progreso WHERE usuario_id=%s ORDER BY fecha DESC,id DESC LIMIT 6',(u['id'],));p=q.fetchall()
    return render_template('dashboard.html',user=u,imc=r,category=clasificacion,progress=p)
@app.route('/perfil',methods=['GET','POST'])
@req
def perfil():
    u=user()
    if request.method=='POST':
        days=','.join(request.form.getlist('dias'))
        with db_cursor() as (c,q):
            q.execute('UPDATE usuarios SET edad=%s,peso=%s,altura=%s,objetivo=%s,nivel=%s,dias_disponibles=%s,minutos_disponibles=%s WHERE id=%s',(request.form.get('edad') or None,request.form.get('peso') or None,request.form.get('altura') or None,request.form.get('objetivo','mejorar_condicion'),request.form.get('nivel','principiante'),days,request.form.get('minutos') or 30,u['id']));c.commit()
        flash('Perfil actualizado.','success');return redirect(url_for('perfil'))
    return render_template('perfil.html',user=u)
@app.route('/ejercicios')
@req
def ejercicios():
    qv=request.args.get('q','').strip();ca=request.args.get('categoria','');lv=request.args.get('nivel','');sql='SELECT * FROM ejercicios WHERE 1=1';pa=[]
    if qv:sql+=' AND (nombre LIKE %s OR descripcion LIKE %s)';pa += [f'%{qv}%',f'%{qv}%']
    if ca:sql+=' AND categoria=%s';pa.append(ca)
    if lv:sql+=' AND dificultad=%s';pa.append(lv)
    sql+=' ORDER BY categoria,nombre'
    with db_cursor(dictionary=True) as (c,q):
        q.execute(sql,pa);ex=q.fetchall()
    return render_template('ejercicios.html',exercises=ex,q=qv,category=ca,level=lv)
@app.route('/rutinas')
@req
def rutinas():
    lv=request.args.get('nivel','');sql='SELECT * FROM rutinas';pa=[]
    if lv:sql+=' WHERE nivel=%s';pa.append(lv)
    sql+=' ORDER BY nivel,duracion'
    with db_cursor(dictionary=True) as (c,q):
        q.execute(sql,pa);rs=q.fetchall()
    return render_template('rutinas.html',routines=rs)
@app.route('/rutina/<int:rid>')
@req
def rutina(rid):
    with db_cursor(dictionary=True) as (c,q):
        q.execute('SELECT * FROM rutinas WHERE id=%s',(rid,));r=q.fetchone()
        if r is None:
            abort(404)
        q.execute('SELECT e.*,re.series,re.repeticiones FROM rutina_ejercicios re JOIN ejercicios e ON e.id=re.ejercicio_id WHERE re.rutina_id=%s ORDER BY re.orden',(rid,));ex=q.fetchall()
    return render_template('rutina_detalle.html',routine=r,exercises=ex)
@app.route('/progreso',methods=['GET','POST'])
@req
def progreso():
    u=user()
    if request.method=='POST':
        with db_cursor() as (c,q):
            q.execute('INSERT INTO progreso(usuario_id,fecha,peso,minutos,entrenamiento,notas) VALUES(%s,%s,%s,%s,%s,%s)',(u['id'],request.form.get('fecha') or date.today(),request.form.get('peso') or None,request.form.get('minutos') or 0,request.form.get('entrenamiento',''),request.form.get('notas','')));c.commit()
        flash('Progreso registrado.','success');return redirect(url_for('progreso'))
    with db_cursor(dictionary=True) as (c,q):
        q.execute('SELECT * FROM progreso WHERE usuario_id=%s ORDER BY fecha DESC,id DESC',(u['id'],));e=q.fetchall()
    return render_template('progreso.html',entries=e,today=date.today().isoformat())
@app.route('/chatbot')
@req
def chatbot():return render_template('chatbot.html',user=user())
@app.post('/api/chat')
@req
def api_chat():
    m=(request.json or {}).get('message','').strip();return jsonify({'reply':ai(m,user())}) if m else (jsonify({'error':'Escribe un mensaje.'}),400)
@app.post('/api/personalized-plan')
@req
def plan():
    u=user();d=request.json or {};goal=d.get('objetivo') or u.get('objetivo');level=d.get('nivel') or u.get('nivel')
    raw_minutes = d['minutos'] if 'minutos' in d else u.get('minutos_disponibles')
    if raw_minutes is None or (isinstance(raw_minutes, str) and not raw_minutes.strip()):
        return jsonify({'error':'Los minutos deben ser un número entero mayor que cero.'}),400
    try:
        minutes=int(raw_minutes)
    except (TypeError,ValueError):
        return jsonify({'error':'Los minutos deben ser un número entero.'}),400
    if minutes <= 0:
        return jsonify({'error':'Los minutos deben ser mayores que cero.'}),400
    days=d.get('dias') or u.get('dias_disponibles') or 'Día 1,Día 2,Día 3';days=[x.strip() for x in days.split(',') if x.strip()][:7]
    with db_cursor(dictionary=True) as (c,q):
        q.execute('SELECT * FROM rutinas WHERE objetivo=%s AND nivel=%s AND duracion<=%s ORDER BY duracion DESC LIMIT 1',(goal,level,minutes));r=q.fetchone()
        if not r:q.execute('SELECT * FROM rutinas WHERE nivel=%s AND duracion<=%s ORDER BY duracion DESC LIMIT 1',(level,minutes));r=q.fetchone()
        if not r:q.execute('SELECT * FROM rutinas ORDER BY duracion LIMIT 1');r=q.fetchone()
        if r is None:
            abort(404)
        q.execute('SELECT e.nombre,re.series,re.repeticiones FROM rutina_ejercicios re JOIN ejercicios e ON e.id=re.ejercicio_id WHERE re.rutina_id=%s ORDER BY re.orden',(r['id'],));ex=q.fetchall()
    return jsonify({'objective':obj(goal),'level':level,'minutes':minutes,'plan':[{'day':x,'routine':r['nombre'],'duration':min(r['duracion'],minutes),'exercises':ex} for x in days]})

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error':'Recurso no encontrado.'}),404
    return render_template('error.html',code=404,message='Recurso no encontrado.'),404

@app.errorhandler(Exception)
def internal_error(error):
    app.logger.exception('Error interno no controlado', exc_info=error)
    if request.path.startswith('/api/'):
        return jsonify({'error':'Ocurrió un error interno. Inténtalo nuevamente.'}),500
    return render_template('error.html',code=500,message='Ocurrió un error interno. Inténtalo nuevamente.'),500
if __name__=='__main__':
    setup();app.run(debug=True)
