import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SchedC1Component } from './sched-c1.component';

describe('SchedC1Component', () => {
  let component: SchedC1Component;
  let fixture: ComponentFixture<SchedC1Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedC1Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedC1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
