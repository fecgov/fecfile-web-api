import { Component, OnInit } from '@angular/core';
import { ImportTransactionsStepsEnum } from './import-transactions-steps.enum';
import * as FileSaver from 'file-saver';
import { ImportTransactionsService } from './service/import-transactions.service';

@Component({
  selector: 'app-import-transactions',
  templateUrl: './import-transactions.component.html',
  styleUrls: ['./import-transactions.component.scss']
})
export class ImportTransactionsComponent implements OnInit {
  public isShowInfo: boolean;
  public steps: Array<any>;
  public currentStep: ImportTransactionsStepsEnum;
  public readonly start = ImportTransactionsStepsEnum.start;
  public readonly step1Upload = ImportTransactionsStepsEnum.step1Upload;
  public readonly step2Review = ImportTransactionsStepsEnum.step2Review;
  public readonly step3Clean = ImportTransactionsStepsEnum.step3Clean;
  public readonly step4ImportDone = ImportTransactionsStepsEnum.step4ImportDone;

  constructor(private _importTransactionsService: ImportTransactionsService) {}

  ngOnInit() {
    this.isShowInfo = false;
    this.steps = [
      { text: 'Upload', step: this.step1Upload },
      { text: 'Review', step: this.step2Review },
      { text: 'Clean', step: this.step3Clean },
      { text: 'Import', step: this.step4ImportDone }
    ];
    this.currentStep = this.start;
  }

  public showInfo(): void {
    this.isShowInfo = true;
  }

  public receiveReturnFromHowTo() {
    this.isShowInfo = false;
  }

  public beginUpload() {
    this.currentStep = this.step1Upload;
  }

  //
  public showNextStep() {
    switch (this.currentStep) {
      case this.step1Upload:
        this.currentStep = this.step2Review;
        break;
      case this.step2Review:
        this.currentStep = this.step3Clean;
        break;
      case this.step3Clean:
        this.currentStep = this.step4ImportDone;
        break;
      default:
        this.currentStep = this.step1Upload;
    }
  }

  // just for devl
  public showPreviousStep() {
    switch (this.currentStep) {
      case this.step4ImportDone:
        this.currentStep = this.step3Clean;
        break;
      case this.step3Clean:
        this.currentStep = this.step2Review;
        break;
      case this.step2Review:
        this.currentStep = this.step1Upload;
        break;
      default:
    }
  }

  public viewFormatSpecs(fileName: string) {
    this._importTransactionsService.getSpecAndTemplate(fileName).subscribe((res: any) => {
      const type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8';
      const blob: Blob = new Blob([res], { type: type });
      FileSaver.saveAs(blob, 'Import Contacts Specs and Template.xlsx');
    });
  }
}
