import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { TwoFactorLoginComponent } from './two-factor-login.component';

describe('TwoFactorLoginComponent', () => {
  let component: TwoFactorLoginComponent;
  let fixture: ComponentFixture<TwoFactorLoginComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ TwoFactorLoginComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TwoFactorLoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
