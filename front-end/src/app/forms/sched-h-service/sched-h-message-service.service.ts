import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Subject } from 'rxjs/Subject';

/**
 * A message service for sending and receiving messages of any type
 * between schedH components.
 */
@Injectable({
  providedIn: 'root'
})
export class SchedHMessageServiceService {
 
  private populateHFormForEdit = new Subject<any>();


   /**
   * A publisher uses this method to send a message to subscribers
   * indicating the form needs to be populated
   *
   * @param message
   */
  public sendpopulateHFormForEditMessage(message: any) {
    this.populateHFormForEdit.next(message);
  }

  /**
   * Clear the filters message.
   */
  public clearpopulateHFormForEditMessage() {
    this.populateHFormForEdit.next();
  }

  /**
   * A method for subscribers of the Apply Filters message.
   */
  public getpopulateHFormForEditMessage(): Observable<any> {
    return this.populateHFormForEdit.asObservable();
  }
}
