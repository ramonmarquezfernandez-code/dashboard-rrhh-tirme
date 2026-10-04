// Matriz de pantallas visibles por rol activo. La usan el guard de rutas y el
// sidebar. Ojo: esto solo oculta menús; el filtrado real de datos lo hace el backend.

export type Rol = 'hr' | 'mando' | 'empleado';

export const ROLES_POR_PRIORIDAD: Rol[] = ['hr', 'mando', 'empleado'];

export const ETIQUETAS_ROL: Record<Rol, string> = {
  hr: 'Recursos Humanos (HR)',
  mando: 'Mando (VB / FI)',
  empleado: 'Empleado',
};

const TODOS: Rol[] = ['hr', 'mando', 'empleado'];

export const PERMISOS_RUTA: Record<string, Rol[]> = {
  // Formulario de parte: todos los perfiles, cada uno sobre sus propios partes
  'nuevo-parte': TODOS,
  'mis-partes': TODOS,
  'mis-partes/:mandt': TODOS,
  'resumen-general': ['hr', 'mando'],
  personal: ['hr', 'mando'],
  'horas-extra': TODOS,
  'horas-extra-empleados': TODOS,
  'ranking-combo': ['hr', 'mando'],
  'sp-retribuidas': TODOS,
};

export function puedeVerRuta(rol: Rol | null, ruta: string): boolean {
  return !!rol && (PERMISOS_RUTA[ruta] ?? []).includes(rol);
}

/** Pantalla de inicio tras el login según el rol activo. */
export function rutaInicio(rol: Rol | null): string {
  return rol === 'empleado' ? '/horas-extra' : '/resumen-general';
}
