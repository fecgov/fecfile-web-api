import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ErrorContactsFieldComponent } from './error-contacts-field.component';

describe('ErrorContactsFieldComponent', () => {
  let component: ErrorContactsFieldComponent;
  let fixture: ComponentFixture<ErrorContactsFieldComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ErrorContactsFieldComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ErrorContactsFieldComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
