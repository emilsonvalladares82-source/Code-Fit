# CodeFit IA — El código exacto para tu bienestar

Proyecto de 12 BTP Informática, Sección 1.

Incluye: registro/login, perfil, IMC orientativo, dashboard progresivo, ejercicios, rutinas por nivel/objetivo, registro de progreso, asistente flotante y plan personalizado por disponibilidad. Diseño responsive Dark Tech + Liquid Glass.

## Ejecutar
1. Instala Python y PostgreSQL.
2. Activa el entorno: `venv\Scripts\activate.bat`
3. `pip install -r requirements.txt`
4. Configura `DATABASE_URL` en tu entorno o archivo `.env` con la URL de PostgreSQL.
5. `python app.py`
6. Abre `http://127.0.0.1:5000`

La app crea/actualiza las tablas automáticamente al ejecutarse con `python app.py`. Para desarrollo local, `DATABASE_URL` puede tener el formato `postgresql://usuario:contraseña@localhost:5432/codefit`. `database/codefit.sql` contiene el esquema manual.

El asistente usa OpenAI si `OPENAI_API_KEY` está configurada; si no, funciona con un respaldo local para que el proyecto siga siendo demostrable. No incluye ninguna clave privada.

Nota: el IMC y las sugerencias son orientación general y no sustituyen la evaluación de profesionales de la salud.
