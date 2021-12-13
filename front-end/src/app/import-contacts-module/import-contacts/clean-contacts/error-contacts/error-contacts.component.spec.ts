import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ErrorContactsComponent } from './error-contacts.component';

describe('ErrorContactsComponent', () => {
  let component: ErrorContactsComponent;
  let fixture: ComponentFixture<ErrorContactsComponent>;

  beforeEach(waitForAsync(() => {
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
