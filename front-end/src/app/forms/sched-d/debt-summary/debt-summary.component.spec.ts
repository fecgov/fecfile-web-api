import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { DebtSummaryComponent } from './debt-summary.component';

describe('DebtSummaryComponent', () => {
  let component: DebtSummaryComponent;
  let fixture: ComponentFixture<DebtSummaryComponent>;

  beforeEach(waitForAsync(() => {
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
