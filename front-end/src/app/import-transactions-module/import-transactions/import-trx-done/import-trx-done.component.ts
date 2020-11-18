import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';
import { ImportTransactionsService } from '../service/import-transactions.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-import-trx-done',
  templateUrl: './import-trx-done.component.html',
  styleUrls: ['./import-trx-done.component.scss']
})
export class ImportTrxDoneComponent implements OnInit {
  @Input()
  public uploadFile: UploadFileModel;

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

  constructor(private _router: Router, private _importTransactionsService: ImportTransactionsService) {}

  ngOnInit() {
    this.progressPercent = 0;
    this.allFilesDone = false;
    this.hasFailure = false;
    this.allFailed = false;

    if (this.uploadFile.status === ImportFileStatusEnum.importing) {
      this._finalizeImport();
    } else {
      this._determineNextStep();
    }
  }

  private _finalizeImport() {
    setInterval(foo => {
      this.uploadFile.status = ImportFileStatusEnum.complete;
      this._determineNextStep();
    }, 2000);
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
    alert('Error log not yet developed');
  }

  public goToNotifications() {
    this._router.navigate(['/notifications/6']);
  }
}
