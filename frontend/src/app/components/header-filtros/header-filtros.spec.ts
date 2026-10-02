import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HeaderFiltros } from './header-filtros';

describe('HeaderFiltros', () => {
  let component: HeaderFiltros;
  let fixture: ComponentFixture<HeaderFiltros>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HeaderFiltros],
    }).compileComponents();

    fixture = TestBed.createComponent(HeaderFiltros);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
