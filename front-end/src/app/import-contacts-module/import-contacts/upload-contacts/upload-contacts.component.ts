import { Component, OnInit, ViewChild, ElementRef, Output, EventEmitter, ViewEncapsulation, ChangeDetectionStrategy, OnDestroy, Input, SimpleChanges, OnChanges } from '@angular/core';
import { CsvConverterService } from '../service/csv-converter.service';
import * as XLSX from 'xlsx';
import { timer, interval, Observable, Subject } from 'rxjs';
import { takeUntil, finalize, switchMap } from 'rxjs/operators';
import { style, animate, transition, trigger } from '@angular/animations';
import { UploadContactsService } from './service/upload-contacts.service';
import { UtilService } from 'src/app/shared/utils/util.service';


@Component({
  selector: 'app-upload-contacts',
  templateUrl: './upload-contacts.component.html',
  styleUrls: ['./upload-contacts.component.scss'],
  // changeDetection: ChangeDetectionStrategy.OnPush
})
export class UploadContactsComponent implements OnInit, OnDestroy, OnChanges {

  @ViewChild('selectFileInput')
  public selectFileInput: ElementRef;

  @Input()
  public forceChangeDetection: Date;

  @Output()
  public userContactsEmitter: EventEmitter<any> = new EventEmitter<any>();

  public userContacts: Array<any>;
  public userContactFields: Array<string>;
  public showUpload: boolean;
  public progressPercent: number;
  public processingPercent: number;
  public hideProcessingProgress: boolean;
  public showSpinner: boolean;
  public uploadingText: string;

  private onDestroy$: Subject<any>;
  private uploadProcessing$: Subject<any>;


  constructor(
    private csvConverterService: CsvConverterService,
    private uploadContactsService: UploadContactsService,
    private utilService: UtilService
  ) { }

  public ngOnInit() {
    this.onDestroy$ = new Subject();
    this.showUpload = true;
    this.hideProcessingProgress = true;
    this.showSpinner = false;
    this.progressPercent = 0;
    this.processingPercent = 0;
    this.getProgress();
  }

  public ngOnDestroy() {
    this.onDestroy$.next();
    if (this.uploadProcessing$) {
      this.uploadProcessing$.next();
    }
  }

  public ngOnChanges(changes: SimpleChanges) {
    this.ngOnInit();
  }

