import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockDetailComponent } from './stock-detail.component';

describe('StockDetailComponent', () => {
  let component: StockDetailComponent;
  let fixture: ComponentFixture<StockDetailComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockDetailComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
