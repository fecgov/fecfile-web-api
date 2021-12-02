import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { SchedH1Component } from './sched-h1.component';

describe('SchedH1Component', () => {
  let component: SchedH1Component;
  let fixture: ComponentFixture<SchedH1Component>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedH1Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedH1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
