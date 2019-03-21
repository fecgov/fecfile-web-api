import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ReportsidebarComponent } from './reportsidebar.component';

describe('ReportsidebarComponent', () => {
  let component: ReportsidebarComponent;
  let fixture: ComponentFixture<ReportsidebarComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ReportsidebarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ReportsidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
