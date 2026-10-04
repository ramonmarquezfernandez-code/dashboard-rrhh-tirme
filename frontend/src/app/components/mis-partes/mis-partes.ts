import { ChangeDetectorRef, Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { elegirAnio, HeService } from '../../services/he.service';
import { PartesService, ResumenParte } from '../../services/partes.service';

// Partes del propio empleado: consulta por ejercicio y acceso a editar o borrar
// los que aún no tienen visto bueno (estado B).
@Component({
  selector: 'app-mis-partes',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './mis-partes.html',
})
export class MisPartes implements OnInit {
  private readonly partesService = inject(PartesService);
  private readonly heService = inject(HeService);
  private readonly changeDetector = inject(ChangeDetectorRef);

  public anio = signal(new Date().getFullYear());
  public anios = signal<number[]>([new Date().getFullYear()]);
  public partes = signal<ResumenParte[]>([]);
  public cargando = signal(true);
  public mensaje = signal<string>(inject(Router).getCurrentNavigation()?.extras.state?.['mensaje'] ?? history.state?.mensaje ?? '');
  public error = signal('');

  public ngOnInit() {
    this.heService.obtenerEjercicios().subscribe({
      next: (respuesta) => {
        const { anios, anio } = elegirAnio(respuesta);
        this.anios.set(anios);
        this.anio.set(anio);
        this.cargar();
      },
      error: () => this.cargar(),
    });
  }

  public cargar() {
    this.cargando.set(true);
    this.partesService.listar(this.anio()).subscribe({
      next: (respuesta) => {
        this.partes.set(respuesta.partes);
        this.cargando.set(false);
        this.changeDetector.markForCheck();
      },
      error: () => {
        this.partes.set([]);
        this.cargando.set(false);
        this.error.set('No se han podido cargar tus partes.');
        this.changeDetector.markForCheck();
      },
    });
  }

  public cambiarAnio(valor: number) {
    this.anio.set(Number(valor));
    this.cargar();
  }

  public borrar(parte: ResumenParte) {
    if (!confirm(`¿Borrar el parte del ${parte.fecha} (turno ${parte.turno})?`)) {
      return;
    }
    this.partesService.borrar(parte.mandt).subscribe({
      next: () => {
        this.mensaje.set(`Parte del ${parte.fecha} borrado.`);
        this.cargar();
      },
      error: (error: HttpErrorResponse) => {
        this.error.set(error.error?.message ?? 'No se ha podido borrar el parte.');
        this.changeDetector.markForCheck();
      },
    });
  }
}
