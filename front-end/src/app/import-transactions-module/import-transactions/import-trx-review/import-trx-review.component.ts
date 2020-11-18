import { Component, OnInit, Input, OnDestroy, Output, EventEmitter } from '@angular/core';
import { S3 } from 'aws-sdk/clients/all';
import {
  ConfirmModalComponent,
  ModalHeaderClassEnum
} from 'src/app/shared/partials/confirm-modal/confirm-modal.component';
import { timer, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { UploadTrxService } from '../import-trx-upload/service/upload-trx.service';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import CryptoJS from 'crypto-js';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';
import { ImportTransactionsService } from '../service/import-transactions.service';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { UploadCompleteMessageComponent } from './upload-complete-message/upload-complete-message.component';

@Component({
  selector: 'app-import-trx-review',
  templateUrl: './import-trx-review.component.html',
  styleUrls: ['./import-trx-review.component.scss']
})
export class ImportTrxReviewComponent implements OnInit, OnDestroy {
  @Input()
  public uploadFile: UploadFileModel;

  @Output()
  public resultsEmitter: EventEmitter<any> = new EventEmitter<any>();

  public progressPercent: number;
  public uploadingText: string;
  public hasDupeFile: boolean;
  public duplicateFileList: Array<any>;

  private onDestroy$: Subject<any>;
  private uploadProcessing$: Subject<any>;
  private checkSum: string;
  private committeeId: string;

  constructor(
    private _dialogService: DialogService,
    private _modalService: NgbModal,
    private _importTransactionsService: ImportTransactionsService
  ) {}

  ngOnInit() {
    this._startReview();
    this.hasDupeFile = false;
    this.duplicateFileList = [];
  }

  public ngOnDestroy() {}

  public proceed() {
    this.resultsEmitter.emit({
      resultType: 'proceed',
      uploadFile: this.uploadFile
    });
  }

  public cancelImport() {
    this.resultsEmitter.emit({
      resultType: 'cancel-file',
      uploadFile: this.uploadFile
    });
  }

  private _startReview() {
    // this.uploadFile.status = ImportFileStatusEnum.review;
    const file = this.uploadFile.file;
    this._importTransactionsService.processingUploadedTransactions(file.name, this.checkSum).subscribe((res: any) => {
      let hasValidationErrors = false;
      if (res.error_list) {
        if (res.error_list.length > 0) {
          hasValidationErrors = true;
        }
      }
      if (res.duplicate_file_list) {
        if (res.duplicate_file_list.length > 0) {
          this.hasDupeFile = true;
          this.duplicateFileList = res.duplicate_file_list;
        }
      }
      if (hasValidationErrors) {
        this.uploadFile.status = ImportFileStatusEnum.failed;
        const message =
          'The system found errors within the import file, ' +
          'and will not be able to complete the import. ' +
          'Please check your file and ensure formatting is correct.';
        this._dialogService
          .confirm(message, ConfirmModalComponent, 'Import Failed!', false, ModalHeaderClassEnum.errorHeader)
          .then(res => {
            this.resultsEmitter.emit({
              resultType: 'validation-error',
              uploadFile: this.uploadFile
            });
          });
      } else if (this.hasDupeFile) {
      } else {
        this._modalService.open(UploadCompleteMessageComponent).result.then((resp: string) => {
          if (resp === 'continue') {
            this.resultsEmitter.emit({
              resultType: 'success',
              uploadFile: this.uploadFile
            });
          }
        });
      }
    });
  }
}
