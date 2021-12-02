import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { IndividualReceiptComponent } from './individual-receipt.component';

describe('IndividualReceiptComponent', () => {
  let component: IndividualReceiptComponent;
  let fixture: ComponentFixture<IndividualReceiptComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ IndividualReceiptComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(IndividualReceiptComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