  /**
   * An event handler when files are dropped into the file drop area for adding files to the queue.
   *
   * @param event the drop event
   */
  public drop(event: any) {
    event.preventDefault();
    const items = event.dataTransfer.items;

    // TODO Add validation error if more than 1 dropped.
    if (items.length > 1) {
      return;
    } else if (items.length === 1) {
      const item = items[0];
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry();
        this.scanFiles(entry);
      }
    }
  }

  /**
   * Scan an entry dropped into the drop area and add to the queue as required.
   *
   * @param entry the file or directory to scan
   */
  private scanFiles(entry: any) {
    if (entry.isFile) {
      const promise = this.parseFileEntry(entry).then(file => {
        this.handleFileType(file);
      });
    }
  }

  private getFileExtention(fileName: string): string {
    let fileExtention = '';
    if (!fileName.includes('.')) {
      return fileExtention;
    }
    fileExtention = fileName.split('.').pop();
    return fileExtention;
  }

  private handleFileType(file: File) {
    if (!this.isValidFileType(file.name)) {
      // console.log(`Invalid file type for ${file.name}`);
    }
    const fileExtention = this.getFileExtention(file.name);
    switch (fileExtention) {
      case 'json':
        // this._handleJsonImport_DEPRECATED(file);
        this._uploadJson(file);
        break;
      case 'csv':
        // this._handleCsvImport_DEPRECATED(file);
        this._uploadCsv(file);
        break;
      case 'xls':
        // this._handleXlsImport_DEPRECATED(file);
        break;
      case 'xlsx':
        // this._handleXlsImport_DEPRECATED(file);
        break;
      default:
      // console.log('invalid file extention for import contacts ' + fileExtention);
    }
  }

  private _handleJsonImport_DEPRECATED(file: File) {
    const fileReader = new FileReader();
    fileReader.onload = (e) => {
      const json = fileReader.result;
      this.userContacts = JSON.parse(json.toString());
      this.prepareUserContactFields();
    };
    fileReader.readAsText(file);
  }

  private _handleCsvImport_DEPRECATED(file: File) {
    const fileReader = new FileReader();
    fileReader.onload = (e) => {
      const csvText: string | ArrayBuffer = fileReader.result;
      if (typeof csvText === 'string') {
        const json = this.csvConverterService.convertCsvToJson(csvText);
        this.userContacts = JSON.parse(json.toString());
        this.prepareUserContactFields();
      }
    };
    fileReader.readAsText(file);
  }

  private _handleXlsImport_DEPRECATED(file: File) {
    const fileReader = new FileReader();
    fileReader.onload = (e) => {

      /* read workbook */
      const bstr = fileReader.result;
      const wb: XLSX.WorkBook = XLSX.read(bstr, { type: 'binary' });

      /* grab first sheet */
      const wsname: string = wb.SheetNames[0];
      const ws: XLSX.WorkSheet = wb.Sheets[wsname];

      /* save data */
      const data = XLSX.utils.sheet_to_json(ws);

      const json = JSON.stringify(data);
      this.userContacts = JSON.parse(json.toString());
      this.prepareUserContactFields();
    };
    fileReader.readAsBinaryString(file);
  }

  private prepareUserContactFields(): void {
    // get property names for mapping user fields
    this.userContactFields = [];
    if (this.userContacts) {
      if (Array.isArray(this.userContacts)) {
        if (this.userContacts.length > 0) {
          for (const prop in this.userContacts[0]) {
            if (prop) {
              this.userContactFields.push(prop);
            }
          }
        }
      }
    }
    this.emitUserContacts();
  }

  /**
   * Programatically trigger a click event on the select file element.
   */
  public triggerSelectFileInputClick(): void {
    this.selectFileInput.nativeElement.click();
  }

  public onClick(event) {
    event.target.value = '';
  }

  public fileSelected() {
    this.progressPercent = 0;
    this.showUpload = false;
    this.uploadingText = 'Uploading...';
    if (this.selectFileInput.nativeElement.files) {
      if (this.selectFileInput.nativeElement.files[0]) {
        const file = this.selectFileInput.nativeElement.files[0];
        this.handleFileType(file);
      }
    }
  }

  private _uploadCsv(file: File) {
    this.uploadContactsService.uploadFile(file).takeUntil(this.onDestroy$)
      .subscribe((data: any) => {
        // read the header record from the uploaded file
        this.uploadContactsService.readCsvFileHeader(file).subscribe((headerFields: Array<string>) => {
          this.userContactFields = headerFields;
        });
        this.checkForProcessingProgress();
        this.uploadContactsService.uploadComplete(file.name).subscribe((res: any) => {
          this.showSpinner = false;
          this.emitUploadResults(res);
        });
      });
  }

  private _uploadJson(file: File) {
    this.uploadContactsService.uploadFile(file).takeUntil(this.onDestroy$)
      .subscribe((data: any) => {
        // read the header record from the uploaded file
        this.uploadContactsService.readJsonFilePropertyNames(file).subscribe((headerFields: Array<string>) => {
          this.userContactFields = headerFields;
          // setTimeout(() => {
          //   this.emitUserContacts();
          // }, 1000);
        });
        this.checkForProcessingProgress();
      });
  }

  /**
   * Check for processing progress now that upload is complete.
   */
  private checkForProcessingProgress() {

    // Ensure Upload complete message and spnner appear simultaneously using delay. 
    const timer1 = timer(300);
    const timerSubject = new Subject<any>();
    const timerSubscription = timer1
      .pipe(takeUntil(timerSubject))
      .subscribe(() => {
        this.uploadingText = 'Upload complete!';
        this.showSpinner = true;
        if (timerSubscription) {
          timerSubscription.unsubscribe();
        }
        timerSubject.next();
        timerSubject.complete();
      });


    // this.hideProcessingProgress = false;
    // const progressPoller = interval(500);
    // this.uploadProcessing$ = new Subject();
    // progressPoller.takeUntil(this.uploadProcessing$);
    // this.processingPercent = 0;
    // progressPoller.subscribe(val => {
    //   this.uploadContactsService.checkUploadProcessing().takeUntil(this.uploadProcessing$).subscribe(res => {
    //     this.processingPercent += res;
    //     if (this.processingPercent > 99) {
    //       this.uploadProcessing$.next();
    //       this.uploadProcessing$.complete();
    //       // Using setTimeout to avoid another subject but should use RxJs (try delay or interval)
    //       // The purpose here is to allow the user to see the 100% completion before switching view.
    //       setTimeout(() => {
    //         // this.emitUserContacts();
    //       }, 1000);
    //     }
    //   });
    // });
  }

  public getProgress() {
    this.uploadContactsService.getProgressPercent().takeUntil(this.onDestroy$).subscribe((percent: number) => {
      this.progressPercent = percent;
      if (this.progressPercent >= 100) {
        // this.uploadingText = 'Upload complete!';
      }
    });
  }

  /**
   * Determine if the file type derived from name is valid for upload.  Return true if it is.
   * @param name file type to check
   */
  private isValidFileType(name: string): boolean {
    if (!name) {
      return false;
    }
    if (name.indexOf('json') !== -1) {
      return true;
    }
    if (name.indexOf('csv') !== -1) {
      return true;
    }
    if (name.indexOf('xls') !== -1) {
      return true;
    }
    if (name.indexOf('xlsx') !== -1) {
      return true;
    }
    return false;
  }

  private parseFileEntry(fileEntry): Promise<File> {
    return new Promise((resolve, reject) => {
      fileEntry.file(
        file => {
          resolve(file);
        },
        err => {
          reject(err);
        }
      );
    });
  }

  /**
   * An event handler when files are dragged into the file drop area for adding files to the queue.
   * 
   * @param event the dragenter event
   */
  public dragEnter(event) {
    // indicates valid drop data
    // false allows drop
    return Array.prototype.every.call(
      event.dataTransfer.items,
      item => item.kind !== 'file'
    );
  }

  /**
   * An event handler when files are dragged over the file drop area 
   * for adding files to the queue.
   * 
   * @param event the dragover event
   */
  public dragOver(event) {
    // indicates valid drop data
    // false allows drop
    return Array.prototype.every.call(
      event.dataTransfer.items,
      item => item.kind !== 'file'
    );
  }

  /**
   * Emit a message with the user contacts to the parent.
   */
  public emitUserContacts(): void {
    this.userContactsEmitter.emit({
      userContactFields: this.userContactFields,
      testMessage: 'Some validation errors and duplicates found'
    });
  }

  /**
 * Emit a message with the user contacts to the parent.
 */
  private emitUploadResults(response: any): void {
    let duplicateCount = 0;
    let validationErrorCount = 0;
    if (response) {
      if (response.Response) {
        if (response.Response.contacts_failed_validation) {
          if (Array.isArray(response.Response.contacts_failed_validation)) {
            validationErrorCount = response.Response.contacts_failed_validation.length;
          }
          if (Array.isArray(response.Response.duplicate)) {
            duplicateCount = response.Response.duplicate.length;
          }
        }
      }
    }
    this.userContactsEmitter.emit({
      userContactFields: this.userContactFields,
      duplicateCount: duplicateCount,
      validationErrorCount: validationErrorCount
    });
  }

}
