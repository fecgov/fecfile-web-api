import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Subject } from 'rxjs/Subject';


/**
 * A message service for sending and receiving messages of any type
 * between F3X components.
 */
@Injectable({
  providedIn: 'root'
})
export class F3xMessageService {

  private populateFormSubject = new Subject<any>();


  /**
   * Used by the F3X parent component to inform the child component
   * to pre-populate the form with the given data.
   *
   * @param message
   */
  public sendPopulateFormMessage(message: any) {
    this.populateFormSubject.next(message);
  }


  /**
   * Clear the Populate Form message.
   */
  public clearPopulateFormMessage() {
    this.populateFormSubject.next();
  }


  /**
   * A method for subscribers of the Populate Form message.
   */
  public getPopulateFormMessage(): Observable<any> {
    return this.populateFormSubject.asObservable();
  }

}
