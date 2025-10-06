# Guía de Despliegue en Koyeb

Esta guía te ayudará a desplegar tu Sistema de Gestión de Notas en Koyeb.

## Prerrequisitos

1. Cuenta en [Koyeb](https://www.koyeb.com/)
2. Cuenta en [GitHub](https://github.com/) (recomendado) o [GitLab](https://gitlab.com/)
3. Tu proyecto subido a un repositorio Git

## Paso 1: Preparar el Repositorio

1. Sube tu proyecto a GitHub o GitLab
2. Asegúrate de que todos los archivos Docker estén incluidos:
   - `backend/Dockerfile`
   - `frontend/Dockerfile`
   - `docker-compose.yml`
   - `.dockerignore` files

## Paso 2: Desplegar el Backend (FastAPI)

### 2.1 Crear Servicio Backend

1. Ve a tu [dashboard de Koyeb](https://app.koyeb.com/)
2. Haz clic en "Create Service"
3. Selecciona "GitHub" o "GitLab" como fuente
4. Conecta tu repositorio
5. Configura el servicio:
   - **Name**: `sistema-notas-backend`
   - **Build Command**: (dejar vacío)
   - **Run Command**: (dejar vacío)
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Port**: `8000`

### 2.2 Variables de Entorno del Backend

Agrega estas variables de entorno en la sección "Environment Variables":

```
SECRET_KEY=tu-clave-secreta-muy-segura-para-produccion
DATABASE_URL=sqlite:///./sistema_notas.db
FRONTEND_URL=https://tu-frontend-url.koyeb.app
```

### 2.3 Configurar el Dominio

1. En la sección "Domains", agrega un dominio personalizado o usa el subdominio de Koyeb
2. Anota la URL del backend (ej: `https://sistema-notas-backend-tu-usuario.koyeb.app`)

## Paso 3: Desplegar el Frontend (React)

### 3.1 Crear Servicio Frontend

1. Crea otro servicio en Koyeb
2. Configura el servicio:
   - **Name**: `sistema-notas-frontend`
   - **Build Command**: (dejar vacío)
   - **Run Command**: (dejar vacío)
   - **Dockerfile Path**: `frontend/Dockerfile`
   - **Port**: `80`

### 3.2 Variables de Entorno del Frontend

Agrega estas variables de entorno:

```
REACT_APP_API_URL=https://tu-backend-url.koyeb.app
```

### 3.3 Configurar el Dominio

1. Agrega un dominio para el frontend
2. Anota la URL del frontend (ej: `https://sistema-notas-frontend-tu-usuario.koyeb.app`)

## Paso 4: Actualizar Configuración

### 4.1 Actualizar Backend

1. Ve al servicio del backend en Koyeb
2. Actualiza la variable de entorno `FRONTEND_URL` con la URL real del frontend
3. Reinicia el servicio

### 4.2 Actualizar Frontend

1. Ve al servicio del frontend en Koyeb
2. Actualiza la variable de entorno `REACT_APP_API_URL` con la URL real del backend
3. Reinicia el servicio

## Paso 5: Configuración de Base de Datos PostgreSQL

### 5.1 Crear Servicio PostgreSQL en Koyeb

1. Ve a tu dashboard de Koyeb
2. Haz clic en "Create Service"
3. Selecciona "PostgreSQL" como tipo de servicio
4. Configura el servicio:
   - **Name**: `sistema-notas-database`
   - **Database Name**: `sistema_notas`
   - **Username**: `postgres` (o el que prefieras)
   - **Password**: Genera una contraseña segura
   - **Version**: PostgreSQL 15 (recomendado)

### 5.2 Obtener URL de Conexión

1. Una vez creado el servicio PostgreSQL, ve a la sección "Environment Variables"
2. Copia la variable `DATABASE_URL` que se genera automáticamente
3. Debería verse así: `postgresql://usuario:password@host:puerto/database`

### 5.3 Actualizar Backend con PostgreSQL

1. Ve al servicio del backend en Koyeb
2. Actualiza la variable de entorno `DATABASE_URL` con la URL de PostgreSQL
3. Reinicia el servicio

### 5.4 Inicializar Base de Datos

El sistema creará automáticamente las tablas y datos iniciales al iniciar. Si necesitas migrar datos existentes:

1. Usa el script `migrate_data.py` incluido en el proyecto
2. O ejecuta manualmente el script de inicialización

### 5.5 Alternativas de Base de Datos

Si prefieres usar servicios externos:
- **[Supabase](https://supabase.com/)** - PostgreSQL gratuito con interfaz web
- **[Railway](https://railway.app/)** - PostgreSQL con plan gratuito
- **[PlanetScale](https://planetscale.com/)** - MySQL compatible
- **[Neon](https://neon.tech/)** - PostgreSQL serverless

## Paso 6: Verificar el Despliegue

1. Visita la URL del frontend
2. Verifica que puedas:
   - Acceder a la página de login
   - Hacer login con credenciales de prueba
   - Navegar por las diferentes secciones

## Comandos Útiles

### Para desarrollo local con Docker:
```bash
# Construir y ejecutar todo el stack (incluyendo PostgreSQL)
docker-compose up --build

# Solo el backend
docker-compose up backend

# Solo el frontend
docker-compose up frontend

# Solo la base de datos
docker-compose up postgres

# Crear datos iniciales
docker-compose exec backend python migrate_data.py
```

### Para ver logs en Koyeb:
1. Ve a tu servicio en Koyeb
2. Haz clic en "Logs" para ver los logs en tiempo real

## Solución de Problemas

### Error de CORS
- Verifica que `FRONTEND_URL` esté configurado correctamente en el backend
- Asegúrate de que la URL no termine con `/`

### Error de conexión a la API
- Verifica que `REACT_APP_API_URL` esté configurado correctamente en el frontend
- Asegúrate de que el backend esté funcionando

### Error de base de datos
- Verifica que `DATABASE_URL` esté configurado correctamente
- Para PostgreSQL, asegúrate de que el servicio esté funcionando
- Verifica que las credenciales de la base de datos sean correctas
- Revisa los logs del servicio PostgreSQL en Koyeb

## Costos

Koyeb ofrece un plan gratuito que incluye:
- 2 servicios
- 512 MB RAM por servicio
- 1 GB de almacenamiento
- 100 GB de transferencia de datos

Para más información sobre precios, visita: https://www.koyeb.com/pricing

## Soporte

- [Documentación de Koyeb](https://www.koyeb.com/docs)
- [Comunidad de Koyeb](https://www.koyeb.com/community)
- [Soporte de Koyeb](https://www.koyeb.com/support)
