import { Component, OnInit } from '@angular/core';
import { ImportTransactionsStepsEnum } from './import-transactions-steps.enum';
import * as FileSaver from 'file-saver';
import { ImportTransactionsService } from './service/import-transactions.service';
import { UploadFileModel } from './model/upload-file.model';
import { ImportFileStatusEnum } from './import-file-status.enum';

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
  // public readonly step1aSelect = ImportTransactionsStepsEnum.step1aSelect;
  public readonly step1Upload = ImportTransactionsStepsEnum.step1Upload;
  public readonly step2Review = ImportTransactionsStepsEnum.step2Review;
  public readonly step3Clean = ImportTransactionsStepsEnum.step3Clean;
  public readonly step4ImportDone = ImportTransactionsStepsEnum.step4ImportDone;
  public sidebarVisibleClass: string;
  public rightSideClassArray: Array<string>;
  public fileQueue: Array<UploadFileModel>;
  public currentFile: any;
  public forceSidebarChangeDetection: Date;
  public openSidebar: boolean;

  constructor() {}

  ngOnInit() {
    this.isShowInfo = false;
    this.steps = [
      // { text: 'Select', step: this.step1aSelect },
      { text: 'Upload', step: this.step1Upload },
      { text: 'Review', step: this.step2Review },
      { text: 'Clean', step: this.step3Clean },
      { text: 'Import', step: this.step4ImportDone }
    ];
    this.currentStep = this.start;
    this.sidebarVisibleClass = 'sidebar-hidden';
  }

  public showInfo(): void {
    this.isShowInfo = true;
  }

  public receiveReturnFromHowTo() {
    this.isShowInfo = false;
  }

  public receiveBeginFileSelect() {
    this.currentStep = this.step1Upload;
    this.sidebarVisibleClass = 'sidebar-hidden';
    this._handleToggleSideBarStyling();
  }

  public receiveToggleSidebar($event: any) {
    this.sidebarVisibleClass = $event.sidebarVisibleClass;
    this._handleToggleSideBarStyling();
  }

  public receiveProceedUploadSidebar() {
    this.currentStep = this.step2Review;
    // this.forceSidebarChangeDetection = new Date();
    this._toggleSidebar(true);
    this._startFileUpload(0);
  }

  public receiveSelectedFiles(queue: any) {
    this.fileQueue = queue;
    this._toggleSidebar(true);
  }

  public receiveReviewResults($event: any) {
    // If the file failed validation, set it in the queue to reflect the updated status.
    // And start processing next file if exists.
    if ($event.resultType === 'validation-error') {

      // TOD is this needed?
      if ($event.uploadFile) {
        const uploadFile: UploadFileModel = $event.uploadFile;
        this.fileQueue[uploadFile.queueIndex] = uploadFile;
      }

      // TODO need requirement clarification.
      // Show message to user the file failed and proceed button to go to next file
      // or finalize import where the error log may be viewed.
      this._proceedNextFile();
    } else {
      this.currentStep = this.step3Clean;
    }
  }

  public receiveProceedNextFile() {
    this._proceedNextFile();
  }

  public receiveCleanResults($event: any) {
    this.currentStep = this.step4ImportDone;
  }

  private _proceedNextFile() {
    const totalFiles = this.fileQueue.length;
    if (this.currentFile.queueIndex + 1 < totalFiles) {
      this._startFileUpload(this.currentFile.queueIndex + 1);
    }
    // else {
    //   this.currentStep = this.step4ImportDone;
    // }
  }

  private _startFileUpload(fileIndex: number) {
    this.fileQueue[fileIndex].status = ImportFileStatusEnum.uploading;
    this.currentFile = this.fileQueue[fileIndex];
  }

  private _toggleSidebar(open: boolean) {
    // style this component
    this.sidebarVisibleClass = open ? 'sidebar-visible' : 'sidebar-hidden';
    this._handleToggleSideBarStyling();

    // open child sidebar
    this.openSidebar = open;
  }

  private _initRightSideClass(): void {
    this.rightSideClassArray = [];
    const stepClass = this.currentStep !== this.start ? 'right-side ' : '';
    if (stepClass) {
      this.rightSideClassArray.push(stepClass);
    }
  }

  /**
   * Handle the styling for the sidebar in this parent component.
   *
   * @param $event the event triggering the toggle
   */
  private _handleToggleSideBarStyling() {
    this._initRightSideClass();
    this.rightSideClassArray.push(this.sidebarVisibleClass);
  }

  //
  public showNextStep() {
    switch (this.currentStep) {
      // case this.step1aSelect:
      //   this.currentStep = this.step1Upload;
      //   break;
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
      case this.step1Upload:
        this.currentStep = this.start;
        break;
      default:
    }
  }
}
