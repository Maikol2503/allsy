import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProviderSelectorComponent } from './provider-selector.component';

describe('ProviderSelectorComponent', () => {
  let component: ProviderSelectorComponent;
  let fixture: ComponentFixture<ProviderSelectorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProviderSelectorComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ProviderSelectorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
