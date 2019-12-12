import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DebtSummaryComponent } from './debt-summary.component';

describe('DebtSummaryComponent', () => {
  let component: DebtSummaryComponent;
  let fixture: ComponentFixture<DebtSummaryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DebtSummaryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DebtSummaryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
