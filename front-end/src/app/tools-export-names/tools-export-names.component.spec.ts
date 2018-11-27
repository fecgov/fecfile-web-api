import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ToolsExportNamesComponent } from './tools-export-names.component';

describe('ToolsExportNamesComponent', () => {
  let component: ToolsExportNamesComponent;
  let fixture: ComponentFixture<ToolsExportNamesComponent>;

  beforeEach(async(() => {
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
