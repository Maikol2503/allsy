import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PapeleraComponent } from './papelera.component';

describe('PapeleraComponent', () => {
  let component: PapeleraComponent;
  let fixture: ComponentFixture<PapeleraComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PapeleraComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PapeleraComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
