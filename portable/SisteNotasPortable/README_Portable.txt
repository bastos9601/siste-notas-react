Sistema de Gestión de Notas - Versión Portable

Resumen
- Esta versión portable incluye backend y frontend listos para usar localmente.
- Al abrir `start.bat`, se inicia el servidor y se abre `http://localhost:8000/`.

Cómo iniciar
- Ejecuta `start.bat` (doble clic).
- Si Windows muestra un aviso de firewall, permite el acceso local.
- Si ves "Error al obtener usuario" al cargar, inicia sesión para continuar.

Ubicación de datos
- Base de datos: `portable/SisteNotasPortable/data/sistema_notas.db`.
- Logos subidos: `portable/SisteNotasPortable/uploads/logos/`.
- Puedes mover la carpeta `SisteNotasPortable` sin perder datos.

Descarga de plantillas
- Las plantillas se sirven desde la ruta `http://localhost:8000/templates/`.
- El botón "Descargar plantilla" en la aplicación descarga el archivo Excel desde
  `http://localhost:8000/templates/Template.xlsx`.
- Si el botón no aparece en tu vista, puedes descargar directamente abriendo:
  `http://localhost:8000/templates/Template.xlsx` en el navegador.
- La descarga irá a tu carpeta de descargas del sistema.

Notas importantes
- Las plantillas están incluidas dentro del portable; no es necesario Internet.
- Si cambias de puerto o ruta, asegúrate de acceder a `http://localhost:8000/templates/...`.
- Si el navegador bloquea descargas, habilítalas para este sitio.

Personalización de plantillas (avanzado)
- Las plantillas viven en el build del frontend y se publican en `/templates`.
- Para cambiar/añadir una plantilla, reemplázala en `frontend/public/templates/` y
  vuelve a compilar el frontend y el portable.
- Luego, la encontrarás disponible en `http://localhost:8000/templates/<tu_archivo>.xlsx`.

Soporte
- Si tienes dudas o necesitas una plantilla adicional, contacta al responsable del sistema.

Cómo usar:
- Copia toda esta carpeta a tu USB o a otra ubicación.
- Ejecuta "start.bat" para iniciar el servidor y abrir el navegador.
- Alternativamente, ejecuta "SistemaNotas.exe" y abre http://localhost:8000/.

Datos y archivos:
- La base de datos SQLite se guarda en la carpeta "data" como "sistema_notas.db".
- Los logos y archivos subidos se guardan en "uploads\\logos".

Requisitos:
- Windows 64-bit.
- Al primer inicio, Windows puede pedir permitir acceso; acepta el acceso local.

Notas:
- Esta versión está pensada para uso local/portable. Para multiusuario en red, considera usar una base de datos en servidor (p.ej., PostgreSQL).