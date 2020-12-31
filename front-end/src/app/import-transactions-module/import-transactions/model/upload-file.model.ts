export class UploadFileModel {
  fileName: string;
  fecFileName: string;
  errorFileName: string;
  status: string;
  file: File;
  formType: string;
  scheduleType: string;
  checkSum: string;
  contacts: Array<any>;

  /**
   * The zero-based index number indicating the position of the file in the queue.
   */
  queueIndex: number;
}
