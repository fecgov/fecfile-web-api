import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CashOnHandComponent } from './cash-on-hand.component';

describe('CashOnHandComponent', () => {
  let component: CashOnHandComponent;
  let fixture: ComponentFixture<CashOnHandComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CashOnHandComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CashOnHandComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
