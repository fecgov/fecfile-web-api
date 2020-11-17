import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';
import { ImportTransactionsService } from '../service/import-transactions.service';

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

  constructor(private _importTransactionsService: ImportTransactionsService) {}

  ngOnInit() {
    this.uploadFile.status = ImportFileStatusEnum.importing;
    this._finalizeImport();
  }

  private _finalizeImport() {
    setInterval(foo => {
      this.uploadFile.status = ImportFileStatusEnum.complete;
      this._determineNextStep();
    }, 2000);
  }

  private _determineNextStep() {
    this.allFilesDone = false;
    this.hasFailure = false;

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
    let allFailed = false;
    if (this.fileQueue.length === failedCount) {
      allFailed = true;
    }
    this.allFilesDone = allQueuedDone || allFailed ? true : false;
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
}
