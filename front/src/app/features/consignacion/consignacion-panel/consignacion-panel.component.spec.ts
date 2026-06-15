import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ConsignacionPanelComponent } from './consignacion-panel.component';

describe('ConsignacionPanelComponent', () => {
  let component: ConsignacionPanelComponent;
  let fixture: ComponentFixture<ConsignacionPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ConsignacionPanelComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ConsignacionPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
