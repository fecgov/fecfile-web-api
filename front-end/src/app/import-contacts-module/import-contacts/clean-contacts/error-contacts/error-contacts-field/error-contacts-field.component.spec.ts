import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ErrorContactsFieldComponent } from './error-contacts-field.component';

describe('ErrorContactsFieldComponent', () => {
  let component: ErrorContactsFieldComponent;
  let fixture: ComponentFixture<ErrorContactsFieldComponent>;

  beforeEach(async(() => {
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
