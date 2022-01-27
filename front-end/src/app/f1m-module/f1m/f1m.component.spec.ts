import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { F1mComponent } from './f1m.component';

describe('F1mComponent', () => {
  let component: F1mComponent;
  let fixture: ComponentFixture<F1mComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ F1mComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(F1mComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
