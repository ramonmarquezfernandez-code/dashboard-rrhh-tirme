import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FiltrosService } from '../../services/filtros';

@Component({
  selector: 'app-header-filtros',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './header-filtros.html',
  styleUrl: './header-filtros.scss',
})
export class HeaderFiltros {
  // Inyectamos el servicio global de Signals
  public filtrosService = inject(FiltrosService);

  // Métodos que capturan los cambios en los selects y actualizan el estado global
  onDireccionChange(event: any) {
    this.filtrosService.actualizarFiltros({ direccion: event.target.value });
  }

  onGrupoChange(event: any) {
    this.filtrosService.actualizarFiltros({ grupo: event.target.value });
  }

  onFechaChange(campo: 'fechaDesde' | 'fechaHasta', valor: string) {
    const cambios = { [campo]: valor } as Partial<ReturnType<typeof this.filtrosService.filtros>>;
    if (campo === 'fechaDesde' && valor) {
      cambios.anio = Number(valor.slice(0, 4));
    }
    this.filtrosService.actualizarFiltros(cambios);
  }
}
