import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { LoanpaymentComponent } from './loanpayment.component';

describe('LoanpaymentComponent', () => {
  let component: LoanpaymentComponent;
  let fixture: ComponentFixture<LoanpaymentComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ LoanpaymentComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LoanpaymentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});