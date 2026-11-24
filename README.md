# Dashboard de logs

Dashboard en Dash que muestra, a partir de la tabla `logs` de PostgreSQL:

- Response time promedio
- Throughput (RPM, peticiones por minuto)
- Conteo de errores 4xx y 5xx
- Response time p95 y p99

## Filtros

- **Servicio**: todos o uno en particular (auth, catalog, checkout, payments, users).
- **Ventana**: últimas 1h, 3h o 24h contadas desde la hora actual.
- **Actualizar cada**: refresco automático cada 10s o 60s.

## Requisitos

- Python 3.10 o superior
- Acceso a la base de datos PostgreSQL con la tabla `logs`

## Cómo correrlo

1. Clonar el repositorio y entrar a la carpeta:

   ```bash
   git clone <url-del-repo>
   cd Dashboard-Dash
   ```

2. Crear y activar un entorno virtual:

   ```bash
   python -m venv .venv
   ```

   Windows:

   ```bash
   .venv\Scripts\activate
   ```

   Linux / macOS:

   ```bash
   source .venv/bin/activate
   ```

3. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Crear un archivo `.env.local` en la raíz del proyecto con la cadena de conexión:

   ```
   DATABASE_URL=postgresql://usuario:contraseña@host:puerto/base_de_datos
   ```

5. Ejecutar el dashboard:

   ```bash
   python app.py
   ```

6. Abrir en el navegador: http://127.0.0.1:8050

## Notas

- La conexión a la base de datos es de solo lectura.
- Las horas se muestran en zona horaria America/Bogota.
