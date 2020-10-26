import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { ImportContactsStepsEnum } from '../import-contacts-setps.enum';

@Component({
  selector: 'app-import-how-to',
  templateUrl: './import-how-to.component.html',
  styleUrls: ['./import-how-to.component.scss']
})
export class ImportHowToComponent implements OnInit {
  @Output()
  public returnEmitter: EventEmitter<any> = new EventEmitter<any>();

  public steps: Array<any>;
  public currentStep: ImportContactsStepsEnum;
  public readonly start = ImportContactsStepsEnum.start;
  public readonly step1Upload = ImportContactsStepsEnum.step1Upload;
  public readonly step3Clean = ImportContactsStepsEnum.step3Clean;
  public readonly step4ImportDone = ImportContactsStepsEnum.step4ImportDone;

  constructor() {}

  ngOnInit() {
    this.steps = [
      { text: 'Upload', step: this.step1Upload },
      { text: 'Clean', step: this.step3Clean },
      { text: 'Import', step: this.step4ImportDone }
    ];
    this.currentStep = this.step1Upload;
  }

  public returnToImport() {
    this.returnEmitter.emit();
  }
}
