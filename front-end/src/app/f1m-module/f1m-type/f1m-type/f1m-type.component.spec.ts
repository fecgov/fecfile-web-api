import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { F1mTypeComponent } from './f1m-type.component';

describe('F1mTypeComponent', () => {
  let component: F1mTypeComponent;
  let fixture: ComponentFixture<F1mTypeComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ F1mTypeComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(F1mTypeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
