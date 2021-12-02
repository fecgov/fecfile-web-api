import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ReportheaderComponent } from './reportheader.component';

describe('ReportheaderComponent', () => {
  let component: ReportheaderComponent;
  let fixture: ComponentFixture<ReportheaderComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ReportheaderComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReportheaderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
