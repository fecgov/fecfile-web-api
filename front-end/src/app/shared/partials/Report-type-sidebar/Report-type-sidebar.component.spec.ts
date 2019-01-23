import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ReportTypeSidebarComponent } from './Report-type-sidebar.component';

describe('FormSidebarComponent', () => {
  let component: ReportTypeSidebarComponent;
  let fixture: ComponentFixture<ReportTypeSidebarComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ReportTypeSidebarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReportTypeSidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
