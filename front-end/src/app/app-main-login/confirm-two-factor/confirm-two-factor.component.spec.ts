import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmTwoFactorComponent } from './confirm-two-factor.component';

describe('ConfirmTwoFactorComponent', () => {
  let component: ConfirmTwoFactorComponent;
  let fixture: ComponentFixture<ConfirmTwoFactorComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ConfirmTwoFactorComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ConfirmTwoFactorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
