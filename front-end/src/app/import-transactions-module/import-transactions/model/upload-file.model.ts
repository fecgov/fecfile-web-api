export class UploadFileModel {
  fileName: string;
  status: string;
  file: File;
  formType: string;
  checkSum: string;

  /**
   * The zero-based index number indicating the position of the file in the queue.
   */
  queueIndex: number;
}
