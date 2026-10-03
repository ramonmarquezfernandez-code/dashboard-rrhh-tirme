#!/bin/bash
# Crea la base de datos vacía que usan los tests (pytest) y da permisos al
# usuario de la aplicación. Los tests crean sus propias tablas y datos.
set -e
TEST_DB="${TEST_DB_NAME:-epartes_test}"
mariadb -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
CREATE DATABASE IF NOT EXISTS \`${TEST_DB}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON \`${TEST_DB}\`.* TO '${MARIADB_USER}'@'%';
FLUSH PRIVILEGES;
SQL
