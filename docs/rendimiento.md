# Rendimiento de las consultas del dashboard

> Generado automáticamente por `dashboard_rrhh/medir_rendimiento.py` el 2026-10-03 18:36. No editar a mano: se sobrescribe en cada ejecución.

## Cómo reproducirlo

```bash
cd dashboard_rrhh
python medir_rendimiento.py
```

Genera los datos con semilla y fecha fijas (mismos datos en cada ejecución), mide y reescribe este documento, `rendimiento.json`, `explain/` e `indices_propuestos.sql`. Los tiempos absolutos dependen del equipo; lo comparable son las proporciones entre escenarios.

## Entorno y datos

| | |
|---|---|
| Servidor | MariaDB 12.3.3-MariaDB-ubu2404 |
| Equipo | Windows 11, AMD64, Python 3.13.14 |
| Datos | generar_datos.py con semilla 2026, fecha final 2026-10-03, ~100.000 partes |
| Filas | zparte: 99.906, userpayroll: 250, zgrroles: 66, zperiodos: 34 |
| Consultas | ejercicio 2025; mando = FI del grupo 3 (26 empleados) |
| Medición | 1 ejecución de calentamiento + 7 repeticiones; se muestra la mediana |
| Caché de consultas | `query_cache_type = OFF` |

## Escenarios de índices sobre `zparte`

- **1. Solo clave primaria**: se eliminan todos los índices secundarios de zparte (incluidos los UNIQUE).
- **2. Índices de producción**: los 20 índices secundarios del esquema de producción.
- **3. Producción + propuestos**: los de producción más 2 índices propuestos (ver más abajo).

## Tiempos por pantalla y perfil

Suma de las medianas de las sentencias sobre `zparte` que ejecuta cada pantalla (ms). **≈** indica que el plan de ejecución es el mismo en los dos escenarios comparados: esa diferencia es ruido de medición, no efecto de los índices.

| Consulta | Perfil | Sentencias | 1. Solo clave primaria | 2. Índices de producción | 3. Producción + propuestos | 1 → 2 | 2 → 3 |
|---|---|---:|---:|---:|---:|---:|---:|
| HE por periodos, ejercicio 2025 completo | hr | 3 | 388.1 | 406.7 | 452.6 | ≈ +5 % | ≈ +11 % |
| HE por periodos, año natural 2025 | hr | 3 | 367.3 | 394.1 | 366.9 | ≈ +7 % | ≈ −7 % |
| HE por periodos, periodo de nómina 06 | hr | 3 | 192.5 | 39.1 | 38.9 | −80 % | ≈ −0 % |
| HE por empleado, ejercicio 2025 | hr | 2 | 237.5 | 204.7 | 202.5 | ≈ −14 % | ≈ −1 % |
| Ranking HE combo, ejercicio 2025 | hr | 2 | 245.2 | 246.5 | 250.6 | ≈ +1 % | ≈ +2 % |
| SP de los últimos 12 y 24 meses | hr | 4 | 164.5 | 166.2 | 25.3 | ≈ +1 % | −85 % |
| Años disponibles (combo de año) | hr | 1 | 49.9 | 0.8 | 0.8 | −98 % | ≈ −4 % |
| HE por periodos, ejercicio 2025 completo | mando | 3 | 245.5 | 47.9 | 49.4 | −80 % | ≈ +3 % |
| HE por periodos, año natural 2025 | mando | 3 | 253.2 | 221.0 | 48.1 | ≈ −13 % | −78 % |
| HE por periodos, periodo de nómina 06 | mando | 3 | 194.7 | 7.7 | 7.8 | −96 % | ≈ +2 % |
| HE por empleado, ejercicio 2025 | mando | 2 | 111.1 | 27.4 | 28.4 | −75 % | ≈ +4 % |
| Ranking HE combo, ejercicio 2025 | mando | 2 | 136.2 | 52.3 | 30.3 | −62 % | ≈ −42 % |
| SP de los últimos 12 y 24 meses | mando | 4 | 257.8 | 218.6 | 16.4 | ≈ −15 % | −93 % |
| Años disponibles (combo de año) | mando | 1 | 54.2 | 27.8 | 21.9 | −49 % | ≈ −21 % |
| HE por periodos, ejercicio 2025 completo | empleado | 3 | 210.2 | 6.8 | 6.1 | −97 % | ≈ −10 % |
| HE por periodos, año natural 2025 | empleado | 3 | 176.7 | 5.1 | 5.0 | −97 % | ≈ −4 % |
| HE por periodos, periodo de nómina 06 | empleado | 3 | 192.2 | 4.7 | 3.7 | −98 % | ≈ −20 % |
| HE por empleado, ejercicio 2025 | empleado | 2 | 97.1 | 5.1 | 4.5 | −95 % | ≈ −11 % |
| Ranking HE combo, ejercicio 2025 | empleado | 2 | 101.3 | 5.2 | 4.3 | −95 % | ≈ −17 % |
| SP de los últimos 12 y 24 meses | empleado | 4 | 154.0 | 5.4 | 7.5 | −97 % | +40 % |
| Años disponibles (combo de año) | empleado | 1 | 37.5 | 1.2 | 1.1 | −97 % | ≈ −11 % |
| **Total** | | | **3 866.7** | **2 094.3** | **1 572.0** | **−46 %** | **−25 %** |

