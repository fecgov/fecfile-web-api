import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ToolsExportNamesComponent } from './tools-export-names.component';

describe('ToolsExportNamesComponent', () => {
  let component: ToolsExportNamesComponent;
  let fixture: ComponentFixture<ToolsExportNamesComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ToolsExportNamesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ToolsExportNamesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
