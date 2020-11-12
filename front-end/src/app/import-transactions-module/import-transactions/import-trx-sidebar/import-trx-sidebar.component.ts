import { Component, OnInit, Output, EventEmitter, Input } from '@angular/core';

@Component({
  selector: 'app-import-trx-sidebar',
  templateUrl: './import-trx-sidebar.component.html',
  styleUrls: ['./import-trx-sidebar.component.scss']
})
export class ImportTrxSidebarComponent implements OnInit {
  @Input()
  public fileQueue_foo: Array<any>;
  public fileQueue: Array<any>;

  @Output()
  public toggleEmitter: EventEmitter<any> = new EventEmitter<any>();

  public iconClass = 'close-icon';
  public sidebarVisibleClass = 'sidebar-visible';
  public headerTitle: string;

  private readonly headerTitleValue = 'Import File(s) Status';

  constructor() {}

  ngOnInit() {
    this.headerTitle = this.headerTitleValue;
  }

  private foo_loadQueue() {
    this.fileQueue = [];
    this.fileQueue.push({
      fileName: 'file_1.csv',
      status: 'Processing'
    });
    for (let i = 1; i < 14; i++) {
      this.fileQueue.push({
        fileName: `file_some_really_long_name_${i}.csv`,
        status: 'Queued'
      });
    }
  }

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
    this.headerTitle = this.headerTitleValue;
    this.iconClass = 'close-icon';
    this.sidebarVisibleClass = 'sidebar-visible';
    this.toggleEmitter.emit({
      showSidebar: true,
      sidebarVisibleClass: this.sidebarVisibleClass
    });

    this.foo_loadQueue();
  }

  public cancelFile(file: any) {
    // TODO emit to parent a message to cancel import on this file.
    // It will call API for cancel.
  }
}
