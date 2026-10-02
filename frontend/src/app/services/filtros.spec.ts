import { TestBed } from '@angular/core/testing';
import { Filtros } from './filtros';

describe('Filtros', () => {
  let service: Filtros;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Filtros);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
