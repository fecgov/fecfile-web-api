import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class CsvConverterService {

  constructor() { }

  /**
   * Convert a CSV file to JSON format.
   * @param csv the CSV file with headers
   *
   * Taken from http://techslides.com/convert-csv-to-json-in-javascript
   */
  public convertCsvToJson(csv: string) {
    const lines = csv.split('\n');
    const result = [];
    const headers = lines[0].split(',');

    for (let i = 1; i < lines.length; i++) {
      const obj = {};
      const currentline = lines[i].split(',');
      for (let j = 0; j < headers.length; j++) {
        obj[headers[j]] = currentline[j];
      }
      result.push(obj);
    }
    return JSON.stringify(result);
  }
}
