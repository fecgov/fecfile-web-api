import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ToolsMergeNamesComponent } from './tools-merge-names.component';

describe('ToolsMergeNamesComponent', () => {
  let component: ToolsMergeNamesComponent;
  let fixture: ComponentFixture<ToolsMergeNamesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ToolsMergeNamesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ToolsMergeNamesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
