import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { F24Component } from './f24.component';

describe('F24Component', () => {
  let component: F24Component;
  let fixture: ComponentFixture<F24Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ F24Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(F24Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
