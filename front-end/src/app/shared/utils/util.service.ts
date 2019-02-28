import { Injectable } from '@angular/core';
import * as _ from "lodash";


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
  public deepClone(objToClone: any) : any {
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


}
