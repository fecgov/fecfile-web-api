import { Component, OnInit } from '@angular/core';
import { ImportContactsStepsEnum } from './import-contacts-setps.enum';

@Component({
  selector: 'app-import-contacts',
  templateUrl: './import-contacts.component.html',
  styleUrls: ['./import-contacts.component.scss']
})
export class ImportContactsComponent implements OnInit {

  public steps: Array<any>;
  public currentStep: ImportContactsStepsEnum;
  public readonly step1Upload = ImportContactsStepsEnum.step1Upload;
  public readonly step2Configure = ImportContactsStepsEnum.step2Configure;
  public readonly step3Clean = ImportContactsStepsEnum.step3Clean;
  public readonly step4ImportDone = ImportContactsStepsEnum.step4ImportDone;

  constructor() { }

  ngOnInit() {
    this.steps = [
      { text: 'Upload', step: this.step1Upload },
      { text: 'Configure', step: this.step2Configure },
      { text: 'Clean', step: this.step3Clean },
      { text: 'Import', step: this.step4ImportDone }
    ];
    this.currentStep = this.step1Upload;
  }

  public showNextStep() {
    switch (this.currentStep) {
      case this.step1Upload:
        this.currentStep = this.step2Configure;
        break;
      case this.step2Configure:
        this.currentStep = this.step3Clean;
        break;
      case this.step3Clean:
        this.currentStep = this.step4ImportDone;
        break;
      default:
        this.currentStep = this.step1Upload;
    }
  }

  public showPreviousStep() {
    switch (this.currentStep) {
      case this.step4ImportDone:
        this.currentStep = this.step3Clean;
        break;
      case this.step3Clean:
        this.currentStep = this.step2Configure;
        break;
      case this.step2Configure:
        this.currentStep = this.step1Upload;
        break;
      default:
    }
  }
}
