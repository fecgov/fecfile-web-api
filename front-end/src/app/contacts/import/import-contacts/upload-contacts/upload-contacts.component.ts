import { Component, OnInit, ViewChild, ElementRef, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-upload-contacts',
  templateUrl: './upload-contacts.component.html',
  styleUrls: ['./upload-contacts.component.scss']
})
export class UploadContactsComponent implements OnInit {

  @ViewChild('selectFileInput')
  public selectFileInput: ElementRef;

  @Output()
  public userContactsEmitter: EventEmitter<any> = new EventEmitter<any>();

  public userContacts: Array<any>;
  public userContactFields: Array<string>;

  constructor() { }

  ngOnInit() {
  }

  /**
   * An event handler when files are dropped into the file drop area for adding files to the queue.
   *
   * @param event the drop event
   */
  public drop(event: any) {
    event.preventDefault();
    const items = event.dataTransfer.items;

    // TODO change to only permit 1 file.
    // Add validation error if more than 1 dropped.
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry();
        console.log('');
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
      // let files = [];
      const promise = this.parseFileEntry(entry).then(file => {
        // files.push(file);
        // if (this.isValidFileType(file.name)) {
        //   const fr = new FileReader();
        //   fr.onload = function (e) {
        //     const text = fr.result;
        //     console.log(text);
        //   };
        //   fr.readAsText(file);
        // }
        this.handleFileType(file);
      });
    }
    // else if (entry.isDirectory) {
    //   const directoryReader = entry.createReader();
    //   directoryReader.readEntries((entries) => {
    //     entries.forEach((entry) => {
    //       this.scanFiles(entry);
    //     });
    //   });
    // }
  }

  private getFileExtention(fileName: string): string {
    let fileExtention = '';
    if (!fileName.includes('.')) {
      return fileExtention;
    }
    fileExtention = fileName.split('.').pop();
    return fileExtention;
  }

  private handleFileType(file: any) {
    if (!this.isValidFileType(file.name)) {
      alert(`Invalid file type for ${file.name}`);
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
      default:
        console.log('invalif file extention for import contacts ' + fileExtention);
    }
  }

  private handleJsonImport(file: any) {
    // TODO do this in an angular/testable way
    const fr = new FileReader();
    fr.onload = (e) => {
      const json = fr.result;
      this.userContacts = JSON.parse(json.toString());

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
    };
    fr.readAsText(file);
  }

  private handleCsvImport(file: any) {
    alert('CSV file import not yet supported');
  }

  private handleXlsImport(file: any) {
    alert('XLS file import not yet supported');
  }

  /**
   * Programatically trigger a click event on the select file element.
   */
  public triggerSelectFileInputClick(): void {
    this.selectFileInput.nativeElement.click();
  }

  public fileSelected() {
    const files = this.selectFileInput.nativeElement.files;
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      this.handleFileType(file);
      // if (this.isValidFileType(file.name)) {
      // }
    }
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
    return false;

    // switch (name) {
    //   case 'csv':
    //     return true;
    //   case 'json':
    //     return true;
    //   case 'xls':
    //     return true;
    //   default:
    //     return false;
    // }
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