## Plan de ejecución (resumen del EXPLAIN)

Acceso a `zparte` en cada sentencia: tipo de acceso (`ALL` = recorrido completo), índice usado y filas estimadas. El EXPLAIN completo (tabular y JSON) y el SQL de cada sentencia están en `docs/explain/`.

| Sentencia | 1. Solo clave primaria | 2. Índices de producción | 3. Producción + propuestos |
|---|---|---|---|
| [he_por_periodo · hr · 1](explain/he_por_periodo__hr__1.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [he_por_periodo · hr · 2](explain/he_por_periodo__hr__2.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [he_por_periodo · hr · 3](explain/he_por_periodo__hr__3.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [he_por_periodo_natural · hr · 1](explain/he_por_periodo_natural__hr__1.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [he_por_periodo_natural · hr · 2](explain/he_por_periodo_natural__hr__2.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [he_por_periodo_natural · hr · 3](explain/he_por_periodo_natural__hr__3.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [he_por_periodo_junio · hr · 1](explain/he_por_periodo_junio__hr__1.txt) | `ALL` — (99931 filas) | `ref` idx_ejer_month (3281 filas) | `ref` idx_ejer_month (3281 filas) |
| [he_por_periodo_junio · hr · 2](explain/he_por_periodo_junio__hr__2.txt) | `ALL` — (99931 filas) | `ref` idx_ejer_month (3281 filas) | `ref` idx_ejer_month (3281 filas) |
| [he_por_periodo_junio · hr · 3](explain/he_por_periodo_junio__hr__3.txt) | `ALL` — (99931 filas) | `ref` idx_ejer_month (3281 filas) | `ref` idx_ejer_month (3281 filas) |
| [he_por_empleado · hr · 1](explain/he_por_empleado__hr__1.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [he_por_empleado · hr · 2](explain/he_por_empleado__hr__2.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [ranking_combo · hr · 1](explain/ranking_combo__hr__1.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [ranking_combo · hr · 2](explain/ranking_combo__hr__2.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `ALL` — (94747 filas) |
| [sp_resumen · hr · 1](explain/sp_resumen__hr__1.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `range` idx_zparte_sp_padat (860 filas) |
| [sp_resumen · hr · 2](explain/sp_resumen__hr__2.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `range` idx_zparte_sp_padat (860 filas) |
| [sp_resumen · hr · 3](explain/sp_resumen__hr__3.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `range` idx_zparte_sp_padat (1798 filas) |
| [sp_resumen · hr · 4](explain/sp_resumen__hr__4.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `range` idx_zparte_sp_padat (1798 filas) |
| [ejercicios · hr · 1](explain/ejercicios__hr__1.txt) | `ALL` — (99931 filas) | `range` idx_ejer_month (3 filas) | `range` idx_ejer_month (3 filas) |
| [he_por_periodo · mando · 1](explain/he_por_periodo__mando__1.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) |
| [he_por_periodo · mando · 2](explain/he_por_periodo__mando__2.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) |
| [he_por_periodo · mando · 3](explain/he_por_periodo__mando__3.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) |
| [he_por_periodo_natural · mando · 1](explain/he_por_periodo_natural__mando__1.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `index_merge` idx_unico_persona_dia,idx_zparte_codgr_padat (3755 filas) |
| [he_por_periodo_natural · mando · 2](explain/he_por_periodo_natural__mando__2.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `index_merge` idx_unico_persona_dia,idx_zparte_codgr_padat (3755 filas) |
| [he_por_periodo_natural · mando · 3](explain/he_por_periodo_natural__mando__3.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `index_merge` idx_unico_persona_dia,idx_zparte_codgr_padat (3755 filas) |
| [he_por_periodo_junio · mando · 1](explain/he_por_periodo_junio__mando__1.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_mes_codgr_stat (347 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_mes_codgr_stat (347 filas) |
| [he_por_periodo_junio · mando · 2](explain/he_por_periodo_junio__mando__2.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_mes_codgr_stat (347 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_mes_codgr_stat (347 filas) |
| [he_por_periodo_junio · mando · 3](explain/he_por_periodo_junio__mando__3.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_mes_codgr_stat (347 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_mes_codgr_stat (347 filas) |
| [he_por_empleado · mando · 1](explain/he_por_empleado__mando__1.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) |
| [he_por_empleado · mando · 2](explain/he_por_empleado__mando__2.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) |
| [ranking_combo · mando · 1](explain/ranking_combo__mando__1.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) |
| [ranking_combo · mando · 2](explain/ranking_combo__mando__2.txt) | `ALL` — (99931 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) | `index_merge` zparte_PERNR_MES_EJERC_IDX,idx_zparte_ejerc_codgr (3776 filas) |
| [sp_resumen · mando · 1](explain/sp_resumen__mando__1.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `range` idx_zparte_sp_padat (860 filas) |
| [sp_resumen · mando · 2](explain/sp_resumen__mando__2.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `range` idx_zparte_sp_padat (860 filas) |
| [sp_resumen · mando · 3](explain/sp_resumen__mando__3.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `range` idx_zparte_sp_padat (1798 filas) |
| [sp_resumen · mando · 4](explain/sp_resumen__mando__4.txt) | `ALL` — (99931 filas) | `ALL` — (97505 filas) | `range` idx_zparte_sp_padat (1798 filas) |
| [ejercicios · mando · 1](explain/ejercicios__mando__1.txt) | `ALL` — (99931 filas) | `range` idx_zparte_ejerc_codgr (97505 filas) | `range` idx_zparte_ejerc_codgr (94747 filas) |
| [he_por_periodo · empleado · 1](explain/he_por_periodo__empleado__1.txt) | `ALL` — (99931 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) |
| [he_por_periodo · empleado · 2](explain/he_por_periodo__empleado__2.txt) | `ALL` — (99931 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) |
| [he_por_periodo · empleado · 3](explain/he_por_periodo__empleado__3.txt) | `ALL` — (99931 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) |
| [he_por_periodo_natural · empleado · 1](explain/he_por_periodo_natural__empleado__1.txt) | `ALL` — (99931 filas) | `range` idx_unico_persona_dia (156 filas) | `range` idx_unico_persona_dia (156 filas) |
| [he_por_periodo_natural · empleado · 2](explain/he_por_periodo_natural__empleado__2.txt) | `ALL` — (99931 filas) | `range` idx_unico_persona_dia (156 filas) | `range` idx_unico_persona_dia (156 filas) |
| [he_por_periodo_natural · empleado · 3](explain/he_por_periodo_natural__empleado__3.txt) | `ALL` — (99931 filas) | `range` idx_unico_persona_dia (156 filas) | `range` idx_unico_persona_dia (156 filas) |
| [he_por_periodo_junio · empleado · 1](explain/he_por_periodo_junio__empleado__1.txt) | `ALL` — (99931 filas) | `ref` zparte_PERNR_MES_EJERC_IDX (11 filas) | `ref` zparte_PERNR_MES_EJERC_IDX (11 filas) |
| [he_por_periodo_junio · empleado · 2](explain/he_por_periodo_junio__empleado__2.txt) | `ALL` — (99931 filas) | `ref` zparte_PERNR_MES_EJERC_IDX (11 filas) | `ref` zparte_PERNR_MES_EJERC_IDX (11 filas) |
| [he_por_periodo_junio · empleado · 3](explain/he_por_periodo_junio__empleado__3.txt) | `ALL` — (99931 filas) | `ref` zparte_PERNR_MES_EJERC_IDX (11 filas) | `ref` zparte_PERNR_MES_EJERC_IDX (11 filas) |
| [he_por_empleado · empleado · 1](explain/he_por_empleado__empleado__1.txt) | `ALL` — (99931 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) |
| [he_por_empleado · empleado · 2](explain/he_por_empleado__empleado__2.txt) | `ALL` — (99931 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) |
| [ranking_combo · empleado · 1](explain/ranking_combo__empleado__1.txt) | `ALL` — (99931 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) |
| [ranking_combo · empleado · 2](explain/ranking_combo__empleado__2.txt) | `ALL` — (99931 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) | `range` zparte_PERNR_MES_EJERC_IDX (150 filas) |
| [sp_resumen · empleado · 1](explain/sp_resumen__empleado__1.txt) | `ALL` — (99931 filas) | `range` idx_unico_persona_dia (162 filas) | `ref|filter` idx_Zparte_pernr_group|idx_zparte_sp_padat (432 (1%) filas) |
| [sp_resumen · empleado · 2](explain/sp_resumen__empleado__2.txt) | `ALL` — (99931 filas) | `range` idx_unico_persona_dia (162 filas) | `ref|filter` idx_Zparte_pernr_group|idx_zparte_sp_padat (432 (1%) filas) |
| [sp_resumen · empleado · 3](explain/sp_resumen__empleado__3.txt) | `ALL` — (99931 filas) | `range` idx_unico_persona_dia (300 filas) | `ref|filter` idx_Zparte_pernr_group|idx_zparte_sp_padat (432 (2%) filas) |
| [sp_resumen · empleado · 4](explain/sp_resumen__empleado__4.txt) | `ALL` — (99931 filas) | `range` idx_unico_persona_dia (300 filas) | `ref|filter` idx_Zparte_pernr_group|idx_zparte_sp_padat (432 (2%) filas) |
| [ejercicios · empleado · 1](explain/ejercicios__empleado__1.txt) | `ALL` — (99931 filas) | `ref` zparte_PERNR_MES_EJERC_IDX (432 filas) | `ref` zparte_PERNR_MES_EJERC_IDX (432 filas) |

## Índices propuestos

Propuesta para el equipo de la aplicación corporativa (el esquema es compartido). No se añaden al dump; el script los crea solo durante la medición. SQL en `docs/indices_propuestos.sql`.

- `idx_zparte_codgr_padat` (CODGR, PADAT): consultas por fecha (año natural) de un mando: filtro "CODGR IN (sus grupos) OR PERNR = suyo" con PADAT entre dos fechas. Con este índice y zparte_PERNR_IDX (PERNR, PADAT) el optimizador combina ambos rangos (index_merge) en lugar de recorrer toda la tabla.
- `idx_zparte_sp_padat` (SP, PADAT): pantalla de SP: partes con SP marcado (~3 %) en los últimos 12/24 meses. Requiere que la condición sobre SP no use funciones (SP IN (...) en lugar de TRIM(SP) IN (...)).

## Conclusiones

- Sin índices secundarios, las consultas del dashboard suman 3 866.7 ms; con los índices de producción, 2 094.3 ms (−46 %).
- La pantalla más costosa sin índices es *HE por periodos, ejercicio 2025 completo* (hr): 388.1 ms.
- Las consultas de un empleado y las de un periodo de nómina concreto son las que más ganan con los índices de producción: pasan de recorrer toda la tabla a leer solo las filas del trabajador o del periodo.
- 4 pantallas recorren toda la tabla en todos los escenarios (p. ej. *HE por periodos, ejercicio 2025 completo* (hr)). Son agregados de RRHH sobre un año entero (un tercio de las filas): para eso el recorrido completo es el plan correcto y un índice no ayudaría.
- Con los índices propuestos: 1 572.0 ms en total (−25 % respecto a producción).
  - Empeora *SP de los últimos 12 y 24 meses* (empleado): 5.4 → 7.5 ms, porque el optimizador cambia de plan (ver su EXPLAIN). Es un coste pequeño frente a la mejora del resto.
