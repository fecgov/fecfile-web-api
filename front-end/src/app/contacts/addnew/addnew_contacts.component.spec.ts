import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { IndividualReceiptComponent } from './addnew_contacts.component';

describe('IndividualReceiptComponent', () => {
  let component: IndividualReceiptComponent;
  let fixture: ComponentFixture<IndividualReceiptComponent>;

  beforeEach(async(() => {
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
