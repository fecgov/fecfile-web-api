import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { SchedFCoreComponent } from './sched-f-core.component';

describe('FormsschedFCoreComponent', () => {
  let component: SchedFCoreComponent;
  let fixture: ComponentFixture<SchedFCoreComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ SchedFCoreComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SchedFCoreComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
