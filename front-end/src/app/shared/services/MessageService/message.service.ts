import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class MessageService {

  private _subject: BehaviorSubject<any> = new BehaviorSubject<any>('');

  constructor() { }

  /**
   * Sends the message to a component.
   *
   * @param      {Any}  message  The message
   */
  public sendMessage(message: any) {
      // console.log('sendMessage: ');
      // console.log('message: ', message);
      this._subject.next(message);
  }

  /**
   * Clears the message if needed.
   *
   */
  public clearMessage() {
      this._subject.next('');
  }

  /**
   * Gets the message.
   *
   * @return     {Observable}  The message.
   */
  public getMessage(): Observable<any> {
      return this._subject.asObservable();
  }
}
