import { Injectable } from '@angular/core';
import * as _ from 'lodash';

@Injectable({
  providedIn: 'root'
})
export class UtilService {
  constructor() { }

  /**
   * Deep clone an object with lodash.  Useful when shallow cloning
   * isn't sufficient.
   *
   * @param objToClone the object to clone
   * @returns a clone of the objToClone
   */
  public deepClone(objToClone: any): any {
    return _.cloneDeep(objToClone);
  }

  /**
   * Determine if an object is a number.
   *
   * @param value the object to check
   * @return true if it is a number
   */
  public isNumber(value: any): boolean {
    return !isNaN(value);
  }

  /**
   * Convert a string to a number.
   *
   * @param value string to convert
   * @returns numeric respresentaion of the value
   */
  public toInteger(value: any): number {
    return parseInt(`${value}`, 10);
  }

  /**
   * Removes all items from local storage based on a string value.
   *
   * @param      {string}  val     The value to search for.
   * @param      {number}  length  The length to be comparing.
   */
  public removeLocalItems(val: string, length: number): void {
    let arr: any = [];

    for (let i = 0; i < localStorage.length; i++) {
      if (localStorage.key(i).substring(0, length) === val) {
        arr.push(localStorage.key(i));
      }
    }

    for (let i = 0; i < arr.length; i++) {
      localStorage.removeItem(arr[i]);
    }
  }

  /**
   * Changes format of date from yyyy-m-d to m/d/yyyy to
   *
   * @param      {string}  date    The date
   * @return     {string}  The new formatted date.
   */
  public formatDate(date: string): string {
    try {
      const dateArr = date.split('-');
      const month: string = dateArr[1];
      const day: string = dateArr[2];
      const year: string = dateArr[0].replace('2018', '2019');

      return `${month}/${day}/${year}`;
    } catch (e) {
      return '';
    }
  }

  /**
   * Changes format of date from m/d/yyyy to yyyy-m-d
   *
   * @param      {string}  date    The date
   * @return     {string}  The new formatted date.
   */
  public formatDateToYYYYMMDD(date: string): string {
    try {
      const dateArr = date.split('/');
      const month: string = dateArr[0];
      const day: string = dateArr[1];
      const year: string = dateArr[2];

      return `${year}-${month}-${day}`;
    } catch (e) {
      return '';
    }
  }

  /**
   * Compare 2 dates and determine if date2 falls after date1.
   *
   * @param date1
   * @param date2
   * @returns true if date2 is after (more recent) than date1.  If either dates are null or undefined,
   *          return null.
   */
  public compareDatesAfter(date1: Date, date2: Date): boolean {
    if (!date1 || !date2) {
      return null;
    }
    if (date2.getTime() > date1.getTime()) {
      return true;
    }
    return false;
  }

  /**
   * Compates 2 dates for equality.  Returns true if the dates are equal by
   * millisecond using getTime() from the Date class, otherwise return false.
   * If both are null, false is returned.  If 1 is null and the other is not,
   * false is returned.
   *
   * @param date1
   * @param date2
   * @returns true if equal
   */
  public compareDatesEqual(date1: Date, date2: Date): boolean {
    if (!date1 && !date2) {
      return true;
    }
    if (date1 && !date2) {
      return false;
    }
    if (!date1 && date2) {
      return false;
    }
    if (date1 && date2) {
      if (date1.getTime() !== date2.getTime()) {
        return false;
      }
    }
    return true;
  }

  public extractNameFromEntityObj(field: string, typeAheadField: any): string {
    if (typeAheadField && typeof typeAheadField !== 'string') {
      return typeAheadField[field];
    }
    return typeAheadField;
  }

  public addOrEditObjectValueInArray(array: any, type: string, name: string, value: string) {
    let field = array.find(element => element.name === name);
    if (field) {
      field.value = value.toString();
    }
    else {
      array.push({ type: type, name: name, value: value.toString() });
    }
  }

  /**
	 * Determine if a String has a value.
	 *
	 * @param strg
	 * @returns {Boolean} true if not an empty string, null or undefined otherwise false.
	 */
  public isStringEmpty(strg: string) {
    return (strg === null || strg === undefined || strg === '');
  }
}
