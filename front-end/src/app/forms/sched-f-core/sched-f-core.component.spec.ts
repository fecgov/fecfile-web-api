import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { SchedFCoreComponent } from './sched-f-core.component';

describe('FormsschedFCoreComponent', () => {
  let component: SchedFCoreComponent;
  let fixture: ComponentFixture<SchedFCoreComponent>;

  beforeEach(waitForAsync(() => {
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
