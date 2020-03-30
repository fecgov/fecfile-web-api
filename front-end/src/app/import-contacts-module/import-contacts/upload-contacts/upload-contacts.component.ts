import { Component, OnInit, ViewChild, ElementRef, Output, EventEmitter, ViewEncapsulation, ChangeDetectionStrategy } from '@angular/core';
import { CsvConverterService } from '../service/csv-converter.service';
import * as XLSX from 'xlsx';
import { timer, interval, Observable } from 'rxjs';
import { takeUntil, finalize } from 'rxjs/operators';
import { style, animate, transition, trigger } from '@angular/animations';
import { UploadContactsService } from './service/upload-contacts.service';
import { UtilService } from 'src/app/shared/utils/util.service';


@Component({
  selector: 'app-upload-contacts',
  templateUrl: './upload-contacts.component.html',
  styleUrls: ['./upload-contacts.component.scss'],
  // changeDetection: ChangeDetectionStrategy.OnPush
})
export class UploadContactsComponent implements OnInit {

  @ViewChild('selectFileInput')
  public selectFileInput: ElementRef;

  @Output()
  public userContactsEmitter: EventEmitter<any> = new EventEmitter<any>();

  public userContacts: Array<any>;
  public userContactFields: Array<string>;
  public showUpload: boolean;
  public progressPercent: number;
  public foo = { progressPercent: 0 };
  // public fooBar = [];

  constructor(
    private csvConverterService: CsvConverterService,
    private uploadContactsService: UploadContactsService,
    private utilService: UtilService
  ) { }

  ngOnInit() {
    this.showUpload = true;
    this.progressPercent = 0;
    this.foo = { progressPercent: 0 };
    // this.fooBar = [0];
  }

  /**
   * An event handler when files are dropped into the file drop area for adding files to the queue.
   *
   * @param event the drop event
   */
  public drop(event: any) {
    // TODO put this in a service for extracting files on drop event.

    event.preventDefault();
    const items = event.dataTransfer.items;

    // TODO change to only permit 1 file.
    // Add validation error if more than 1 dropped.
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
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
        this.handleJsonImport(file);
        break;
      case 'csv':
        this.handleCsvImport(file);
        break;
      case 'xls':
        this.handleXlsImport(file);
        break;
      case 'xlsx':
        this.handleXlsImport(file);
        break;
      default:
      // console.log('invalid file extention for import contacts ' + fileExtention);
    }
  }

  private handleJsonImport(file: File) {
    const fileReader = new FileReader();
    fileReader.onload = (e) => {
      const json = fileReader.result;
      this.userContacts = JSON.parse(json.toString());
      this.prepareUserContactFields();
    };
    fileReader.readAsText(file);
  }

  private handleCsvImport(file: File) {
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

  private handleXlsImport(file: File) {
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

  public fileSelected() {
    this.progressPercent = 0;
    this.foo.progressPercent = 0;
    // this.fooBar = [0];
    this.showUpload = false;

    if (this.selectFileInput.nativeElement.files) {
      if (this.selectFileInput.nativeElement.files[0]) {
        const file = this.selectFileInput.nativeElement.files[0];
        // this.uploadContactsService.uploadFile(file).subscribe((res: any) => {
        //   const userCols = res;
        // });
        this.uploadContactsService.uploadFileAWS_InsecureVeresion(file);
      }
    }

    // For development of the progress bar for file upload, this code is
    // simulating a long file upload time.  The file to be uploaded in production
    // may be a big as 10-20 GB.

    const fakeUploadTime = 4000;
    const fakeUploadInterval = fakeUploadTime / 4; // 2000 and 4 will = 500 milliseconds

    // emit value every interval to increase percent done
    const source = interval(fakeUploadInterval);
    // after fakeUploadTime has passed, read the file client side.  This will be server side
    // read in the future.
    const timer$ = timer(fakeUploadTime).pipe(finalize(() => {
      // console.log('All done!');
      this.progressPercent = 100;
      this.foo.progressPercent = 100;
      // this.fooBar = [100];
      const files = this.selectFileInput.nativeElement.files;
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        this.handleFileType(file);
      }
    }));
    // when timer emits after 5s, complete source
    const example = source.pipe(takeUntil(timer$));
    // sub to observable emitted by the interval.
    const subscribe = example
      .subscribe(val => {
        const percentageIncrease = (fakeUploadInterval) * 100 / fakeUploadTime;
        this.progressPercent = this.progressPercent + percentageIncrease;
        this.foo.progressPercent = this.foo.progressPercent + percentageIncrease;
        // this.fooBar = [this.foo.progressPercent + percentageIncrease];
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
      userContacts: this.userContacts,
      userContactFields: this.userContactFields
    });
  }

}
