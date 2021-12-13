import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { SchedH3Component } from './sched-h3.component';

describe('SchedH3Component', () => {
  let component: SchedH3Component;
  let fixture: ComponentFixture<SchedH3Component>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedH3Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedH3Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
