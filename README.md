# CodeFit IA — El código exacto para tu bienestar

Proyecto de 12 BTP Informática, Sección 1.

Incluye: registro/login, perfil, IMC orientativo, dashboard progresivo, ejercicios, rutinas por nivel/objetivo, registro de progreso, asistente flotante y plan personalizado por disponibilidad. Diseño responsive Dark Tech + Liquid Glass.

## Ejecutar
1. Instala Python y MySQL.
2. Activa el entorno: `venv\Scripts\activate.bat`
3. `pip install -r requirements.txt`
4. Copia `.env.example` a `.env` y coloca tu contraseña de MySQL.
5. `python app.py`
6. Abre `http://127.0.0.1:5000`

La app crea/actualiza las tablas automáticamente. `database/codefit.sql` contiene el esquema manual.

El asistente usa OpenAI si `OPENAI_API_KEY` está configurada; si no, funciona con un respaldo local para que el proyecto siga siendo demostrable. No incluye ninguna clave privada.

Nota: el IMC y las sugerencias son orientación general y no sustituyen la evaluación de profesionales de la salud.
