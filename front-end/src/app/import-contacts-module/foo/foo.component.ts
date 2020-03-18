import { Component, OnInit } from '@angular/core';
import { ImportContactsStepsEnum } from '../import-contacts/import-contacts-setps.enum';

@Component({
  selector: 'app-foo',
  templateUrl: './foo.component.html',
  styleUrls: ['./foo.component.scss']
})
export class FooComponent implements OnInit {

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

}
