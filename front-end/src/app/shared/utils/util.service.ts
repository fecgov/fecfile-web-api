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


}
