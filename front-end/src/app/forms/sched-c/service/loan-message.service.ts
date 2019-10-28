import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Subject } from 'rxjs/Subject';
import { ActiveView } from '../loan.component';


/**
 * A message service for sending and receiving messages of any type
 * between transaction components.
 */
@Injectable({
  providedIn: 'root'
})
export class LoanMessageService {

  private subject = new Subject<any>();
  private applyFiltersSubject = new Subject<any>();
  private doKeywordFilterSearchSubject = new Subject<any>();
  private editContactSubject = new Subject<any>();
  private showLoanSubject = new Subject<any>();
  private removeFilterSubject = new Subject<any>();
  private switchFilterViewSubject = new Subject<any>();
  private populateFormSubject = new Subject<any>();
  private loadFormFieldsSubject = new Subject<any>();
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
   * indicating the filters are to be applies to the contacts.
   * 
   * @param message
   */
  public sendApplyFiltersMessage(message: any) {
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


  public sendMessage(message: any) {
    this.subject.next(message);
  }

  public clearMessage() {
    this.subject.next();
  }

  public getMessage(): Observable<any> {
    return this.subject.asObservable();
  }


  public sendEditContactMessage(message: any) {
    this.editContactSubject.next(message);
  }

  public clearEditContactMessage() {
    this.editContactSubject.next();
  }

  public getEditContactMessage(): Observable<any> {
    return this.editContactSubject.asObservable();
  }


  public sendShowLoanMessage(message: any) {
    this.showLoanSubject.next(message);
  }

  public clearShowLoanMessage() {
    this.showLoanSubject.next();
  }

  public getShowLoanMessage(): Observable<any> {
    return this.showLoanSubject.asObservable();
  }

  /**
   * A publisher uses this method to send a message to the Loan Filter
   * Component to remove a filter.
   *
   * @param message
   */
  public sendRemoveFilterMessage(message: any) {
    this.removeFilterSubject.next(message);
  }


  /**
   * Clear the Remove Filter message.
   */
  public clearRemoveFilterMessage() {
    this.removeFilterSubject.next();
  }


  /**
   * A method for subscribers of the Remove Filter message.
   */
  public getRemoveFilterMessage(): Observable<any> {
    return this.removeFilterSubject.asObservable();
  }


  /**
   * A publisher uses this method to send a message to the Loan Filter
   * Component to change the filter fields for the particular type of table view shown.
   *
   * @param message
   */
  public sendSwitchFilterViewMessage(message: ActiveView) {
    this.switchFilterViewSubject.next(message);
  }


  /**
   * Clear the Switch Filter View message.
   */
  public clearSwitchFilterViewMessage() {
    this.switchFilterViewSubject.next();
  }


  /**
   * A method for subscribers of the Switch Filter View message.
   */
  public getSwitchFilterViewMessage(): Observable<ActiveView> {
    return this.switchFilterViewSubject.asObservable();
  }

  /**
   * A method for subscribers of the Populate Form message.
   */
  public getPopulateFormMessage(): Observable<any> {
    return this.populateFormSubject.asObservable();
  }

  public getLoadFormFieldsMessage(): Observable<any> {
    return this.loadFormFieldsSubject.asObservable();
  }
}
