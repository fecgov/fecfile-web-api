import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Subject } from 'rxjs/Subject';
import { ActiveView } from '../transactions.component';

/**
 * A message service for sending and receiving messages of any type
 * between transaction components.
 */
@Injectable({
  providedIn: 'root'
})
export class TransactionsMessageService {
 
  private subject = new Subject<any>();
  private applyFiltersSubject = new Subject<any>();
  private doKeywordFilterSearchSubject = new Subject<any>();
  private editTransactionSubject = new Subject<any>();
  private editDebtSummaryTransactionSubject = new Subject<any>();
  private showTransactionsSubject = new Subject<any>();
  private removeFilterSubject = new Subject<any>();
  private switchFilterViewSubject = new Subject<any>();
  private loadTransactionsSubject = new Subject<any>();
  private removeTagSubject = new Subject<any>();
  private loadDefaultTab = new Subject<any>();
  private clearAllFiltersSubject = new Subject<any>();
  private removeH1TransactionsSubject = new Subject<any>();
  private viewTransactionSubject = new Subject<any>();
  private restoreTransactionsSubject = new Subject<any>();
  private removeHTransactionsSubject = new Subject<any>();
  private reattributeTransactionSubject = new Subject<any>();

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
   * A method for subscribers of Remove Tag message
   */
  public getRemoveTagMessage(): Observable<any> {
    return this.removeTagSubject.asObservable();
  }

  public clearRemoveTagMessage(){
    this.removeTagSubject.next();
  }

  public sendRemoveTagMessage(message:any){
    this.removeTagSubject.next(message);
  }


  /**
   * A method for subscribers of loading default tab
   */
  public getClearAllFiltersMessage(): Observable<any> {
    return this.clearAllFiltersSubject.asObservable();
  }

  public clearClearAllFiltersMessage(){
    this.clearAllFiltersSubject.next();
  }

  public sendClearAllFiltersMessage(message:any){
    this.clearAllFiltersSubject.next(message);
  }

 /**
   * Method to clear All filters and tags. 
   */
  public getLoadDefaultTabMessage(): Observable<any> {
    return this.loadDefaultTab.asObservable();
  }

  public clearLoadDefaultTabMessage(){
    this.loadDefaultTab.next();
  }

  public sendLoadDefaultTabMessage(message:any){
    this.loadDefaultTab.next(message);
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

  public sendEditTransactionMessage(message: any) {
    this.editTransactionSubject.next(message);
  }

  public clearEditTransactionMessage() {
    this.editTransactionSubject.next();
  }

  public getEditTransactionMessage(): Observable<any> {
    return this.editTransactionSubject.asObservable();
  }

  public sendReattributeTransactionMessage(message: any) {
    this.reattributeTransactionSubject.next(message);
  }

  public clearReattributeTransactionMessage() {
    this.reattributeTransactionSubject.next();
  }

  public getReattributeTransactionMessage(): Observable<any> {
    return this.reattributeTransactionSubject.asObservable();
  }

  public sendEditDebtSummaryTransactionMessage(message: any) {
    this.editDebtSummaryTransactionSubject.next(message);
  }

  public clearEditDebtSummaryTransactionMessage() {
    this.editDebtSummaryTransactionSubject.next();
  }

  public getEditDebtSummaryTransactionMessage(): Observable<any> {
    return this.editDebtSummaryTransactionSubject.asObservable();
  }

  public sendShowTransactionsMessage(message: any) {
    this.showTransactionsSubject.next(message);
  }

  public clearShowTransactionsMessage() {
    this.showTransactionsSubject.next();
  }

  public getShowTransactionsMessage(): Observable<any> {
    return this.showTransactionsSubject.asObservable();
  }

  /**
   * A publisher uses this method to send a message to the Transactions Filter
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
   * A publisher uses this method to send a message to the Transactions Filter
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



  public sendLoadTransactionsMessage(message: any) {
    this.loadTransactionsSubject.next(message);
  }

  public clearLoadTransactionsMessage() {
    this.loadTransactionsSubject.next();
  }

  public getLoadTransactionsMessage(): Observable<any> {
    return this.loadTransactionsSubject.asObservable();
  }

  public sendRemoveH1TransactionsMessage(message: any) {
    this.removeH1TransactionsSubject.next(message);
  }

  public clearRemoveH1TransactionsMessage() {
    this.removeH1TransactionsSubject.next();
  }

  public getRemoveH1TransactionsMessage(): Observable<any> {
    return this.removeH1TransactionsSubject.asObservable();
  }

  public sendViewTransactionMessage(message: any) {
    this.viewTransactionSubject.next(message);
  }

  public clearViewTransactionMessage() {
    this.viewTransactionSubject.next();
  }

  public getViewTransactionMessage(): Observable<any> {
    return this.viewTransactionSubject.asObservable();
  }

  public sendRestoreTransactionsMessage(message: any) {
    this.restoreTransactionsSubject.next(message);
  }

  public clearRestoreTransactionsMessage() {
    this.restoreTransactionsSubject.next();
  }

  public getRestoreTransactionsMessage(): Observable<any> {
    return this.restoreTransactionsSubject.asObservable();
  }

  public sendRemoveHTransactionsMessage(message: any) {
    this.removeHTransactionsSubject.next(message);
  }

  public clearRemoveHTransactionsMessage() {
    this.removeHTransactionsSubject.next();
  }

  public getRemoveHTransactionsMessage(): Observable<any> {
    return this.removeHTransactionsSubject.asObservable();
  }

}
