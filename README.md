# Manicure Dates Backend

Sistema de gestión de citas para centros de manicura. Permite a clientes reservar, cancelar y consultar citas, y a administradores/empleados gestionar los servicios, clientes y notificaciones por email.
Soporta roles (admin, staff, cliente) y lógica avanzada de reservas.

## Tecnologías principales

- **Python 3.12+**
- **FastAPI** – Framework API asíncrono y robusto
- **SQLAlchemy (async)** – ORM para acceso a base de datos
- **Alembic** – Migraciones de esquema de base de datos
- **PostgreSQL (NeonDB)** – Base de datos cloud, conexión asíncrona vía `asyncpg`
- **Resend** – Envío de emails transaccionales
- **Pydantic v2** – Validación y serialización de datos
- **JWT** – Autenticación basada en tokens
- **Uvicorn** – Servidor ASGI para desarrollo

## Funcionalidades principales

- Registro y login de usuarios (JWT)
- Gestión de clientes, servicios y citas
- Reservas de citas, cancelación (con validaciones), finalización
- Notificaciones por email (resend.com)
- Control de permisos por rol (admin, staff, cliente)
- Soporte para soft delete en cancelaciones
- Paginación y filtros en endpoints

---

## Requisitos previos

- Python 3.12+
- [Poetry](https://python-poetry.org/) **(opcional, si gestionas dependencias así)**
- PostgreSQL (usa el string de conexión de NeonDB provisto)
- Cuenta en [Resend](https://resend.com/) (para el envío de emails transaccionales)

---

## Clonar el proyecto

```bash
git clone https://github.com/tuusuario/manicure-dates-backend.git
cd manicure-dates-backend
```

## Configuración de variables de entorno

Crea un archivo `.env` en la raíz del proyecto y copia este contenido (modifica los valores según tus credenciales):

```bash
DATABASE_URL=postgresql+asyncpg://<YOUR_URL_DATABASE>
SECRET_KEY=<YOUR_SECRET>
ACCESS_TOKEN_EXPIRE_MINUTES=1440
RESEND_API_KEY=re_YvoGq7bt_6gLdutNWd87ca7sc5taCRfEL
RESEND_FROM_EMAIL=ejemplo@tudominio.com
```

- **DATABASE_URL**: Cadena de conexión a tu base de datos PostgreSQL.
- **SECRET_KEY**: Clave secreta para firmar JWTs.
- **ACCESS_TOKEN_EXPIRE_MINUTES**: Minutos de expiración de los tokens de acceso (por defecto se establecerá un valor en caso de no existir esta property).
- **RESEND_API_KEY**: API key de tu cuenta [Resend](https://resend.com/]).
- **RESEND_FROM_EMAIL**: Email verificado desde el que se enviarán las notificaciones (debe ser validado en Resend).

## Instalación de dependencias

Si usas **pip** y `requirements.txt`:

```bash
python -m venv .venv
source .venv/bin/activate      # En Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Si usas **Poetry**:
```bash
poetry install
```

## Migraciones de base de datos

Asegurate de tener alembic instalado dentro del proyecto. Está incluido dentro del `requirements.txt`.

```bash
alembic upgrade head
```

Recuerda establecer tu cadena de conexión en la variable `sqlalchemy.url` del `alembic.ini`.

## Levantar el servidor en local

- Primero activa el entorno virtual:
```bash
source .venv/bin/activate   #En Windows: .venv\Scripts\activate
```
- *Opcional*: Puedes poblar la **base de datos** con un pack inicial. Tendrías que ejecutar el `seed.py` que está en la ráiz del proyecto:
```bash
python seed.py
```
- Levantar el servidor **uvicorn** en local:
```bash
uvicorn app.main:app --reload
```

Por defecto estará disponible en `http://localhost:8000`. Puedes consultar la documentación **OpenAPI** en `http://localhost:8000/docs`.


## Estructura de carpetas principal

```bash
app/
 ├── api/
 │    └── routes/         # Endpoints
 ├── models/              # Modelos SQLAlchemy
 ├── schemas/             # Schemas Pydantic
 ├── services/            # Lógica de negocio
 ├── database.py
 ├── main.py
 └── ...
alembic/
 └── versions/
requirements.txt
.env
README.md
```

## Notas adicionales

- Para enviar emails con **Resend**, necesitas tener un dominio verificado y el `RESEND_FROM_EMAIL` correspondiente en tu fichero `.env`.
- Si cambias el esquema de base de datos recuerda generar una nueva migración con:
```bash
alembic revision --autogenerate -m "<mensaje>"  #Las revisiones se generan en alembic/versions/
alembic upgrade head
```
- Puedes probar los endpoints en la documentación: `http://localhost:8000/docs`.

## Contribuciones

Pull Requests y mejoras bienvenidas. Por favor, sigue las buenas prácticas de Python, usa typing y revisa los test antes de subir cambios.
