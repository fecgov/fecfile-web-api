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
  private clearFormSubject = new Subject<any>();
  private loadFormFieldsSubject = new Subject<any>();
  private storeParentModelSubject = new Subject<any>();
  private populateHiddenFieldsSubject = new Subject<any>();
  private clearFormFieldsForRedesignationSubject = new Subject<any>();


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

   /**
   * Used by the F3X parent component to inform the child component
   * to pre-populate the form's hidden fields with the given data.
   *
   * @param message
   */
  public sendPopulateHiddenFieldsMessage(message: any) {
    this.populateHiddenFieldsSubject.next(message);
  }


  /**
   * Clear the Populate form's hidden fields.
   */
  public clearPopulateHiddenFieldsMessage() {
    this.populateHiddenFieldsSubject.next();
  }


  /**
   * A method for subscribers of the Populate form's hidden fields.
   */
  public getPopulateHiddenFieldsMessage(): Observable<any> {
    return this.populateHiddenFieldsSubject.asObservable();
  }

  /**
   * Used by the Transaction Type component to inform the Save Form (Individual Receipt)
   * component to clear any form fields previously set.
   *
   * @param message
   */
  public sendInitFormMessage(message: any) {
    this.clearFormSubject.next(message);
  }


  /**
   * Clear the Init Form Form message.
   */
  public clearInitFormMessage() {
    this.clearFormSubject.next();
  }


  /**
   * A method for subscribers of the Init Form message.
   */
  public getInitFormMessage(): Observable<any> {
    return this.clearFormSubject.asObservable();
  }

  /**
   * Send a message to Load the form fields.
   *
   * @param message
   */
  public sendLoadFormFieldsMessage(message: any) {
    this.loadFormFieldsSubject.next(message);
  }


  /**
   * Clear the Load Form Fields message.
   */
  public clearLoadFormFieldsMessage() {
    this.loadFormFieldsSubject.next();
  }


  /**
   * A method for subscribers of the Load Form Fields message.
   */
  public getLoadFormFieldsMessage(): Observable<any> {
    return this.loadFormFieldsSubject.asObservable();
  }

  /**
   * Send a message with the parent transaction ID
   * to the child sub-schedule of a different type.
   *
   * @param message
   */
  public sendParentModelMessage(message: any) {
    this.storeParentModelSubject.next(message);
  }


  /**
   * Clear the parent model message.
   */
  public clearParentModelMessage() {
    this.storeParentModelSubject.next();
  }


  /**
   * A method for subscribers of the store parent model message.
   */
  public getParentModelMessage(): Observable<any> {
    return this.storeParentModelSubject.asObservable();
  }

  public sendClearFormValuesForRedesignationMessage(message: any) {
    this.clearFormFieldsForRedesignationSubject.next(message);
  }


  /**
   * Clear the Populate Form message.
   */
  public clearClearFormValuesForRedesignationMessage() {
    this.clearFormFieldsForRedesignationSubject.next();
  }


  /**
   * A method for subscribers of the Populate Form message.
   */
  public getClearFormValuesForRedesignationMessage(): Observable<any> {
    return this.clearFormFieldsForRedesignationSubject.asObservable();
  }

}
