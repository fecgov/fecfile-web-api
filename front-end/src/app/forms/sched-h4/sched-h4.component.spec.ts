import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SchedH4Component } from './sched-h4.component';

describe('SchedH4Component', () => {
  let component: SchedH4Component;
  let fixture: ComponentFixture<SchedH4Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedH4Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedH4Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
