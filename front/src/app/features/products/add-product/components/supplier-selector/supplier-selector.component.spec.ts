import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SupplierSelectorComponent } from './supplier-selector.component';

describe('SupplierSelectorComponent', () => {
  let component: SupplierSelectorComponent;
  let fixture: ComponentFixture<SupplierSelectorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SupplierSelectorComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SupplierSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
