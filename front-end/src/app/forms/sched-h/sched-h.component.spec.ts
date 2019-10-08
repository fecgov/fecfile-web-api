import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SchedHComponent } from './sched-h.component';

describe('SchedHComponent', () => {
  let component: SchedHComponent;
  let fixture: ComponentFixture<SchedHComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedHComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedHComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
