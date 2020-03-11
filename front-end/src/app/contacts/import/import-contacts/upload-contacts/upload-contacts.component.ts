import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-upload-contacts',
  templateUrl: './upload-contacts.component.html',
  styleUrls: ['./upload-contacts.component.scss']
})
export class UploadContactsComponent implements OnInit {

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
      let files = [];
      const promise = this.parseFileEntry(entry).then(file => {
        files.push(file);
        if (this.isValidFileType(file.name)) {
          // this.uploader.addToQueue(files, this.uploader.options);
          const fr = new FileReader();
          fr.onload = function (e) {
            const text = fr.result;
            console.log(text);
          };
          fr.readAsText(files[0]);
        }
      });
    } else if (entry.isDirectory) {
      const directoryReader = entry.createReader();
      directoryReader.readEntries((entries) => {
        entries.forEach((entry) => {
          this.scanFiles(entry);
        });
      });
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

}
