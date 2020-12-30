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
  public readonly step1Select = ImportTransactionsStepsEnum.step1Select;
  // public readonly step1Upload = ImportTransactionsStepsEnum.step1Upload;
  public readonly step2Review = ImportTransactionsStepsEnum.step2Review;
  public readonly step3Clean = ImportTransactionsStepsEnum.step3Clean;
  public readonly step4ImportDone = ImportTransactionsStepsEnum.step4ImportDone;
  // public fileSelectStep1: boolean;
  public sidebarVisibleClass: string;
  public rightSideClassArray: Array<string>;
  public fileQueue: Array<UploadFileModel>;
  public currentFile: UploadFileModel;
  public forceSidebarChangeDetection: Date;
  public forceReviewChangeDetection: Date;
  public openSidebar: boolean;
  public cleanImportAction: string;

  constructor() {}

  ngOnInit() {
    this._initialize();
  }

  private _initialize() {
    this.isShowInfo = false;
    this.steps = [
      // { text: 'Select', step: this.step1aSelect },
      { text: 'Upload', step: this.step1Select },
      { text: 'Review', step: this.step2Review },
      { text: 'Clean', step: this.step3Clean },
      { text: 'Import', step: this.step4ImportDone }
    ];
    this.fileQueue = [];
    this.currentStep = this.start;
    // this.fileSelectStep1 = false;
    this.sidebarVisibleClass = 'sidebar-hidden';
    this.openSidebar = false;
    this.rightSideClassArray = [];
  }

  public showInfo(): void {
    this.isShowInfo = true;
  }

  public receiveReturnFromHowTo() {
    this.isShowInfo = false;
  }

  public receiveBeginFileSelect() {
    this.currentStep = this.step1Select;
    // this.fileSelectStep1 = true;
    this.sidebarVisibleClass = 'sidebar-hidden';
    this._handleToggleSideBarStyling();
  }

  public receiveToggleSidebar($event: any) {
    this.sidebarVisibleClass = $event.sidebarVisibleClass;
    this._handleToggleSideBarStyling();
  }

  public receiveProceedUploadSidebar() {
    this._toggleSidebar(true);
    this._startFileUpload(0);
  }

  public receiveSidebarCancel($event: any) {
    // for now just supporting cancel all.
    // Not sure what to do in UI, if cancel file in progress.
    // start next file?
    if ($event.cancelType === 'cancel-all') {
      this._initialize();
    } else if ($event.cancelType === 'cancel-file') {
      this._cancelFile($event.file);
    }
  }

  public receiveSelectedFiles(queue: any) {
    this.fileQueue = queue;
    this._toggleSidebar(true);
  }

  // public receiveUploadResults($event: any) {
  //   this.currentFile.status = ImportFileStatusEnum.review;
  //   this.currentStep = this.step2Review;
  // }

  public receiveReviewResults($event: any) {
    // If the file failed validation, set it in the queue to reflect the updated status.
    // And start processing next file if exists.
    if ($event.resultType === 'validation-error') {
      if (this._checkQueuedFileExists()) {
        this._proceedNextFile();
      } else {
        this.currentStep = this.step4ImportDone;
      }
    } else if ($event.resultType === 'cancel-file') {
      this._cancelFile($event.file);
    } else {
      this.currentStep = this.step3Clean;
      this.currentFile.status = ImportFileStatusEnum.clean;
    }
  }

  public receiveCleanResults($event: any) {
    if ($event.resultType === 'cancel-file') {
      this._cancelFile($event.file);
      // } else if ($event.resultType === 'ignore_dupe_save') {
      //   this.currentStep = this.step4ImportDone;
      //   this.currentFile.status = ImportFileStatusEnum.importing;
      // } else if ($event.resultType === 'merge_dupe_save') {
      //   this.currentStep = this.step4ImportDone;
      //   this.currentFile.status = ImportFileStatusEnum.importing;
    } else {
      this.cleanImportAction = $event.resultType;
      this.currentStep = this.step4ImportDone;
      this.currentFile.status = ImportFileStatusEnum.importing;
    }
  }

  public receiveProceedNextFile() {
    this._proceedNextFile();
  }

  private _proceedNextFile() {
    if (this._checkQueuedFileExists()) {
      this._startFileUpload(this.currentFile.queueIndex + 1);
    }
  }

  /**
   * Check if there are files in the Queued status to be imported.
   * Files in the Failed status will not apply.
   */
  private _checkQueuedFileExists(): boolean {
    // const totalFiles = this.fileQueue.length;
    // return this.currentFile.queueIndex + 1 < totalFiles ? true : false;
    for (const file of this.fileQueue) {
      if (file.status === ImportFileStatusEnum.queued) {
        return true;
      }
    }
    return false;
  }

  private _startFileUpload(fileIndex: number) {
    this.fileQueue[fileIndex].status = ImportFileStatusEnum.uploading;
    this.currentFile = this.fileQueue[fileIndex];

    // If current step is review, force change detection to start review of next file
    if (this.currentStep === this.step2Review) {
      this.forceReviewChangeDetection = new Date();
    } else {
      this.currentStep = this.step2Review;
      // this.fileSelectStep1 = false;
    }
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

  private _cancelFile(cancelledFile: UploadFileModel) {
    // remove canceled file from the queue, resequence the queueIndex
    // on the fileQueue and determine where to go
    // based on the queue contents.
    //
    // 1) all files canceled? then go back to start.
    // 2) still have file in queued status?  then continue.
    // 3) none in queued status, but some failed? then go to done.
    // See case# below.

    const newQueue = new Array<UploadFileModel>();
    let i = 0;
    for (const file of this.fileQueue) {
      if (file.queueIndex !== cancelledFile.queueIndex) {
        file.queueIndex = i;
        newQueue.push(file);
        i++;
      }
    }
    this.fileQueue = newQueue;
    if (this.fileQueue.length === 0) {
      // case 1
      this._initialize();
    } else if (this._checkQueuedFileExists()) {
      // case 2
      // find the first queued file starting from the top.
      // Can't simply proceed to next file following the cancelled one
      // because the cancelled file may fall after a queued one.
      for (const file of this.fileQueue) {
        if (file.status === ImportFileStatusEnum.queued) {
          this.currentFile = file;
          break;
        }
      }
      this._startFileUpload(this.currentFile.queueIndex);
    } else if (this._checkAllFailed()) {
      // case 3 - if all files in the queue have failed, go to done.
      this.currentStep = this.step4ImportDone;
    } else {
      // no change to currentStep.
    }
  }

  /**
   * If all files in the queue have a status of failed, return true.
   */
  private _checkAllFailed(): boolean {
    let count = 0;
    for (const file of this.fileQueue) {
      if (file.status === ImportFileStatusEnum.failed) {
        count++;
      }
    }
    return count === this.fileQueue.length;
  }

  // //
  // public showNextStep() {
  //   switch (this.currentStep) {
  //     // case this.step1aSelect:
  //     //   this.currentStep = this.step1Upload;
  //     //   break;
  //     case this.step1Upload:
  //       this.currentStep = this.step2Review;
  //       break;
  //     case this.step2Review:
  //       this.currentStep = this.step3Clean;
  //       break;
  //     case this.step3Clean:
  //       this.currentStep = this.step4ImportDone;
  //       break;
  //     default:
  //       this.currentStep = this.step1Upload;
  //   }
  // }

  // // just for devl
  // public showPreviousStep() {
  //   switch (this.currentStep) {
  //     case this.step4ImportDone:
  //       this.currentStep = this.step3Clean;
  //       break;
  //     case this.step3Clean:
  //       this.currentStep = this.step2Review;
  //       break;
  //     case this.step2Review:
  //       this.currentStep = this.step1Upload;
  //       break;
  //     case this.step1Upload:
  //       this.currentStep = this.start;
  //       break;
  //     default:
  //   }
  // }
}
