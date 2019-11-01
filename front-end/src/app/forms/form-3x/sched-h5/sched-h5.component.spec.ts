import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SchedH5Component } from './sched-h5.component';

describe('SchedH5Component', () => {
  let component: SchedH5Component;
  let fixture: ComponentFixture<SchedH5Component>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedH5Component ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedH5Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
