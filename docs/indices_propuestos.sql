-- Índices propuestos para zparte (generado por medir_rendimiento.py).
-- Propuesta para revisar con el equipo de la app corporativa: el esquema es compartido.

-- consultas por fecha (año natural) de un mando: filtro "CODGR IN (sus grupos) OR PERNR = suyo" con PADAT entre dos fechas. Con este índice y zparte_PERNR_IDX (PERNR, PADAT) el optimizador combina ambos rangos (index_merge) en lugar de recorrer toda la tabla.
ALTER TABLE zparte ADD INDEX `idx_zparte_codgr_padat` (`CODGR`, `PADAT`);

-- pantalla de SP: partes con SP marcado (~3 %) en los últimos 12/24 meses. Requiere que la condición sobre SP no use funciones (SP IN (...) en lugar de TRIM(SP) IN (...)).
ALTER TABLE zparte ADD INDEX `idx_zparte_sp_padat` (`SP`, `PADAT`);
