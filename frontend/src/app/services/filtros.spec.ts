import { TestBed } from '@angular/core/testing';
import { FiltrosService } from './filtros';

describe('Filtros', () => {
  let service: FiltrosService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FiltrosService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
