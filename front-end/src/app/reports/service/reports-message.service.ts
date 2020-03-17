import { Injectable , ChangeDetectionStrategy } from '@angular/core';
import { Observable } from 'rxjs';
import { Subject } from 'rxjs/Subject';

/**
 * A message service for sending and receiving messages of any type
 * between transaction components.
 */
@Injectable({
  providedIn: 'root'
})
export class ReportsMessageService {

  private subject = new Subject<any>();
  private applyFiltersSubject = new Subject<any>();
  private doKeywordFilterSearchSubject = new Subject<any>();


  /**
   * A publisher uses this method to send a message to subscribers
   * indicating the Pin Column options are to be shown.
   *
   * @param message any message
   */
  public sendShowPinColumnMessage(message: any) {
    this.subject.next(message);
  }


  /**
   * Clear the Pin Column message
   */
  public clearShowPinColumnMessage() {
    this.subject.next();
  }


  /**
   * A method for subscribers of the show PIN Column message.
   */
  public getShowPinColumnMessage(): Observable<any> {
    return this.subject.asObservable();
  }


  /**
   * A publisher uses this method to send a message to subscribers
   * indicating the filters are to be applies to the transactions.
   * 
   * @param message
   */
  public sendApplyFiltersMessage(message: any) {
    //console.log("sendApplyFiltersMessage message = ", message);
    this.applyFiltersSubject.next(message);
  }


  /**
   * Clear the filters message.
   */
  public clearApplyFiltersMessage() {
    this.applyFiltersSubject.next();
  }


  /**
   * A method for subscribers of the Apply Filters message.
   */
  public getApplyFiltersMessage(): Observable<any> {
    return this.applyFiltersSubject.asObservable();
  }


  /**
   * A publisher uses this method to send a message to subscribers
   * to run the Keyword + Filter search
   * 
   * @param message
   */
  public sendDoKeywordFilterSearchMessage(message: any) {
    this.doKeywordFilterSearchSubject.next(message);
  }


  /**
   * Clear the "do keyword + filters" message.
   */
  public clearDoKeywordFilterSearchMessage() {
    this.doKeywordFilterSearchSubject.next();
  }


  /**
   * A method for subscribers of the Keyword + Filter search message.
   */
  public getDoKeywordFilterSearchMessage(): Observable<any> {
    return this.doKeywordFilterSearchSubject.asObservable();
  }

  /*private subject = new Subject<any>();
  private applyFiltersSubject = new Subject<any>();*/

  public sendMessage(message: any) {
    this.subject.next(message);
  }

  public clearMessage() {
    this.subject.next();
  }

  public getMessage(): Observable<any> {
    return this.subject.asObservable();
  }

  /*public sendApplyFiltersMessage(message: any) {
    this.applyFiltersSubject.next(message);
  }

  public clearApplyFiltersMessage() {
    this.applyFiltersSubject.next();
  }

  public getApplyFiltersMessage(): Observable<any> {
    return this.applyFiltersSubject.asObservable();
  }  */
}
