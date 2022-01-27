import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ToolsCreateBackupComponent } from './tools-create-backup.component';

describe('ToolsCreateBackupComponent', () => {
  let component: ToolsCreateBackupComponent;
  let fixture: ComponentFixture<ToolsCreateBackupComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ToolsCreateBackupComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ToolsCreateBackupComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
