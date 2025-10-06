# Sistema de Gestión de Notas Académicas

Un sistema completo de gestión académica de notas con backend en Python (FastAPI) y frontend en React + TailwindCSS, con tres roles: Administrador, Docente y Alumno.

## Características

### Backend (FastAPI)
- **Base de datos**: SQLite (fácil migración a PostgreSQL)
- **Autenticación**: JWT con roles (admin, docente, alumno)
- **API REST**: Documentación automática con Swagger
- **Modelos**: Usuario, Alumno, Docente, Asignatura, Nota
- **Validaciones**: DNI único, ciclo válido, notas entre 0-20

### Frontend (React + TailwindCSS)
- **Diseño minimalista** con sidebar de navegación
- **Responsive**: Adaptable a móviles y tablets
- **Navegación por roles**: Menús específicos según el tipo de usuario
- **Autenticación**: JWT con protección de rutas
- **UI moderna**: Componentes con TailwindCSS y Lucide React

## Estructura del Proyecto

```
sistema-notas/
├── backend/
│   ├── main.py                 # Aplicación principal FastAPI
│   ├── database.py             # Configuración de base de datos
│   ├── models.py               # Modelos SQLAlchemy
│   ├── schemas.py              # Esquemas Pydantic
│   ├── auth.py                 # Autenticación JWT
│   ├── config.py               # Configuración
│   ├── requirements.txt        # Dependencias Python
│   └── routers/
│       ├── __init__.py
│       ├── auth.py             # Endpoints de autenticación
│       ├── admin.py            # Endpoints de administrador
│       ├── docente.py          # Endpoints de docente
│       └── alumno.py           # Endpoints de alumno
└── frontend/
    ├── public/
    │   └── index.html
    ├── src/
    │   ├── components/         # Componentes React
    │   ├── pages/              # Páginas de la aplicación
    │   ├── services/           # Servicios API
    │   ├── contexts/           # Contextos React
    │   ├── App.js
    │   └── index.js
    ├── package.json
    ├── tailwind.config.js
    └── postcss.config.js
```

## Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- Node.js 16+
- npm o yarn

### Backend

1. **Navegar al directorio del backend:**
   ```bash
   cd backend
   ```

2. **Crear entorno virtual:**
   ```bash
   python -m venv venv
   ```

3. **Activar entorno virtual:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configurar variables de entorno:**
   Crear archivo `.env` en el directorio backend:
   ```env
   SECRET_KEY=tu-clave-secreta-muy-segura-aqui-cambiar-en-produccion
   DATABASE_URL=sqlite:///./sistema_notas.db
   ```

6. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

   El backend estará disponible en: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Frontend

1. **Navegar al directorio del frontend:**
   ```bash
   cd frontend
   ```

2. **Instalar dependencias:**
   ```bash
   npm install
   ```

3. **Configurar variables de entorno:**
   Crear archivo `.env` en el directorio frontend:
   ```env
   PORT=3001
   REACT_APP_API_URL=http://localhost:8000
   ```

4. **Ejecutar la aplicación:**
   ```bash
   npm start
   ```

   El frontend estará disponible en: `http://localhost:3001`

## Uso del Sistema

### Roles y Permisos

#### Administrador
- **Dashboard**: Estadísticas generales del sistema
- **Gestionar Alumnos**: Crear, editar y eliminar alumnos
- **Gestionar Docentes**: Crear, editar y eliminar docentes
- **Gestionar Asignaturas**: Crear y asignar asignaturas a docentes
- **Matricular Alumnos**: Matricular alumnos en asignaturas

#### Docente
- **Mis Asignaturas**: Ver asignaturas asignadas
- **Registrar Notas**: Registrar y gestionar notas de alumnos
- **Ver Alumnos**: Ver alumnos matriculados en sus asignaturas

#### Alumno
- **Mis Asignaturas**: Ver asignaturas matriculadas
- **Mis Notas**: Ver calificaciones y promedios
- **Promedios**: Ver promedios por asignatura y general

### Flujo de Trabajo

1. **Configuración inicial (Admin):**
   - Crear docentes
   - Crear alumnos
   - Crear asignaturas y asignarlas a docentes
   - Matricular alumnos en asignaturas

2. **Gestión académica (Docente):**
   - Ver asignaturas asignadas
   - Registrar notas de alumnos matriculados
   - Actualizar notas existentes

3. **Consulta académica (Alumno):**
   - Ver asignaturas matriculadas
   - Consultar calificaciones
   - Ver promedios y estadísticas

## API Endpoints

### Autenticación
- `POST /auth/login` - Iniciar sesión
- `GET /auth/me` - Obtener usuario actual

### Administrador
- `GET /admin/dashboard` - Dashboard con estadísticas
- `GET|POST /admin/alumnos` - Gestión de alumnos
- `GET|POST /admin/docentes` - Gestión de docentes
- `GET|POST /admin/asignaturas` - Gestión de asignaturas
- `GET|POST /admin/matriculas` - Gestión de matrículas

### Docente
- `GET /docente/mis-asignaturas` - Asignaturas del docente
- `GET /docente/asignaturas/{id}/alumnos` - Alumnos por asignatura
- `GET|POST|PUT|DELETE /docente/notas` - Gestión de notas

### Alumno
- `GET /alumno/mis-asignaturas` - Asignaturas del alumno
- `GET /alumno/mis-notas` - Notas del alumno
- `GET /alumno/promedio` - Promedio general
- `GET /alumno/promedio-por-asignatura` - Promedios por asignatura

## Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para Python
- **SQLite**: Base de datos ligera
- **JWT**: Autenticación con tokens
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI

### Frontend
- **React**: Biblioteca de interfaz de usuario
- **React Router**: Enrutamiento
- **TailwindCSS**: Framework de CSS
- **Axios**: Cliente HTTP
- **Lucide React**: Iconos
- **Context API**: Gestión de estado

## Desarrollo

### Estructura de Base de Datos

```sql
-- Usuarios del sistema
usuarios (id, nombre, email, password_hash, rol, activo, fecha_creacion)

-- Información de alumnos
alumnos (id, nombre_completo, dni, ciclo, usuario_id)

-- Información de docentes
docentes (id, nombre_completo, dni, usuario_id)

-- Asignaturas
asignaturas (id, nombre, docente_id)

-- Notas
notas (id, alumno_id, asignatura_id, calificacion, fecha_registro)

-- Matrículas (relación muchos a muchos)
matriculas (alumno_id, asignatura_id)
```

### Validaciones Implementadas
- DNI único por tipo de usuario
- Email único en el sistema
- Calificaciones entre 0 y 20
- Contraseñas encriptadas con bcrypt
- Tokens JWT con expiración

## Despliegue

### Backend en Producción
1. Cambiar `DATABASE_URL` a PostgreSQL
2. Configurar `SECRET_KEY` segura
3. Usar servidor WSGI como Gunicorn
4. Configurar proxy reverso (Nginx)

### Frontend en Producción
1. Ejecutar `npm run build`
2. Servir archivos estáticos
3. Configurar variables de entorno de producción

## Contribución

1. Fork el proyecto
2. Crear rama para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o preguntas, contactar al administrador del sistema.
