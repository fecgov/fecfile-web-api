import { Component, OnInit, Output, EventEmitter, Input, OnChanges, SimpleChanges } from '@angular/core';
import { ImportTransactionsStepsEnum } from '../import-transactions-steps.enum';
import { UploadFileModel } from '../model/upload-file.model';
import { ImportFileStatusEnum } from '../import-file-status.enum';
import { DialogService } from 'src/app/shared/services/DialogService/dialog.service';
import { ConfirmModalComponent } from 'src/app/shared/partials/confirm-modal/confirm-modal.component';

@Component({
  selector: 'app-import-trx-sidebar',
  templateUrl: './import-trx-sidebar.component.html',
  styleUrls: ['./import-trx-sidebar.component.scss']
})
export class ImportTrxSidebarComponent implements OnInit, OnChanges {
  @Input()
  public fileQueue: Array<UploadFileModel>;

  @Input()
  public currentFile: UploadFileModel;

  @Input()
  public currentStep: ImportTransactionsStepsEnum;

  @Input()
  public forceChangeDetection: Date;

  @Input()
  public open: boolean;

  @Output()
  public toggleEmitter: EventEmitter<any> = new EventEmitter<any>();

  @Output()
  public proceedUploadEmitter: EventEmitter<any> = new EventEmitter<any>();

  @Output()
  public proceedCancelEmitter: EventEmitter<any> = new EventEmitter<any>();

  public iconClass = 'bars-icon';
  public sidebarVisibleClass = 'sidebar-hidden';
  public headerTitle: string;
  public readonly step1Select = ImportTransactionsStepsEnum.step1Select;
  public readonly step4ImportDone = ImportTransactionsStepsEnum.step4ImportDone;
  public readonly completeStatus = ImportFileStatusEnum.complete;

  private readonly headerTitleValue = 'Import File(s) Status';

  constructor(private _dialogService: DialogService) {}

  ngOnInit() {
    this.headerTitle = this.headerTitleValue;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.open !== undefined) {
      if (changes.open.currentValue === true) {
        this._openSideBar();
      } else {
        this._closeSideBar();
      }
    }
  }

  public toggleSidebar() {
    if (this.iconClass === 'close-icon') {
      this._closeSideBar();
    } else {
      this._openSideBar();
    }
  }

  public cancelFile(file: any) {
    // TODO emit to parent a message to cancel import on this file.
    // It will call API for cancel.
    const message = 'Import for this file will be canceled. ' + 'Are you sure you would like to continue?';
    this._dialogService.confirm(message, ConfirmModalComponent, 'Caution!', true).then(res => {
      if (res === 'okay') {
        // this._closeSideBar();
        this.proceedCancelEmitter.emit({
          cancelType: 'cancel-file',
          file: file
        });
      }
    });
  }

  public cancelImportAll() {
    // TODO emit to parent the cancel action
    const message =
      'This action will cancel all remaining Imports that have not been completed. ' +
      'Are you sure you would like to continue?';
    this._dialogService.confirm(message, ConfirmModalComponent, 'Caution!', true).then(res => {
      if (res === 'okay') {
        this._closeSideBar();
        this.proceedCancelEmitter.emit({ cancelType: 'cancel-all' });
      }
    });
  }

  public proceed() {
    this.proceedUploadEmitter.emit();
  }

  /**
   * Closes the sidebar.
   */
  private _closeSideBar(): void {
    this.open = false;
    this.headerTitle = null;
    this.iconClass = 'bars-icon';
    this.sidebarVisibleClass = 'sidebar-hidden';
    this.toggleEmitter.emit({
      showSidebar: false,
      sidebarVisibleClass: this.sidebarVisibleClass
    });
  }

  /**
   * Opens the navbar.
   */
  private _openSideBar(): void {
    this.open = true;
    this.headerTitle = this.headerTitleValue;
    this.iconClass = 'close-icon';
    this.sidebarVisibleClass = 'sidebar-visible';
    this.toggleEmitter.emit({
      showSidebar: true,
      sidebarVisibleClass: this.sidebarVisibleClass
    });
  }

  /**
   * Check if there are files in the Queued status to be imported.
   * Files in the Failed status will not apply.
   */
  // public checkQueuedFileExists(): boolean {
  //   // const totalFiles = this.fileQueue.length;
  //   // return this.currentFile.queueIndex + 1 < totalFiles ? true : false;
  //   for (const file of this.fileQueue) {
  //     if (file.status === ImportFileStatusEnum.queued) {
  //       return true;
  //     }
  //   }
  //   return false;
  // }
}
