import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class MessageService {

    private _subject: BehaviorSubject<any> = new BehaviorSubject<any>('');
    private _populateChildComponentsubject: BehaviorSubject<any> = new BehaviorSubject<any>('');
    private _rollbackChangesSubject: BehaviorSubject<any> = new BehaviorSubject<any>('');
    private _updateReportTypeToReportType: BehaviorSubject<any> = new BehaviorSubject<any>('');
    private _updateReportTypeToReportTypeSidebar: BehaviorSubject<any> = new BehaviorSubject<any>('');
    

    constructor() { }

    /**
     * Sends the message to a component.
     *
     * @param      {Any}  message  The message
     */
    public sendMessage(message: any) {
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

    /**
     * Sends the message to a component.
     *
     * @param      {Any}  message  The message
     */
    public sendPopulateChildComponentMessage(message: any) {
        this._populateChildComponentsubject.next(message);
    }

    /**
     * Clears the message if needed.
     *
     */
    public clearPopulateChildComponentMessage() {
        this._populateChildComponentsubject.next('');
    }

    /**
     * Gets the message.
     *
     * @return     {Observable}  The message.
     */
    public getPopulateChildComponentMessage(): Observable<any> {
        return this._populateChildComponentsubject.asObservable();
    }

    /**
     * Sends the message to a component.
     *
     * @param      {Any}  message  The message
     */
    public sendRollbackChangesMessage(message: any) {
        this._rollbackChangesSubject.next(message);
    }

    /**
     * Clears the message if needed.
     *
     */
    public clearRollbackChangesMessage() {
        this._rollbackChangesSubject.next('');
    }

    /**
     * Gets the message.
     *
     * @return     {Observable}  The message.
     */
    public getRollbackChangesMessage(): Observable<any> {
        return this._rollbackChangesSubject.asObservable();
    }

        /**
     * Sends the message to a component.
     *
     * @param      {Any}  message  The message
     */
    public sendUpdateReportTypeMessageToReportType(message: any) {
        this._updateReportTypeToReportType.next(message);
    }

        /**
     * Sends the message to a component.
     *
     * @param      {Any}  message  The message
     */
    public sendUpdateReportTypeMessageToReportTypeSidebar(message: any) {
        this._updateReportTypeToReportTypeSidebar.next(message);
    }

    /**
     * Clears the message if needed.
     *
     */
    public clearUpdateReportTypeMessageToReportType() {
        this._updateReportTypeToReportType.next('');
    }
    
    /**
     * Clears the message if needed.
     *
     */
    public clearUpdateReportTypeMessageToReportTypeSidebar() {
        this._updateReportTypeToReportTypeSidebar.next('');
    }    

    /**
     * Gets the message.
     *
     * @return     {Observable}  The message.
     */
    public getUpdateReportTypeMessageToReportType(): Observable<any> {
        return this._updateReportTypeToReportType.asObservable();
    }

    /**
     * Gets the message.
     *
     * @return     {Observable}  The message.
     */
    public getUpdateReportTypeMessageToReportTypeSidebar(): Observable<any> {
        return this._updateReportTypeToReportTypeSidebar.asObservable();
    }

}
