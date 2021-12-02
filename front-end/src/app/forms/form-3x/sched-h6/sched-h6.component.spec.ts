import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { SchedH6Component } from './sched-h6.component';

describe('SchedH6Component', () => {
  let component: SchedH6Component;
  let fixture: ComponentFixture<SchedH6Component>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedH6Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedH6Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
