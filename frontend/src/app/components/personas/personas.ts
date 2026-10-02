import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FiltrosService } from '../../services/filtros';

@Component({
  selector: 'app-personas',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './personas.html',
})
export class Personas {
  public filtrosService = inject(FiltrosService);
} 
