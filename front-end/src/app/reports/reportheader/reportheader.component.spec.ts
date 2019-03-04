import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ReportheaderComponent } from './reportheader.component';

describe('ReportheaderComponent', () => {
  let component: ReportheaderComponent;
  let fixture: ComponentFixture<ReportheaderComponent>;

  beforeEach(async(() => {
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
