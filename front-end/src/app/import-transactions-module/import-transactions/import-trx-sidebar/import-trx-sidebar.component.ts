import { Component, OnInit, Output, EventEmitter, Input, OnChanges, SimpleChanges } from '@angular/core';
import { ImportTransactionsStepsEnum } from '../import-transactions-steps.enum';
import { UploadFileModel } from '../model/upload-file.model';

@Component({
  selector: 'app-import-trx-sidebar',
  templateUrl: './import-trx-sidebar.component.html',
  styleUrls: ['./import-trx-sidebar.component.scss']
})
export class ImportTrxSidebarComponent implements OnInit, OnChanges {
  @Input()
  // public fileQueue_foo: Array<any>;
  public fileQueue: Array<UploadFileModel>;

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

  public iconClass = 'bars-icon';
  public sidebarVisibleClass = 'sidebar-hidden';
  public headerTitle: string;
  // public open: boolean;
  public readonly step1Upload = ImportTransactionsStepsEnum.step1Upload;
  // public readonly step1aSelect = ImportTransactionsStepsEnum.step1aSelect;

  private readonly headerTitleValue = 'Import File(s) Status';

  constructor() {}

  ngOnInit() {
    this.headerTitle = this.headerTitleValue;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.currentStep) {
      if (changes.currentStep.currentValue === this.step1Upload) {
        // this._openSideBar();
      }
    }
    if (changes.open !== undefined) {
      if (changes.open.currentValue === true) {
        this._openSideBar();
      } else {
        this._closeSideBar();
      }
    }
  }

  // // for devl
  // private foo_loadQueue() {
  //   this.fileQueue = [];
  //   this.fileQueue.push({
  //     fileName: 'file_1.csv',
  //     status: 'Processing'
  //   });
  //   for (let i = 1; i < 14; i++) {
  //     this.fileQueue.push({
  //       fileName: `file_some_really_long_name_${i}.csv`,
  //       status: 'Queued'
  //     });
  //   }
  // }

  public toggleSidebar() {
    if (this.iconClass === 'close-icon') {
      this._closeSideBar();
    } else {
      this._openSideBar();
    }
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

    // this.foo_loadQueue();
  }

  public cancelFile(file: any) {
    // TODO emit to parent a message to cancel import on this file.
    // It will call API for cancel.
  }

  public cancelImportAll() {
    // TODO emit to parent the cancel action
  }

  public proceed() {
    this.proceedUploadEmitter.emit();
  }
}
