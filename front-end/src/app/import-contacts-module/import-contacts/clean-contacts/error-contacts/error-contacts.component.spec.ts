import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ErrorContactsComponent } from './error-contacts.component';

describe('ErrorContactsComponent', () => {
  let component: ErrorContactsComponent;
  let fixture: ComponentFixture<ErrorContactsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ErrorContactsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ErrorContactsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
