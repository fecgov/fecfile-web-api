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
   * Changes format of date from m/d/yyyy to yyyy-m-d.
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
}
