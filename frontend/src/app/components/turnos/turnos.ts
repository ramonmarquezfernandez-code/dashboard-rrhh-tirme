import { CommonModule } from '@angular/common';
import { Component, computed, inject } from '@angular/core';
import { FiltrosService } from '../../services/filtros';

@Component({
  selector: 'app-turnos',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './turnos.html',
})
export class Turnos {
  public filtrosService = inject(FiltrosService);

  public turnosManana = computed(() => {
    const filtros = this.filtrosService.filtros();
    let base = 120;

    if (filtros.direccion === 'Administracion') {
      base = 35;
    }
    if (filtros.direccion === 'Operaciones') {
      base = 85;
    }
    if (filtros.anio === 2025) {
      base = 110;
    }

    return base;
  });

  public turnosTarde = computed(() => Math.round(this.turnosManana() * 0.65));
  public turnosNoche = computed(() => Math.round(this.turnosManana() * 0.25));
}