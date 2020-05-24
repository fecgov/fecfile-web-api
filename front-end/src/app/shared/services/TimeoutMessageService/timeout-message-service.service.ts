import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

/**
 * A service used by the appComponent timeout feature to inform components that timeout has occured.
 * The initial use of the service is to bypass the CanDeactivate check when a timeout has occurred.
 * Other components such as F3X are using localStorage properties to determine if deactivate can occur.
 * This service is the preferred choice going forward.
 */
@Injectable({
  providedIn: 'root'
})
export class TimeoutMessageService {

  private _subject: BehaviorSubject<any> = new BehaviorSubject<any>('');

  constructor() { }

  /**
   * Sends the message to a component.
   *
   * @param      {Any}  message  The message
   */
  public sendTimeoutMessage(message: any) {
    this._subject.next(message);
  }

  /**
   * Clears the message if needed.
   *
   */
  public clearTimeoutMessage() {
    this._subject.next('');
  }

  /**
   * Gets the message.
   *
   * @return     {Observable}  The message.
   */
  public getTimeoutMessage(): Observable<any> {
    return this._subject.asObservable();
  }
}
