import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Subject } from 'rxjs/Subject';

export enum ReportTypeDateEnum {
  fromDate = 'fromDate',
  toDate = 'toDate'
}

/**
 * A message service for sending and receiving messages of any type
 * between report type components.
 */
@Injectable({
  providedIn: 'root'
})
export class ReportTypeMessageService {

  private dateChangeSubject = new Subject<any>();


  /**
   * A publisher uses this method to send a message to subscribers
   * indicating a date has changed.
   *
   * @param message any message
   */
  public sendDateChangeMessage(message: any) {
    this.dateChangeSubject.next(message);
  }


  /**
   * Clear the Date Change message
   */
  public clearDateChangeMessage() {
    this.dateChangeSubject.next();
  }


  /**
   * A method for subscribers of date change message.
   */
  public getDateChangeMessage(): Observable<any> {
    return this.dateChangeSubject.asObservable();
  }

}
