import { Injectable } from '@angular/core';
import * as FileSaver from 'file-saver';
import * as XLSX from 'xlsx';

@Injectable({
  providedIn: 'root'
})
export class ExportService {
  constructor() {}

  private excelFileType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8';
  private excelFileExtension = '.xlsx';
  private csvFileType = 'text/plain;charset=UTF-8';
  private csvFileExtension = '.csv';

  public exportExcel(data: any[], fileName: string): void {
    const ws: XLSX.WorkSheet = XLSX.utils.json_to_sheet(data);
    const wb: XLSX.WorkBook = { Sheets: { data: ws }, SheetNames: ['data'] };
    const excelBuffer: any = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    this.saveExcelFile(excelBuffer, fileName);
  }

  public saveExcelFile(buffer: any, fileName: string): void {
    const data: Blob = new Blob([buffer], { type: this.excelFileType });
    FileSaver.saveAs(data, fileName + this.excelFileExtension);
  }

  public exportCsv(data: any[], fileName: string): void {
    const ws: XLSX.WorkSheet = XLSX.utils.json_to_sheet(data);
    const csv = XLSX.utils.sheet_to_csv(ws, { FS: ',' });
    this.saveCsvFile(csv, fileName);
  }

  private saveCsvFile(csv: any, fileName: string): void {
    const blob = new Blob([csv], { type: this.csvFileType });
    FileSaver.saveAs(blob, fileName + this.csvFileExtension);
  }
}
