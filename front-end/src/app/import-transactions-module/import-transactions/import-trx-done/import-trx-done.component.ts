import { Component, OnInit, Input, Output, EventEmitter, OnDestroy } from '@angular/core';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';
import { ImportTransactionsService } from '../service/import-transactions.service';
import { Router } from '@angular/router';
import { timer, Observable, Subscription } from 'rxjs';
import { concatMap, map } from 'rxjs/operators';
import * as FileSaver from 'file-saver';
import { UploadContactsService } from 'src/app/import-contacts-module/import-contacts/upload-contacts/service/upload-contacts.service';

@Component({
  selector: 'app-import-trx-done',
  templateUrl: './import-trx-done.component.html',
  styleUrls: ['./import-trx-done.component.scss']
})
export class ImportTrxDoneComponent implements OnInit, OnDestroy {
  @Input()
  public uploadFile: UploadFileModel;

  @Input()
  public action: string;

  @Input()
  public fileQueue: Array<UploadFileModel>;

  @Output()
  public proceedEmitter: EventEmitter<any> = new EventEmitter<any>();

  public hasFailure: boolean;
  public allFilesDone: boolean;
  public allFailed: boolean;
  public readonly completeStatus = ImportFileStatusEnum.complete;
  public readonly importingStatus = ImportFileStatusEnum.importing;
  public progressPercent: number;

  private progressSubscription: Subscription;
  private committeeId: string;
  private currentFileDone: boolean;

  constructor(
    private _router: Router,
    private _importTransactionsService: ImportTransactionsService,
    private _uploadContactsService: UploadContactsService
  ) {}

  ngOnInit() {
    this.committeeId = null;
    if (localStorage.getItem('committee_details') !== null) {
      const cmteDetails: any = JSON.parse(localStorage.getItem(`committee_details`));
      this.committeeId = cmteDetails.committeeid;
    }
    this.progressPercent = 0;
    this.allFilesDone = false;
    this.hasFailure = false;
    this.allFailed = false;
    this.currentFileDone = false;

    if (this.uploadFile.status === ImportFileStatusEnum.importing) {
      this._finalizeImport();
    } else {
      this._determineNextStep();
    }
  }

  ngOnDestroy() {
    if (this.progressSubscription) {
      this.progressSubscription.unsubscribe();
    }
  }

  private _finalizeImport() {
    switch (this.action) {
      case 'ignore_dupe_save':
        this._importTransactionsService.saveContactIgnoreDupes(this.uploadFile, true).subscribe((res: any) => {
          this.currentFileDone = true;
        });
        break;
      case 'merge_dupe_save':
        this._importTransactionsService.mergeAll(this.uploadFile, true).subscribe((res: any) => {
          this.currentFileDone = true;
        });
        break;
      case 'proceed':
        this._importTransactionsService.saveProceedNoDupes(this.uploadFile, true).subscribe((res: any) => {
          this.currentFileDone = true;
        });
        break;
      default:
    }
    this._pollForProgress();
    // setInterval(foo => {
    //   this.uploadFile.status = ImportFileStatusEnum.complete;
    //   this._determineNextStep();
    // }, 2000);
  }

  private _pollForProgress() {
    // mock the progress until the API is ready
    // mocking it here increments it by 10 each call since the result from mock API is alsways 10.
    let mockPercent = 0;
    this.progressSubscription = this._importTransactionsService.pollForProgress().subscribe((percent: number) => {
      mockPercent += percent;
      if (mockPercent > 130) {
        this.currentFileDone = true;
      }
      if (mockPercent >= 100 && this.currentFileDone) {
        // if (percent >= 100) {
        this.progressSubscription.unsubscribe();
        this.progressPercent = 100;
        this.uploadFile.status = ImportFileStatusEnum.complete;
        this._determineNextStep();
      } else {
        this.progressPercent = mockPercent;
        // this.progressPercent = percent;
      }
    });
  }

  private _determineNextStep() {
    // Any file with a status of queued means not all are done.
    let allQueuedDone = true;
    let failedCount = 0;
    for (const file of this.fileQueue) {
      if (file.status === ImportFileStatusEnum.queued) {
        allQueuedDone = false;
      } else if (file.status === ImportFileStatusEnum.failed) {
        failedCount++;
      }
    }

    // If all are failed, then all are done.
    if (this.fileQueue.length === failedCount) {
      this.allFailed = true;
    }
    // this.allFilesDone = allQueuedDone || allFailed ? true : false;

    this.allFilesDone = allQueuedDone ? true : false;
    // If all are done and any one file failed, show error log.
    if (this.allFilesDone) {
      if (failedCount > 0) {
        this.hasFailure = true;
      }
    }
  }

  public proceed() {
    this.proceedEmitter.emit();
  }

  public showErrorLog() {
    for (const errorFile of this.fileQueue) {
      if (errorFile.status === ImportFileStatusEnum.failed && errorFile.errorFileName) {
        this._downloadErrorFile(errorFile);
      }
    }
  }

  private _downloadErrorFile(errorFile: UploadFileModel) {
    // this._uploadContactsService.getObject(`transactions/${this.committeeId}/error_files/${fileName}`).subscribe(res => {
    this._uploadContactsService.getObject(errorFile.errorFileName).subscribe(res => {
      const type = 'text/csv;charset=utf-8';
      const blob: Blob = new Blob([res.Body], { type: type });

      // TODO for large files, look at https://github.com/jimmywarting/StreamSaver.js
      FileSaver.saveAs(blob, 'errors_' + errorFile.fileName);
    });
  }

  public goToNotifications() {
    this._router.navigate(['/notifications/6']);
  }
}
