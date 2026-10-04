import { ChangeDetectorRef, Component, computed, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize, Subject, Subscription, takeUntil } from 'rxjs';
import { Empleado, HeService } from '../../services/he.service';

// Directorio de empleados activos. El backend ya limita la lista al perfil:
// HR ve toda la plantilla y un mando solo la de sus grupos.
@Component({
  selector: 'app-personas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './personas.html',
})
export class Personas implements OnInit, OnDestroy {
  private readonly heService = inject(HeService);
  private readonly changeDetector = inject(ChangeDetectorRef);
  private readonly destroy$ = new Subject<void>();
  private solicitud?: Subscription;

  public grupo = signal('');
  public area = signal('');
  public busqueda = signal('');
  public grupos = signal<string[]>([]);
  public areas = signal<string[]>([]);
  public empleados = signal<Empleado[]>([]);
  public isLoading = signal(false);
  public errorMessage = signal('');

  // Filtro de texto en el navegador: nombre, apellidos, nº de personal o correo
  public empleadosVisibles = computed(() => {
    const texto = this.busqueda().trim().toLowerCase();
    if (!texto) {
      return this.empleados();
    }
    return this.empleados().filter((empleado) =>
      [empleado.pernr, empleado.nombre, empleado.apellidos, empleado.email]
        .some((valor) => (valor || '').toLowerCase().includes(texto)),
    );
  });

  public ngOnInit() {
    this.cargar();
  }

  public cargar() {
    this.solicitud?.unsubscribe();
    this.isLoading.set(true);
    this.errorMessage.set('');

    this.solicitud = this.heService
      .obtenerPersonal({ grupo: this.grupo(), direccion: this.area() })
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.isLoading.set(false);
          this.changeDetector.markForCheck();
        }),
      )
      .subscribe({
        next: (respuesta) => {
          this.empleados.set(respuesta.empleados || []);
          this.grupos.set(respuesta.grupos || []);
          this.areas.set(respuesta.areas || []);
          this.changeDetector.markForCheck();
        },
        error: (error) => {
          this.empleados.set([]);
          this.errorMessage.set(error?.error?.message || 'No se ha podido cargar el directorio de personal.');
          this.changeDetector.markForCheck();
        },
      });
  }

  public nombreCompleto(empleado: Empleado) {
    return [empleado.nombre, empleado.apellidos].filter(Boolean).join(' ') || 'Sin nombre';
  }

  public ngOnDestroy() {
    this.solicitud?.unsubscribe();
    this.destroy$.next();
    this.destroy$.complete();
  }
}
