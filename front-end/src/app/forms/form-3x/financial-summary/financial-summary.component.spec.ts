import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FinancialSummaryComponent } from './financial-summary.component';

describe('FinancialSummaryComponent', () => {
  let component: FinancialSummaryComponent;
  let fixture: ComponentFixture<FinancialSummaryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FinancialSummaryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FinancialSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
